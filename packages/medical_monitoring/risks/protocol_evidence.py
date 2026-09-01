"""Protocol evidence requirements and expected-set expansion."""

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
    _GAP_LABELS, _canonical_sorted, _date_precision, _day_date, _freeze_tuple,
    _parse_decimal, _validate_nonempty, _validate_optional_str,
)
from .protocol_applicability import *

@dataclass(frozen=True)
class EvaluationWindowSpec:
    """Versioned evaluation window for one control point (§5)."""

    eval_anchor_kind: str = ANCHOR_OTHER
    window_start: str = ""
    window_end: str = ""
    precision: str = ""
    endpoint_inclusivity: str = ""

    def __post_init__(self) -> None:
        if self.eval_anchor_kind not in ANCHOR_KINDS:
            raise ProtocolSliceError(
                f"eval_anchor_kind={self.eval_anchor_kind!r} invalid")
        if self.precision not in ("", *PRECISIONS):
            raise ProtocolSliceError(
                f"precision={self.precision!r} invalid")
        if self.endpoint_inclusivity not in ("", *INCLUSIVITIES):
            raise ProtocolSliceError(
                f"endpoint_inclusivity={self.endpoint_inclusivity!r} invalid")


# ---------------------------------------------------------------------------
# Evidence requirements and bindings (§4)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RuleEvidenceRequirement:
    """One per-control-point evidence requirement (§4.2)."""

    requirement_id: str
    control_point_id: str
    component_id: str
    required_evidence_roles: Tuple[str, ...]
    alternate_evidence_roles: Tuple[str, ...] = ()
    coverage_complete_required: bool = True
    retest_or_confirmation_policy: str = ""
    rule_lineage: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.requirement_id,
                           "RuleEvidenceRequirement.requirement_id")
        _validate_nonempty(self.control_point_id,
                           "RuleEvidenceRequirement.control_point_id")
        req = _freeze_tuple(self.required_evidence_roles,
                            "RuleEvidenceRequirement.required_evidence_roles")
        if not req:
            raise ProtocolSliceError(
                "RuleEvidenceRequirement requires required_evidence_roles")
        object.__setattr__(self, "required_evidence_roles", req)
        object.__setattr__(
            self, "alternate_evidence_roles",
            _freeze_tuple(self.alternate_evidence_roles,
                          "RuleEvidenceRequirement.alternate_evidence_roles"))
        if not isinstance(self.coverage_complete_required, bool):
            raise ProtocolSliceError(
                "RuleEvidenceRequirement.coverage_complete_required must be "
                "a literal bool")
        _validate_optional_str(
            self.rule_lineage, "RuleEvidenceRequirement.rule_lineage")


def build_rule_evidence_requirement(
    *,
    control_point_id: str,
    component_id: str,
    required_evidence_roles: Sequence[str],
    alternate_evidence_roles: Sequence[str] = (),
    coverage_complete_required: bool = True,
    retest_or_confirmation_policy: str = "",
    rule_lineage: str = D04_RULE_LINEAGE_DEFAULT,
) -> RuleEvidenceRequirement:
    """Deterministic public builder for one D04 evidence requirement (§4.2).

    The requirement id is content-addressed over the full semantic payload
    (control point/component identity, required/alternate roles,
    completeness requirement, retest/confirmation policy and rule
    lineage): identical accepted inputs replay to the identical id, and
    any semantic evidence-requirement change produces a new id.  Required
    identity fields and the literal-boolean completeness requirement fail
    closed -- no silent defaults, no inferred role list.
    """
    if not control_point_id.strip():
        raise ProtocolSliceError(
            "build_rule_evidence_requirement requires control_point_id")
    if not component_id.strip():
        raise ProtocolSliceError(
            "build_rule_evidence_requirement requires component_id")
    req_roles = _canonical_sorted(required_evidence_roles)
    if not req_roles:
        raise ProtocolSliceError(
            "RuleEvidenceRequirement requires required_evidence_roles")
    alt_roles = _canonical_sorted(alternate_evidence_roles)
    if not isinstance(coverage_complete_required, bool):
        raise ProtocolSliceError(
            "RuleEvidenceRequirement.coverage_complete_required must be a "
            "literal bool")
    lineage = rule_lineage if rule_lineage.strip() else D04_RULE_LINEAGE_DEFAULT
    requirement_id = "d04-req-" + content_hash({
        "control_point_id": control_point_id,
        "component_id": component_id,
        "required_evidence_roles": list(req_roles),
        "alternate_evidence_roles": list(alt_roles),
        "coverage_complete_required": coverage_complete_required,
        "retest_or_confirmation_policy": retest_or_confirmation_policy,
        "rule_lineage": lineage,
    })
    return RuleEvidenceRequirement(
        requirement_id=requirement_id,
        control_point_id=control_point_id,
        component_id=component_id,
        required_evidence_roles=req_roles,
        alternate_evidence_roles=alt_roles,
        coverage_complete_required=coverage_complete_required,
        retest_or_confirmation_policy=retest_or_confirmation_policy,
        rule_lineage=lineage)


def expand_rule_evidence_requirements(
    control_point: ProtocolControlPoint,
    components: Optional[Mapping[str, ProtocolComponent]] = None,
    rule_lineage: str = D04_RULE_LINEAGE_DEFAULT,
) -> Tuple[RuleEvidenceRequirement, ...]:
    """Generate exactly one RuleEvidenceRequirement per atomic root and per
    package component (§4.2/§5).

    The atomic root's synthesized component carries the control point id,
    so its single requirement uses ``component_id == control_point_id``.
    Package roots generate one requirement per official component in
    ``component_ids`` order.  The completeness requirement is always
    ``True``: §4.3/§6.1/§6.2 require the required roles' accepted-source
    coverage to be complete for any determinate verdict, and the frozen
    rule schema carries no per-rule completeness override.  Producer-owned
    /delegated control points and applicability/routing gates never
    fabricate D04 requirements here.
    """
    if not isinstance(control_point, ProtocolControlPoint):
        raise ProtocolSliceError(
            "expand_rule_evidence_requirements requires a "
            "ProtocolControlPoint")
    lineage = rule_lineage if rule_lineage.strip() else D04_RULE_LINEAGE_DEFAULT
    if control_point.evaluation_root_kind == NODE_ATOMIC:
        rule = control_point.structured_rule
        if rule is None:
            raise ProtocolSliceError(
                "atomic control point requires structured_rule for its "
                "evidence requirement")
        return (build_rule_evidence_requirement(
            control_point_id=control_point.control_point_id,
            component_id=control_point.control_point_id,
            required_evidence_roles=rule.required_evidence_roles,
            alternate_evidence_roles=rule.alternate_evidence_roles,
            coverage_complete_required=True,
            retest_or_confirmation_policy=rule.retest_or_confirmation_policy,
            rule_lineage=lineage),)
    component_map = components or {}
    reqs: List[RuleEvidenceRequirement] = []
    for cid in control_point.component_ids:
        comp = component_map.get(cid)
        if comp is None:
            raise ProtocolSliceError(
                f"package {control_point.control_point_id} references "
                f"unknown component {cid!r} for evidence requirement")
        if not isinstance(comp, ProtocolComponent):
            raise ProtocolSliceError(
                f"package component {cid!r} must be a ProtocolComponent, "
                f"got {type(comp).__name__}")
        rule = comp.structured_rule
        reqs.append(build_rule_evidence_requirement(
            control_point_id=control_point.control_point_id,
            component_id=cid,
            required_evidence_roles=rule.required_evidence_roles,
            alternate_evidence_roles=rule.alternate_evidence_roles,
            coverage_complete_required=True,
            retest_or_confirmation_policy=rule.retest_or_confirmation_policy,
            rule_lineage=lineage))
    return tuple(reqs)


