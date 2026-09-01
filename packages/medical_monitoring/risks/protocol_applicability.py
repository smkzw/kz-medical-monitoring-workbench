"""Protocol version applicability and control-point routing."""

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
from .protocol_contracts import (
    _canonical_sorted, _date_precision, _day_date, _validate_nonempty,
)

def _version_covers_event(
    version: ProtocolVersionRecord, event_date: datetime.date,
    version_lo: datetime.date, version_hi: Optional[datetime.date],
) -> bool:
    if version_lo > event_date:
        return False
    if version_hi is not None and event_date > version_hi:
        return False
    return True


def _version_supported_at_enrollment(
    version: ProtocolVersionRecord, enroll_day: datetime.date,
    adoption_lo: Optional[datetime.date],
) -> bool:
    """True when a predecessor version was in force at the subject's
    enrollment time: approved, its effective interval covers the day and
    the site adoption (when given) had started (§2.3
    existing_continue_old).  The version's own ``effective_end`` may lie
    before the evaluated event -- the explicit transition keeps existing
    subjects on the old version, so project-wide end dates never by
    themselves force the subject onto the amendment."""
    if not version.approval_date.strip():
        return False
    lo = _day_date(version.effective_start)
    if lo is None or enroll_day < lo:
        return False
    hi = (_day_date(version.effective_end)
          if version.effective_end.strip() else None)
    if hi is not None and enroll_day > hi:
        return False
    if adoption_lo is not None and enroll_day < adoption_lo:
        return False
    return True


