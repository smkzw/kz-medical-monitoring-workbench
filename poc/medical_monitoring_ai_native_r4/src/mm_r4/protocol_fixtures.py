"""R4-D04 protocol synthetic fixtures, 83-case challenge matrix and
deterministic golden hashes (worker_03).

Every fixture is **deterministic, synthetic and offline**.  No real-project
data, protocol number, drug name, fixed threshold, listing layout, visit
window or medication rule is encoded.  The fixtures build the same frozen
public value objects the D04 protocol engine (``mm_r4.protocol``) and the
D04 projection (``mm_r4.protocol_projection``) use, so the tests exercise
the real engine evaluation, the real projection join invariants, the real
R2 identity public API and the real coverage ledger rather than mocks.

The module delivers what the frozen D04 contract
``FROZEN_R4_D04_CONTRACT_V1_1`` §12/§13 requires:

1. Thin primitive builders (``make_locator``, ``make_version``,
   ``make_applicability``, ``make_plan``, ``make_numeric_rule``,
   ``make_control_point``, ``make_component``, ``make_binding``,
   ``make_policy``, ``make_enrollment``, ``make_exception``,
   ``make_conversion``, ``make_retest``, ``make_guidance``,
   ``make_routing``, ``make_producer_ref``, ``make_window``) that
   construct the frozen versioned inputs with stable hashes.
2. :func:`build_protocol_challenge_matrix` -- the full numbered frozen
   §12 **83-case** challenge matrix.  Every challenge row maps to a
   focused executable D04 assertion, or -- where the N->N+1 lifecycle,
   shared flag normalization or adjacent-slice behavior is already
   accepted by a dedicated adjacent test -- to an explicit named
   adjacent accepted test (``adjacent_test`` field).  The matrix test
   verifies that every adjacent reference resolves to a real test.
3. Deterministic golden hashes: ``GOLDEN_EXPECTED_SET_HASH`` /
   ``GOLDEN_UNIT_IDS`` / ``GOLDEN_COMPONENT_ASSESSMENT_IDS`` /
   ``GOLDEN_CANDIDATE_IDS`` / ``GOLDEN_PROJECTION_PAYLOAD_HASH`` freeze
   the unit/component/expected-set/payload identities for the most
   contract-critical cases (challenges 1, 2, 8, 9, 46-48, 58, 59, 60,
   68, 71, 72-74, 82, 83), and the tests verify they are stable across
   reruns.
4. Entry points :func:`evaluate`, :func:`evaluate_slice` and
   :func:`run_determinism_replay` for focused slice evaluation and
   byte-deterministic replay checks.

All data is synthetic.  No production UI, real project, provider,
dictionary, or product service is involved; port 8911 is never touched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .contracts import (
    L1Disposition,
    MONITORING_PRIORITY_MEDIUM,
    MONITORING_PRIORITY_UNKNOWN,
    SourceLocator,
    content_hash,
)
from . import protocol as p
from . import protocol_projection as pp

__all__ = [
    # constants
    "PROJECT_ID",
    "DOMAIN_ID",
    "RUN_ID",
    "RULE_LINEAGE",
    "SNAPSHOT_ID",
    "SOURCE_REV_ID",
    "SITE_REF",
    "SUBJECT",
    "DEFAULT_ROLE_COVERAGE",
    # primitive builders
    "make_locator",
    "make_version",
    "make_applicability",
    "make_plan",
    "make_numeric_rule",
    "make_control_point",
    "make_component",
    "make_issue_expression",
    "make_binding",
    "make_policy",
    "make_enrollment",
    "make_exception",
    "make_conversion",
    "make_retest",
    "make_guidance",
    "make_routing",
    "make_producer_ref",
    "make_cd_ref",
    "make_window",
    # entry points
    "evaluate",
    "evaluate_slice",
    "run_determinism_replay",
    # challenge matrix
    "ProtocolExpectedUnit",
    "ProtocolChallengeCase",
    "ProtocolChallengeMatrix",
    "build_protocol_challenge_matrix",
    # golden hashes
    "GOLDEN_EXPECTED_SET_HASH",
    "GOLDEN_UNIT_IDS",
    "GOLDEN_COMPONENT_ASSESSMENT_IDS",
    "GOLDEN_CANDIDATE_IDS",
    "GOLDEN_PROJECTION_PAYLOAD_HASH",
]


# ---------------------------------------------------------------------------
# Stable synthetic constants (no project specifics, no fixed table names)
# ---------------------------------------------------------------------------

PROJECT_ID = "proj-synthetic-001"
DOMAIN_ID = p.D04_DOMAIN
RUN_ID = "run-synthetic-d04-001"
RULE_LINEAGE = p.D04_RULE_LINEAGE_DEFAULT
SNAPSHOT_ID = "snap-d04-accepted-001"
SOURCE_REV_ID = "sr-d04-listing-001"
SITE_REF = "SITE01"
SUBJECT = "SYN-001"

#: Default role coverage: primary semantic roles are covered.  Auxiliary
#: roles (IE/DV summaries, monitoring notes, emails) are auxiliary-only
#: and never prove a criterion (§4.1/§4.2).  Challenge cases that probe
#: coverage gaps override individual roles.
DEFAULT_ROLE_COVERAGE: Dict[str, bool] = {
    "subject_identity": True,
    "site_identity": True,
    "randomization": True,
    "consent": True,
    "demographics": True,
    "laboratory": True,
    "vital_sign": True,
    "medical_history": True,
    "adverse_event": True,
    "concomitant_medication": True,
    "pregnancy_test": True,
    "ecg": True,
    "physical_exam": True,
    "questionnaire": True,
    "other_assessment": True,
    "ip_exposure": True,
    "procedure": True,
    "assessment": True,
    "visit": True,
    "sample": True,
    "disposition": True,
    "first_dose": True,
    "aggregate_ie_status": False,
    "deviation_listing": False,
    "monitoring_note": False,
    "email_or_edc_note": False,
}


# ---------------------------------------------------------------------------
# Primitive builders (mirror the worker_02 test conventions)
# ---------------------------------------------------------------------------

def make_locator(
    record_id: str, table_semantic: str = "protocol_text",
    snapshot_id: str = SNAPSHOT_ID,
    source_revision_id: str = SOURCE_REV_ID,
) -> SourceLocator:
    return SourceLocator(
        snapshot_id=snapshot_id, source_revision_id=source_revision_id,
        table_semantic=table_semantic, record_id=record_id,
        column_or_anchor="row")


def make_version(
    version: str = "V2.0", amendment: str = "am2",
    approval_date: str = "2026-01-01", effective_start: str = "2026-01-15",
    effective_end: str = "", rule_hash: str = "rc2",
    transition_scope: str = p.TRANSITION_ALL_SWITCH,
    new_enrollment_only: Optional[bool] = None,
    site_adoption_start: str = "",
    extraction_hash: str = "",
) -> p.ProtocolVersionRecord:
    return p.ProtocolVersionRecord(
        protocol_id="PROTO-1", protocol_version=version,
        amendment_id_or_hash=amendment, approval_date=approval_date,
        effective_start=effective_start, effective_end=effective_end,
        rule_content_hash=rule_hash,
        extraction_hash=extraction_hash or "ex-" + version,
        transition_scope=transition_scope,
        new_enrollment_only=new_enrollment_only,
        site_adoption_start=site_adoption_start)


def make_applicability(
    status: str = p.APPLICABILITY_UNIQUE_ACTIVE,
    version: str = "V2.0", amendment: str = "am2",
    anchor: str = p.ANCHOR_SCREENING, anchor_date: str = "2026-03-01",
    fingerprints: Sequence[str] = ("fp-1",),
    protocol_id: str = "PROTO-1",
    site: str = SITE_REF, subject: str = SUBJECT,
    phase: str = "",
) -> p.ProtocolApplicabilityDecision:
    return p.ProtocolApplicabilityDecision(
        subject_ref=subject, site_ref=site,
        decision_time_anchor=anchor, decision_time_anchor_date=anchor_date,
        decision_status=status, protocol_id=protocol_id,
        protocol_version=version, amendment_id_or_hash=amendment,
        phase=phase,
        feasible_version_fingerprints=fingerprints,
        stable_source_content_key="stable-key-1",
        source_locators=(make_locator("appl-1"),))


def make_plan(
    root_ids: Sequence[str] = (), rule_hash: str = "rc2",
    plan_id: str = "plan-1", verification: str = "verified",
    protocol_version: str = "V2.0", amendment: str = "am2",
    mapping_version: str = "mv1", unit_term_policy_version: str = "utp1",
) -> p.ProtocolRuleEvaluationPlan:
    return p.ProtocolRuleEvaluationPlan(
        plan_id=plan_id, protocol_id="PROTO-1",
        protocol_version=protocol_version, amendment_id_or_hash=amendment,
        rule_content_hash=rule_hash, extraction_hash="ex2",
        mapping_version=mapping_version,
        unit_term_policy_version=unit_term_policy_version,
        verification_status=verification, root_ids=tuple(root_ids))


def make_numeric_rule(
    operator: str = p.OP_NUMERIC_AT_LEAST,
    comparison: str = "at_least", threshold: str = "10",
    lower_inclusive: Optional[bool] = True,
    unit: str = "U/L", roles: Sequence[str] = ("laboratory",),
    rounding_policy: str = p.ROUNDING_BEFORE, precision: int = 0,
    window_start: str = "", window_end: str = "",
    exception_policy: str = "", alternate_roles: Sequence[str] = (),
    retest_policy: str = "", anchor: str = p.ANCHOR_SCREENING,
    value_set: Sequence[str] = (),
) -> p.ProtocolStructuredRule:
    return p.ProtocolStructuredRule(
        operator=operator,
        value_set=tuple(value_set),
        comparison=p.RuleComparison(
            comparison=comparison, threshold=threshold,
            lower_inclusive=lower_inclusive, canonical_unit=unit,
            rounding_policy=rounding_policy, rounding_precision=precision),
        required_evidence_roles=tuple(roles),
        alternate_evidence_roles=tuple(alternate_roles),
        temporal_anchor=anchor,
        evaluation_window_start=window_start,
        evaluation_window_end=window_end,
        window_start_inclusive=True if window_start else None,
        window_end_inclusive=True if window_end else None,
        exception_or_waiver_policy=exception_policy,
        retest_or_confirmation_policy=retest_policy)


def make_control_point(
    control_point_id: str = "CP-INC-1",
    control_point_type: str = p.CONTROL_INCLUSION,
    official_section_id: str = "5.1",
    official_criterion_id: str = "5.1.3",
    heading: str = "入选标准",
    structured_rule: Optional[p.ProtocolStructuredRule] = None,
    issue_expression: Optional[p.IssueExpression] = None,
    component_ids: Sequence[str] = (),
    root_kind: str = p.NODE_ATOMIC,
    source_locator: Optional[SourceLocator] = None,
    verbatim: str = "筛选期指标 X 不低于 10 U/L",
) -> p.ProtocolControlPoint:
    return p.ProtocolControlPoint(
        control_point_id=control_point_id,
        control_point_type=control_point_type,
        official_section_id=official_section_id,
        official_criterion_id=official_criterion_id,
        official_heading=heading,
        evaluation_root_kind=root_kind,
        display_order="1", nesting_path="5",
        verbatim_text=verbatim,
        source_locator=source_locator or make_locator("cp-" + control_point_id),
        source_revision_hash="revhash",
        extraction_status="verified", verification_status="verified",
        structured_rule=structured_rule,
        issue_expression=issue_expression,
        component_ids=tuple(component_ids))


def make_component(
    component_id: str, control_point_id: str,
    rule: p.ProtocolStructuredRule,
    official_criterion_id: str = "5.1.3-1",
) -> p.ProtocolComponent:
    return p.ProtocolComponent(
        component_id=component_id, control_point_id=control_point_id,
        official_criterion_id=official_criterion_id,
        parent_rule_id=control_point_id, display_order="1",
        nesting_path="5", verbatim_text="子条件",
        source_locator=make_locator("comp-" + component_id),
        source_revision_hash="h", structured_rule=rule)


def make_issue_expression(
    operator: str, component_ids: Sequence[str], at_least_n: int = 0,
) -> p.IssueExpression:
    return p.IssueExpression(
        operator=operator, component_ids=tuple(component_ids),
        at_least_n=at_least_n)


def make_binding(
    binding_id: str, component_id: str = "",
    control_point_id: str = "CP-INC-1",
    subject_ref: str = SUBJECT, site_ref: str = SITE_REF,
    role: str = "laboratory", value: str = "8", unit: str = "U/L",
    date_raw: str = "2026-03-01",
    cross_domain_ref=None, confirmed: bool = True,
    blocked: bool = False, blocked_reason: str = "",
    expected_producer_unit_id: str = "",
    table_semantic: str = "",
) -> p.RuleEvidenceBinding:
    return p.RuleEvidenceBinding(
        binding_id=binding_id, control_point_id=control_point_id,
        component_id=component_id or control_point_id,
        subject_ref=subject_ref,
        site_ref=site_ref, source_role=role,
        stable_source_event_key=f"{role}:{binding_id}",
        source_locator=make_locator(
            binding_id, table_semantic or role),
        value=value, unit=unit, date_raw=date_raw,
        relationship_confirmation=(
            p.CONFIRMATION_CONFIRMED if confirmed
            else p.CONFIRMATION_UNRESOLVED),
        cross_domain_ref=cross_domain_ref,
        expected_producer_unit_id=expected_producer_unit_id,
        producer_dependency_blocked=blocked,
        producer_dependency_reason=blocked_reason)


def make_policy(
    subtype: str = p.SUBTYPE_INCLUSION_NOT_MET,
    priority: str = "high",
    critical: bool = False, close_forbidden: bool = False,
    policy_id: str = "pol-1", version: str = "v1",
    extra_subtypes: Sequence[Tuple[str, str]] = (),
) -> p.D04PriorityPolicy:
    """Build a valid content-addressed policy."""
    priorities = [(subtype, priority)] + list(extra_subtypes)
    ch = p.policy_content_hash_value(
        policy_id=policy_id, version=version,
        rationale="合成默认优先级策略",
        subtype_priorities=priorities,
        subtype_critical=((subtype, critical),),
        subtype_machine_close_forbidden=((subtype, close_forbidden),))
    return p.D04PriorityPolicy(
        policy_id=policy_id, version=version, policy_content_hash=ch,
        rationale="合成默认优先级策略",
        subtype_priorities=priorities,
        subtype_critical=((subtype, critical),),
        subtype_machine_close_forbidden=((subtype, close_forbidden),))


def make_enrollment(
    query_context: str = p.QUERY_CONTEXT_NOT_OCCURRED,
) -> p.EnrollmentContext:
    return p.EnrollmentContext(
        subject_ref=SUBJECT, query_context=query_context,
        rationale="合成入组情境")


def make_exception(
    exception_id: str, control_point_id: str = "CP-INC-1",
    component_id: str = "",
    effect: str = p.EXCEPTION_PROTOCOL_DEFINED,
    approved: Optional[bool] = True,
    effective: Optional[bool] = True,
    window_start: str = "", window_end: str = "",
    subject: str = SUBJECT, site: str = SITE_REF,
    date_raw: str = "2026-03-01", rationale: str = "合成例外记录",
) -> p.ProtocolExceptionBinding:
    return p.ProtocolExceptionBinding(
        exception_id=exception_id, subject_ref=subject,
        site_ref=site, control_point_id=control_point_id,
        component_id=component_id or control_point_id,
        window_start=window_start, window_end=window_end,
        exception_effect=effect,
        approved_or_confirmed=approved,
        effective_at_event_time=effective,
        decision_date_raw=date_raw,
        source_locator=make_locator(exception_id, "protocol_exception"),
        rationale=rationale)


def make_conversion(
    conversion_id: str, from_unit: str, to_unit: str, factor: str,
) -> p.UnitConversionRule:
    return p.UnitConversionRule(
        conversion_id=conversion_id, from_unit=from_unit, to_unit=to_unit,
        factor=factor, content_hash_value=f"ch-{conversion_id}")


def make_retest(
    value: str = "11", unit: str = "U/L", date_raw: str = "2026-03-05",
    in_window: Optional[bool] = True, authority_ok: Optional[bool] = True,
    count_ok: Optional[bool] = True, meets: Optional[bool] = True,
    conflict: bool = False, rationale: str = "合成复测结果",
) -> p.RetestOutcome:
    return p.RetestOutcome(
        has_retest=True, retest_value=value, retest_unit=unit,
        retest_date_raw=date_raw, retest_in_allowed_window=in_window,
        retest_authority_ok=authority_ok, retest_count_ok=count_ok,
        meets_criterion=meets, conflict_with_initial=conflict,
        rationale=rationale)


def make_guidance(
    version_id: str, effective_start: str, effective_end: str = "",
    content_reference: str = "",
) -> p.RegulatoryGuidanceVersion:
    return p.RegulatoryGuidanceVersion(
        version_id=version_id, effective_start=effective_start,
        effective_end=effective_end, content_reference=content_reference)


def make_routing(
    control_point_id: str, owner_domain: str, owner_signal_type: str,
    producer_unit_id: str = "", routing_gap: str = "",
    component_id: str = "", candidate_owners: Sequence[str] = (),
) -> p.ProtocolControlRoutingRecord:
    return p.ProtocolControlRoutingRecord(
        control_point_id=control_point_id, owner_domain=owner_domain,
        owner_signal_type=owner_signal_type,
        routing_rule_version="routing-table-v1",
        routing_rule_hash="routing-table-v1",
        producer_unit_id=producer_unit_id, routing_gap=routing_gap,
        component_id=component_id,
        candidate_owners=tuple(candidate_owners),
        decision_rationale="合成路由记录")


def make_producer_ref(
    ref_id: str, owner_domain: str, producer_unit_id: str,
    marker_or_query: str = "", risk_identity: str = "",
    audience_label: str = "", priority: str = MONITORING_PRIORITY_UNKNOWN,
    control_point_id: str = "",
) -> p.ProtocolProducerReference:
    return p.ProtocolProducerReference(
        ref_id=ref_id, owner_domain=owner_domain,
        producer_unit_id=producer_unit_id,
        producer_marker_or_query_id=marker_or_query,
        producer_risk_identity_id=risk_identity,
        audience_label=audience_label, monitoring_priority=priority,
        control_point_id=control_point_id)


def make_cd_ref(
    record_id: str, subject_ref: str = SUBJECT,
    site_ref: str = SITE_REF, producer_unit: str = "d02-unit-9",
    role: str = "cm_usage", claim_scope: str = "screening_window",
    context: Optional[Mapping[str, Any]] = None,
) -> p.CrossDomainEvidenceRef:
    """Build a canonical public cross-domain evidence reference
    (frozen §7.4)."""
    from .contracts import CrossDomainEvidenceRef, cross_domain_evidence_content_hash
    loc = make_locator(record_id, "recorded_cm")
    payload = {
        "subject_ref": subject_ref, "site_ref": site_ref,
        **(context or {}),
    }
    ch = cross_domain_evidence_content_hash(
        source_locator=loc, evidence_role=role, claim_scope=claim_scope,
        context_payload=payload)
    return CrossDomainEvidenceRef(
        evidence_ref_id=f"cer-{record_id}", producer_domain="D02_cm",
        consumer_domain=p.D04_DOMAIN, evidence_role=role,
        source_locator=loc, producer_unit_id=producer_unit,
        claim_scope=claim_scope, content_hash=ch,
        context_payload=tuple(sorted(
            (k, v) for k, v in payload.items())))


def make_window(
    anchor: str = p.ANCHOR_ON_TREATMENT,
    start: str = "", end: str = "",
    precision: str = p.PRECISION_DAY,
    inclusivity: str = p.INCLUSIVITY_INCLUSIVE,
) -> p.EvaluationWindowSpec:
    return p.EvaluationWindowSpec(
        eval_anchor_kind=anchor, window_start=start, window_end=end,
        precision=precision, endpoint_inclusivity=inclusivity)


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def evaluate(
    *,
    applicability: p.ProtocolApplicabilityDecision,
    control_points: Sequence[p.ProtocolControlPoint],
    plan: p.ProtocolRuleEvaluationPlan,
    components: Optional[Mapping[str, p.ProtocolComponent]] = None,
    bindings: Sequence[p.RuleEvidenceBinding] = (),
    coverage: Optional[Mapping[str, bool]] = None,
    exceptions: Sequence[p.ProtocolExceptionBinding] = (),
    conversions: Sequence[p.UnitConversionRule] = (),
    retests: Optional[Mapping[str, p.RetestOutcome]] = None,
    enrollment: Optional[p.EnrollmentContext] = None,
    policy: Optional[p.D04PriorityPolicy] = None,
    routing: Sequence[p.ProtocolControlRoutingRecord] = (),
    windows: Optional[Mapping[str, p.EvaluationWindowSpec]] = None,
    snapshot_id: str = SNAPSHOT_ID,
) -> Tuple[p.ProtocolExpectedSetExpansion, List[p.ProtocolUnitResult]]:
    """Expand + evaluate a synthetic D04 collection through the engine."""
    expansion = p.expand_protocol_expected_set(
        project_id=PROJECT_ID, applicability=applicability,
        control_points=control_points, plan=plan, components=components,
        routing_records=routing, window_by_control_point=windows)
    results: List[p.ProtocolUnitResult] = []
    for eu in expansion.units:
        results.append(p.evaluate_protocol_unit(
            project_id=PROJECT_ID, expanded=eu, bindings=bindings,
            coverage_complete_roles=coverage, exceptions=exceptions,
            unit_conversion_rules=conversions, retest_outcomes=retests,
            enrollment_context=enrollment, priority_policy=policy,
            snapshot_id=snapshot_id))
    return expansion, results


def evaluate_slice(
    *,
    applicability: p.ProtocolApplicabilityDecision,
    control_points: Sequence[p.ProtocolControlPoint],
    plan: p.ProtocolRuleEvaluationPlan,
    components: Optional[Mapping[str, p.ProtocolComponent]] = None,
    bindings: Sequence[p.RuleEvidenceBinding] = (),
    coverage: Optional[Mapping[str, bool]] = None,
    exceptions: Sequence[p.ProtocolExceptionBinding] = (),
    conversions: Sequence[p.UnitConversionRule] = (),
    retests: Optional[Mapping[str, p.RetestOutcome]] = None,
    enrollment: Optional[p.EnrollmentContext] = None,
    policy: Optional[p.D04PriorityPolicy] = None,
    routing: Sequence[p.ProtocolControlRoutingRecord] = (),
    windows: Optional[Mapping[str, p.EvaluationWindowSpec]] = None,
    producer_refs: Sequence[p.ProtocolProducerReference] = (),
    snapshot_id: str = SNAPSHOT_ID,
) -> p.ProtocolSliceResult:
    """Evaluate a synthetic D04 collection through the slice entry point."""
    return p.evaluate_protocol_slice(
        project_id=PROJECT_ID, applicability=applicability,
        control_points=control_points, plan=plan, components=components,
        routing_records=routing, window_by_control_point=windows,
        bindings=bindings, coverage_complete_roles=coverage,
        exceptions=exceptions, unit_conversion_rules=conversions,
        retest_outcomes=retests, enrollment_context=enrollment,
        priority_policy=policy, producer_references=producer_refs,
        snapshot_id=snapshot_id)


def run_determinism_replay(
    case_number: int,
) -> Tuple[p.ProtocolExpectedSetExpansion, List[p.ProtocolUnitResult],
          p.ProtocolExpectedSetExpansion, List[p.ProtocolUnitResult]]:
    """Build a matrix case twice and return both outcomes; the caller
    asserts unit ids / candidate ids / expected-set hash are identical
    (challenge 48)."""
    case = build_protocol_challenge_matrix().by_number(case_number)
    exp1, results1 = case.build()
    exp2, results2 = case.build()
    return exp1, results1, exp2, results2


# ---------------------------------------------------------------------------
# Challenge matrix
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolExpectedUnit:
    """Expected outcome for one expanded unit identified by a substring
    of its ``control_point_id`` or by ``unit_index``.

    Exactly one of ``control_point_id_contains`` / ``unit_index`` should
    identify the unit.  ``expected_l1`` is the L1 disposition that unit
    must receive.  Optional count fields default to ``None`` (don't
    assert) so each case asserts only what the contract requires.
    """

    expected_l1: str
    control_point_id_contains: str = ""
    unit_index: Optional[int] = None
    expected_candidate_count: Optional[int] = None
    expected_query_count: Optional[int] = None
    expected_positive_subtype: str = ""
    expected_audience_label: str = ""
    expected_gap_reason: str = ""

    def matches_unit(self, unit_result: p.ProtocolUnitResult) -> bool:
        if self.unit_index is not None:
            return False  # index match handled by caller
        if self.control_point_id_contains and (
                self.control_point_id_contains
                not in unit_result.control_point_id):
            return False
        return bool(self.control_point_id_contains)


@dataclass(frozen=True)
class ProtocolChallengeCase:
    """One numbered frozen §12 challenge case.

    ``build_*`` are zero-arg factories returning the synthetic inputs
    (rebuilt fresh so cases are independent and deterministic).
    ``expected_units`` lists the expected per-unit outcomes;
    ``expected_slice`` is the optional ``(positive, negative, boundary,
    not_evaluable, not_applicable)`` slice-level tuple; the optional
    ``check_fn`` runs extra focused assertions (e.g. golden ids, payload
    determinism, language checks).  A case with a non-empty
    ``adjacent_test`` is an explicit mapping to a named adjacent accepted
    test (``module::Class::test_name`` or ``module::test_name``) that
    already covers the challenge; the matrix test resolves it against the
    real test suite.
    """

    number: int
    name: str
    category: str
    description: str
    adjacent_test: str = ""
    build_applicability: Any = field(default=make_applicability, repr=False)
    build_control_points: Any = field(default=tuple, repr=False)
    build_plan: Any = field(default=tuple, repr=False)
    build_components: Any = field(default=dict, repr=False)
    build_bindings: Any = field(default=tuple, repr=False)
    build_coverage: Any = field(default=dict, repr=False)
    build_exceptions: Any = field(default=tuple, repr=False)
    build_conversions: Any = field(default=tuple, repr=False)
    build_retests: Any = field(default=dict, repr=False)
    build_enrollment: Any = field(default=lambda: None, repr=False)
    build_policy: Any = field(default=lambda: None, repr=False)
    build_routing: Any = field(default=tuple, repr=False)
    build_windows: Any = field(default=dict, repr=False)
    build_producer_refs: Any = field(default=tuple, repr=False)
    expected_units: Tuple[ProtocolExpectedUnit, ...] = ()
    expected_set_size: Optional[int] = None
    expected_slice: Optional[Tuple[int, int, int, int, int]] = None
    expected_candidates: Optional[int] = None
    expected_queries: Optional[int] = None
    expected_coverage_gaps: Optional[int] = None
    check_fn: Optional[Callable[..., None]] = None

    # -- input collection helpers ----------------------------------------

    def _coverage(self) -> Dict[str, bool]:
        cov = dict(DEFAULT_ROLE_COVERAGE)
        cov.update(dict(self.build_coverage() or {}))
        return cov

    # -- evaluation ------------------------------------------------------

    def build(
        self, **overrides: Any,
    ) -> Tuple[p.ProtocolExpectedSetExpansion, List[p.ProtocolUnitResult]]:
        """Build inputs and run the engine, returning
        ``(expansion, [results])``."""
        snapshot_id = overrides.pop("snapshot_id", SNAPSHOT_ID)
        if overrides:
            raise TypeError(f"unexpected build overrides {sorted(overrides)}")
        applicability = self.build_applicability()
        control_points = tuple(self.build_control_points())
        plan = self.build_plan()
        if not plan:
            plan = make_plan(
                root_ids=tuple(cp.control_point_id
                               for cp in control_points))
        return evaluate(
            applicability=applicability, control_points=control_points,
            plan=plan, components=self.build_components(),
            bindings=tuple(self.build_bindings()),
            coverage=self._coverage(),
            exceptions=tuple(self.build_exceptions()),
            conversions=tuple(self.build_conversions()),
            retests=self.build_retests(),
            enrollment=self.build_enrollment(),
            policy=self.build_policy(),
            routing=tuple(self.build_routing()),
            windows=self.build_windows(),
            snapshot_id=snapshot_id)

    def build_slice(
        self,
    ) -> Tuple[p.ProtocolSliceResult, p.ProtocolExpectedSetExpansion]:
        """Run the slice entry point (subject -> ProtocolSliceResult)."""
        applicability = self.build_applicability()
        control_points = tuple(self.build_control_points())
        plan = self.build_plan()
        if not plan:
            plan = make_plan(
                root_ids=tuple(cp.control_point_id
                               for cp in control_points))
        sr = evaluate_slice(
            applicability=applicability, control_points=control_points,
            plan=plan, components=self.build_components(),
            bindings=tuple(self.build_bindings()),
            coverage=self._coverage(),
            exceptions=tuple(self.build_exceptions()),
            conversions=tuple(self.build_conversions()),
            retests=self.build_retests(),
            enrollment=self.build_enrollment(),
            policy=self.build_policy(),
            routing=tuple(self.build_routing()),
            windows=self.build_windows(),
            producer_refs=tuple(self.build_producer_refs()))
        expansion = p.expand_protocol_expected_set(
            project_id=PROJECT_ID, applicability=applicability,
            control_points=control_points, plan=plan,
            components=self.build_components(),
            routing_records=tuple(self.build_routing()),
            window_by_control_point=self.build_windows())
        return sr, expansion

    def project(self) -> pp.ProtocolSubjectJourneyProjection:
        """Run the slice entry point and project the subject journey."""
        sr, expansion = self.build_slice()
        return pp.project_protocol_subject_journey(
            sr, expansions=expansion,
            producer_references=tuple(self.build_producer_refs()))

    def expected_count(self) -> int:
        if self.expected_set_size is not None:
            return self.expected_set_size
        return len(self.expected_units)


@dataclass(frozen=True)
class ProtocolChallengeMatrix:
    """The full numbered frozen §12 challenge matrix for D04 (83 rows)."""

    cases: Tuple[ProtocolChallengeCase, ...]

    @property
    def case_count(self) -> int:
        return len(self.cases)

    @property
    def numbers(self) -> Tuple[int, ...]:
        return tuple(c.number for c in self.cases)

    def by_number(self, number: int) -> ProtocolChallengeCase:
        for c in self.cases:
            if c.number == number:
                return c
        raise KeyError(f"no challenge case #{number}")

    def by_name(self, name: str) -> ProtocolChallengeCase:
        for c in self.cases:
            if c.name == name:
                return c
        raise KeyError(f"no challenge case named {name!r}")


# -- helpers for building the cases ----------------------------------------

def _ev(
    l1: str, *, cp_contains: str = "", index: Optional[int] = None,
    cand: Optional[int] = None, query: Optional[int] = None,
    subtype: str = "", audience: str = "", gap: str = "",
) -> ProtocolExpectedUnit:
    return ProtocolExpectedUnit(
        expected_l1=l1, control_point_id_contains=cp_contains,
        unit_index=index, expected_candidate_count=cand,
        expected_query_count=query, expected_positive_subtype=subtype,
        expected_audience_label=audience, expected_gap_reason=gap)


def _positive(
    cp: str, cand: int = 1, query: Optional[int] = 1,
    subtype: str = "", audience: str = "",
) -> ProtocolExpectedUnit:
    return _ev(L1Disposition.POSITIVE, cp_contains=cp, cand=cand,
               query=query, subtype=subtype, audience=audience)


def _negative(cp: str) -> ProtocolExpectedUnit:
    return _ev(L1Disposition.NEGATIVE, cp_contains=cp)


def _boundary(cp: str, cand: Optional[int] = 1, query: int = 0) -> ProtocolExpectedUnit:
    return _ev(L1Disposition.BOUNDARY, cp_contains=cp, cand=cand,
               query=query)


def _not_evaluable(cp: str, gap: str = "") -> ProtocolExpectedUnit:
    return _ev(L1Disposition.NOT_EVALUABLE, cp_contains=cp, gap=gap)


def _gate(status: str, gap: str = "") -> ProtocolExpectedUnit:
    return _ev(status, cp_contains="protocol_applicability", gap=gap)


def _no_cp() -> Tuple[()]:
    return ()


# ---------------------------------------------------------------------------
# Golden hashes (frozen deterministic identities, challenge 48)
# ---------------------------------------------------------------------------
#
# The values below are the canonical, deterministic outputs of the frozen
# engine for the fixed synthetic inputs of the listed cases.  They are
# recomputed at test time and asserted equal -- a change in any hash
# dimension, canonical JSON ordering or evaluation path breaks the test.

GOLDEN_EXPECTED_SET_HASH: Dict[int, str] = {
    1: 'd04-eset-575e551c5bc02d835ad84030d6fbb9fc3144a56b7535358cb437933d800bd7bc',
    2: 'd04-eset-f513315f8d83b153dfa3517b10ec27dbe7ba06ff5f675bb7eef978309f3852fb',
    8: 'd04-eset-fbe021cfc06d245c48688969976c008bf87d21235ecbc61a1a3294b7d2ba86f8',
    9: 'd04-eset-a76f6c7a842fceff42d248cb3698f948d8b4cb5682eb0ff1e1dd4a89e1c90852',
    46: 'd04-eset-195af16fcc8dcb6a2b6a110bb26f4bc18611f7ec19a7b35e546df714831ae003',
    47: 'd04-eset-028fc03cce31991613234ab22de27d051e643149f8340e17537dc1f676d2e4c4',
    48: 'd04-eset-3d67bf49237e284801d37376e70434614041abe621ec6ba0b941902d07332c81',
    58: 'd04-eset-5af5c8f306e629bf0b69322a81330fe1cf5b43ab1b65578e155fd1086c0b3126',
    59: 'd04-eset-a5bfbd00a562b47629bf117c463acaa35d8c0ea5d153ebddd30f2de47a99932e',
    60: 'd04-eset-8f7fd348b8b25f4482c0259c9f4d26d9549fa951e477483eab238c9fcd6eb795',
    68: 'd04-eset-e5cdce733e99197e624b28156624d8a84de82a0a4c7bde3e41c8456b0b208402',
    71: 'd04-eset-8f7fd348b8b25f4482c0259c9f4d26d9549fa951e477483eab238c9fcd6eb795',
    72: 'd04-eset-621ad09b9f96e94cc57f260828b34848334edd9432c230cb6fd3099571ff5c8e',
    73: 'd04-eset-34b30ec4518526c76fc42f5da35e9acdbf796e7af7772e2ea03dc8abdcaacfc2',
    74: 'd04-eset-06d1483a8daaa6ac276faf6f8a62da77ad27c3dc0205c2c88df6f45ca470a54e',
    82: 'd04-eset-6cdb863a350713c4181f6d13d823806995b13b0732077eaf2e55f4bef8862d29',
    83: 'd04-eset-6779e710cbd96315bc58e3c9bcc31ed05e762d62b58d2ccd9be144b53c54423b',
}

GOLDEN_UNIT_IDS: Dict[int, Tuple[str, ...]] = {
    1: ('unit-16ba4970c74da0979cff7ae31b3ae082d056cd63fbe509e787db167b1a952bcf',),
    2: ('unit-f9f023a3f0e3abbee35cde73e77f86a5c7916a5372b7e8558724369b02992539',),
    8: ('unit-00ef56d3ef954053b208ac3937efdb6ddb02362462eb312ef672d3c8755aadcd',
        'unit-38b2cd5d193286e2cc7ccece30621cd7c0e68a57fd6f40984ad418c9fee3899a'),
    9: ('unit-268f6f11bf36216788ab239fdb7392a24abfb8cddd0dc11dc01fcf94cd47fee3',),
    46: ('unit-f9ca898ab8f074c3d04d1d3c4b633b611730c81788cf2f3dd036965065172da0',),
    47: ('unit-057ba5eaa25c3cb0bdcd9c01a6656a850bf6a92cfb2ccae2e8948beefdf4bee1',),
    48: ('unit-e61178051fbc29f55a3f8015c8fa50950c645cbb1137155c793150326ddd10d3',),
    58: ('unit-e73094a926a341eb5bd109c2ab88f949b4e8b0ebbcacc52e00b3d05c866fa3b9',),
    59: ('unit-edbc42f83adaeae98d19eefdb1b146a78851a9cf518dc55304b37d22ce0ec4c2',),
    60: ('unit-4437bd44957a8e601bc91402f78d214fcf464aa13de5db96e8ced79d260833f1',),
    68: ('unit-be76c0085b8022ccb3b893f37e0e380ebaeef435764fced19266262b9995dcdb',
         'unit-50d1bc35d1d7d8bcb5e77a5e9fb02fdd4d39e25efb168e592e91f621f7b460eb'),
    71: ('unit-4437bd44957a8e601bc91402f78d214fcf464aa13de5db96e8ced79d260833f1',),
    72: ('unit-63cf676cb667820bfa87dd636d6fda5016491c1e9083e21e8d14ddccdb346e76',),
    73: ('unit-aa9820229824768b4754231efaf1d279e4429ad963f3ec7532eb79302f9b78c8',),
    74: ('unit-3eb58666b7e81e90609b22b83c482bd3f6a6679f4f535b2c3f823ecbb4b4bab6',
         'unit-0c6d0efd36473523d9685a7d68e993c5586197ad35446790b6b8ab56f75bd832',
         'unit-77832734daa0b2f52bd68c88464a713cea8c4623271b014fabb65080ea7beaec'),
    82: ('unit-e58e0cae5f9c30ffb8ca62806a496456cd72d029966774ad8afc0315accde78c',),
    83: ('unit-6771d36b7739e93e7344d49bd6237f0bdc20c89659ba5f251420c0272510efc4',),
}

GOLDEN_COMPONENT_ASSESSMENT_IDS: Dict[int, Tuple[str, ...]] = {
    1: ('d04-ca-2b690c1f3765affb43f8001ca9772b5b991164cb3ca623aed5758d89f0a45326',),
    2: ('d04-ca-93658cdcaec96f795e4e7e4a4d280de922276024930589cf745ac69712584407',),
    8: ('d04-ca-44c5f933882927d83cd5aba2a7393948ff4a9856c61ef4de62bc6fccf367ffff',
        'd04-ca-63269022d58a55f865f4758ee6d74629b57364e56968139a44d5096428bb12b0',
        'd04-ca-656e1817fe3c5d611cee7938bf41a4e3f6ed44d5a0d9654eb74d7fd91a383e36',
        'd04-ca-e2024c6f7a7cae62418cfaff9c81c60d72f1c655e3ef66af9023c39b6da0330a'),
    9: ('d04-ca-3d8f5674498b5592d5a0d44b016ed13f7c43b91dd2b66c6432a34bfb4f10c804',
        'd04-ca-e6fe330ebe07bf45c45b67ca7be95211c0d79a2bbfaa43dc15db3dc82597df1c'),
    46: ('d04-ca-c5fe4c16f75ca62750b3c7092570af945328b1ac76d28b4f4efb874abaefcc02',),
    47: ('d04-ca-56e4c832ef9a5ddac39818ae5861f415472cb35d1e0f8f0aa2d0ddaa0709bdbe',),
    48: ('d04-ca-ca113a149b45a0126a1478b06591df2c92aba3c962ec5d6366e9c66aa7ccac24',),
    58: ('d04-ca-76ed657804927fe497cbd7d59a25b11eb073ac6d4cf5a8618c1a8dbf5088a088',
         'd04-ca-c240ab8a75fc4ed0092d600f352d6b7a104ace574c7a9da70e48f3c129b1bf00'),
    59: ('d04-ca-035206c7fff3864c427406fb724a6665288fd536e590bcba96b9273f66b915db',
         'd04-ca-d0cb66f55c3c734e9b8a2159b3e9ec28f8f07495038221f4ba7060cf85af58f9'),
    60: (),
    68: ('d04-ca-5689bc7bdd58307dc78b41dbd90aa7d135b7f25b53ef385e71979cf2fba04be9',
         'd04-ca-5eee6801a2eb494e93395a8989a163d5bc5ecb30a4c8bb83bc8da874e2255c65'),
    71: (),
    72: ('d04-ca-16b44568afec663db7fe8909a71ecb98f896218551628b2b150c2811c2e84e8e',
         'd04-ca-4dbed10e46d060626d3bc54d4a99885546ed21ff61b995edd1516e6b731a549f'),
    73: ('d04-ca-0da8a3ae814b46819bfc30bf22c5963f7f3d486fbe01898097a6e4eee7a008b2',
         'd04-ca-fb2c5399af1ea2ebaa6c90655794e61811aac55ed39a94bfab7cf2ababce3269'),
    74: ('d04-ca-1b91bf1184c6aca1c8f4d18bba189729a62a1b0311a776e6c76d87ac94c5d0ed',
         'd04-ca-29b3638b1720c01c11045ec6426f950235c59fc8c2bf8c7638406a47831ee83a',
         'd04-ca-8863dae6ee074480b0b9d4079f105282f255b29461adb0d83b8e70089cc80d89',
         'd04-ca-9c4ab599f4eb824c67416b1110a621e84ea63c56f3a6f65c8cad4e48952daaf8',
         'd04-ca-addc5207d04ae8099cd9df6997d313b9a69d163ef984570ba0617f010515a3d8',
         'd04-ca-c3c8f65d958c1f4cb301b74e4b72f7efadc900eb6eb5d3b1a0918693203eb4ac',
         'd04-ca-f61d44430a0c6f5d9fb8a9dbf00491dc114edf219d0cf44842117682dac11bb2',
         'd04-ca-fdb86fe6dc2a39f7d1f87419283d0e169b0e7da8f15ae6c6fedbe7ae6c4dfe07',
         'd04-ca-fdd200bc7f95c425ea4ac8ac385e621ec3ee44a6f72f7043e90ca5777c79b149'),
    82: (),
    83: (),
}

GOLDEN_CANDIDATE_IDS: Dict[int, Tuple[str, ...]] = {
    1: ('cand-91f2a4bde7b558c9004bca0ca1b197fc59cc6cedfe0a72b1217b9b984e3d5503',),
    2: (),
    8: ('cand-a7902c7390bd693904f65add94049140cabbceb3b6c828f56025320833d00650',),
    9: ('cand-30b55d36e01112c8ed806f3ae2099023576a10fb17e4b826b294df8258ba3884',),
    46: ('cand-6bc987caeab7bad7cb5e013370424228278389e1e2cf95375bc0ef37936c3ad3',),
    47: ('cand-42b6d653e3d7522e2bafdc1545e194b73175cec55969d34f94be33046c0ff559',),
    48: ('cand-a38b62519f1f987a7e16791d0f133196a6c15bebdafade5e5b3bc1394447ff3a',),
    58: ('cand-957e3e00c171cdaab6dfc154970ea6891d1ff973059efdb9c96d2d229ac18dd5',),
    59: (),
    60: (),
    68: ('cand-b3e5128c7ab4fa81f78bd3dc657c65ce844255d29166658ce514fdedaa4c7a32',),
    71: (),
    72: (),
    73: ('cand-25de16b689374580b008889f84c7da7baa1a04480395092b8d2eea32a5eecd21',),
    74: ('cand-3d854a0d6850dbedfae06b614618814ae9e3fb7f25ccaff2169b3c9d3d6148d0',),
    82: (),
    83: (),
}

GOLDEN_PROJECTION_PAYLOAD_HASH: Dict[int, str] = {
    1: 'd511bcdd0cc113165864ab59d11e6e6971a0cf099ab401f28bb314f7023adbf3',
    2: '4b9400d8f2f718ae6af016c90ae271e73c15d9509c87b492dd70cbf625a78f9d',
    8: '87c346ca24685bcc32378293ac0732e58514d6900a5c13c6acece109aa56ad8f',
    9: '97f639633e444353e26fa44bc9a1e1e3401636a904a5323d46a0d59304c22da0',
    46: '6ba8ea6a88535d6c1505c7ec93a37156a4fb6baf58841be8212813d9ba8305a9',
    47: '932dc6a22b1467b1cb3c55b95f9617bb4ec7573a05761378523d9fbfbeda834e',
    48: '7166628d77435b819ae9780bc168c9cf04e1f301bc1445eaaa66b3bf9770a7f4',
    58: '395d795a495b56429aebd4fab8b3a18779cd29e4a08fe68f516925e573e7c6ad',
    59: '9dae6a4c6fc85e860dec502f7132a9543b81ddac7c3d84a1b4123e9b59257fd0',
    60: 'c822594f4f7124075134adcbc67f7bd0c60efe7a1762d1aa8e6ef907085dfb89',
    68: '41dd8377a193b23101dbcacefa4e2bf85047a901754fbfd0f8475144223c6f8f',
    71: 'c822594f4f7124075134adcbc67f7bd0c60efe7a1762d1aa8e6ef907085dfb89',
    72: '39c644797425f12d932bf95a04b5b11e1190ae6f715b67822af678fcbb3cf920',
    73: '7a455e2a8193e7d397933f5db8c7857bf87d0e24ec3cfad21216f7a3b2096eeb',
    74: 'aea94ffc6838422da0243cba2eca52f9a28a52e878cb0b7192938a0ef1bbb2fb',
    82: '64eb90b70b7f5550f69c611e5ac58dd643fb4c59338beb6613b8c088b5c14bb3',
    83: '7e24ef6f4cefc48996ee11abb1567427a0ba3530cc5135aed8323f7e66812130',
}


def _payload_hash(proj: pp.ProtocolSubjectJourneyProjection) -> str:
    """Canonical content hash of the projected subject journey payload."""
    return content_hash(proj.canonical_payload())


# ---------------------------------------------------------------------------
# 83-case matrix
# ---------------------------------------------------------------------------

def build_protocol_challenge_matrix() -> ProtocolChallengeMatrix:
    """Build the frozen §12 83-case synthetic challenge matrix.

    Every frozen challenge row is represented as an executable case with
    explicit expected per-unit L1 assertions, or -- for the N->N+1
    lifecycle, shared flag normalization and adjacent-slice rows already
    accepted by a dedicated adjacent test -- an explicit named adjacent
    accepted-test mapping (``adjacent_test``).  The matrix test verifies
    both paths.

    Layout (frozen §12 numbering):

    1-6   inclusion/exclusion core dispositions (incl. IE/DV evidence
          gates); 7-10 protocol text fidelity; 11-15 applicability/
          regulatory; 16-24 numeric/unit/rounding/retest; 25-28
          exceptions; 29-33 producer routing (D02/D03/D05); 34-40
          evidence identity and sequence anchors; 41-45
          discontinuation / Query / coverage gap; 46-48 journey +
          determinism; 49-55 lifecycle + adjacent regression; 56-58
          producer risk identity + package determinate-with-gap;
          59-71 identity/window/routing/gate invariants; 72-74 package
          expressions; 75-76 query contexts; 77-78 amendment
          transitions; 79-83 cross-domain fact / age / retest / wording
          / order independence.
    """
    cases: List[ProtocolChallengeCase] = []

    # -- 1-6 core dispositions -------------------------------------------

    cases.append(ProtocolChallengeCase(
        number=1, name="inclusion_not_met_positive", category="positive",
        description=("challenge 1/16: unique active version, value below "
                     "the inclusion lower bound -> "
                     "inclusion_requirement_not_met positive"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP01-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b1", control_point_id="CP01-INC", value="8"),),
        expected_units=(_positive(
            "CP01-INC", subtype=p.SUBTYPE_INCLUSION_NOT_MET,
            audience="入选条件待核实"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=2, name="inclusion_met_negative", category="negative",
        description="challenge 2: full evidence satisfies the inclusion",
        build_control_points=lambda: (make_control_point(
            control_point_id="CP02-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b2", control_point_id="CP02-INC", value="12"),),
        expected_units=(_negative("CP02-INC"),),
        expected_slice=(0, 1, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
    ))

    cases.append(ProtocolChallengeCase(
        number=3, name="exclusion_present_positive", category="positive",
        description="challenge 3: exclusion condition determinately present",
        build_control_points=lambda: (make_control_point(
            control_point_id="CP03-EXC",
            control_point_type=p.CONTROL_EXCLUSION,
            official_criterion_id="5.2.1", heading="排除标准",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_EXISTS,
                exists_target_role="concomitant_medication",
                required_evidence_roles=("concomitant_medication",),
                temporal_anchor=p.ANCHOR_SCREENING,
                evaluation_window_start="2026-02-01",
                evaluation_window_end="2026-03-01",
                window_start_inclusive=True, window_end_inclusive=True,
                exception_or_waiver_policy="")),),
        build_bindings=lambda: (make_binding(
            "b3", control_point_id="CP03-EXC", role="concomitant_medication",
            value="有", date_raw="2026-02-10",
            table_semantic="recorded_cm"),),
        expected_units=(_positive(
            "CP03-EXC", subtype=p.SUBTYPE_EXCLUSION_PRESENT,
            audience="排除条件待核实"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=4, name="exclusion_absent_negative", category="negative",
        description=("challenge 4: exclusion condition clearly absent with "
                     "complete source coverage -> negative (no DV zero-row "
                     "inference)"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP04-EXC",
            control_point_type=p.CONTROL_EXCLUSION,
            official_criterion_id="5.2.2", heading="排除标准",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_EXISTS,
                exists_target_role="concomitant_medication",
                required_evidence_roles=("concomitant_medication",),
                temporal_anchor=p.ANCHOR_SCREENING)),),
        expected_units=(_negative("CP04-EXC"),),
        expected_slice=(0, 1, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
    ))

    cases.append(ProtocolChallengeCase(
        number=5, name="ie_summary_only_not_evaluable", category="not_evaluable",
        description=("challenge 5: IEYN=Yes without per-criterion evidence "
                     "is auxiliary-only -> not_evaluable"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP05-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b5", control_point_id="CP05-INC", role="aggregate_ie_status",
            value="Yes", table_semantic="ie_summary"),),
        build_coverage=lambda: {"laboratory": False},
        expected_units=(_not_evaluable(
            "CP05-INC", gap=p.GAP_IE_SUMMARY_ONLY),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=6, name="ie_zero_rows_not_negative", category="not_evaluable",
        description=("challenge 6: no failed IE row / zero DV rows alone "
                     "can never prove negative"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP06-EXC",
            control_point_type=p.CONTROL_EXCLUSION,
            official_criterion_id="5.2.3", heading="排除标准",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_EXISTS,
                exists_target_role="medical_history",
                required_evidence_roles=("medical_history",),
                temporal_anchor=p.ANCHOR_SCREENING)),),
        build_coverage=lambda: {"medical_history": False},
        expected_units=(_not_evaluable(
            "CP06-EXC", gap=p.GAP_RECORD_MISSING_UNPROVEN),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    # -- 7-10 protocol text fidelity -------------------------------------

    cases.append(ProtocolChallengeCase(
        number=7, name="official_hierarchy_preserved", category="fidelity",
        description=("challenge 7: official numbering, parent rule, "
                     "component hierarchy and display order preserved"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP07-PKG",
            root_kind=p.NODE_PACKAGE,
            issue_expression=make_issue_expression(
                p.EXPR_AND, ("C7a", "C7b")),
            component_ids=("C7a", "C7b"),
            official_section_id="5.1", official_criterion_id="5.1.7",
            heading="入选标准（组合）",
            verbatim="以下条件需同时满足"),),
        build_components=lambda: {
            "C7a": make_component("C7a", "CP07-PKG",
                                  make_numeric_rule(threshold="10")),
            "C7b": make_component("C7b", "CP07-PKG",
                                  make_numeric_rule(threshold="5")),
        },
        build_bindings=lambda: (
            make_binding("b7a", component_id="C7a",
                         control_point_id="CP07-PKG", value="12"),
            make_binding("b7b", component_id="C7b",
                         control_point_id="CP07-PKG", value="3"),
        ),
        expected_set_size=1,
        expected_units=(_negative("CP07-PKG"),),
        expected_slice=(0, 1, 0, 0, 0),
        check_fn=_check_hierarchy_preserved,
    ))

    cases.append(ProtocolChallengeCase(
        number=8, name="any_vs_all_package_units", category="package",
        description=("challenge 8: '以下任一' and '以下全部' each generate "
                     "one package EvaluationUnit with different issue "
                     "expressions and different determinate logic"),
        build_control_points=lambda: (
            make_control_point(
                control_point_id="CP08-ANY",
                root_kind=p.NODE_PACKAGE,
                official_criterion_id="5.1.8",
                heading="入选标准（任一）",
                issue_expression=make_issue_expression(
                    p.EXPR_AND, ("C8a", "C8b")),
                component_ids=("C8a", "C8b")),
            make_control_point(
                control_point_id="CP08-ALL",
                root_kind=p.NODE_PACKAGE,
                official_criterion_id="5.1.9",
                heading="入选标准（全部）",
                issue_expression=make_issue_expression(
                    p.EXPR_OR, ("C8c", "C8d")),
                component_ids=("C8c", "C8d")),
        ),
        build_components=lambda: {
            "C8a": make_component("C8a", "CP08-ANY",
                                  make_numeric_rule(threshold="10")),
            "C8b": make_component("C8b", "CP08-ANY",
                                  make_numeric_rule(threshold="5")),
            "C8c": make_component("C8c", "CP08-ALL",
                                  make_numeric_rule(threshold="10")),
            "C8d": make_component("C8d", "CP08-ALL",
                                  make_numeric_rule(threshold="5")),
        },
        build_bindings=lambda: (
            make_binding("b8a", component_id="C8a",
                         control_point_id="CP08-ANY", value="12"),
            make_binding("b8c", component_id="C8c",
                         control_point_id="CP08-ALL", value="8"),
        ),
        expected_set_size=2,
        expected_units=(
            _negative("CP08-ANY"),
            _positive("CP08-ALL"),
        ),
        expected_slice=(1, 1, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
        check_fn=_check_any_all_units,
    ))

    cases.append(ProtocolChallengeCase(
        number=9, name="package_components_not_in_expected_set",
        category="package",
        description=("challenge 9: component assessments never enter "
                     "expected-set/L1/L2/lifecycle; the package unit does "
                     "not hide boundary/not_evaluable components"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP09-PKG",
            root_kind=p.NODE_PACKAGE,
            issue_expression=make_issue_expression(
                p.EXPR_OR, ("C9a", "C9b")),
            component_ids=("C9a", "C9b")),),
        build_components=lambda: {
            "C9a": make_component("C9a", "CP09-PKG",
                                  make_numeric_rule(threshold="10")),
            "C9b": make_component("C9b", "CP09-PKG",
                                  make_numeric_rule(threshold="5")),
        },
        build_bindings=lambda: (
            make_binding("b9a", component_id="C9a",
                         control_point_id="CP09-PKG", value="8"),),
        expected_set_size=1,
        expected_units=(_positive("CP09-PKG"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
        expected_coverage_gaps=1,
        check_fn=_check_package_assessments,
    ))

    cases.append(ProtocolChallengeCase(
        number=10, name="derived_id_not_official", category="fidelity",
        description=("challenge 10: no official criterion id -> stable "
                     "derived id that is visibly derived, never "
                     "masquerading as official numbering"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP10-INC",
            official_criterion_id="",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b10", control_point_id="CP10-INC", value="12"),),
        expected_units=(_negative("CP10-INC"),),
        expected_slice=(0, 1, 0, 0, 0),
        check_fn=_check_derived_id,
    ))

    # -- 11-15 applicability and regulatory ------------------------------

    cases.append(ProtocolChallengeCase(
        number=11, name="site_not_adopted_old_version", category="applicability",
        description=("challenge 11: latest amendment not yet enabled at "
                     "the site -> evaluate by the old version"),
        build_applicability=lambda: p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01",
            versions=(
                make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                             "", "rc1", p.TRANSITION_ALL_SWITCH),
                make_version("V2.0", "am2", "2026-01-01", "2026-01-15",
                             "", "rc2", p.TRANSITION_ALL_SWITCH,
                             site_adoption_start="2026-04-01"),
            ),
            site_adoption_start="2026-01-01",
            stable_source_content_key="stable-key-1"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP11-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b11", control_point_id="CP11-INC", value="8"),),
        expected_units=(_positive("CP11-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
        check_fn=_check_version_v1,
    ))

    cases.append(ProtocolChallengeCase(
        number=12, name="same_day_adoption_boundary", category="applicability",
        description=("challenge 12: same-day site enablement with undefined "
                     "endpoint -> applicability gate boundary"),
        build_applicability=lambda: p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01",
            versions=(make_version(),),
            site_adoption_start="2026-03-01",
            stable_source_content_key="stable-key-1"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP12-INC",
            structured_rule=make_numeric_rule()),),
        expected_set_size=1,
        expected_units=(_gate(L1Disposition.BOUNDARY),),
        expected_slice=(0, 0, 1, 0, 0),
        expected_candidates=0, expected_queries=0,
    ))

    cases.append(ProtocolChallengeCase(
        number=13, name="two_feasible_versions_boundary", category="applicability",
        description=("challenge 13: two versions both feasible with source "
                     "support -> applicability gate boundary, no N medical "
                     "units"),
        build_applicability=lambda: p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01",
            versions=(
                make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                             "2026-06-30", "rc1", p.TRANSITION_ALL_SWITCH),
                make_version("V2.0", "am2", "2026-01-01", "2026-01-15",
                             "", "rc2", p.TRANSITION_ALL_SWITCH),
            ),
            site_adoption_start="2026-01-01",
            stable_source_content_key="stable-key-1"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP13-INC",
            structured_rule=make_numeric_rule()),),
        expected_set_size=1,
        expected_units=(_gate(L1Disposition.BOUNDARY),),
        expected_slice=(0, 0, 1, 0, 0),
        expected_candidates=0, expected_queries=0,
    ))

    cases.append(ProtocolChallengeCase(
        number=14, name="missing_approval_dates_not_evaluable",
        category="applicability",
        description=("challenge 14: key approval/site dates missing -> "
                     "applicability gate not_evaluable"),
        build_applicability=lambda: p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01",
            versions=(make_version(approval_date=""),),
            site_adoption_start="",
            stable_source_content_key="stable-key-1"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP14-INC",
            structured_rule=make_numeric_rule()),),
        expected_set_size=1,
        expected_units=(_gate(
            L1Disposition.NOT_EVALUABLE,
            gap=p.GAP_APPLICABILITY_UNDETERMINED),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=15, name="gcp_version_switch", category="applicability",
        description=("challenge 15: China GCP 2020 -> 2026 switch at "
                     "2026-09-01 is data-driven; the kernel hardcodes no "
                     "regulatory calendar"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP15-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b15", control_point_id="CP15-INC", value="12"),),
        expected_units=(_negative("CP15-INC"),),
        expected_slice=(0, 1, 0, 0, 0),
        check_fn=_check_gcp_switch,
    ))

    # -- 16-24 numeric/unit/rounding/retest ------------------------------

    cases.append(ProtocolChallengeCase(
        number=16, name="below_lower_bound_positive", category="positive",
        description=("challenge 16: value clearly below the inclusion lower "
                     "bound -> positive"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP16-INC",
            structured_rule=make_numeric_rule(threshold="50", unit="kg"),),
        ),
        build_bindings=lambda: (make_binding(
            "b16", control_point_id="CP16-INC", value="45", unit="kg"),),
        expected_units=(_positive(
            "CP16-INC", subtype=p.SUBTYPE_INCLUSION_NOT_MET),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=17, name="exact_threshold_inclusive_determinate",
        category="determinate",
        description=("challenge 17: value exactly at threshold with "
                     "explicit inclusivity -> determinate negative"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP17-INC",
            structured_rule=make_numeric_rule(
                threshold="10", lower_inclusive=True)),),
        build_bindings=lambda: (make_binding(
            "b17", control_point_id="CP17-INC", value="10"),),
        expected_units=(_negative("CP17-INC"),),
        expected_slice=(0, 1, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
    ))

    cases.append(ProtocolChallengeCase(
        number=18, name="unstated_equality_boundary", category="boundary",
        description=("challenge 18: equality semantics undefined -> "
                     "boundary (clue, no Query)"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP18-INC",
            structured_rule=make_numeric_rule(lower_inclusive=None)),),
        build_bindings=lambda: (make_binding(
            "b18", control_point_id="CP18-INC", value="10"),),
        expected_units=(_boundary("CP18-INC", cand=1, query=0),),
        expected_slice=(0, 0, 1, 0, 0),
        expected_candidates=1, expected_queries=0,
    ))

    cases.append(ProtocolChallengeCase(
        number=19, name="unit_conversion_determinate", category="determinate",
        description=("challenge 19: versioned unit conversion -> determinate "
                     "evaluation"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP19-INC",
            structured_rule=make_numeric_rule(threshold="10")),),
        build_bindings=lambda: (make_binding(
            "b19", control_point_id="CP19-INC", value="1.2", unit="mmol/L"),),
        build_conversions=lambda: (
            make_conversion("cv1", "mmol/L", "U/L", "10"),),
        expected_units=(_negative("CP19-INC"),),
        expected_slice=(0, 1, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
    ))

    cases.append(ProtocolChallengeCase(
        number=20, name="unknown_unit_not_evaluable", category="not_evaluable",
        description=("challenge 20: unknown unit with no conversion basis "
                     "-> not_evaluable"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP20-INC",
            structured_rule=make_numeric_rule(threshold="10")),),
        build_bindings=lambda: (make_binding(
            "b20", control_point_id="CP20-INC", value="1.2", unit="XX"),),
        expected_units=(_not_evaluable(
            "CP20-INC", gap=p.GAP_UNIT_UNCONVERTIBLE),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=21, name="rounding_before_after_differ", category="determinate",
        description=("challenge 21: compare-before vs compare-after rounding "
                     "produce predictably different results"),
        build_control_points=lambda: (
            make_control_point(
                control_point_id="CP21-BEFORE",
                structured_rule=make_numeric_rule(
                    threshold="1.1", rounding_policy=p.ROUNDING_BEFORE,
                    precision=1),
                official_criterion_id="5.1.21a"),
            make_control_point(
                control_point_id="CP21-AFTER",
                structured_rule=make_numeric_rule(
                    threshold="1.1", rounding_policy=p.ROUNDING_AFTER,
                    precision=1),
                official_criterion_id="5.1.21b"),
        ),
        build_bindings=lambda: (
            make_binding("b21a", control_point_id="CP21-BEFORE",
                         value="1.05"),
            make_binding("b21b", control_point_id="CP21-AFTER",
                         value="1.05"),
        ),
        expected_set_size=2,
        expected_units=(
            _positive("CP21-BEFORE"),
            _negative("CP21-AFTER"),
        ),
        expected_slice=(1, 1, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=22, name="retest_in_window_covers_negative",
        category="retest",
        description=("challenge 22: rule allows retest; qualifying retest "
                     "in window covers the initial -> negative + "
                     "counterevidence"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP22-INC",
            structured_rule=make_numeric_rule(
                retest_policy="retest-v1")),),
        build_bindings=lambda: (make_binding(
            "b22", control_point_id="CP22-INC", value="8"),),
        build_retests=lambda: {"CP22-INC": make_retest()},
        expected_units=(_negative("CP22-INC"),),
        expected_slice=(0, 1, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
        check_fn=_check_counterevidence,
    ))

    cases.append(ProtocolChallengeCase(
        number=23, name="retest_not_satisfied_positive", category="retest",
        description=("challenge 23: retest window/count/authority "
                     "explicitly not satisfied -> the original determinate "
                     "problem stays positive"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP23-INC",
            structured_rule=make_numeric_rule(
                retest_policy="retest-v1")),),
        build_bindings=lambda: (make_binding(
            "b23", control_point_id="CP23-INC", value="8"),),
        build_retests=lambda: {
            "CP23-INC": make_retest(in_window=False)},
        expected_units=(_positive("CP23-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=24, name="conflicting_retests_boundary", category="boundary",
        description=("challenge 24: two equally authoritative retests with "
                     "no rule priority -> boundary"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP24-INC",
            structured_rule=make_numeric_rule(
                retest_policy="retest-v1")),),
        build_bindings=lambda: (make_binding(
            "b24", control_point_id="CP24-INC", value="8"),),
        build_retests=lambda: {
            "CP24-INC": make_retest(conflict=True)},
        expected_units=(_boundary("CP24-INC", cand=1, query=0),),
        expected_slice=(0, 0, 1, 0, 0),
        expected_candidates=1, expected_queries=0,
    ))

    # -- 25-28 exceptions ------------------------------------------------

    cases.append(ProtocolChallengeCase(
        number=25, name="protocol_defined_exception_negative",
        category="exception",
        description=("challenge 25: active-protocol pre-allowed exception "
                     "precisely bound -> negative + counterevidence"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP25-INC",
            structured_rule=make_numeric_rule(
                exception_policy="protocol_exception_allowed")),),
        build_bindings=lambda: (make_binding(
            "b25", control_point_id="CP25-INC", value="8"),),
        build_exceptions=lambda: (make_exception(
            "ex25", control_point_id="CP25-INC"),),
        expected_units=(_negative("CP25-INC"),),
        expected_slice=(0, 1, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
        check_fn=_check_counterevidence,
    ))

    cases.append(ProtocolChallengeCase(
        number=26, name="waiver_wording_not_enough", category="exception",
        description=("challenge 26: '已批准豁免' wording, retrospective/"
                     "unapproved records cannot rewrite a non-conformance "
                     "to negative"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP26-INC",
            structured_rule=make_numeric_rule(
                exception_policy="protocol_exception_allowed")),),
        build_bindings=lambda: (make_binding(
            "b26", control_point_id="CP26-INC", value="8"),),
        build_exceptions=lambda: (
            make_exception(
                "ex26", control_point_id="CP26-INC",
                effect=p.EXCEPTION_RETROSPECTIVE,
                approved=None, effective=None),
            make_exception(
                "ex26b", control_point_id="CP26-INC",
                effect=p.EXCEPTION_PROTOCOL_DEFINED,
                approved=False, effective=False),
        ),
        expected_units=(_positive("CP26-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=27, name="investigator_judgment_missing_not_evaluable",
        category="not_evaluable",
        description=("challenge 27: investigator judgment is a required "
                     "input but not recorded -> not_evaluable; never "
                     "inferred from clinical common sense"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP27-INC",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_INVESTIGATOR_JUDGMENT,
                investigator_judgment_required=True,
                required_evidence_roles=("laboratory",),
                temporal_anchor=p.ANCHOR_SCREENING)),),
        build_bindings=lambda: (make_binding(
            "b27", control_point_id="CP27-INC", value="8"),),
        expected_units=(_not_evaluable(
            "CP27-INC", gap=p.GAP_INVESTIGATOR_JUDGMENT_MISSING),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=28, name="urgent_hazard_context_not_negative",
        category="exception",
        description=("challenge 28: urgent-hazard exception fully "
                     "documented explains the disposition but does not "
                     "erase the deviation fact"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP28-INC",
            structured_rule=make_numeric_rule(
                exception_policy="protocol_exception_allowed")),),
        build_bindings=lambda: (make_binding(
            "b28", control_point_id="CP28-INC", value="8"),),
        build_exceptions=lambda: (make_exception(
            "ex28", control_point_id="CP28-INC",
            effect=p.EXCEPTION_URGENT_HAZARD),),
        expected_units=(_positive("CP28-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
    ))

    # -- 29-33 producer routing ------------------------------------------

    cases.append(ProtocolChallengeCase(
        number=29, name="d02_cm_routed_out", category="routing",
        description=("challenge 29/56: D02-owned CM control point is "
                     "excluded from the D04 expected-set; zero D04 "
                     "unit/risk/Query; producer reference passes through"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP29-CM",
            control_point_type=p.CONTROL_PROHIBITED_OR_RESTRICTED_TREATMENT,
            official_section_id="6.1", official_criterion_id="6.1.2",
            heading="禁限用要求",
            structured_rule=make_numeric_rule(
                roles=("concomitant_medication",),
                anchor=p.ANCHOR_ON_TREATMENT)),),
        build_routing=lambda: (make_routing(
            "CP29-CM", p.OWNER_D02, p.OWNER_D02,
            producer_unit_id="d02-unit-29"),),
        build_producer_refs=lambda: (make_producer_ref(
            "ref29", p.OWNER_D02, "d02-unit-29",
            marker_or_query="marker-d02-29",
            risk_identity="rid-d02-29",
            audience_label="禁限用要求待核实",
            priority=MONITORING_PRIORITY_MEDIUM,
            control_point_id="CP29-CM"),),
        expected_set_size=0,
        expected_units=(),
        expected_slice=(0, 0, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
    ))

    cases.append(ProtocolChallengeCase(
        number=30, name="d02_ambiguous_identity_no_escalation",
        category="routing",
        description=("challenge 30: D02-only ambiguous drug identity never "
                     "escalates to a determinate D04 risk"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP30-CM",
            control_point_type=p.CONTROL_PROHIBITED_OR_RESTRICTED_TREATMENT,
            official_section_id="6.1", official_criterion_id="6.1.3",
            heading="禁限用要求",
            structured_rule=make_numeric_rule(
                roles=("concomitant_medication",),
                anchor=p.ANCHOR_ON_TREATMENT)),),
        build_routing=lambda: (make_routing(
            "CP30-CM", p.OWNER_D02, p.OWNER_D02,
            producer_unit_id="d02-unit-30"),),
        expected_set_size=0,
        expected_slice=(0, 0, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
    ))

    cases.append(ProtocolChallengeCase(
        number=31, name="d03_ip_action_routed_out", category="routing",
        description=("challenge 31/57: D03 study-drug pause/reduce/stop "
                     "control points route to D03; D04 builds no "
                     "unit/risk/Query"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP31-IP",
            control_point_type=p.CONTROL_DOSE_OR_TREATMENT_MANAGEMENT,
            official_section_id="6.2", official_criterion_id="6.2.1",
            heading="给药处置要求",
            structured_rule=make_numeric_rule(
                roles=("ip_exposure",), anchor=p.ANCHOR_ON_TREATMENT)),),
        build_routing=lambda: (make_routing(
            "CP31-IP", p.OWNER_D03, p.OWNER_D03,
            producer_unit_id="d03-unit-31"),),
        expected_set_size=0,
        expected_slice=(0, 0, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
    ))

    cases.append(ProtocolChallengeCase(
        number=32, name="d03_dependency_not_evaluable", category="routing",
        description=("challenge 32: D03 episode/assignment not_evaluable "
                     "blocks the dependent D04 unit -> not_evaluable"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP32-INC",
            structured_rule=make_numeric_rule(
                roles=("ip_exposure",)),),),
        build_bindings=lambda: (make_binding(
            "b32", control_point_id="CP32-INC", role="ip_exposure",
            value="50", blocked=True,
            blocked_reason="D03 上游评价暂无法评价",
            expected_producer_unit_id="d03-unit-32"),),
        expected_units=(_not_evaluable(
            "CP32-INC", gap=p.GAP_PRODUCER_DEPENDENCY),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=33, name="d05_visit_window_stub_routed", category="routing",
        description=("challenge 33/69: planned visit/assessment/sample "
                     "windows route to the D05 synthetic producer stub; "
                     "D04 never copies the window algorithm"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP33-VISIT",
            control_point_type=p.CONTROL_REQUIRED_PROCEDURE_OR_ASSESSMENT,
            official_section_id="7.1", official_criterion_id="7.1.1",
            heading="计划访视/评估要求",
            structured_rule=make_numeric_rule(
                roles=("visit",), anchor=p.ANCHOR_ON_TREATMENT)),),
        build_routing=lambda: (make_routing(
            "CP33-VISIT", p.OWNER_D05, p.OWNER_D05,
            routing_gap="d05_stub_not_frozen"),),
        expected_set_size=0,
        expected_slice=(0, 0, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
    ))

    # -- 34-40 evidence identity and sequence anchors --------------------

    cases.append(ProtocolChallengeCase(
        number=34, name="alternate_source_allowed_negative",
        category="evidence",
        description=("challenge 34: alternate lab/diagnostic source only "
                     "when the rule explicitly allows it"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP34-INC",
            structured_rule=make_numeric_rule(
                roles=("laboratory",),
                alternate_roles=("other_assessment",)),),),
        build_bindings=lambda: (make_binding(
            "b34", control_point_id="CP34-INC",
            role="other_assessment", value="12"),),
        expected_units=(_negative("CP34-INC"),),
        expected_slice=(0, 1, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
    ))

    cases.append(ProtocolChallengeCase(
        number=35, name="wrong_identity_fails_closed", category="evidence",
        description=("challenge 35: wrong subject/site/rule bindings are "
                     "excluded; no valid evidence remains -> not_evaluable"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP35-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (
            make_binding("b35a", control_point_id="CP35-INC",
                         value="8", subject_ref="OTHER-1"),
            make_binding("b35b", control_point_id="CP35-INC",
                         value="8", site_ref="SITE99"),
        ),
        build_coverage=lambda: {"laboratory": True},
        expected_units=(_not_evaluable(
            "CP35-INC", gap=p.GAP_SOURCE_ROLE_NOT_COVERED),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=36, name="same_record_id_different_subject_fails_closed",
        category="evidence",
        description=("challenge 36/63: same record id on a different "
                     "subject cannot establish a cross-domain link"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP36-EXC",
            control_point_type=p.CONTROL_EXCLUSION,
            official_criterion_id="5.2.6", heading="排除标准",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_EXISTS,
                exists_target_role="concomitant_medication",
                required_evidence_roles=("concomitant_medication",),
                temporal_anchor=p.ANCHOR_SCREENING,
                evaluation_window_start="2026-02-01",
                evaluation_window_end="2026-03-01",
                window_start_inclusive=True, window_end_inclusive=True)),),
        build_bindings=lambda: (make_binding(
            "b36", control_point_id="CP36-EXC",
            role="concomitant_medication", value="有",
            date_raw="2026-02-10",
            cross_domain_ref=make_cd_ref(
                record_id="CM#36", subject_ref="SYN-002",
                producer_unit="d02-unit-36"),
            table_semantic="recorded_cm"),),
        build_coverage=lambda: {"concomitant_medication": True},
        expected_units=(_not_evaluable(
            "CP36-EXC", gap=p.GAP_RELATION_UNCONFIRMED),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=37, name="partial_date_boundary", category="boundary",
        description=("challenge 37: partial date possibly hitting/missing "
                     "the window -> boundary"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP37-SEQ",
            control_point_type=p.CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT,
            official_section_id="8.1", official_criterion_id="8.1.1",
            heading="知情与入组时序",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_SEQUENCE, order_direction="before",
                anchor_role_a="consent", anchor_role_b="randomization",
                required_evidence_roles=("consent", "randomization"),
                temporal_anchor=p.ANCHOR_RANDOMIZATION)),),
        build_bindings=lambda: (
            make_binding("b37a", control_point_id="CP37-SEQ",
                         role="consent", date_raw="2026-03",
                         value=""),
            make_binding("b37b", control_point_id="CP37-SEQ",
                         role="randomization", date_raw="2026-03-01",
                         value=""),
        ),
        expected_units=(_boundary("CP37-SEQ", cand=1, query=0),),
        expected_slice=(0, 0, 1, 0, 0),
        expected_candidates=1, expected_queries=0,
    ))

    cases.append(ProtocolChallengeCase(
        number=38, name="consent_after_procedure_positive",
        category="sequence",
        description=("challenge 38: consent after the first "
                     "protocol-required procedure -> determinate sequence "
                     "conflict (positive)"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP38-SEQ",
            control_point_type=p.CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT,
            official_section_id="8.1", official_criterion_id="8.1.2",
            heading="知情与入组时序",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_SEQUENCE, order_direction="before",
                anchor_role_a="consent", anchor_role_b="procedure",
                required_evidence_roles=("consent", "procedure"),
                temporal_anchor=p.ANCHOR_RANDOMIZATION)),),
        build_bindings=lambda: (
            make_binding("b38a", control_point_id="CP38-SEQ",
                         role="consent", date_raw="2026-03-02",
                         value=""),
            make_binding("b38b", control_point_id="CP38-SEQ",
                         role="procedure", date_raw="2026-03-01",
                         value=""),
        ),
        expected_units=(_positive(
            "CP38-SEQ", subtype=p.SUBTYPE_CONSENT_SEQUENCE_INCONSISTENT,
            audience="知情与入组时序待核实"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=39, name="anchors_not_interchangeable", category="sequence",
        description=("challenge 39: screening/randomization/first-dose "
                     "anchors are distinct roles; a screening record cannot "
                     "satisfy the randomization role"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP39-SEQ",
            control_point_type=p.CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT,
            official_section_id="8.1", official_criterion_id="8.1.3",
            heading="知情与入组时序",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_SEQUENCE, order_direction="before",
                anchor_role_a="consent", anchor_role_b="randomization",
                required_evidence_roles=("consent", "randomization"),
                temporal_anchor=p.ANCHOR_RANDOMIZATION)),),
        build_bindings=lambda: (
            make_binding("b39a", control_point_id="CP39-SEQ",
                         role="consent", date_raw="2026-02-20",
                         value=""),
            make_binding("b39b", control_point_id="CP39-SEQ",
                         role="screening", date_raw="2026-02-01",
                         value=""),
        ),
        expected_units=(_not_evaluable(
            "CP39-SEQ", gap=p.GAP_SOURCE_ROLE_NOT_COVERED),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=40, name="ie_dv_semantics_separate", category="evidence",
        description=("challenge 40: pre-enrollment IE semantics are "
                     "separate from post-enrollment DV; a DV/deviation "
                     "listing never overrides per-item IE evidence"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP40-EXC",
            control_point_type=p.CONTROL_EXCLUSION,
            official_criterion_id="5.2.7", heading="排除标准",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_EXISTS,
                exists_target_role="medical_history",
                required_evidence_roles=("medical_history",),
                temporal_anchor=p.ANCHOR_SCREENING)),),
        build_bindings=lambda: (make_binding(
            "b40", control_point_id="CP40-EXC",
            role="deviation_listing", value="无偏离",
            table_semantic="deviation_listing"),),
        build_coverage=lambda: {"medical_history": False},
        expected_units=(_not_evaluable(
            "CP40-EXC", gap=p.GAP_FREE_TEXT_ONLY),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    # -- 41-45 discontinuation / Query / coverage gap --------------------

    cases.append(ProtocolChallengeCase(
        number=41, name="discontinuation_inconsistent_positive",
        category="discontinuation",
        description=("challenge 41: trigger reached but disposition "
                     "determinately inconsistent -> D04 positive; study "
                     "drug stop actions stay D03-owned"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP41-DISC",
            control_point_type=p.CONTROL_DISCONTINUATION_OR_WITHDRAWAL,
            official_section_id="7.3", official_criterion_id="7.3.1",
            heading="退出标准",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_DISCONTINUATION_TRIGGER,
                trigger_comparison=p.RuleComparison(
                    comparison="above", threshold="5",
                    canonical_unit="xULN"),
                expected_disposition_values=("withdrawn", "terminated"),
                required_evidence_roles=("laboratory",),
                temporal_anchor=p.ANCHOR_ON_TREATMENT)),),
        build_bindings=lambda: (
            make_binding("b41l", control_point_id="CP41-DISC",
                         role="laboratory", value="6", unit="xULN",
                         date_raw="2026-03-01"),
            make_binding("b41d", control_point_id="CP41-DISC",
                         role="disposition", value="active",
                         date_raw="2026-03-10"),
        ),
        expected_units=(_positive(
            "CP41-DISC", subtype=p.SUBTYPE_DISCONTINUATION_INCONSISTENT,
            audience="退出或终止参与标准待核实"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=42, name="discontinuation_missing_input_not_evaluable",
        category="discontinuation",
        description=("challenge 42: D04-native discontinuation input "
                     "missing -> not_evaluable (IP pause/stop inputs are "
                     "D03-owned)"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP42-DISC",
            control_point_type=p.CONTROL_DISCONTINUATION_OR_WITHDRAWAL,
            official_section_id="7.3", official_criterion_id="7.3.2",
            heading="退出标准",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_DISCONTINUATION_TRIGGER,
                trigger_comparison=p.RuleComparison(
                    comparison="above", threshold="5",
                    canonical_unit="xULN"),
                expected_disposition_values=("withdrawn", "terminated"),
                required_evidence_roles=("laboratory",),
                temporal_anchor=p.ANCHOR_ON_TREATMENT)),),
        build_bindings=lambda: (make_binding(
            "b42l", control_point_id="CP42-DISC",
            role="laboratory", value="6", unit="xULN",
            date_raw="2026-03-01"),),
        expected_units=(_not_evaluable("CP42-DISC"),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=43, name="three_part_query_enrolled", category="query",
        description=("challenge 43: three-part Query contains version, "
                     "clause, facts and action; enrolled context requests "
                     "PD evaluation by the accountable party"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP43-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b43", control_point_id="CP43-INC", value="8"),),
        build_enrollment=lambda: make_enrollment(
            p.QUERY_CONTEXT_ENROLLED),
        expected_units=(_positive("CP43-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
        check_fn=_check_three_part_query,
    ))

    cases.append(ProtocolChallengeCase(
        number=44, name="query_forbids_confirmed_pd", category="query",
        description=("challenge 44: Query must not contain confirmed/major "
                     "PD, reported or closed language in any context"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP44-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b44", control_point_id="CP44-INC", value="8"),),
        expected_units=(_positive("CP44-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
        check_fn=_check_query_no_pd_language,
    ))

    cases.append(ProtocolChallengeCase(
        number=45, name="not_evaluable_gap_notice_no_query",
        category="coverage_gap",
        description=("challenge 45: not_evaluable unit generates a "
                     "coverage-gap notice bound to unit/reason/protocol "
                     "locators/reachable sources; no candidate/risk/L2 "
                     "Query; never writes determinate non-compliance"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP45-INC",
            structured_rule=make_numeric_rule()),),
        build_coverage=lambda: {"laboratory": False},
        expected_units=(_not_evaluable(
            "CP45-INC", gap=p.GAP_SOURCE_ROLE_NOT_COVERED),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
        check_fn=_check_gap_notice,
    ))

    # -- 46-48 journey + determinism -------------------------------------

    cases.append(ProtocolChallengeCase(
        number=46, name="journey_actual_anchor_and_unresolved",
        category="journey",
        description=("challenge 46: journey events anchor on actual "
                     "dates/visits; events without any precise date go to "
                     "the unresolved area (no fabricated time point)"),
        build_control_points=lambda: (
            make_control_point(
                control_point_id="CP46-INC",
                structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b46", control_point_id="CP46-INC", value="8"),),
        expected_units=(_positive("CP46-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        check_fn=_check_journey_anchor,
    ))

    cases.append(ProtocolChallengeCase(
        number=47, name="journey_labels_typed_join_reachable",
        category="journey",
        description=("challenge 47: journey keeps concrete Chinese labels, "
                     "typed join and one-hop drill-back to protocol text/"
                     "evidence/Query; tracks stay distinct"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP47-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b47", control_point_id="CP47-INC", value="8"),),
        build_enrollment=lambda: make_enrollment(p.QUERY_CONTEXT_ENROLLED),
        expected_units=(_positive("CP47-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        check_fn=_check_journey_labels,
    ))

    cases.append(ProtocolChallengeCase(
        number=48, name="deterministic_rerun", category="determinism",
        description=("challenge 48: same input rerun -> unit/candidate/"
                     "payload hashes stable"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP48-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b48", control_point_id="CP48-INC", value="8"),),
        expected_units=(_positive("CP48-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        check_fn=_check_determinism,
    ))

    # -- 49-55 lifecycle + adjacent regression ---------------------------

    cases.append(ProtocolChallengeCase(
        number=49, name="linked_negative_closes_low_medium",
        category="lifecycle",
        description=("challenge 49: N+1 exact linked-negative + complete "
                     "coverage closes only low/medium risks"),
        adjacent_test=("test_protocol_slice.py::TestLifecycleIntegration::"
                       "test_machine_close_requires_linked_negative_and_"
                       "closed_ledger"),
    ))

    cases.append(ProtocolChallengeCase(
        number=50, name="high_not_machine_closed", category="lifecycle",
        description=("challenge 50: high, user-confirmed and "
                     "identity_ambiguous risks are never machine-closed; "
                     "mapped to the test that proves all three protected "
                     "states refuse machine close with the real close "
                     "prerequisites present"),
        adjacent_test=("test_protocol_slice.py::TestLifecycleIntegration::"
                       "test_high_user_confirmed_and_identity_ambiguous_"
                       "never_machine_close"),
    ))

    cases.append(ProtocolChallengeCase(
        number=51, name="data_correction_resolved_by_data",
        category="lifecycle",
        description=("challenge 51: data correction with unchanged lineage "
                     "is resolved_by_data"),
        adjacent_test=("test_protocol_slice.py::TestLifecycleIntegration::"
                       "test_machine_close_requires_linked_negative_and_"
                       "closed_ledger"),
    ))

    cases.append(ProtocolChallengeCase(
        number=52, name="lineage_change_superseded", category="lifecycle",
        description=("challenge 52: protocol/rule/mapping/algorithm "
                     "lineage change -> superseded, never resolved_by_data; "
                     "mapped to the test that executes the reconcile and "
                     "asserts SUPERSEDED plus closed == ()"),
        adjacent_test=("test_lifecycle_projection.py::"
                       "TestSupersedeAndTerminate::"
                       "test_supersede_on_lineage_change"),
    ))

    cases.append(ProtocolChallengeCase(
        number=53, name="new_rule_lineage_new_run", category="lifecycle",
        description=("challenge 53: a new natural-language special rule "
                     "forms a new versioned lineage and only affects "
                     "subsequent Runs; past results stay immutable"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP53-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b53", control_point_id="CP53-INC", value="8"),),
        expected_units=(_positive("CP53-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        check_fn=_check_new_lineage,
    ))

    cases.append(ProtocolChallengeCase(
        number=54, name="counts_never_contaminate", category="counts",
        description=("challenge 54: source/evidence/candidate/risk/Query "
                     "counts stay separate; coverage-gap notices never "
                     "enter Query count"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP54-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b54", control_point_id="CP54-INC", value="8"),),
        build_enrollment=lambda: make_enrollment(p.QUERY_CONTEXT_ENROLLED),
        expected_units=(_positive("CP54-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
        check_fn=_check_counts,
    ))

    cases.append(ProtocolChallengeCase(
        number=55, name="adjacent_regression_suites", category="regression",
        description=("challenge 55: D01-D03, R2 and R3 adjacent regressions "
                     "stay green; port 8911 stays stopped"),
        adjacent_test=("test_ip_challenge_matrix.py::TestAdjacentRegression"),
    ))

    # -- 56-58 producer identity + determinate-with-gap ------------------

    cases.append(ProtocolChallengeCase(
        number=56, name="d02_single_producer_risk_no_dup",
        category="routing",
        description=("challenge 56: D02 prohibited-CM positive and D04 "
                     "share no control point/stable event; only the "
                     "producer risk + Query exist; the overview typed-link "
                     "carries the producer identity"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP56-CM",
            control_point_type=p.CONTROL_PROHIBITED_OR_RESTRICTED_TREATMENT,
            official_section_id="6.1", official_criterion_id="6.1.4",
            heading="禁限用要求",
            structured_rule=make_numeric_rule(
                roles=("concomitant_medication",),
                anchor=p.ANCHOR_ON_TREATMENT)),),
        build_routing=lambda: (make_routing(
            "CP56-CM", p.OWNER_D02, p.OWNER_D02,
            producer_unit_id="d02-unit-56"),),
        build_producer_refs=lambda: (make_producer_ref(
            "ref56", p.OWNER_D02, "d02-unit-56",
            marker_or_query="marker-d02-56",
            risk_identity="rid-d02-56",
            audience_label="禁限用要求待核实",
            priority=MONITORING_PRIORITY_MEDIUM,
            control_point_id="CP56-CM"),),
        expected_set_size=0,
        expected_slice=(0, 0, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
        check_fn=_check_producer_overview,
    ))

    cases.append(ProtocolChallengeCase(
        number=57, name="d03_action_single_producer_risk",
        category="routing",
        description=("challenge 57: D03 unsupported_ip_action and D04 share "
                     "no study-drug action unit; only the producer risk is "
                     "kept, D04 never upgrades or copies it"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP57-IP",
            control_point_type=p.CONTROL_DOSE_OR_TREATMENT_MANAGEMENT,
            official_section_id="6.2", official_criterion_id="6.2.2",
            heading="给药处置要求",
            structured_rule=make_numeric_rule(
                roles=("ip_exposure",), anchor=p.ANCHOR_ON_TREATMENT)),),
        build_routing=lambda: (make_routing(
            "CP57-IP", p.OWNER_D03, p.OWNER_D03,
            producer_unit_id="d03-unit-57"),),
        build_producer_refs=lambda: (make_producer_ref(
            "ref57", p.OWNER_D03, "d03-unit-57",
            marker_or_query="marker-d03-57",
            risk_identity="rid-d03-57",
            audience_label="研究药暴露信息待核实",
            priority=MONITORING_PRIORITY_MEDIUM,
            control_point_id="CP57-IP"),),
        expected_set_size=0,
        expected_slice=(0, 0, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
        check_fn=_check_producer_overview,
    ))

    cases.append(ProtocolChallengeCase(
        number=58, name="package_determinate_with_gap", category="package",
        description=("challenge 58: package issue_true + not_evaluable -> "
                     "one determinate positive unit with one candidate/"
                     "Query; L0 partial + gap notice block domain "
                     "completeness"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP58-PKG",
            root_kind=p.NODE_PACKAGE,
            issue_expression=make_issue_expression(
                p.EXPR_OR, ("C58a", "C58b")),
            component_ids=("C58a", "C58b")),),
        build_components=lambda: {
            "C58a": make_component("C58a", "CP58-PKG",
                                   make_numeric_rule(threshold="10")),
            "C58b": make_component("C58b", "CP58-PKG",
                                   make_numeric_rule(threshold="5")),
        },
        build_bindings=lambda: (make_binding(
            "b58a", component_id="C58a",
            control_point_id="CP58-PKG", value="8"),),
        expected_set_size=1,
        expected_units=(_positive("CP58-PKG"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
        expected_coverage_gaps=1,
        check_fn=_check_determinate_package,
    ))

    # -- 59-71 identity/window/routing/gate invariants -------------------

    cases.append(ProtocolChallengeCase(
        number=59, name="pipe_ids_distinct_identity", category="identity",
        description=("challenge 59: control point/component ids containing "
                     "'|' still produce distinct canonical unit/assessment "
                     "ids; package unit ids never mix with assessment ids"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP59|PKG",
            root_kind=p.NODE_PACKAGE,
            issue_expression=make_issue_expression(
                p.EXPR_AND, ("C59|a", "C59|b")),
            component_ids=("C59|a", "C59|b")),),
        build_components=lambda: {
            "C59|a": make_component("C59|a", "CP59|PKG",
                                    make_numeric_rule(threshold="10")),
            "C59|b": make_component("C59|b", "CP59|PKG",
                                    make_numeric_rule(threshold="5")),
        },
        build_bindings=lambda: (
            make_binding("b59a", component_id="C59|a",
                         control_point_id="CP59|PKG", value="12"),
            make_binding("b59b", component_id="C59|b",
                         control_point_id="CP59|PKG", value="3"),
        ),
        expected_set_size=1,
        expected_units=(_negative("CP59|PKG"),),
        expected_slice=(0, 1, 0, 0, 0),
        check_fn=_check_pipe_ids,
    ))

    cases.append(ProtocolChallengeCase(
        number=60, name="two_versions_one_gate", category="gate",
        description=("challenge 60/71: two feasible versions produce one "
                     "applicability gate unit, never N medical units, and "
                     "input order does not matter"),
        build_applicability=lambda: make_applicability(
            status=p.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
            fingerprints=("fp-a", "fp-b")),
        build_control_points=lambda: (
            make_control_point(
                control_point_id="CP60-INC",
                structured_rule=make_numeric_rule()),
            make_control_point(
                control_point_id="CP60-EXC",
                control_point_type=p.CONTROL_EXCLUSION,
                official_criterion_id="5.2.8",
                structured_rule=make_numeric_rule()),
        ),
        expected_set_size=1,
        expected_units=(_gate(L1Disposition.BOUNDARY),),
        expected_slice=(0, 0, 1, 0, 0),
        expected_candidates=0, expected_queries=0,
        check_fn=_check_gate_order,
    ))

    cases.append(ProtocolChallengeCase(
        number=61, name="n1_preallowed_exception_reevaluates_negative",
        category="lifecycle",
        description=("challenge 61: N positive; N+1 adds an already-effective "
                     "pre-allowed exception -> re-evaluated negative + "
                     "counterevidence; history is not rewritten"),
        adjacent_test=("test_protocol_slice.py::TestRetestAndExceptions::"
                       "test_n1_pre_allowed_exception_reevaluates_negative"),
    ))

    cases.append(ProtocolChallengeCase(
        number=62, name="lineage_change_not_resolved_by_data",
        category="identity",
        description=("challenge 62: mapping/rule lineage change keeps the "
                     "classifier stable and goes superseded, never "
                     "resolved_by_data; mapped to the test that executes "
                     "the reconcile and asserts SUPERSEDED plus "
                     "closed == ()"),
        adjacent_test=("test_lifecycle_projection.py::"
                       "TestSupersedeAndTerminate::"
                       "test_supersede_on_lineage_change"),
    ))

    cases.append(ProtocolChallengeCase(
        number=63, name="cross_domain_join_rejected", category="identity",
        description=("challenge 63: same record id on a different subject, "
                     "date-proximate rows and unconfirmed relations are all "
                     "rejected cross-domain joins"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP63-EXC",
            control_point_type=p.CONTROL_EXCLUSION,
            official_criterion_id="5.2.9", heading="排除标准",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_EXISTS,
                exists_target_role="concomitant_medication",
                required_evidence_roles=("concomitant_medication",),
                temporal_anchor=p.ANCHOR_SCREENING,
                evaluation_window_start="2026-02-01",
                evaluation_window_end="2026-03-01",
                window_start_inclusive=True, window_end_inclusive=True)),),
        build_bindings=lambda: (make_binding(
            "b63", control_point_id="CP63-EXC",
            role="concomitant_medication", value="有",
            date_raw="2026-02-10", confirmed=False,
            table_semantic="recorded_cm"),),
        build_coverage=lambda: {"concomitant_medication": True},
        expected_units=(_not_evaluable(
            "CP63-EXC", gap=p.GAP_EVIDENCE_IDENTITY_UNCONFIRMED),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=64, name="site_transfer_lineage", category="identity",
        description=("challenge 64: site stays in the risk lineage scope; "
                     "a centre-transfer cannot silently merge identities"),
        adjacent_test=("test_protocol_slice.py::TestRemainingSemantics::"
                       "test_site_ref_stays_in_lineage"),
    ))

    cases.append(ProtocolChallengeCase(
        number=65, name="event_time_not_run_time_version",
        category="applicability",
        description=("challenge 65: V1 enrollment criterion evaluated at "
                     "enrollment time; V2 treatment rules by new window; "
                     "Run date never back-dates V2 onto V1 events"),
        adjacent_test=("test_protocol_slice.py::TestApplicability::"
                       "test_event_time_not_run_time_selects_version"),
    ))

    cases.append(ProtocolChallengeCase(
        number=66, name="candidate_flags_force_high", category="lifecycle",
        description=("challenge 66: rights_or_safety_critical or "
                     "machine_close_forbidden true forces severity=high "
                     "via the shared adapter even when the caller passes "
                     "medium, and the persisted high severity refuses "
                     "machine close; mapped to the shared lifecycle test "
                     "that proves medium -> persisted high -> refusal in "
                     "one test.  The reader-only strict flag readers "
                     "(test_shared_domain_protocol.py::"
                     "TestCandidateCriticalityFlags) remain supporting "
                     "coverage, not the producer mapping"),
        adjacent_test=("test_lifecycle_projection.py::"
                       "TestCriticalityFlagNormalization::"
                       "test_flagged_high_instance_refuses_machine_close"),
    ))

    cases.append(ProtocolChallengeCase(
        number=67, name="owner_competition_single_routing_gate",
        category="routing",
        description=("challenge 67: owner routing competition produces "
                     "exactly one protocol_routing not_evaluable gate; no "
                     "duplicate expected units across domains"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP67-CM",
            control_point_type=p.CONTROL_OTHER_PROTOCOL_REQUIREMENT,
            official_section_id="6.3", official_criterion_id="6.3.1",
            heading="方案要求",
            structured_rule=make_numeric_rule(
                roles=("concomitant_medication",),
                anchor=p.ANCHOR_ON_TREATMENT)),),
        build_routing=lambda: (make_routing(
            "CP67-CM", p.OWNER_UNRESOLVED, p.OWNER_UNRESOLVED,
            routing_gap="owner_competition_d02_d03",
            candidate_owners=(p.OWNER_D02, p.OWNER_D03)),),
        expected_set_size=1,
        expected_units=(_ev(
            L1Disposition.NOT_EVALUABLE,
            cp_contains="CP67-CM",
            gap=p.GAP_ROUTING_UNRESOLVED),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=68, name="two_windows_distinct_identity", category="identity",
        description=("challenge 68: same control point, same on_treatment "
                     "anchor, two disjoint evaluation windows -> different "
                     "unit ids and risk identities; window A linked-negative "
                     "never closes window B"),
        build_control_points=lambda: (
            make_control_point(
                control_point_id="CP68-INC",
                structured_rule=make_numeric_rule()),
            make_control_point(
                control_point_id="CP68-INC2",
                official_criterion_id="5.1.68b",
                structured_rule=make_numeric_rule()),
        ),
        build_windows=lambda: {
            "CP68-INC": make_window(
                p.ANCHOR_ON_TREATMENT, "2026-01-01", "2026-01-31"),
            "CP68-INC2": make_window(
                p.ANCHOR_ON_TREATMENT, "2026-02-01", "2026-02-28"),
        },
        build_plan=lambda: make_plan(root_ids=("CP68-INC", "CP68-INC2")),
        build_bindings=lambda: (make_binding(
            "b68", control_point_id="CP68-INC", value="8"),),
        expected_set_size=2,
        expected_units=(),
        expected_slice=(1, 0, 0, 1, 0),
        check_fn=_check_two_windows,
    ))

    cases.append(ProtocolChallengeCase(
        number=69, name="split_failure_single_routing_gate",
        category="routing",
        description=("challenge 69: when a control point cannot be split "
                     "across owners, exactly one routing gate is generated "
                     "(never one risk per competing domain)"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP69-SPLIT",
            control_point_type=p.CONTROL_OTHER_PROTOCOL_REQUIREMENT,
            official_section_id="6.3", official_criterion_id="6.3.2",
            heading="跨域要求",
            structured_rule=make_numeric_rule(
                roles=("visit", "ip_exposure"),
                anchor=p.ANCHOR_ON_TREATMENT)),),
        build_routing=lambda: (make_routing(
            "CP69-SPLIT", p.OWNER_UNRESOLVED, p.OWNER_UNRESOLVED,
            routing_gap="cannot_split_d03_d05",
            candidate_owners=(p.OWNER_D03, p.OWNER_D05)),),
        expected_set_size=1,
        expected_units=(_ev(
            L1Disposition.NOT_EVALUABLE,
            cp_contains="CP69-SPLIT",
            gap=p.GAP_ROUTING_UNRESOLVED),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=70, name="adapter_flag_normalization", category="lifecycle",
        description=("challenge 70: the shared lifecycle adapter forces "
                     "effective priority high before establishing a risk "
                     "when either flag is true; D01-D03 behavior stays "
                     "unchanged"),
        adjacent_test=("test_protocol_slice.py::TestLifecycleIntegration::"
                       "test_machine_close_forbidden_forces_high_and_"
                       "blocks_close"),
    ))

    cases.append(ProtocolChallengeCase(
        number=71, name="many_cps_still_one_gate", category="gate",
        description=("challenge 71: two feasible versions x multiple "
                     "control points still produce one subject-level "
                     "applicability gate; affected ids stay in context, "
                     "the L1 denominator is 1"),
        build_applicability=lambda: make_applicability(
            status=p.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
            fingerprints=("fp-a", "fp-b")),
        build_control_points=lambda: (
            make_control_point(
                control_point_id="CP71-INC",
                structured_rule=make_numeric_rule()),
            make_control_point(
                control_point_id="CP71-EXC",
                control_point_type=p.CONTROL_EXCLUSION,
                official_criterion_id="5.2.10",
                structured_rule=make_numeric_rule()),
            make_control_point(
                control_point_id="CP71-DISC",
                control_point_type=p.CONTROL_DISCONTINUATION_OR_WITHDRAWAL,
                official_criterion_id="7.3.3", heading="退出标准",
                structured_rule=make_numeric_rule(
                    anchor=p.ANCHOR_ON_TREATMENT)),
        ),
        expected_set_size=1,
        expected_units=(_gate(L1Disposition.BOUNDARY),),
        expected_slice=(0, 0, 1, 0, 0),
        expected_candidates=0, expected_queries=0,
    ))

    # -- 72-74 package expressions ---------------------------------------

    cases.append(ProtocolChallengeCase(
        number=72, name="any_of_one_met_one_ne_negative",
        category="package",
        description=("challenge 72: '满足以下任一项' one met + one "
                     "not_evaluable -> package L1 negative, L0/domain "
                     "incomplete, no candidate/Query"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP72-PKG",
            root_kind=p.NODE_PACKAGE,
            issue_expression=make_issue_expression(
                p.EXPR_AND, ("C72a", "C72b")),
            component_ids=("C72a", "C72b")),),
        build_components=lambda: {
            "C72a": make_component("C72a", "CP72-PKG",
                                   make_numeric_rule(threshold="10")),
            "C72b": make_component("C72b", "CP72-PKG",
                                   make_numeric_rule(threshold="5")),
        },
        build_bindings=lambda: (make_binding(
            "b72", component_id="C72a",
            control_point_id="CP72-PKG", value="12"),),
        expected_set_size=1,
        expected_units=(_negative("CP72-PKG"),),
        expected_slice=(0, 1, 0, 0, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
        check_fn=_check_any_ne_negative,
    ))

    cases.append(ProtocolChallengeCase(
        number=73, name="all_of_one_unmet_one_ne_positive",
        category="package",
        description=("challenge 73: '需同时满足全部' one unmet + one "
                     "not_evaluable -> package L1 positive, L0/domain "
                     "incomplete, one risk/Query listing decisive and "
                     "unresolved components"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP73-PKG",
            root_kind=p.NODE_PACKAGE,
            issue_expression=make_issue_expression(
                p.EXPR_OR, ("C73a", "C73b")),
            component_ids=("C73a", "C73b")),),
        build_components=lambda: {
            "C73a": make_component("C73a", "CP73-PKG",
                                   make_numeric_rule(threshold="10")),
            "C73b": make_component("C73b", "CP73-PKG",
                                   make_numeric_rule(threshold="5")),
        },
        build_bindings=lambda: (make_binding(
            "b73", component_id="C73a",
            control_point_id="CP73-PKG", value="8"),),
        build_enrollment=lambda: make_enrollment(p.QUERY_CONTEXT_ENROLLED),
        build_policy=lambda: make_policy(),
        expected_set_size=1,
        expected_units=(_positive("CP73-PKG"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
        expected_coverage_gaps=1,
        check_fn=_check_all_ne_positive,
    ))

    cases.append(ProtocolChallengeCase(
        number=74, name="at_least_n_all_variants", category="package",
        description=("challenge 74: AT_LEAST_N constant true -> positive, "
                     "constant false -> negative, variable -> "
                     "not_evaluable; input order never changes the result; "
                     "component assessments stay out of coverage/lifecycle"),
        build_control_points=lambda: (
            make_control_point(
                control_point_id="CP74-TRUE",
                root_kind=p.NODE_PACKAGE,
                official_criterion_id="5.1.74a",
                issue_expression=make_issue_expression(
                    p.EXPR_AT_LEAST_N, ("C74a", "C74b", "C74c"),
                    at_least_n=2),
                component_ids=("C74a", "C74b", "C74c")),
            make_control_point(
                control_point_id="CP74-FALSE",
                root_kind=p.NODE_PACKAGE,
                official_criterion_id="5.1.74b",
                issue_expression=make_issue_expression(
                    p.EXPR_AT_LEAST_N, ("C74d", "C74e", "C74f"),
                    at_least_n=2),
                component_ids=("C74d", "C74e", "C74f")),
            make_control_point(
                control_point_id="CP74-VAR",
                root_kind=p.NODE_PACKAGE,
                official_criterion_id="5.1.74c",
                issue_expression=make_issue_expression(
                    p.EXPR_AT_LEAST_N, ("C74g", "C74h", "C74i"),
                    at_least_n=2),
                component_ids=("C74g", "C74h", "C74i")),
        ),
        build_components=lambda: {
            "C74a": make_component("C74a", "CP74-TRUE",
                                   make_numeric_rule(threshold="10")),
            "C74b": make_component("C74b", "CP74-TRUE",
                                   make_numeric_rule(threshold="5")),
            "C74c": make_component("C74c", "CP74-TRUE",
                                   make_numeric_rule(threshold="1")),
            "C74d": make_component("C74d", "CP74-FALSE",
                                   make_numeric_rule(threshold="10")),
            "C74e": make_component("C74e", "CP74-FALSE",
                                   make_numeric_rule(threshold="5")),
            "C74f": make_component("C74f", "CP74-FALSE",
                                   make_numeric_rule(threshold="1")),
            "C74g": make_component("C74g", "CP74-VAR",
                                   make_numeric_rule(threshold="10")),
            "C74h": make_component("C74h", "CP74-VAR",
                                   make_numeric_rule(threshold="5")),
            "C74i": make_component("C74i", "CP74-VAR",
                                   make_numeric_rule(threshold="1")),
        },
        build_bindings=lambda: (
            # TRUE: two unmet -> issue count >= 2 always true.
            make_binding("b74a", component_id="C74a",
                         control_point_id="CP74-TRUE", value="8"),
            make_binding("b74b", component_id="C74b",
                         control_point_id="CP74-TRUE", value="3"),
            # FALSE: all met -> issue count 0 always.
            make_binding("b74d", component_id="C74d",
                         control_point_id="CP74-FALSE", value="12"),
            make_binding("b74e", component_id="C74e",
                         control_point_id="CP74-FALSE", value="8"),
            make_binding("b74f", component_id="C74f",
                         control_point_id="CP74-FALSE", value="2"),
            # VAR: one unmet + one met + one not_evaluable -> 1 or 2.
            make_binding("b74g", component_id="C74g",
                         control_point_id="CP74-VAR", value="8"),
            make_binding("b74h", component_id="C74h",
                         control_point_id="CP74-VAR", value="12"),
        ),
        expected_set_size=3,
        expected_units=(
            _positive("CP74-TRUE"),
            _negative("CP74-FALSE"),
            _not_evaluable("CP74-VAR"),
        ),
        expected_slice=(1, 1, 0, 1, 0),
        check_fn=_check_at_least_n,
    ))

    # -- 75-76 query contexts --------------------------------------------

    cases.append(ProtocolChallengeCase(
        number=75, name="not_enrolled_query_screening_only",
        category="query",
        description=("challenge 75: screening not met, determinately not "
                     "randomized/enrolled -> Query only verifies screening "
                     "conclusion/records; no '评估是否构成方案偏离'"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP75-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b75", control_point_id="CP75-INC", value="8"),),
        build_enrollment=lambda: make_enrollment(
            p.QUERY_CONTEXT_NOT_OCCURRED),
        expected_units=(_positive("CP75-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
        check_fn=_check_query_not_occurred,
    ))

    cases.append(ProtocolChallengeCase(
        number=76, name="unresolved_enrollment_query_state_first",
        category="query",
        description=("challenge 76: randomization/enrollment state "
                     "unresolved -> Query first asks to verify the state "
                     "and states insufficient data"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP76-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b76", control_point_id="CP76-INC", value="8"),),
        expected_units=(_positive("CP76-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
        check_fn=_check_query_unresolved,
    ))

    # -- 77-78 amendment transitions -------------------------------------

    cases.append(ProtocolChallengeCase(
        number=77, name="new_enrollment_only_amendment_grandfather",
        category="applicability",
        description=("challenge 77: V2 enabled at the site but the "
                     "transition applies only to new enrollment; an "
                     "already-enrolled subject's past eligibility stays on "
                     "V1 -- site adoption alone never back-dates V2"),
        build_applicability=lambda: p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_RANDOMIZATION,
            event_anchor_date="2026-02-01",
            subject_enrollment_date="2026-01-10",
            versions=(
                make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                             "", "rc1", p.TRANSITION_ALL_SWITCH),
                make_version("V2.0", "am2", "2026-01-01", "2026-01-15",
                             "", "rc2", p.TRANSITION_NEW_ENROLLMENT_ONLY,
                             new_enrollment_only=True,
                             site_adoption_start="2026-01-20"),
            ),
            site_adoption_start="2026-01-01",
            stable_source_content_key="stable-key-1"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP77-INC",
            structured_rule=make_numeric_rule()),),
        build_bindings=lambda: (make_binding(
            "b77", control_point_id="CP77-INC", value="8"),),
        expected_units=(_positive("CP77-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
        check_fn=_check_version_v1,
    ))

    cases.append(ProtocolChallengeCase(
        number=78, name="reconsent_switch_single_gate",
        category="applicability",
        description=("challenge 78: a revision switching at re-consent/next "
                     "visit with a missing or ambiguous trigger timing is "
                     "one not_evaluable applicability gate, never version "
                     "x control-point units; mapped to the resolver-driven "
                     "next-visit/re-consent test (not a hand-constructed "
                     "gate-only test)"),
        adjacent_test=("test_protocol_slice.py::TestApplicability::"
                       "test_next_visit_or_reconsent_missing_trigger_one_"
                       "gate"),
    ))

    # -- 79-83 cross-domain / age / retest / wording / order -------------

    cases.append(ProtocolChallengeCase(
        number=79, name="cm_fact_as_eligibility_positive",
        category="cross_domain",
        description=("challenge 79: exclusion 'X drug within window' "
                     "consumes a CM record as a fact; D04 builds one "
                     "exclusion_condition_present risk and no independent "
                     "D02 risk is created here"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP79-EXC",
            control_point_type=p.CONTROL_EXCLUSION,
            official_criterion_id="5.2.11", heading="排除标准",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_EXISTS,
                exists_target_role="concomitant_medication",
                required_evidence_roles=("concomitant_medication",),
                temporal_anchor=p.ANCHOR_SCREENING,
                evaluation_window_start="2026-02-01",
                evaluation_window_end="2026-03-01",
                window_start_inclusive=True, window_end_inclusive=True)),),
        build_bindings=lambda: (make_binding(
            "b79", control_point_id="CP79-EXC",
            role="concomitant_medication", value="有",
            date_raw="2026-02-10", table_semantic="recorded_cm"),),
        expected_units=(_positive(
            "CP79-EXC", subtype=p.SUBTYPE_EXCLUSION_PRESENT,
            audience="排除条件待核实"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
        check_fn=_check_cm_fact_d04_domain,
    ))

    cases.append(ProtocolChallengeCase(
        number=80, name="age_algorithm_unfrozen_not_evaluable",
        category="not_evaluable",
        description=("challenge 80: age inclusion with only birth year + "
                     "consent date and no frozen age algorithm -> "
                     "not_evaluable, never default 周岁/实足年龄"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP80-AGE",
            official_criterion_id="5.1.80", heading="年龄入选标准",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_AGE,
                comparison=p.RuleComparison(
                    comparison="at_least", threshold="18",
                    lower_inclusive=True, canonical_unit="year"),
                required_evidence_roles=("demographics", "consent"),
                temporal_anchor=p.ANCHOR_CONSENT)),),
        build_bindings=lambda: (
            make_binding("b80d", control_point_id="CP80-AGE",
                         role="demographics", value="2005",
                         date_raw="2005"),
            make_binding("b80c", control_point_id="CP80-AGE",
                         role="consent", value="", date_raw="2026-03-01"),
        ),
        expected_units=(_not_evaluable(
            "CP80-AGE", gap=p.GAP_AGE_ALGORITHM_UNFROZEN),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=81, name="retest_outside_window_keeps_positive",
        category="retest",
        description=("challenge 81: retest qualifies but falls outside the "
                     "allowed retest window -> cannot serve as exclusion "
                     "evidence; the original determinate problem stays "
                     "positive"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP81-INC",
            structured_rule=make_numeric_rule(
                retest_policy="retest-v1")),),
        build_bindings=lambda: (make_binding(
            "b81", control_point_id="CP81-INC", value="8"),),
        build_retests=lambda: {
            "CP81-INC": make_retest(
                date_raw="2026-05-01", in_window=False)},
        expected_units=(_positive("CP81-INC"),),
        expected_slice=(1, 0, 0, 0, 0),
        expected_candidates=1, expected_queries=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=82, name="ambiguous_any_all_not_evaluable",
        category="package",
        description=("challenge 82: original text only says '需满足下列"
                     "标准' with no determinable 任一/全部/至少 N -> "
                     "package not_evaluable; AND/OR is never defaulted"),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP82-PKG",
            root_kind=p.NODE_PACKAGE,
            issue_expression=make_issue_expression(
                p.EXPR_AND, ("C82a", "C82b")),
            component_ids=("C82a", "C82b"),
            verbatim="需满足下列标准"),),
        build_plan=lambda: make_plan(
            root_ids=("CP82-PKG",), verification="unverified"),
        build_components=lambda: {
            "C82a": make_component("C82a", "CP82-PKG",
                                   make_numeric_rule(threshold="10")),
            "C82b": make_component("C82b", "CP82-PKG",
                                   make_numeric_rule(threshold="5")),
        },
        build_bindings=lambda: (
            make_binding("b82a", component_id="C82a",
                         control_point_id="CP82-PKG", value="8"),
            make_binding("b82b", component_id="C82b",
                         control_point_id="CP82-PKG", value="3"),
        ),
        expected_set_size=1,
        expected_units=(_not_evaluable(
            "CP82-PKG", gap=p.GAP_RULE_NOT_VERIFIED),),
        expected_slice=(0, 0, 0, 1, 0),
        expected_candidates=0, expected_queries=0,
        expected_coverage_gaps=1,
    ))

    cases.append(ProtocolChallengeCase(
        number=83, name="reverse_order_same_gate_hash",
        category="determinism",
        description=("challenge 83: two feasible versions passed in "
                     "opposite input order -> sorted feasible fingerprints, "
                     "gate unit id and expected-set hash are identical"),
        build_applicability=lambda: make_applicability(
            status=p.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
            fingerprints=("fp-z", "fp-a")),
        build_control_points=lambda: (make_control_point(
            control_point_id="CP83-INC",
            structured_rule=make_numeric_rule()),),
        expected_set_size=1,
        expected_units=(_gate(L1Disposition.BOUNDARY),),
        expected_slice=(0, 0, 1, 0, 0),
        check_fn=_check_reverse_order,
    ))

    return ProtocolChallengeMatrix(cases=tuple(cases))


# ---------------------------------------------------------------------------
# check_fn implementations (focused D04 assertions)
# ---------------------------------------------------------------------------

#: Every check function receives ``(case, expansion, results, slice_result)``
#: and must raise on any violated invariant.


def _check_hierarchy_preserved(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    cp = exp.units[0].control_point
    assert cp.control_point_id == "CP07-PKG"
    assert cp.official_section_id == "5.1"
    assert cp.official_criterion_id == "5.1.7"
    assert cp.official_heading == "入选标准（组合）"
    assert cp.display_order == "1"
    assert cp.nesting_path == "5"
    assert cp.component_ids == ("C7a", "C7b")
    assert cp.verbatim_text == "以下条件需同时满足"


def _check_any_all_units(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    by_id = {r.control_point_id: r for r in results}
    assert len(exp.unit_ids) == 2
    assert len(set(exp.unit_ids)) == 2
    assert by_id["CP08-ANY"].l1_disposition == L1Disposition.NEGATIVE
    assert by_id["CP08-ALL"].l1_disposition == L1Disposition.POSITIVE
    # Distinct issue expressions drive the distinct determinate logic.
    any_cp = [u for u in exp.units
              if u.control_point.control_point_id == "CP08-ANY"][0]
    all_cp = [u for u in exp.units
              if u.control_point.control_point_id == "CP08-ALL"][0]
    assert any_cp.issue_expression.operator == p.EXPR_AND
    assert all_cp.issue_expression.operator == p.EXPR_OR
    # One package EvaluationUnit per root, never per component.
    assert exp.count == 2


def _check_package_assessments(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    r = results[0]
    assert r.evaluation_node_id == p.NODE_PACKAGE
    assert len(r.component_assessments) == 2
    for a in r.component_assessments:
        assert a.assessment_id not in exp.unit_ids
        assert a.assessment_id.startswith("d04-ca-")
        assert a.assessment_id != r.unit_id
    assert "C9b" in r.unresolved_component_ids
    assert r.l0_status == "partial"


def _check_derived_id(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    cp = exp.units[0].control_point
    assert cp.official_criterion_id == "d04-CP10-INC"
    assert cp.derived_id_note
    # The derived id is visibly derived, never presented as official.
    assert "d04-" in cp.official_criterion_id


def _check_version_v1(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    assert exp.applicability.decision_status == p.APPLICABILITY_UNIQUE_ACTIVE
    assert exp.applicability.protocol_version == "V1.0"


def _check_gcp_switch(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    records = (
        make_guidance("gcp-2020", "2020-07-01", "2026-08-31",
                      "GCP 2020"),
        make_guidance("gcp-2026", "2026-09-01", "",
                      "GCP 2026"),
    )
    g1, r1 = p.resolve_regulatory_guidance(
        evaluation_time="2026-08-01", guidance_records=records)
    g2, r2 = p.resolve_regulatory_guidance(
        evaluation_time="2026-10-01", guidance_records=records)
    assert g1 is not None and g1.version_id == "gcp-2020"
    assert g2 is not None and g2.version_id == "gcp-2026"
    # Before any registered guidance: unresolved, never a default version.
    g3, r3 = p.resolve_regulatory_guidance(
        evaluation_time="2019-01-01", guidance_records=records)
    assert g3 is None and r3


def _check_counterevidence(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    assert any(ev.polarity == "counterevidence"
               for ev in results[0].evidence)


def _check_three_part_query(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    unit = results[0]
    assert len(unit.query_refs) == 1
    q = unit.query_refs[0]
    assert q.basis and q.finding and q.action
    assert "V2.0" in q.basis or "方案" in q.basis
    assert q.source_locator_ids
    assert "评估是否构成方案偏离" in q.action
    for token in ("已确认PD", "重大PD", "已报送", "已关闭"):
        assert token not in (q.basis + q.finding + q.action)


def _check_query_no_pd_language(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    for unit in results:
        for q in unit.query_refs:
            text = q.basis + q.finding + q.action
            for token in ("已确认PD", "重大PD", "已报送", "已关闭",
                          "候选信号", "正式事实", "模型置信度"):
                assert token not in text


def _check_gap_notice(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    r = results[0]
    assert len(r.coverage_gap_notices) == 1
    assert not r.r2_candidates and not r.query_refs
    notice = r.coverage_gap_notices[0]
    assert notice.unit_id == r.unit_id
    assert notice.audience_text
    assert notice.protocol_locator_ids


def _check_journey_anchor(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    proj = pp.project_protocol_subject_journey(
        sr, expansions=exp,
        nominal_visits={"CP46-INC": "筛选访视 V1"},
        actual_visits={"CP46-INC": "V1"})
    assert proj.event_count >= 1
    for e in proj.events:
        assert e.domain_track == pp.PROTOCOL_TRACK
        if e.anchor_kind == p.ANCHOR_OTHER:
            # unresolved area: no fabricated date, listed explicitly
            assert not e.start and not e.end
            assert e.event_id in proj.unresolved_event_ids
        else:
            assert e.start  # actual anchor date present
    # Nominal and actual visit tokens stay distinct fields.
    ev = proj.events[0]
    assert ev.nominal_visit == "筛选访视 V1"
    assert ev.actual_visit == "V1"


def _check_journey_labels(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    proj = pp.project_protocol_subject_journey(
        sr, expansions=exp,
        nominal_visits={"CP47-INC": "筛选访视 V1"},
        actual_visits={"CP47-INC": "V1"})
    markers = [m for m in proj.risk_markers if m.candidate_or_risk_id]
    assert markers, "positive unit must project a typed risk marker"
    for m in markers:
        assert m.audience_label == "入选条件待核实"
        assert m.risk_family == p.SIGNAL_INCLUSION
        assert m.query_ids, "positive marker carries its Query ids"
        assert not any(tok in m.audience_label
                       for tok in ("positive", "candidate", "候选信号",
                                   "正式事实", "只读"))
    assert proj.risk_marker_count >= 1
    # Bidirectional join edges reference only reachable ids.
    event_ids = {e.event_id for e in proj.events}
    marker_ids = {m.marker_id for m in proj.risk_markers}
    for rec in proj.join.records:
        assert rec.event_id in event_ids
        assert rec.marker_id in marker_ids
        assert rec.join_reason in p.JOIN_REASONS
    # One-hop drill-back: event source locators are reachable.
    for e in proj.events:
        assert e.source_locator_ids


def _check_determinism(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    exp2, results2 = case.build()
    assert exp.unit_ids == exp2.unit_ids
    assert exp.expected_set_hash == exp2.expected_set_hash
    cand_ids = sorted(c.candidate_id
                      for r in results for c in r.r2_candidates)
    cand_ids2 = sorted(c.candidate_id
                       for r in results2 for c in r.r2_candidates)
    assert cand_ids == cand_ids2
    proj = pp.project_protocol_subject_journey(sr, expansions=exp)
    payload1 = proj.canonical_payload()
    payload2 = proj.canonical_payload()
    assert payload1 == payload2


def _check_new_lineage(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    # The same stable inputs with a new rule lineage produce a new unit id
    # and a new expected-set hash, while the previous run's identity stays
    # intact (immutable history, only future Runs are affected).
    plan_new = make_plan(
        root_ids=("CP53-INC",), rule_hash="rc2-newlineage",
        plan_id="plan-53-new")
    exp_new = p.expand_protocol_expected_set(
        project_id=PROJECT_ID, applicability=exp.applicability,
        control_points=(make_control_point(
            control_point_id="CP53-INC",
            structured_rule=make_numeric_rule()),),
        plan=plan_new)
    assert exp_new.unit_ids != exp.unit_ids
    assert exp_new.expected_set_hash != exp.expected_set_hash
    assert len(exp_new.unit_ids) == len(exp.unit_ids)


def _check_counts(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    sr.verify_count_invariants()
    positives = [r for r in sr.unit_results
                 if r.l1_disposition == L1Disposition.POSITIVE]
    assert sr.candidate_count == len(positives)
    assert sr.query_draft_count == len(positives)
    assert sr.coverage_gap_count == 0
    # Query count never feeds risk count and vice versa.
    assert sr.candidate_count >= sr.query_draft_count


def _check_producer_overview(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    proj = pp.project_protocol_subject_journey(
        sr, expansions=exp,
        producer_references=sr.producer_references)
    assert proj.producer_reference_count == 1
    ref = proj.producer_references[0]
    assert ref.owner_domain in (p.OWNER_D02, p.OWNER_D03)
    assert ref.producer_unit_id
    assert proj.risk_marker_count == 0, (
        "producer-owned control points must never create D04 markers")
    assert proj.coverage_gap_marker_count == 0


def _check_determinate_package(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    r = results[0]
    assert r.l1_disposition == L1Disposition.POSITIVE
    assert len(r.r2_candidates) == 1
    assert len(r.query_refs) == 1
    assert "C58b" in r.unresolved_component_ids
    assert r.l0_status == "partial"
    assert len(r.coverage_gap_notices) == 1


def _check_pipe_ids(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    r = results[0]
    assert len(set(exp.unit_ids)) == 1
    for a in r.component_assessments:
        assert a.assessment_id != r.unit_id
        assert a.assessment_id.startswith("d04-ca-")
    # '|' inside ids is preserved inside the canonical JSON hash.
    assert "|" in exp.units[0].control_point.control_point_id


def _case_plan(case: ProtocolChallengeCase) -> p.ProtocolRuleEvaluationPlan:
    plan = case.build_plan()
    if not plan:
        plan = make_plan(
            root_ids=tuple(cp.control_point_id
                           for cp in case.build_control_points()))
    return plan


def _check_gate_order(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    # Reversed feasible fingerprints -> same gate unit id + expected-set
    # hash (challenges 60/83).
    rev = make_applicability(
        status=p.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
        fingerprints=("fp-b", "fp-a"))
    exp_rev = p.expand_protocol_expected_set(
        project_id=PROJECT_ID, applicability=rev,
        control_points=tuple(case.build_control_points()),
        plan=_case_plan(case))
    assert exp.unit_ids == exp_rev.unit_ids
    assert exp.expected_set_hash == exp_rev.expected_set_hash


def _check_two_windows(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    assert len(exp.unit_ids) == 2
    assert len(set(exp.unit_ids)) == 2
    cps = sorted(r.control_point_id for r in results)
    assert cps == ["CP68-INC", "CP68-INC2"]
    # Distinct windows -> distinct unit ids and distinct risk identities.
    by_win = {r.evaluation_window_id: r for r in results}
    assert len(by_win) == 2
    identities = sorted({
        c.detail.get("risk_identity_id", "")
        for r in results for c in r.r2_candidates})
    assert identities and len(identities) == len(set(identities))


def _check_any_ne_negative(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    r = results[0]
    assert r.l1_disposition == L1Disposition.NEGATIVE
    assert r.l0_status == "partial"
    assert "C72b" in r.unresolved_component_ids
    assert not r.r2_candidates and not r.query_refs


def _check_all_ne_positive(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    r = results[0]
    assert r.l1_disposition == L1Disposition.POSITIVE
    assert r.l0_status == "partial"
    assert "C73a" in r.decisive_component_ids
    assert "C73b" in r.unresolved_component_ids
    assert len(r.r2_candidates) == 1
    assert len(r.query_refs) == 1


def _check_at_least_n(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    by_id = {r.control_point_id: r for r in results}
    assert by_id["CP74-TRUE"].l1_disposition == L1Disposition.POSITIVE
    assert by_id["CP74-FALSE"].l1_disposition == L1Disposition.NEGATIVE
    assert by_id["CP74-VAR"].l1_disposition == L1Disposition.NOT_EVALUABLE
    assert not by_id["CP74-VAR"].r2_candidates
    # Component assessments never enter the expected-set/lifecycle.
    assessment_ids = {a.assessment_id
                      for r in results for a in r.component_assessments}
    assert not (assessment_ids & set(exp.unit_ids))


def _check_query_not_occurred(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    unit = results[0]
    assert len(unit.query_refs) == 1
    q = unit.query_refs[0]
    assert "评估是否构成方案偏离" not in q.action
    assert "筛选" in (q.action + q.basis)


def _check_query_unresolved(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    unit = results[0]
    assert len(unit.query_refs) == 1
    q = unit.query_refs[0]
    assert "评估是否构成方案偏离" not in q.action
    assert "资料不足" in (q.basis + q.finding + q.action)


def _check_cm_fact_d04_domain(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    r = results[0]
    assert r.l1_disposition == L1Disposition.POSITIVE
    assert r.positive_subtype == p.SUBTYPE_EXCLUSION_PRESENT
    for c in r.r2_candidates:
        assert c.detail.get("domain") == p.D04_DOMAIN
    assert sr.query_draft_count == 1


def _check_reverse_order(
    case: ProtocolChallengeCase, exp: p.ProtocolExpectedSetExpansion,
    results: Sequence[p.ProtocolUnitResult],
    sr: p.ProtocolSliceResult,
) -> None:
    rev = make_applicability(
        status=p.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
        fingerprints=("fp-a", "fp-z"))
    exp_rev = p.expand_protocol_expected_set(
        project_id=PROJECT_ID, applicability=rev,
        control_points=tuple(case.build_control_points()),
        plan=_case_plan(case))
    assert exp.unit_ids == exp_rev.unit_ids
    assert exp.expected_set_hash == exp_rev.expected_set_hash
    # Sorted feasible fingerprints are canonical regardless of input order.
    assert exp.applicability.feasible_version_fingerprints == \
        exp_rev.applicability.feasible_version_fingerprints