CONFIRMATION_CONFIRMED = "confirmed"
CONFIRMATION_UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class RuleEvidenceBinding:
    """One identity/time-matched evidence binding (§4.2).

    The binding must carry subject/site, official rule id/component,
    source role, stable source event key, value/unit/date/precision,
    source locator, accepted revision, relationship confirmation status
    and applicability lineage.  A binding whose identity is unconfirmed or
    whose cross-domain relation is not exactly verified fails closed at
    evaluation time (challenges 35/36/63).
    """

    binding_id: str
    control_point_id: str
    component_id: str
    subject_ref: str
    site_ref: str
    source_role: str
    stable_source_event_key: str
    source_locator: SourceLocator
    value: str = ""
    unit: str = ""
    date_raw: str = ""
    relationship_confirmation: str = CONFIRMATION_CONFIRMED
    accepted_revision_id: str = ""
    applicability_lineage: str = ""
    rule_lineage: str = ""
    cross_domain_ref: Optional[CrossDomainEvidenceRef] = None
    expected_producer_unit_id: str = ""
    producer_dependency_blocked: bool = False
    producer_dependency_reason: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.binding_id, "RuleEvidenceBinding.binding_id")
        _validate_nonempty(self.control_point_id,
                           "RuleEvidenceBinding.control_point_id")
        _validate_nonempty(self.component_id,
                           "RuleEvidenceBinding.component_id")
        _validate_nonempty(self.subject_ref,
                           "RuleEvidenceBinding.subject_ref")
        _validate_nonempty(self.site_ref, "RuleEvidenceBinding.site_ref")
        _validate_nonempty(self.source_role,
                           "RuleEvidenceBinding.source_role")
        _validate_nonempty(self.stable_source_event_key,
                           "RuleEvidenceBinding.stable_source_event_key")
        if not isinstance(self.source_locator, SourceLocator):
            raise ProtocolSliceError(
                "RuleEvidenceBinding.source_locator must be a SourceLocator")
        if self.relationship_confirmation not in (
                CONFIRMATION_CONFIRMED, CONFIRMATION_UNRESOLVED):
            raise ProtocolSliceError(
                f"relationship_confirmation="
                f"{self.relationship_confirmation!r} invalid")
        if (self.cross_domain_ref is not None
                and not isinstance(self.cross_domain_ref,
                                   CrossDomainEvidenceRef)):
            raise ProtocolSliceError(
                "RuleEvidenceBinding.cross_domain_ref must be a "
                "CrossDomainEvidenceRef or None")

    @property
    def is_confirmed(self) -> bool:
        return self.relationship_confirmation == CONFIRMATION_CONFIRMED


@dataclass(frozen=True)
class UnitConversionRule:
    """Versioned unit conversion (factor-based, exact Decimal math)."""

    conversion_id: str
    from_unit: str
    to_unit: str
    factor: str
    content_hash_value: str

    def __post_init__(self) -> None:
        _validate_nonempty(self.conversion_id, "UnitConversionRule.conversion_id")
        if not self.from_unit.strip() or not self.to_unit.strip():
            raise ProtocolSliceError(
                "UnitConversionRule requires from_unit and to_unit")
        if self.from_unit == self.to_unit:
            raise ProtocolSliceError(
                "UnitConversionRule from_unit must differ from to_unit")
        if _parse_decimal(self.factor) is None:
            raise ProtocolSliceError(
                f"UnitConversionRule.factor={self.factor!r} is not numeric")
        if not self.content_hash_value.strip():
            raise ProtocolSliceError(
                "UnitConversionRule.content_hash_value is required")


@dataclass(frozen=True)
class RetestOutcome:
    """Versioned retest/confirmation outcome (§7.1).

    A retest may cover the initial result only when the rule's
    retest_or_confirmation_policy allows it and the retest falls inside
    the allowed retest window with the required count/authority.
    """

    has_retest: bool
    retest_value: str = ""
    retest_unit: str = ""
    retest_date_raw: str = ""
    retest_in_allowed_window: Optional[bool] = None
    retest_authority_ok: Optional[bool] = None
    retest_count_ok: Optional[bool] = None
    meets_criterion: Optional[bool] = None
    conflict_with_initial: bool = False
    rationale: str = ""


@dataclass(frozen=True)
class ProtocolExceptionBinding:
    """One exception/waiver/investigator-judgment record (§7.3).

    Only an active-protocol pre-allowed exception path, or a formal rule
    change already effective at the evaluated event time and bound to this
    subject/site/rule/component/window, may enter rule arithmetic as
    counterevidence.  "已批准豁免" wording, retrospective acknowledgements,
    unapproved records and wrong rule/subject/site/window bindings are
    context only and can never rewrite a non-conformance (challenge 26).
    """

    exception_id: str
    subject_ref: str
    site_ref: str
    control_point_id: str
    component_id: str
    window_start: str
    window_end: str
    exception_effect: str
    approved_or_confirmed: Optional[bool] = None
    effective_at_event_time: Optional[bool] = None
    decision_date_raw: str = ""
    source_locator: Optional[SourceLocator] = None
    rationale: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.exception_id,
                           "ProtocolExceptionBinding.exception_id")
        if self.exception_effect not in EXCEPTION_EFFECTS:
            raise ProtocolSliceError(
                f"exception_effect={self.exception_effect!r} invalid")
        if (self.source_locator is not None
                and not isinstance(self.source_locator, SourceLocator)):
            raise ProtocolSliceError(
                "ProtocolExceptionBinding.source_locator must be a "
                "SourceLocator or None")