def resolve_protocol_applicability(
    *,
    subject_ref: str, site_ref: str, event_anchor_kind: str,
    event_anchor_date: str,
    versions: Sequence[ProtocolVersionRecord],
    site_adoption_start: str = "", site_adoption_end: str = "",
    adoption_start_inclusive: Optional[bool] = None,
    adoption_end_inclusive: Optional[bool] = None,
    subject_enrollment_date: str = "",
    subject_consent_date: str = "",
    subject_randomization_date: str = "",
    subject_first_dose_date: str = "",
    cohort: str = "", phase: str = "", arm: str = "",
    treatment_role: str = "", control_point_applicability: str = "",
    event_time_rule_scope: str = "",
    stable_source_content_key: str = "",
    source_locators: Sequence[SourceLocator] = (),
) -> ProtocolApplicabilityDecision:
    """Resolve the unique active protocol version (§2.3 fixed order).

    1. Explicit protocol/amendment link (the caller may pass exactly one
       version; then its effective interval still must cover the event).
    2. Ethics/authority approval and site adoption dates.
    3. Amendment transition scope -- assessed BEFORE the feasible-count
       shortcut (corrective 03): ``all_switch`` keeps the interval/
       adoption behaviour only without a re-consent dependency;
       ``new_enrollment_only`` requires a day-comparable enrollment date
       (missing -> not_evaluable) and grandfathers pre-amendment
       enrollees; ``existing_continue_old`` keeps the unique predecessor
       supported at the subject's enrollment time (zero -> not_evaluable,
       two -> boundary, never the amendment); ``next_visit_or_reconsent``
       or any ``re_consent_required=True`` and ``undetermined`` return one
       not_evaluable gate -- the subject is never pushed onto a newer
       version merely because its effective/site interval covers the event.
    4. Subject event times (consent/randomization/first dose/enrollment).
    5. Cohort/phase/arm/treatment role and control-point applicability.
    6. Only when all conditions yield exactly one active version.

    Never defaults to the latest version or the event-nearest version.
    Missing/conflicting key dates -> ``not_evaluable``; two or more
    feasible versions with support -> ``multi_feasible_boundary``.
    """
    if event_anchor_kind not in ANCHOR_KINDS:
        raise ProtocolSliceError(
            f"event_anchor_kind={event_anchor_kind!r} invalid")
    if not versions:
        raise ProtocolSliceError("at least one ProtocolVersionRecord required")
    if not stable_source_content_key.strip():
        raise ProtocolSliceError(
            "resolve_protocol_applicability requires a non-empty "
            "stable_source_content_key: the decision identity must stay "
            "attached to stable source lineage (run/snapshot/revision "
            "remain excluded)")
    event_date = _day_date(event_anchor_date)
    missing_key_dates = not event_date or not site_adoption_start.strip()

    # Site adoption interval (day precision required for a determinate
    # adoption check; partial adoption dates stay boundary).
    adoption_lo = _day_date(site_adoption_start)
    adoption_hi = _day_date(site_adoption_end)
    adoption_partial = (
        (bool(site_adoption_start.strip())
         and _date_precision(site_adoption_start) != PRECISION_DAY)
        or (bool(site_adoption_end.strip())
            and _date_precision(site_adoption_end) != PRECISION_DAY)
    )
    adoption_boundary = (
        adoption_partial
        or (event_date is not None and adoption_lo is not None
            and event_date == adoption_lo
            and adoption_start_inclusive is None)
        or (event_date is not None and adoption_hi is not None
            and event_date == adoption_hi
            and adoption_end_inclusive is None)
    )

    def site_covers(day: datetime.date) -> bool:
        if adoption_lo is not None:
            if adoption_start_inclusive is False:
                if day <= adoption_lo:
                    return False
            elif day < adoption_lo:
                return False
        if adoption_hi is not None:
            if adoption_end_inclusive is False:
                if day >= adoption_hi:
                    return False
            elif day > adoption_hi:
                return False
        return True

    def _version_fingerprint(version: ProtocolVersionRecord) -> str:
        return feasible_version_fingerprint(
            protocol_id=version.protocol_id,
            protocol_version=version.protocol_version,
            amendment_id_or_hash=version.amendment_id_or_hash,
            approval_date=version.approval_date,
            effective_start=version.effective_start,
            effective_end=version.effective_end,
            transition_scope=version.transition_scope,
            new_enrollment_only=version.new_enrollment_only,
            re_consent_required=version.re_consent_required,
            rule_content_hash=version.rule_content_hash,
            extraction_hash=version.extraction_hash,
            cohort=cohort, phase=phase, arm=arm,
            treatment_role=treatment_role,
            control_point_applicability=control_point_applicability)

    base_feasible: List[ProtocolVersionRecord] = []
    for version in versions:
        if not version.approval_date.strip():
            continue  # unapproved version is not feasible
        v_lo = _day_date(version.effective_start)
        v_hi = (_day_date(version.effective_end)
                if version.effective_end.strip() else None)
        if v_lo is None:
            continue
        if event_date is not None and not _version_covers_event(
                version, event_date, v_lo, v_hi):
            continue
        if event_date is not None and not site_covers(event_date):
            continue
        # Version-level site adoption (challenge 11: the latest amendment
        # may not yet be enabled at the centre).  When a version declares
        # its own adoption interval it must additionally cover the event;
        # otherwise the shared site adoption interval already governs.
        if version.site_adoption_start.strip():
            v_lo = _day_date(version.site_adoption_start)
            v_hi = (_day_date(version.site_adoption_end)
                    if version.site_adoption_end.strip() else None)
            if v_lo is None or event_date is None or event_date < v_lo:
                continue
            if v_hi is not None and event_date > v_hi:
                continue
        base_feasible.append(version)

    # Base feasible-version fingerprints (event/site coverage only) are
    # preserved in every gate's lineage/context; the §2.3 transition
    # assessment below may then restrict or reject them.
    base_fps = _canonical_sorted(
        [_version_fingerprint(v) for v in base_feasible])

    # ------------------------------------------------------------------
    # §2.3 transition-scope assessment (fail closed, BEFORE the
    # feasible-count shortcut): a subject is never pushed onto a newer
    # version merely because its effective/site interval covers the
    # event.  Missing/conflicting transition inputs yield one
    # not_evaluable/boundary applicability gate and no candidate,
    # risk or Query downstream (corrective 03).
    # ------------------------------------------------------------------
    feasible: List[ProtocolVersionRecord] = base_feasible
    gate_status: Optional[str] = None
    gate_rationale = ""
    gate_scope = ""
    gate_fps: Tuple[str, ...] = base_fps
    gate_new_enrollment_only: Optional[bool] = None
    gate_re_consent: Optional[bool] = None
    chosen_old: Optional[ProtocolVersionRecord] = None

    def re_consent_dependent(version: ProtocolVersionRecord) -> bool:
        return (version.re_consent_required is True
                or version.transition_scope
                == TRANSITION_NEXT_VISIT_OR_RECONSENT)

    reconsent = [v for v in base_feasible if re_consent_dependent(v)]
    if reconsent:
        # The schema does not distinguish original consent from
        # re-consent and carries no versioned next-visit/re-consent
        # trigger policy: subject_consent_date is never reinterpreted as
        # re-consent and no earliest/AND/OR semantics are invented.
        gate_status = APPLICABILITY_NOT_EVALUABLE
        gate_rationale = (
            "修订依赖重新知情/下次访视触发切换，当前输入无法区分原始知情"
            "与重新知情且缺少版本化触发策略，适用性无法评价")
        gate_scope = reconsent[0].transition_scope
        gate_re_consent = True
    else:
        undetermined = [
            v for v in base_feasible
            if v.transition_scope == TRANSITION_UNDETERMINED]
        if undetermined:
            gate_status = APPLICABILITY_NOT_EVALUABLE
            gate_rationale = (
                "修订过渡范围未声明，无法确定新旧版本的适用规则，"
                "适用性无法评价")
            gate_scope = undetermined[0].transition_scope
        else:
            new_only = [
                v for v in base_feasible
                if v.new_enrollment_only is True
                or v.transition_scope == TRANSITION_NEW_ENROLLMENT_ONLY]
            if new_only:
                enroll_day = _day_date(subject_enrollment_date)
                if enroll_day is None:
                    # A day-comparable enrollment date is mandatory for a
                    # new-enrollment-only amendment; missing input is
                    # never silently admitted as a unique version.
                    gate_status = APPLICABILITY_NOT_EVALUABLE
                    gate_rationale = (
                        "仅新入组适用的修订缺少可比较的入组日期，"
                        "适用性无法评价")
                    gate_scope = new_only[0].transition_scope
                    gate_new_enrollment_only = True
                else:
                    # Grandfathering: a subject enrolled before the
                    # amendment start excludes it; post-start enrollment
                    # may admit it.
                    feasible = [
                        v for v in base_feasible
                        if not (
                            (v.new_enrollment_only is True
                             or v.transition_scope
                             == TRANSITION_NEW_ENROLLMENT_ONLY)
                            and _day_date(v.effective_start) is not None
                            and enroll_day < _day_date(v.effective_start))]
            if gate_status is None:
                existing_old = [
                    v for v in feasible
                    if v.transition_scope
                    == TRANSITION_EXISTING_CONTINUE_OLD]
                if existing_old:
                    gate_scope = existing_old[0].transition_scope
                    enroll_day = _day_date(subject_enrollment_date)
                    if enroll_day is None:
                        gate_status = APPLICABILITY_NOT_EVALUABLE
                        gate_rationale = (
                            "既有受试者延续旧版需要可比较的入组日期，"
                            "入组日期缺失，适用性无法评价")
                    else:
                        predecessors = [
                            v for v in versions
                            if v.transition_scope
                            != TRANSITION_EXISTING_CONTINUE_OLD]
                        supported = [
                            v for v in predecessors
                            if _version_supported_at_enrollment(
                                v, enroll_day, adoption_lo)]
                        if len(supported) == 1:
                            chosen_old = supported[0]
                        elif not supported:
                            gate_status = APPLICABILITY_NOT_EVALUABLE
                            gate_rationale = (
                                "既有受试者延续旧版，但入组时点有来源支持"
                                "的旧版本不足一个，适用性无法评价")
                        else:
                            gate_status = (
                                APPLICABILITY_MULTI_FEASIBLE_BOUNDARY)
                            gate_rationale = (
                                "多个既有版本在受试者入组时点均有来源"
                                "支持，适用性存在边界")
                            gate_fps = _canonical_sorted(
                                [_version_fingerprint(v)
                                 for v in supported])

    fps = _canonical_sorted(
        [_version_fingerprint(v) for v in feasible])

    if chosen_old is not None:
        # existing_continue_old: exactly one predecessor is supported at
        # the subject's enrollment time -- the old version continues even
        # after the amendment's project effective start.
        v = chosen_old
        return ProtocolApplicabilityDecision(
            subject_ref=subject_ref, site_ref=site_ref,
            decision_time_anchor=event_anchor_kind,
            decision_time_anchor_date=event_anchor_date,
            decision_status=APPLICABILITY_UNIQUE_ACTIVE,
            protocol_id=v.protocol_id, protocol_version=v.protocol_version,
            amendment_id_or_hash=v.amendment_id_or_hash,
            ethics_or_authority_approval_date=v.approval_date,
            effective_start=v.effective_start,
            effective_end=v.effective_end,
            site_activation_or_adoption_start=site_adoption_start,
            site_activation_or_adoption_end=site_adoption_end,
            amendment_transition_scope=gate_scope,
            new_enrollment_only=v.new_enrollment_only,
            re_consent_requirement=v.re_consent_required,
            cohort=cohort, phase=phase, arm=arm,
            treatment_role=treatment_role,
            control_point_applicability=control_point_applicability,
            event_time_rule_scope=event_time_rule_scope,
            source_locators=tuple(source_locators),
            feasible_version_fingerprints=_canonical_sorted(
                [_version_fingerprint(v)]),
            stable_source_content_key=stable_source_content_key,
            rationale=(
                f"既有受试者按过渡条款延续旧版，唯一适用版本 "
                f"{v.protocol_version}"))

    if gate_status is not None:
        # One subject-level applicability gate: not_evaluable (missing /
        # insufficient transition evidence) or multi_feasible_boundary
        # (two supported predecessors).  Never a unique version, and no
        # candidate/risk/Query is generated downstream.
        return ProtocolApplicabilityDecision(
            subject_ref=subject_ref, site_ref=site_ref,
            decision_time_anchor=event_anchor_kind,
            decision_time_anchor_date=event_anchor_date,
            decision_status=gate_status,
            protocol_id=versions[0].protocol_id,
            amendment_id_or_hash=versions[0].amendment_id_or_hash,
            site_activation_or_adoption_start=site_adoption_start,
            site_activation_or_adoption_end=site_adoption_end,
            amendment_transition_scope=gate_scope,
            new_enrollment_only=gate_new_enrollment_only,
            re_consent_requirement=gate_re_consent,
            cohort=cohort, phase=phase, arm=arm,
            treatment_role=treatment_role,
            control_point_applicability=control_point_applicability,
            event_time_rule_scope=event_time_rule_scope,
            source_locators=tuple(source_locators),
            feasible_version_fingerprints=gate_fps,
            stable_source_content_key=stable_source_content_key,
            rationale=gate_rationale)

    if missing_key_dates or adoption_boundary:
        status = (
            APPLICABILITY_NOT_EVALUABLE if missing_key_dates
            else APPLICABILITY_MULTI_FEASIBLE_BOUNDARY)
        rationale = (
            "批准/启用/事件关键日期缺失或冲突，无法确定适用版本"
            if missing_key_dates
            else "中心启用日期与事件时点端点未定义，适用性存在边界")
        return ProtocolApplicabilityDecision(
            subject_ref=subject_ref, site_ref=site_ref,
            decision_time_anchor=event_anchor_kind,
            decision_time_anchor_date=event_anchor_date,
            decision_status=status,
            protocol_id=versions[0].protocol_id,
            amendment_id_or_hash=versions[0].amendment_id_or_hash,
            site_activation_or_adoption_start=site_adoption_start,
            site_activation_or_adoption_end=site_adoption_end,
            amendment_transition_scope=versions[0].transition_scope,
            cohort=cohort, phase=phase, arm=arm,
            treatment_role=treatment_role,
            control_point_applicability=control_point_applicability,
            event_time_rule_scope=event_time_rule_scope,
            source_locators=tuple(source_locators),
            feasible_version_fingerprints=fps,
            stable_source_content_key=stable_source_content_key,
            rationale=rationale)

    if len(feasible) == 1:
        v = feasible[0]
        return ProtocolApplicabilityDecision(
            subject_ref=subject_ref, site_ref=site_ref,
            decision_time_anchor=event_anchor_kind,
            decision_time_anchor_date=event_anchor_date,
            decision_status=APPLICABILITY_UNIQUE_ACTIVE,
            protocol_id=v.protocol_id, protocol_version=v.protocol_version,
            amendment_id_or_hash=v.amendment_id_or_hash,
            ethics_or_authority_approval_date=v.approval_date,
            effective_start=v.effective_start,
            effective_end=v.effective_end,
            site_activation_or_adoption_start=site_adoption_start,
            site_activation_or_adoption_end=site_adoption_end,
            amendment_transition_scope=v.transition_scope,
            new_enrollment_only=v.new_enrollment_only,
            re_consent_requirement=v.re_consent_required,
            cohort=cohort, phase=phase, arm=arm,
            treatment_role=treatment_role,
            control_point_applicability=control_point_applicability,
            event_time_rule_scope=event_time_rule_scope,
            source_locators=tuple(source_locators),
            feasible_version_fingerprints=fps,
            stable_source_content_key=stable_source_content_key,
            rationale=f"唯一适用版本 {v.protocol_version}")

    if len(feasible) > 1:
        return ProtocolApplicabilityDecision(
            subject_ref=subject_ref, site_ref=site_ref,
            decision_time_anchor=event_anchor_kind,
            decision_time_anchor_date=event_anchor_date,
            decision_status=APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
            protocol_id=versions[0].protocol_id,
            amendment_id_or_hash=versions[0].amendment_id_or_hash,
            site_activation_or_adoption_start=site_adoption_start,
            site_activation_or_adoption_end=site_adoption_end,
            amendment_transition_scope=versions[0].transition_scope,
            cohort=cohort, phase=phase, arm=arm,
            treatment_role=treatment_role,
            control_point_applicability=control_point_applicability,
            event_time_rule_scope=event_time_rule_scope,
            source_locators=tuple(source_locators),
            feasible_version_fingerprints=fps,
            stable_source_content_key=stable_source_content_key,
            rationale=(
                f"{len(feasible)} 个可行方案版本均有来源支持，"
                f"无法唯一确定适用版本"))

    # Zero feasible versions with complete inputs is an inability to
    # identify an applicable version -- not a supported competing
    # interpretation: not_evaluable, one subject-level gate, zero
    # candidate/risk/Query (§2.3, §5).
    return ProtocolApplicabilityDecision(
        subject_ref=subject_ref, site_ref=site_ref,
        decision_time_anchor=event_anchor_kind,
        decision_time_anchor_date=event_anchor_date,
        decision_status=APPLICABILITY_NOT_EVALUABLE,
        protocol_id=versions[0].protocol_id,
        amendment_id_or_hash=versions[0].amendment_id_or_hash,
        site_activation_or_adoption_start=site_adoption_start,
        site_activation_or_adoption_end=site_adoption_end,
        amendment_transition_scope=versions[0].transition_scope,
        cohort=cohort, phase=phase, arm=arm,
        treatment_role=treatment_role,
        control_point_applicability=control_point_applicability,
        event_time_rule_scope=event_time_rule_scope,
        source_locators=tuple(source_locators),
        feasible_version_fingerprints=fps,
        stable_source_content_key=stable_source_content_key,
        rationale="无任何方案版本覆盖该事件时点，适用性无法确定")