# ---------------------------------------------------------------------------
# Priority policy (§8.1) -- versioned, content-addressed
# ---------------------------------------------------------------------------

def policy_content_hash_value(
    *,
    policy_id: str,
    version: str,
    rationale: str,
    subtype_priorities: Sequence[Tuple[str, str]] = (),
    subtype_critical: Sequence[Tuple[str, bool]] = (),
    subtype_machine_close_forbidden: Sequence[Tuple[str, bool]] = (),
) -> str:
    """Canonical content address of the policy semantic payload.

    Covers policy id, version, rationale and the three sorted subtype
    pair lists; the supplied ``policy_content_hash`` itself is excluded
    (it IS this value).  Duplicate subtypes are rejected upstream, so the
    sorted pair lists are unambiguous and order-independent.
    """
    return "d04-policy-" + content_hash({
        "policy_id": policy_id,
        "version": version,
        "rationale": rationale,
        "subtype_priorities": sorted(
            (s, pri) for s, pri in subtype_priorities),
        "subtype_critical": sorted(
            (s, bool(f)) for s, f in subtype_critical),
        "subtype_machine_close_forbidden": sorted(
            (s, bool(f)) for s, f in subtype_machine_close_forbidden),
    })


@dataclass(frozen=True)
class D04PriorityPolicy:
    """Versioned, content-addressed monitoring-priority policy (§8.1).

    Priorities come from this policy only -- never model-scored, never a
    fixed universal threshold.  ``unknown`` is never defaulted to low.
    The frozen boolean candidate keys ``rights_or_safety_critical`` and
    ``machine_close_forbidden`` are read through the public strict readers
    in ``contracts.py`` by the shared lifecycle adapter (§8.1, §10.4).

    Invariants enforced at construction:

    * nested pairs are deep-frozen tuples, flags are literal ``bool`` and
      duplicate subtype entries are rejected (mutable aliases fail
      closed);
    * ``policy_content_hash`` must equal the canonical content address
      :func:`policy_content_hash_value` of the semantic payload (tampered
      hashes fail closed);
    * frozen producer invariant: any subtype with
      ``rights_or_safety_critical=true`` must also carry
      ``machine_close_forbidden=true`` and an effective monitoring
      priority of ``high`` -- enforced here, not only by the shared
      lifecycle adapter's either-flag normalization (§10.4).
    """

    policy_id: str
    version: str
    policy_content_hash: str
    rationale: str
    subtype_priorities: Tuple[Tuple[str, str], ...] = ()
    subtype_critical: Tuple[Tuple[str, bool], ...] = ()
    subtype_machine_close_forbidden: Tuple[Tuple[str, bool], ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.policy_id, "D04PriorityPolicy.policy_id")
        _validate_nonempty(self.version, "D04PriorityPolicy.version")
        _validate_nonempty(self.policy_content_hash,
                           "D04PriorityPolicy.policy_content_hash")
        if not self.rationale.strip():
            raise ProtocolSliceError(
                "D04PriorityPolicy.rationale is required")
        priorities = self._freeze_pairs(
            self.subtype_priorities, "subtype_priorities",
            flag_kind=False)
        critical = self._freeze_pairs(
            self.subtype_critical, "subtype_critical", flag_kind=True)
        forbidden = self._freeze_pairs(
            self.subtype_machine_close_forbidden,
            "subtype_machine_close_forbidden", flag_kind=True)
        object.__setattr__(self, "subtype_priorities", priorities)
        object.__setattr__(self, "subtype_critical", critical)
        object.__setattr__(self, "subtype_machine_close_forbidden", forbidden)
        # Frozen producer invariant (§10.4) -- fail closed at construction.
        for subtype, flag in critical:
            if not flag:
                continue
            if not self.machine_close_forbidden_for_subtype(subtype):
                raise ProtocolSliceError(
                    f"subtype {subtype!r} rights_or_safety_critical=true "
                    f"requires machine_close_forbidden=true")
            if self.priority_for_subtype(subtype) != MONITORING_PRIORITY_HIGH:
                raise ProtocolSliceError(
                    f"subtype {subtype!r} rights_or_safety_critical=true "
                    f"requires effective monitoring priority high")
        computed = policy_content_hash_value(
            policy_id=self.policy_id, version=self.version,
            rationale=self.rationale,
            subtype_priorities=priorities,
            subtype_critical=critical,
            subtype_machine_close_forbidden=forbidden)
        if self.policy_content_hash != computed:
            raise ProtocolSliceError(
                f"D04PriorityPolicy.policy_content_hash "
                f"{self.policy_content_hash!r} is not the canonical content "
                f"address {computed!r} of the policy semantic payload")

    def _freeze_pairs(
        self, value: Sequence[Any], field_name: str, *, flag_kind: bool,
    ) -> Tuple[Tuple[str, Any], ...]:
        """Deep-freeze one nested pair list; flags must be literal bools;
        duplicate subtypes are rejected."""
        result: List[Tuple[str, Any]] = []
        seen: Set[str] = set()
        for entry in value:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise ProtocolSliceError(
                    f"D04PriorityPolicy.{field_name} entries must be "
                    f"2-tuples, got {type(entry).__name__}")
            subtype, second = entry
            if not isinstance(subtype, str) or not subtype.strip():
                raise ProtocolSliceError(
                    f"D04PriorityPolicy.{field_name} subtype must be a "
                    f"non-empty string")
            if subtype not in POSITIVE_SUBTYPES:
                raise ProtocolSliceError(
                    f"unknown subtype {subtype!r} in {field_name}")
            if subtype in seen:
                raise ProtocolSliceError(
                    f"duplicate subtype {subtype!r} in "
                    f"D04PriorityPolicy.{field_name}")
            seen.add(subtype)
            if flag_kind:
                if type(second) is not bool:
                    raise ProtocolSliceError(
                        f"D04PriorityPolicy.{field_name} flag for "
                        f"{subtype!r} must be a literal bool, got "
                        f"{type(second).__name__}")
            else:
                if second not in VALID_MONITORING_PRIORITIES:
                    raise ProtocolSliceError(
                        f"priority {second!r} invalid in "
                        f"D04PriorityPolicy.{field_name}")
            result.append((subtype, second))
        return tuple(result)

    def priority_for_subtype(self, subtype: str) -> str:
        for s, priority in self.subtype_priorities:
            if s == subtype:
                return priority
        return MONITORING_PRIORITY_UNKNOWN

    def critical_for_subtype(self, subtype: str) -> bool:
        for s, flag in self.subtype_critical:
            if s == subtype:
                return bool(flag)
        return False

    def machine_close_forbidden_for_subtype(self, subtype: str) -> bool:
        for s, flag in self.subtype_machine_close_forbidden:
            if s == subtype:
                return bool(flag)
        return False


# ---------------------------------------------------------------------------
# Enrollment context (§8.3) -- Query wording gate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EnrollmentContext:
    """Frozen query context decided by locatable screening/randomization/
    enrollment/first-dose/disposition records (§8.3)."""

    subject_ref: str
    query_context: str
    rationale: str
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref, "EnrollmentContext.subject_ref")
        if self.query_context not in QUERY_CONTEXTS:
            raise ProtocolSliceError(
                f"query_context={self.query_context!r} invalid")
        if not self.rationale.strip():
            raise ProtocolSliceError("EnrollmentContext.rationale is required")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))


def resolve_enrollment_context(
    *,
    subject_ref: str,
    randomized_or_enrolled: Optional[bool],
    received_study_intervention: Optional[bool],
    disposition_recorded: Optional[bool] = None,
    coverage_complete: bool = False,
    source_locator_ids: Sequence[str] = (),
) -> EnrollmentContext:
    """Decide the enrollment query context (§8.3).

    ``enrolled_or_post_enrollment`` when randomization/enrollment/study
    intervention/disposition is determinately recorded; ``enrollment_
    not_occurred`` when determinately not randomized/enrolled and no study
    intervention (with complete coverage); otherwise ``enrollment_state_
    unresolved`` -- never guessed from the current page or model.
    """
    enrolled = (
        coverage_complete
        and (randomized_or_enrolled is True
             or received_study_intervention is True
             or disposition_recorded is True))
    if enrolled:
        return EnrollmentContext(
            subject_ref=subject_ref,
            query_context=QUERY_CONTEXT_ENROLLED,
            rationale="已记录随机/入组、接受研究干预或处置记录",
            source_locator_ids=tuple(source_locator_ids))
    not_occurred = (
        coverage_complete
        and randomized_or_enrolled is False
        and received_study_intervention is False
        and disposition_recorded is not True)
    if not_occurred:
        return EnrollmentContext(
            subject_ref=subject_ref,
            query_context=QUERY_CONTEXT_NOT_OCCURRED,
            rationale="确定尚未随机/入组且未接受研究干预",
            source_locator_ids=tuple(source_locator_ids))
    return EnrollmentContext(
        subject_ref=subject_ref,
        query_context=QUERY_CONTEXT_UNRESOLVED,
        rationale="随机/入组/首次给药状态或时序无法确定，资料不足",
        source_locator_ids=tuple(source_locator_ids))


# ---------------------------------------------------------------------------
# Regulatory guidance metadata (challenge 15) -- data-driven, no hardcode
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegulatoryGuidanceVersion:
    """One externally effective regulatory guidance version (§2.1)."""

    version_id: str
    effective_start: str
    effective_end: str = ""
    content_reference: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.version_id,
                           "RegulatoryGuidanceVersion.version_id")
        _validate_nonempty(self.effective_start,
                           "RegulatoryGuidanceVersion.effective_start")


def resolve_regulatory_guidance(
    *,
    evaluation_time: str,
    guidance_records: Sequence[RegulatoryGuidanceVersion],
) -> Tuple[Optional[RegulatoryGuidanceVersion], str]:
    """Select the regulatory guidance effective at the Run evaluation time
    (§2.1).  The kernel holds no hardcoded regulatory calendar; the
    2026-09-01 China GCP boundary is supplied by the caller as data, so a
    re-interpretation of past results requires a new Run, never a rewrite.
    """
    day = _day_date(evaluation_time)
    if day is None:
        return None, "评价时点日期缺失或精度不足，无法选择适用规范版本"
    candidates: List[RegulatoryGuidanceVersion] = []
    for rec in guidance_records:
        lo = _day_date(rec.effective_start)
        hi = _day_date(rec.effective_end) if rec.effective_end.strip() else None
        if lo is None:
            continue
        if lo > day:
            continue
        if hi is not None and day > hi:
            continue
        candidates.append(rec)
    if len(candidates) == 1:
        return candidates[0], ""
    if not candidates:
        return None, "评价时点不在任何已登记规范版本有效期内"
    return None, "多个规范版本同时有效或边界重叠，无法唯一确定"


# ---------------------------------------------------------------------------
# Coverage-gap notice (§6.4)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolCoverageGapNotice:
    """资料不足提示: bound to unit, reason, protocol locators and
    reachable source locators.  ``notice_id`` is a canonical content hash
    over unit + reason + sorted missing roles + sorted locators -- it never
    contains runtime free text, so reruns are deterministic (challenge 48).
    """

    notice_id: str
    unit_id: str
    reason_code: str
    missing_evidence_roles: Tuple[str, ...] = ()
    protocol_locator_ids: Tuple[str, ...] = ()
    reachable_source_locator_ids: Tuple[str, ...] = ()
    audience_text: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.unit_id, "ProtocolCoverageGapNotice.unit_id")
        if self.reason_code not in GAP_REASON_CODES:
            raise ProtocolSliceError(
                f"reason_code={self.reason_code!r} invalid")
        missing = _canonical_sorted(self.missing_evidence_roles)
        protocol_loc = _canonical_sorted(self.protocol_locator_ids)
        reachable = _canonical_sorted(self.reachable_source_locator_ids)
        object.__setattr__(self, "missing_evidence_roles", missing)
        object.__setattr__(self, "protocol_locator_ids", protocol_loc)
        object.__setattr__(self, "reachable_source_locator_ids", reachable)
        computed = "d04-gap-" + content_hash({
            "unit_id": self.unit_id,
            "reason_code": self.reason_code,
            "missing_evidence_roles": list(missing),
            "protocol_locator_ids": list(protocol_loc),
            "reachable_source_locator_ids": list(reachable),
        })
        if self.notice_id and self.notice_id != computed:
            raise ProtocolSliceError(
                f"ProtocolCoverageGapNotice.notice_id {self.notice_id!r} "
                f"does not match the canonical hash {computed!r}")
        object.__setattr__(self, "notice_id", computed)


def _gap_notice(
    *, unit_id: str, reason_code: str,
    missing_evidence_roles: Sequence[str] = (),
    protocol_locator_ids: Sequence[str] = (),
    reachable_source_locator_ids: Sequence[str] = (),
    audience_text: str = "",
) -> ProtocolCoverageGapNotice:
    return ProtocolCoverageGapNotice(
        notice_id="", unit_id=unit_id, reason_code=reason_code,
        missing_evidence_roles=tuple(missing_evidence_roles),
        protocol_locator_ids=tuple(protocol_locator_ids),
        reachable_source_locator_ids=tuple(reachable_source_locator_ids),
        audience_text=audience_text or _GAP_LABELS.get(
            reason_code, "资料不足，暂无法核实"))