# ---------------------------------------------------------------------------
# Routing (§3.2) -- closed owner decision table
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolControlRoutingRecord:
    """Versioned routing record for one control point/component.

    Routing precedes expected-set generation.  Producer-owned control
    points never enter the D04 medical expected-set; they only surface as
    typed producer references in the compliance overview.  When the owner
    cannot be uniquely determined, exactly one ``protocol_routing``
    not_evaluable gate is generated -- never one risk per competing
    domain (challenge 67).
    """

    control_point_id: str
    owner_domain: str
    owner_signal_type: str
    routing_rule_version: str
    routing_rule_hash: str
    producer_unit_id: str = ""
    routing_gap: str = ""
    component_id: str = ""
    source_locators: Tuple[SourceLocator, ...] = ()
    candidate_owners: Tuple[str, ...] = ()
    decision_rationale: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.control_point_id,
                           "ProtocolControlRoutingRecord.control_point_id")
        if self.owner_domain not in OWNER_DOMAINS:
            raise ProtocolSliceError(
                f"owner_domain={self.owner_domain!r} invalid")
        _validate_nonempty(self.owner_signal_type,
                           "ProtocolControlRoutingRecord.owner_signal_type")
        if self.owner_domain == OWNER_D04:
            raise ProtocolSliceError(
                "a routing record must not point a control point back to "
                "D04 itself; D04-native points are evaluated, not routed")
        has_producer = bool(self.producer_unit_id.strip())
        has_gap = bool(self.routing_gap.strip())
        if self.owner_domain == OWNER_UNRESOLVED:
            if not self.candidate_owners:
                raise ProtocolSliceError(
                    "owner_unresolved routing requires candidate_owners")
            if not has_gap or has_producer:
                raise ProtocolSliceError(
                    "owner_unresolved routing requires a routing_gap and "
                    "no producer_unit_id")
        else:
            if has_producer == has_gap:
                raise ProtocolSliceError(
                    "routed control point requires exactly one of "
                    "producer_unit_id or routing_gap (§11: every delegated "
                    "item must tie to an owner expected unit or a routing "
                    "gap, never both)")
        object.__setattr__(self, "source_locators",
                           tuple(self.source_locators))
        object.__setattr__(self, "candidate_owners",
                           _canonical_sorted(self.candidate_owners))