# ---------------------------------------------------------------------------
# Journey / marker / typed producer value objects (§7.4, §9)
# ---------------------------------------------------------------------------
#
# These fixed schemas are renderer-neutral payloads.  The journey
# *projection* functions live in ``protocol_projection.py`` (worker_03);
# this module owns the value objects only.

@dataclass(frozen=True)
class ProtocolJourneyEvent:
    """One protocol-compliance journey event (§9 minimal fields)."""

    event_id: str
    domain_track: str
    subject_ref: str
    site_ref: str
    anchor_kind: str
    start: str = ""
    end: str = ""
    date_precision: str = ""
    nominal_visit: str = ""
    actual_visit: str = ""
    phase: str = ""
    protocol_version: str = ""
    control_point_id: str = ""
    evaluation_node_id: str = ""
    decisive_component_ids: Tuple[str, ...] = ()
    display_label: str = ""
    source_locator_ids: Tuple[str, ...] = ()
    unit_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.event_id, "ProtocolJourneyEvent.event_id")
        _validate_nonempty(self.domain_track,
                           "ProtocolJourneyEvent.domain_track")
        _validate_nonempty(self.subject_ref,
                           "ProtocolJourneyEvent.subject_ref")
        if self.anchor_kind not in ANCHOR_KINDS:
            raise ProtocolSliceError(
                f"ProtocolJourneyEvent.anchor_kind={self.anchor_kind!r} "
                f"invalid")
        object.__setattr__(self, "decisive_component_ids",
                           _canonical_sorted(self.decisive_component_ids))
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        object.__setattr__(self, "unit_ids",
                           _canonical_sorted(self.unit_ids))


@dataclass(frozen=True)
class ProtocolRiskMarker:
    """One protocol-compliance risk marker (§9 minimal fields)."""

    marker_id: str
    risk_family: str
    audience_label: str
    monitoring_priority: str
    anchor_kind: str
    anchor_start: str = ""
    anchor_end: str = ""
    date_precision: str = ""
    unit_id: str = ""
    candidate_or_risk_id: str = ""
    protocol_locator_ids: Tuple[str, ...] = ()
    supporting_locator_ids: Tuple[str, ...] = ()
    counterevidence_locator_ids: Tuple[str, ...] = ()
    query_ids: Tuple[str, ...] = ()
    coverage_gap: bool = False

    def __post_init__(self) -> None:
        _validate_nonempty(self.marker_id, "ProtocolRiskMarker.marker_id")
        if self.anchor_kind not in ANCHOR_KINDS:
            raise ProtocolSliceError(
                f"ProtocolRiskMarker.anchor_kind={self.anchor_kind!r} invalid")
        if self.monitoring_priority not in VALID_MONITORING_PRIORITIES:
            raise ProtocolSliceError(
                f"monitoring_priority={self.monitoring_priority!r} invalid")
        object.__setattr__(self, "protocol_locator_ids",
                           _canonical_sorted(self.protocol_locator_ids))
        object.__setattr__(self, "supporting_locator_ids",
                           _canonical_sorted(self.supporting_locator_ids))
        object.__setattr__(self, "counterevidence_locator_ids",
                           _canonical_sorted(self.counterevidence_locator_ids))
        object.__setattr__(self, "query_ids",
                           _canonical_sorted(self.query_ids))


@dataclass(frozen=True)
class ProtocolEventMarkerJoin:
    """Fixed event-marker join (§7.4).  Every id must be reachable and
    share subject/site/window; tamper fails before projection."""

    event_id: str
    marker_id: str
    unit_id: str
    risk_identity_id: str
    join_reason: str
    typed_ref_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.event_id, "ProtocolEventMarkerJoin.event_id")
        _validate_nonempty(self.marker_id, "ProtocolEventMarkerJoin.marker_id")
        _validate_nonempty(self.unit_id, "ProtocolEventMarkerJoin.unit_id")
        if self.join_reason not in JOIN_REASONS:
            raise ProtocolSliceError(
                f"join_reason={self.join_reason!r} invalid")
        object.__setattr__(self, "typed_ref_ids",
                           _canonical_sorted(self.typed_ref_ids))


@dataclass(frozen=True)
class ProtocolProducerReference:
    """Typed producer join for the compliance overview (§7.4, §9).

    Carries the producer's own marker/Query/risk identity; D04 never
    copies a producer candidate/risk/Query or creates a second identity.
    """

    ref_id: str
    owner_domain: str
    producer_unit_id: str
    producer_marker_or_query_id: str = ""
    producer_risk_identity_id: str = ""
    audience_label: str = ""
    monitoring_priority: str = MONITORING_PRIORITY_UNKNOWN
    control_point_id: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.ref_id, "ProtocolProducerReference.ref_id")
        if self.owner_domain not in (
                OWNER_D02, OWNER_D03, OWNER_D05, OWNER_D08):
            raise ProtocolSliceError(
                f"ProtocolProducerReference.owner_domain="
                f"{self.owner_domain!r} must be a producer domain "
                f"(D02/D03/D05/D08), never D04/self or owner_unresolved")
        _validate_nonempty(self.producer_unit_id,
                           "ProtocolProducerReference.producer_unit_id")
        if self.monitoring_priority not in VALID_MONITORING_PRIORITIES:
            raise ProtocolSliceError(
                f"monitoring_priority={self.monitoring_priority!r} invalid")


# ---------------------------------------------------------------------------
# Expected-set expansion (§5): eight frozen hash dimensions
# ---------------------------------------------------------------------------

def build_protocol_unit(
    *,
    project_id: str,
    subject_ref: str,
    control_point_id: str,
    evaluation_node_id: str,
    signal_type: str,
    protocol_applicability_id: str,
    eval_anchor_kind: str,
    window_start: str,
    window_end: str,
    precision: str,
    endpoint_inclusivity: str,
    protocol_id: str,
    protocol_version: str,
    amendment_id_or_hash: str,
    rule_content_hash: str,
    extraction_hash: str,
    mapping_version: str,
    unit_term_policy_version: str,
    feasible_version_fingerprints: Sequence[str] = (),
) -> EvaluationUnit:
    """Build the D04 EvaluationUnit from the frozen eight dimensions (§5).

    All nested objects are canonical-JSON serialized into single strings
    before hashing; control-point ids containing ``|`` still produce
    distinct canonical unit ids (challenge 59).
    """
    if evaluation_node_id not in NODE_IDS:
        raise ProtocolSliceError(
            f"evaluation_node_id={evaluation_node_id!r} invalid")
    if signal_type not in SIGNAL_TYPES:
        raise ProtocolSliceError(f"signal_type={signal_type!r} invalid")
    if eval_anchor_kind not in ANCHOR_KINDS:
        raise ProtocolSliceError(
            f"eval_anchor_kind={eval_anchor_kind!r} invalid")
    norm = content_hash({
        "control_point_id": control_point_id,
        "evaluation_node_id": evaluation_node_id,
        "signal_type": signal_type,
    })
    window = content_hash({
        "protocol_applicability_id": protocol_applicability_id,
        "eval_anchor_kind": eval_anchor_kind,
        "window_start": window_start,
        "window_end": window_end,
        "precision": precision,
        "endpoint_inclusivity": endpoint_inclusivity,
    })
    lineage_payload: Dict[str, Any] = {
        "protocol_id": protocol_id,
        "protocol_version": protocol_version,
        "amendment_id_or_hash": amendment_id_or_hash,
        "rule_content_hash": rule_content_hash,
        "extraction_hash": extraction_hash,
        "mapping_version": mapping_version,
        "unit_term_policy_version": unit_term_policy_version,
    }
    fps = _canonical_sorted(feasible_version_fingerprints)
    if fps:
        lineage_payload["feasible_version_fingerprints"] = list(fps)
    lineage = content_hash(lineage_payload)
    return EvaluationUnit(
        project_id=project_id, domain_id=D04_DOMAIN,
        scope_type="subject", scope_key=subject_ref,
        normalized_concept_or_rule_item=norm,
        temporal_window=window,
        rule_or_knowledge_lineage=lineage,
        unit_algorithm_version=D04_UNIT_ALGO_VERSION)


def expected_set_hash(unit_ids: Sequence[str]) -> str:
    """D04 expected-set hash -- input-order independent (challenge 48/83).

    Duplicate unit ids are rejected, never silently deduplicated: each
    expected unit appears exactly once (§11)."""
    if isinstance(unit_ids, str):
        raise ProtocolSliceError(
            "expected_set_hash requires a sequence, not a string")
    seen: Set[str] = set()
    for uid in unit_ids:
        if not isinstance(uid, str) or not uid.strip():
            raise ProtocolSliceError(
                "expected-set unit ids must be non-empty strings")
        if uid in seen:
            raise ProtocolSliceError(
                f"duplicate unit_id {uid!r} in expected set "
                f"(§11: each unit id appears exactly once)")
        seen.add(uid)
    return "d04-eset-" + content_hash(sorted(seen))