def route_control_point(
    control_point_type: str, claim_kind: str = CLAIM_OTHER,
) -> str:
    """Closed routing decision table (§3.2).

    CM/合并用药禁限用 claim -> D02; 研究药计划/实际暴露、剂量或给药
    动作 claim -> D03; 名义/实际访视、检查/评估/样本计划和时窗 claim ->
    D05; 知情/筛选/随机/入组时序、入排资格、非计划型前置动作及退出
    触发条件 claim -> D04; 多表关系本身 -> D08.
    """
    if control_point_type == CONTROL_PROHIBITED_OR_RESTRICTED_TREATMENT:
        return OWNER_D02
    if control_point_type == CONTROL_DOSE_OR_TREATMENT_MANAGEMENT:
        return OWNER_D03
    if control_point_type == CONTROL_REQUIRED_PROCEDURE_OR_ASSESSMENT:
        if claim_kind == CLAIM_VISIT_WINDOW:
            return OWNER_D05
        return OWNER_D04
    if control_point_type in (
            CONTROL_INCLUSION, CONTROL_EXCLUSION,
            CONTROL_DISCONTINUATION_OR_WITHDRAWAL,
            CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT):
        return OWNER_D04
    if control_point_type == CONTROL_OTHER_PROTOCOL_REQUIREMENT:
        if claim_kind == CLAIM_CONCOMITANT_MEDICATION:
            return OWNER_D02
        if claim_kind == CLAIM_IP_DOSING_ACTION:
            return OWNER_D03
        if claim_kind == CLAIM_VISIT_WINDOW:
            return OWNER_D05
        if claim_kind == CLAIM_MULTI_TABLE_RELATION:
            return OWNER_D08
        return OWNER_D04
    raise ProtocolSliceError(
        f"cannot route unknown control point type {control_point_type!r}")


@dataclass(frozen=True)
class ProtocolDelegatedControlPoint:
    """One producer-owned control point excluded from the D04 expected-set
    (§11).  Each item must tie to an exact owner expected unit
    (``producer_unit_id``) or a ``routing_gap``."""

    control_point_id: str
    owner_domain: str
    owner_signal_type: str
    producer_unit_id: str = ""
    routing_gap: str = ""
    component_id: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.control_point_id,
                           "ProtocolDelegatedControlPoint.control_point_id")
        if self.owner_domain not in (
                OWNER_D02, OWNER_D03, OWNER_D05, OWNER_D08):
            raise ProtocolSliceError(
                f"delegated control point owner_domain="
                f"{self.owner_domain!r} must be a producer domain "
                f"(D02/D03/D05/D08), never D04/self or owner_unresolved")
        has_producer = bool(self.producer_unit_id.strip())
        has_gap = bool(self.routing_gap.strip())
        if has_producer == has_gap:
            raise ProtocolSliceError(
                "delegated control point requires exactly one of "
                "producer_unit_id or routing_gap")