@dataclass(frozen=True)
class ProtocolUnitExpanded:
    """One expanded expected EvaluationUnit seed for D04."""

    subject_ref: str
    site_ref: str
    applicability: ProtocolApplicabilityDecision
    evaluation_node_id: str
    signal_type: str
    plan: ProtocolRuleEvaluationPlan
    control_point: Optional[ProtocolControlPoint] = None
    issue_expression: Optional[IssueExpression] = None
    component_ids: Tuple[str, ...] = ()
    components: Optional[Mapping[str, ProtocolComponent]] = None
    evidence_requirements: Tuple[RuleEvidenceRequirement, ...] = ()
    route: Optional[ProtocolControlRoutingRecord] = None
    window: EvaluationWindowSpec = EvaluationWindowSpec()
    control_point_not_applicable: bool = False
    affected_control_point_ids: Tuple[str, ...] = ()
    candidate_owners: Tuple[str, ...] = ()
    not_evaluable_reason_hint: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref, "ProtocolUnitExpanded.subject_ref")
        _validate_nonempty(self.site_ref, "ProtocolUnitExpanded.site_ref")
        if not isinstance(self.applicability, ProtocolApplicabilityDecision):
            raise ProtocolSliceError(
                "ProtocolUnitExpanded.applicability must be a "
                "ProtocolApplicabilityDecision")
        if self.evaluation_node_id not in NODE_IDS:
            raise ProtocolSliceError(
                f"evaluation_node_id={self.evaluation_node_id!r} invalid")
        if self.signal_type not in SIGNAL_TYPES:
            raise ProtocolSliceError(
                f"signal_type={self.signal_type!r} invalid")
        if not isinstance(self.plan, ProtocolRuleEvaluationPlan):
            raise ProtocolSliceError(
                "ProtocolUnitExpanded.plan must be a "
                "ProtocolRuleEvaluationPlan")
        object.__setattr__(self, "component_ids",
                           _freeze_tuple(self.component_ids,
                                         "ProtocolUnitExpanded.component_ids"))
        object.__setattr__(self, "affected_control_point_ids",
                           _canonical_sorted(self.affected_control_point_ids))
        object.__setattr__(self, "candidate_owners",
                           _canonical_sorted(self.candidate_owners))
        # Deep-freeze the component mapping: a read-only view over a
        # defensive copy.  Direct mutation and caller-alias mutation are
        # both impossible, so package evaluation stays deterministic.
        # Key/value identity is validated (key == component.component_id).
        if self.components is not None:
            frozen: Dict[str, ProtocolComponent] = dict(self.components)
            for key, comp in frozen.items():
                if not isinstance(key, str) or not key.strip():
                    raise ProtocolSliceError(
                        "component map keys must be non-empty strings")
                if not isinstance(comp, ProtocolComponent):
                    raise ProtocolSliceError(
                        "component map values must be ProtocolComponent "
                        "instances")
                if comp.component_id != key:
                    raise ProtocolSliceError(
                        f"component map key {key!r} must equal its "
                        f"component_id {comp.component_id!r}")
            object.__setattr__(self, "components",
                               MappingProxyType(frozen))
        reqs = tuple(self.evidence_requirements)
        for req in reqs:
            if not isinstance(req, RuleEvidenceRequirement):
                raise ProtocolSliceError(
                    "evidence_requirements must be RuleEvidenceRequirement "
                    "instances")
            cp_id = (self.control_point.control_point_id
                     if self.control_point is not None else "")
            if req.control_point_id != cp_id:
                raise ProtocolSliceError(
                    f"evidence requirement {req.requirement_id!r} is bound "
                    f"to control point {req.control_point_id!r}, expected "
                    f"{cp_id!r}")
        if self.evaluation_node_id in (NODE_ATOMIC, NODE_PACKAGE):
            if not reqs:
                raise ProtocolSliceError(
                    "atomic/package unit requires generated "
                    "evidence_requirements (never inferred at evaluation)")
            if self.evaluation_node_id == NODE_ATOMIC:
                if (len(reqs) != 1
                        or reqs[0].component_id
                        != self.control_point.control_point_id):
                    raise ProtocolSliceError(
                        "atomic unit requires exactly one evidence "
                        "requirement for the control point component")
            else:
                req_components = [r.component_id for r in reqs]
                if len(set(req_components)) != len(req_components):
                    raise ProtocolSliceError(
                        "package unit evidence requirements must be unique "
                        "per component")
                if set(req_components) != set(self.component_ids):
                    raise ProtocolSliceError(
                        "package unit evidence requirements must cover "
                        "exactly its component ids")
        else:
            if reqs:
                raise ProtocolSliceError(
                    "applicability/routing gate units must not fabricate "
                    "evidence requirements")
        object.__setattr__(self, "evidence_requirements", reqs)
        if self.evaluation_node_id in (NODE_ATOMIC, NODE_PACKAGE):
            if self.control_point is None:
                raise ProtocolSliceError(
                    "atomic/package unit requires control_point")
            if (self.evaluation_node_id == NODE_PACKAGE
                    and self.issue_expression is None):
                raise ProtocolSliceError(
                    "package unit requires issue_expression")
            if self.signal_type != self.control_point.signal_type():
                raise ProtocolSliceError(
                    "unit signal_type must match control point signal type")
        if self.evaluation_node_id == NODE_APPLICABILITY_GATE:
            if self.signal_type != SIGNAL_PROTOCOL_APPLICABILITY:
                raise ProtocolSliceError(
                    "applicability gate requires signal_type "
                    "protocol_applicability")
        if self.evaluation_node_id == NODE_ROUTING_GATE:
            if self.signal_type != SIGNAL_PROTOCOL_ROUTING:
                raise ProtocolSliceError(
                    "routing gate requires signal_type protocol_routing")

    def build_unit(self, project_id: str) -> EvaluationUnit:
        appl = self.applicability
        if self.evaluation_node_id == NODE_APPLICABILITY_GATE:
            cp_id = "protocol_applicability"
            protocol_version = "multi_feasible"
            amendment = "multi_feasible"
            if appl.decision_status == APPLICABILITY_NOT_EVALUABLE:
                protocol_version = "undetermined"
                amendment = "undetermined"
            return build_protocol_unit(
                project_id=project_id, subject_ref=self.subject_ref,
                control_point_id=cp_id,
                evaluation_node_id=NODE_APPLICABILITY_GATE,
                signal_type=SIGNAL_PROTOCOL_APPLICABILITY,
                protocol_applicability_id=appl.protocol_applicability_id,
                eval_anchor_kind=ANCHOR_OTHER,
                window_start="", window_end="",
                precision=PRECISION_UNKNOWN,
                endpoint_inclusivity=INCLUSIVITY_GATE,
                protocol_id=appl.protocol_id,
                protocol_version=protocol_version,
                amendment_id_or_hash=amendment,
                rule_content_hash="applicability_gate",
                extraction_hash="applicability_gate",
                mapping_version=self.plan.mapping_version,
                unit_term_policy_version=self.plan.unit_term_policy_version,
                feasible_version_fingerprints=appl.feasible_version_fingerprints)
        if self.evaluation_node_id == NODE_ROUTING_GATE:
            cp_id = (self.control_point.control_point_id
                     if self.control_point is not None
                     else "protocol_routing")
            return build_protocol_unit(
                project_id=project_id, subject_ref=self.subject_ref,
                control_point_id=cp_id,
                evaluation_node_id=NODE_ROUTING_GATE,
                signal_type=SIGNAL_PROTOCOL_ROUTING,
                protocol_applicability_id=appl.protocol_applicability_id,
                eval_anchor_kind=appl.decision_time_anchor,
                window_start="", window_end="",
                precision=appl.applicability_precision,
                endpoint_inclusivity=INCLUSIVITY_GATE,
                protocol_id=appl.protocol_id,
                protocol_version=(
                    appl.protocol_version or "routing_undetermined"),
                amendment_id_or_hash=(
                    appl.amendment_id_or_hash or "routing_undetermined"),
                rule_content_hash="routing_gate",
                extraction_hash="routing_gate",
                mapping_version=self.plan.mapping_version,
                unit_term_policy_version=self.plan.unit_term_policy_version)
        assert self.control_point is not None
        return build_protocol_unit(
            project_id=project_id, subject_ref=self.subject_ref,
            control_point_id=self.control_point.control_point_id,
            evaluation_node_id=self.evaluation_node_id,
            signal_type=self.signal_type,
            protocol_applicability_id=appl.protocol_applicability_id,
            eval_anchor_kind=self.window.eval_anchor_kind,
            window_start=self.window.window_start,
            window_end=self.window.window_end,
            precision=self.window.precision,
            endpoint_inclusivity=self.window.endpoint_inclusivity,
            protocol_id=appl.protocol_id,
            protocol_version=appl.protocol_version,
            amendment_id_or_hash=appl.amendment_id_or_hash,
            rule_content_hash=self.plan.rule_content_hash,
            extraction_hash=self.plan.extraction_hash,
            mapping_version=self.plan.mapping_version,
            unit_term_policy_version=self.plan.unit_term_policy_version)


@dataclass(frozen=True)
class ProtocolExpectedSetExpansion:
    """Expansion result: evaluation-root units + delegated routing list."""

    units: Tuple[ProtocolUnitExpanded, ...]
    project_id: str
    applicability: ProtocolApplicabilityDecision
    plan: ProtocolRuleEvaluationPlan
    delegated_control_points: Tuple[ProtocolDelegatedControlPoint, ...] = ()
    unit_ids: Tuple[str, ...] = ()
    expected_set_hash: str = ""

    def __post_init__(self) -> None:
        ids = tuple(u.build_unit(self.project_id).unit_id for u in self.units)
        object.__setattr__(self, "unit_ids", ids)
        object.__setattr__(self, "expected_set_hash", expected_set_hash(ids))

    @property
    def count(self) -> int:
        return len(self.units)


def _window_for_control_point(
    control_point: ProtocolControlPoint,
    applicability: ProtocolApplicabilityDecision,
    window_by_control_point: Optional[Mapping[str, EvaluationWindowSpec]],
) -> EvaluationWindowSpec:
    if window_by_control_point is not None:
        spec = window_by_control_point.get(control_point.control_point_id)
        if spec is not None:
            return spec
    rule = control_point.structured_rule
    if rule is not None and rule.evaluation_window_start.strip():
        return EvaluationWindowSpec(
            eval_anchor_kind=rule.temporal_anchor,
            window_start=rule.evaluation_window_start,
            window_end=rule.evaluation_window_end,
            precision=_date_precision(rule.evaluation_window_start),
            endpoint_inclusivity=_inclusivity_token(
                rule.window_start_inclusive, rule.window_end_inclusive))
    return EvaluationWindowSpec(
        eval_anchor_kind=applicability.decision_time_anchor,
        precision=applicability.applicability_precision)


def _inclusivity_token(
    start_inclusive: Optional[bool], end_inclusive: Optional[bool],
) -> str:
    if start_inclusive is None or end_inclusive is None:
        return INCLUSIVITY_UNSTATED
    if start_inclusive and end_inclusive:
        return INCLUSIVITY_INCLUSIVE
    if not start_inclusive and not end_inclusive:
        return INCLUSIVITY_EXCLUSIVE
    return INCLUSIVITY_MIXED


def expand_protocol_expected_set(
    *,
    project_id: str,
    applicability: ProtocolApplicabilityDecision,
    control_points: Sequence[ProtocolControlPoint],
    plan: ProtocolRuleEvaluationPlan,
    components: Optional[Mapping[str, ProtocolComponent]] = None,
    routing_records: Optional[Sequence[ProtocolControlRoutingRecord]] = None,
    window_by_control_point: Optional[Mapping[str, EvaluationWindowSpec]] = None,
) -> ProtocolExpectedSetExpansion:
    """Expand control points into the D04 expected unit set (§5).

    One EvaluationUnit per atomic/package root; producer-owned control
    points never enter the expected-set (they become delegated items);
    owner competition produces exactly one ``protocol_routing`` gate;
    a non-unique applicability decision produces exactly one subject-level
    ``protocol_applicability`` gate and no per-control-point medical units
    (challenges 60/67/71).
    """
    if not project_id.strip():
        raise ProtocolSliceError("project_id is required")
    if not isinstance(plan, ProtocolRuleEvaluationPlan):
        raise ProtocolSliceError("plan must be a ProtocolRuleEvaluationPlan")
    component_map: Dict[str, ProtocolComponent] = dict(components or {})
    routing_by_cp: Dict[str, ProtocolControlRoutingRecord] = {}
    for rec in routing_records or ():
        if rec.control_point_id in routing_by_cp:
            raise ProtocolSliceError(
                f"duplicate routing record for control point "
                f"{rec.control_point_id!r}: one owner decision per control "
                f"point (§3.2)")
        routing_by_cp[rec.control_point_id] = rec

    units: List[ProtocolUnitExpanded] = []
    delegated: List[ProtocolDelegatedControlPoint] = []

    for cp in control_points:
        if not isinstance(cp, ProtocolControlPoint):
            raise ProtocolSliceError(
                "control_points must be ProtocolControlPoint instances")
        if cp.control_point_id not in plan.root_ids:
            # A control point that is not an evaluation root is not an
            # expected unit (e.g. a display grouping node) -- §5: chapter
            # headings and display groups never masquerade as units.
            continue
        route = routing_by_cp.get(cp.control_point_id)
        if route is None:
            owner = route_control_point(cp.control_point_type)
            if owner == OWNER_D04:
                route = None
            else:
                route = ProtocolControlRoutingRecord(
                    control_point_id=cp.control_point_id,
                    owner_domain=owner,
                    owner_signal_type=owner,
                    routing_rule_version="routing-table-v1",
                    routing_rule_hash="routing-table-v1",
                    routing_gap="routing_by_control_point_type",
                    decision_rationale="closed routing decision table §3.2")
        if route is not None and route.owner_domain == OWNER_UNRESOLVED:
            units.append(ProtocolUnitExpanded(
                subject_ref=applicability.subject_ref,
                site_ref=applicability.site_ref,
                applicability=applicability,
                evaluation_node_id=NODE_ROUTING_GATE,
                signal_type=SIGNAL_PROTOCOL_ROUTING,
                plan=plan,
                control_point=cp,
                route=route,
                candidate_owners=route.candidate_owners,
                not_evaluable_reason_hint=route.routing_gap))
            continue
        if route is not None:
            delegated.append(ProtocolDelegatedControlPoint(
                control_point_id=cp.control_point_id,
                owner_domain=route.owner_domain,
                owner_signal_type=route.owner_signal_type,
                producer_unit_id=route.producer_unit_id,
                routing_gap=route.routing_gap,
                component_id=route.component_id))
            continue
        # D04-native root.
        if applicability.decision_status != APPLICABILITY_UNIQUE_ACTIVE:
            # Applicability gate covers all D04-native control points;
            # affected ids stay in the decision context only (§5, 71).
            continue
        if (cp.control_point_id
                in applicability.not_applicable_control_point_ids):
            not_applicable = True
        else:
            not_applicable = False
        window = _window_for_control_point(
            cp, applicability, window_by_control_point)
        if cp.evaluation_root_kind == NODE_ATOMIC:
            units.append(ProtocolUnitExpanded(
                subject_ref=applicability.subject_ref,
                site_ref=applicability.site_ref,
                applicability=applicability,
                evaluation_node_id=NODE_ATOMIC,
                signal_type=cp.signal_type(),
                plan=plan,
                control_point=cp,
                window=window,
                control_point_not_applicable=not_applicable,
                evidence_requirements=expand_rule_evidence_requirements(
                    cp, rule_lineage=plan.rule_content_hash)))
        else:
            ids: List[str] = []
            for cid in cp.component_ids:
                if cid not in component_map:
                    raise ProtocolSliceError(
                        f"package {cp.control_point_id} references unknown "
                        f"component {cid!r}")
                ids.append(cid)
            units.append(ProtocolUnitExpanded(
                subject_ref=applicability.subject_ref,
                site_ref=applicability.site_ref,
                applicability=applicability,
                evaluation_node_id=NODE_PACKAGE,
                signal_type=cp.signal_type(),
                plan=plan,
                control_point=cp,
                issue_expression=cp.issue_expression,
                component_ids=tuple(ids),
                components=component_map,
                window=window,
                control_point_not_applicable=not_applicable,
                evidence_requirements=expand_rule_evidence_requirements(
                    cp, components=component_map,
                    rule_lineage=plan.rule_content_hash)))

    if applicability.decision_status != APPLICABILITY_UNIQUE_ACTIVE:
        blocked_roots = sorted(
            cp.control_point_id for cp in control_points
            if cp.control_point_id in plan.root_ids)
        units.insert(0, ProtocolUnitExpanded(
            subject_ref=applicability.subject_ref,
            site_ref=applicability.site_ref,
            applicability=applicability,
            evaluation_node_id=NODE_APPLICABILITY_GATE,
            signal_type=SIGNAL_PROTOCOL_APPLICABILITY,
            plan=plan,
            affected_control_point_ids=tuple(blocked_roots),
            not_evaluable_reason_hint=applicability.rationale))

    return ProtocolExpectedSetExpansion(
        units=tuple(units), project_id=project_id,
        applicability=applicability, plan=plan,
        delegated_control_points=tuple(delegated))
