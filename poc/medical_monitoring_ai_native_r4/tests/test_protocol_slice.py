"""R4-D04 protocol slice deterministic tests (worker_02).

Proves the frozen D04 protocol domain engine
(``FROZEN_R4_D04_CONTRACT_V1_1``) implements the mandatory contract with
deterministic synthetic-only assertions, covering the core semantics
behind contract challenges 1-45, 48-54 and 58-83:

* Immutable value objects with fail-closed invariant validation; closed
  owner-domain and signal-type enums (no ``|``-joined free signals).
* Deterministic canonical identities: eight frozen EvaluationUnit hash
  dimensions, sorted applicability-gate fingerprints, canonical
  ``protocol_applicability_id``, and N->N+1-compatible R2 risk identities
  built only through the public ``make_risk_identity``.
* One EvaluationUnit per atomic/package root; component assessments keep
  separate stable ids and never enter expected-set/L1/L2/lifecycle.
* AND/OR/NOT/AT_LEAST_N parent issue-expression evaluation over feasible
  uncertain assignments; L0/L1 orthogonality with coverage-gap notices
  blocking domain completeness.
* Applicability gates (unique/multi-feasible/not_evaluable), version
  selection by event time + site adoption + transition scope, routing
  gates, and producer-owned control points excluded from the D04
  expected-set.
* Exact cross-domain evidence gates; not_evaluable with zero
  candidate/risk/Query; three-part Chinese Query wording conditional on
  the enrollment context; separate coverage-gap/Query/candidate counts.
* Shared lifecycle adapter integration: flagged candidates force
  severity=high, low/medium machine close requires exact linked negative
  + closed complete ledger.

All data is synthetic and offline.  No real project, provider, threshold,
listing layout, visit window or medication rule.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import pytest  # noqa: E402

from mm_r4 import protocol as p  # noqa: E402
from mm_r4.contracts import (  # noqa: E402
    CrossDomainEvidenceRef,
    L1Disposition,
    RiskDomainUnitResult,
    SourceLocator,
    UnitEvaluation,
    UnitJoinError,
    cross_domain_evidence_content_hash,
)
from mm_r4.coverage import (  # noqa: E402
    CoverageLedger,
    ExpectedSet,
    is_domain_complete,
)
from mm_r4.lifecycle import R4LifecycleAdapter  # noqa: E402
from mm_r4.fixtures import (  # noqa: E402
    make_acceptance_service,
    make_baseline_snapshot,
    make_lifecycle,
    make_subsequent_snapshot,
)
from mm_r2.identity import make_risk_identity  # noqa: E402

PROJECT_ID = "proj-synthetic-001"
SNAPSHOT_ID = "snap-accepted-001"
SOURCE_REV_ID = "sr-listing-001"
SITE_REF = "SITE01"
SUBJECT = "SYN-001"


# ===========================================================================
# Synthetic helpers
# ===========================================================================

def make_locator(
    record_id: str, table_semantic: str = "protocol_text",
    snapshot_id: str = SNAPSHOT_ID,
) -> SourceLocator:
    return SourceLocator(
        snapshot_id=snapshot_id, source_revision_id=SOURCE_REV_ID,
        table_semantic=table_semantic, record_id=record_id,
        column_or_anchor="row")


def make_version(
    version: str = "V2.0", amendment: str = "am2",
    approval_date: str = "2026-01-01", effective_start: str = "2026-01-15",
    effective_end: str = "", rule_hash: str = "rc2",
    transition_scope: str = p.TRANSITION_ALL_SWITCH,
    new_enrollment_only: Optional[bool] = None,
    site_adoption_start: str = "",
) -> p.ProtocolVersionRecord:
    return p.ProtocolVersionRecord(
        protocol_id="PROTO-1", protocol_version=version,
        amendment_id_or_hash=amendment, approval_date=approval_date,
        effective_start=effective_start, effective_end=effective_end,
        rule_content_hash=rule_hash, extraction_hash="ex-" + version,
        transition_scope=transition_scope,
        new_enrollment_only=new_enrollment_only,
        site_adoption_start=site_adoption_start)


def make_applicability(
    status: str = p.APPLICABILITY_UNIQUE_ACTIVE,
    version: str = "V2.0", amendment: str = "am2",
    anchor: str = p.ANCHOR_SCREENING, anchor_date: str = "2026-03-01",
    fingerprints: Sequence[str] = ("fp-1",),
    protocol_id: str = "PROTO-1",
) -> p.ProtocolApplicabilityDecision:
    return p.ProtocolApplicabilityDecision(
        subject_ref=SUBJECT, site_ref=SITE_REF,
        decision_time_anchor=anchor, decision_time_anchor_date=anchor_date,
        decision_status=status, protocol_id=protocol_id,
        protocol_version=version, amendment_id_or_hash=amendment,
        feasible_version_fingerprints=fingerprints,
        stable_source_content_key="stable-key-1",
        source_locators=(make_locator("appl-1"),))


def make_plan(
    root_ids: Sequence[str] = (), rule_hash: str = "rc2",
    plan_id: str = "plan-1", verification: str = "verified",
    protocol_version: str = "V2.0", amendment: str = "am2",
) -> p.ProtocolRuleEvaluationPlan:
    return p.ProtocolRuleEvaluationPlan(
        plan_id=plan_id, protocol_id="PROTO-1",
        protocol_version=protocol_version, amendment_id_or_hash=amendment,
        rule_content_hash=rule_hash, extraction_hash="ex2",
        mapping_version="mv1", unit_term_policy_version="utp1",
        verification_status=verification, root_ids=tuple(root_ids))


def make_numeric_rule(
    operator: str = p.OP_NUMERIC_AT_LEAST,
    comparison: str = "at_least", threshold: str = "10",
    lower_inclusive: Optional[bool] = True,
    unit: str = "U/L", roles: Sequence[str] = ("laboratory",),
    rounding_policy: str = p.ROUNDING_BEFORE, precision: int = 0,
    window_start: str = "", window_end: str = "",
    exception_policy: str = "", alternate_roles: Sequence[str] = (),
) -> p.ProtocolStructuredRule:
    return p.ProtocolStructuredRule(
        operator=operator,
        comparison=p.RuleComparison(
            comparison=comparison, threshold=threshold,
            lower_inclusive=lower_inclusive, canonical_unit=unit,
            rounding_policy=rounding_policy, rounding_precision=precision),
        required_evidence_roles=tuple(roles),
        alternate_evidence_roles=tuple(alternate_roles),
        temporal_anchor=p.ANCHOR_SCREENING,
        evaluation_window_start=window_start,
        evaluation_window_end=window_end,
        window_start_inclusive=True if window_start else None,
        window_end_inclusive=True if window_end else None,
        exception_or_waiver_policy=exception_policy)


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
    component_id: str, control_point_id: str, rule: p.ProtocolStructuredRule,
    official_criterion_id: str = "5.1.3-1",
) -> p.ProtocolComponent:
    return p.ProtocolComponent(
        component_id=component_id, control_point_id=control_point_id,
        official_criterion_id=official_criterion_id,
        parent_rule_id=control_point_id, display_order="1",
        nesting_path="5", verbatim_text="子条件",
        source_locator=make_locator("comp-" + component_id),
        source_revision_hash="h", structured_rule=rule)


def make_binding(
    binding_id: str, component_id: str = "",
    control_point_id: str = "CP-INC-1",
    subject_ref: str = SUBJECT, site_ref: str = SITE_REF,
    role: str = "laboratory", value: str = "8", unit: str = "U/L",
    date_raw: str = "2026-03-01",
    cross_domain_ref=None, confirmed: bool = True,
    blocked: bool = False, blocked_reason: str = "",
    expected_producer_unit_id: str = "",
) -> p.RuleEvidenceBinding:
    return p.RuleEvidenceBinding(
        binding_id=binding_id, control_point_id=control_point_id,
        component_id=component_id or control_point_id,
        subject_ref=subject_ref,
        site_ref=site_ref, source_role=role,
        stable_source_event_key=f"{role}:{binding_id}",
        source_locator=make_locator(binding_id, role),
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
) -> p.D04PriorityPolicy:
    """Build a valid content-addressed policy.  ``policy_content_hash``
    is the canonical content address of the semantic payload."""
    ch = p.policy_content_hash_value(
        policy_id=policy_id, version=version,
        rationale="合成默认优先级策略",
        subtype_priorities=((subtype, priority),),
        subtype_critical=((subtype, critical),),
        subtype_machine_close_forbidden=((subtype, close_forbidden),))
    return p.D04PriorityPolicy(
        policy_id=policy_id, version=version, policy_content_hash=ch,
        rationale="合成默认优先级策略",
        subtype_priorities=((subtype, priority),),
        subtype_critical=((subtype, critical),),
        subtype_machine_close_forbidden=((subtype, close_forbidden),))


def make_enrollment(
    query_context: str = p.QUERY_CONTEXT_NOT_OCCURRED,
) -> p.EnrollmentContext:
    return p.EnrollmentContext(
        subject_ref=SUBJECT, query_context=query_context,
        rationale="合成入组情境")


def evaluate_unit(
    expanded: p.ProtocolUnitExpanded,
    bindings: Sequence[p.RuleEvidenceBinding] = (),
    roles: Optional[Mapping[str, bool]] = None,
    exceptions: Sequence[p.ProtocolExceptionBinding] = (),
    conversions: Sequence[p.UnitConversionRule] = (),
    retests: Optional[Mapping[str, p.RetestOutcome]] = None,
    enrollment: Optional[p.EnrollmentContext] = None,
    policy: Optional[p.D04PriorityPolicy] = None,
) -> p.ProtocolUnitResult:
    return p.evaluate_protocol_unit(
        project_id=PROJECT_ID, expanded=expanded, bindings=bindings,
        coverage_complete_roles=roles or {}, exceptions=exceptions,
        unit_conversion_rules=conversions, retest_outcomes=retests,
        enrollment_context=enrollment, priority_policy=policy,
        snapshot_id=SNAPSHOT_ID)


def expand_one(
    cp: p.ProtocolControlPoint, plan: p.ProtocolRuleEvaluationPlan,
    components: Optional[Mapping[str, p.ProtocolComponent]] = None,
    applicability: Optional[p.ProtocolApplicabilityDecision] = None,
    routing: Sequence[p.ProtocolControlRoutingRecord] = (),
    windows: Optional[Mapping[str, p.EvaluationWindowSpec]] = None,
) -> p.ProtocolExpectedSetExpansion:
    return p.expand_protocol_expected_set(
        project_id=PROJECT_ID,
        applicability=applicability or make_applicability(),
        control_points=(cp,), plan=plan, components=components,
        routing_records=routing,
        window_by_control_point=windows)


def evaluate_single(
    cp: p.ProtocolControlPoint, plan: p.ProtocolRuleEvaluationPlan,
    components: Optional[Mapping[str, p.ProtocolComponent]] = None,
    applicability: Optional[p.ProtocolApplicabilityDecision] = None,
    routing: Sequence[p.ProtocolControlRoutingRecord] = (),
    bindings: Sequence[p.RuleEvidenceBinding] = (),
    roles: Optional[Mapping[str, bool]] = None,
    **kw,
) -> p.ProtocolUnitResult:
    expansion = expand_one(cp, plan, components, applicability, routing)
    return evaluate_unit(expansion.units[0], bindings, roles, **kw)


def atomic_single(
    cp: p.ProtocolControlPoint, bindings: Sequence[p.RuleEvidenceBinding] = (),
    roles: Optional[Mapping[str, bool]] = None, **kw,
) -> p.ProtocolUnitResult:
    plan = make_plan(root_ids=(cp.control_point_id,))
    return evaluate_single(cp, plan, bindings=bindings, roles=roles, **kw)


def _cd_ref(
    record_id: str = "CM#9", subject_ref: str = SUBJECT,
    site_ref: str = SITE_REF, producer_unit: str = "d02-unit-9",
    role: str = "cm_usage", claim_scope: str = "screening_window",
    context: Optional[Mapping[str, Any]] = None,
) -> CrossDomainEvidenceRef:
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
        consumer_domain="D04_protocol_compliance", evidence_role=role,
        source_locator=loc, producer_unit_id=producer_unit,
        content_hash=ch, claim_scope=claim_scope,
        context_payload=tuple(payload.items()))


# ===========================================================================
# 0. Input value-object invariants
# ===========================================================================

class TestInputInvariants:
    def test_issue_expression_requires_closed_operator(self):
        with pytest.raises(p.ProtocolSliceError):
            p.IssueExpression(operator="XOR", component_ids=("C1", "C2"))

    def test_not_expression_requires_exactly_one_operand(self):
        with pytest.raises(p.ProtocolSliceError):
            p.IssueExpression(operator=p.EXPR_NOT, component_ids=("C1", "C2"))

    def test_at_least_n_bounds(self):
        with pytest.raises(p.ProtocolSliceError):
            p.IssueExpression(operator=p.EXPR_AT_LEAST_N,
                              component_ids=("C1", "C2"), at_least_n=3)

    def test_duplicate_component_ids_rejected(self):
        with pytest.raises(p.ProtocolSliceError):
            p.IssueExpression(operator=p.EXPR_AND,
                              component_ids=("C1", "C1"))

    def test_signal_type_is_closed(self):
        with pytest.raises(p.ProtocolSliceError):
            p.build_protocol_unit(
                project_id=PROJECT_ID, subject_ref=SUBJECT,
                control_point_id="CP-1", evaluation_node_id=p.NODE_ATOMIC,
                signal_type="inclusion|exclusion",
                protocol_applicability_id="appl-1",
                eval_anchor_kind=p.ANCHOR_SCREENING,
                window_start="", window_end="",
                precision=p.PRECISION_DAY,
                endpoint_inclusivity=p.INCLUSIVITY_INCLUSIVE,
                protocol_id="P", protocol_version="V1",
                amendment_id_or_hash="", rule_content_hash="r",
                extraction_hash="e", mapping_version="m",
                unit_term_policy_version="u")

    def test_owner_domain_is_closed(self):
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolControlRoutingRecord(
                control_point_id="CP-1", owner_domain="D99",
                owner_signal_type="x", routing_rule_version="v",
                routing_rule_hash="h", routing_gap="g")

    def test_routed_record_requires_producer_or_gap(self):
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolControlRoutingRecord(
                control_point_id="CP-1", owner_domain=p.OWNER_D02,
                owner_signal_type="D02_cm", routing_rule_version="v",
                routing_rule_hash="h")

    def test_unresolved_owner_requires_candidates(self):
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolControlRoutingRecord(
                control_point_id="CP-1", owner_domain=p.OWNER_UNRESOLVED,
                owner_signal_type="x", routing_rule_version="v",
                routing_rule_hash="h", routing_gap="g")

    def test_routing_record_cannot_point_to_d04(self):
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolControlRoutingRecord(
                control_point_id="CP-1", owner_domain=p.OWNER_D04,
                owner_signal_type="D04", routing_rule_version="v",
                routing_rule_hash="h", producer_unit_id="u")

    def test_unknown_operator_rejected(self):
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolStructuredRule(
                operator="magic", required_evidence_roles=("laboratory",))

    def test_numeric_operator_requires_comparison(self):
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolStructuredRule(
                operator=p.OP_NUMERIC_AT_LEAST,
                required_evidence_roles=("laboratory",))

    def test_equality_requires_value_set(self):
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolStructuredRule(
                operator=p.OP_EQUALS, required_evidence_roles=("laboratory",))

    def test_atomic_cp_requires_rule_and_package_requires_expression(self):
        with pytest.raises(p.ProtocolSliceError):
            make_control_point(structured_rule=None)
        with pytest.raises(p.ProtocolSliceError):
            make_control_point(
                root_kind=p.NODE_PACKAGE,
                structured_rule=make_numeric_rule())

    def test_package_components_must_be_referenced(self):
        with pytest.raises(p.ProtocolSliceError):
            make_control_point(
                root_kind=p.NODE_PACKAGE,
                issue_expression=p.IssueExpression(
                    operator=p.EXPR_AND, component_ids=("C1",)),
                component_ids=("C2",))

    def test_gap_notice_hash_is_canonical(self):
        n1 = p.ProtocolCoverageGapNotice(
            notice_id="", unit_id="u1", reason_code=p.GAP_VALUE_MISSING,
            missing_evidence_roles=("b", "a"),
            protocol_locator_ids=("l2", "l1"),
            reachable_source_locator_ids=())
        n2 = p.ProtocolCoverageGapNotice(
            notice_id="", unit_id="u1", reason_code=p.GAP_VALUE_MISSING,
            missing_evidence_roles=("a", "b"),
            protocol_locator_ids=("l1", "l2"),
            reachable_source_locator_ids=())
        assert n1.notice_id == n2.notice_id
        assert n1.notice_id.startswith("d04-gap-")
        assert n1.missing_evidence_roles == ("a", "b")

    def test_gap_notice_id_rejects_tamper(self):
        p.ProtocolCoverageGapNotice(
            notice_id="", unit_id="u1", reason_code=p.GAP_VALUE_MISSING)
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolCoverageGapNotice(
                notice_id="d04-gap-" + "0" * 64, unit_id="u1",
                reason_code=p.GAP_VALUE_MISSING)

    def test_enrollment_context_closed(self):
        with pytest.raises(p.ProtocolSliceError):
            p.EnrollmentContext(subject_ref=SUBJECT, query_context="maybe",
                                rationale="x")

    def test_assessment_id_never_masquerades_as_unit(self):
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolComponentAssessment(
                assessment_id="unit-abc", unit_id="unit-abc",
                component_id="C1", official_criterion_id="5.1",
                issue_predicate_result=p.ISSUE_TRUE)

    def test_applicability_decision_requires_stable_source_key(self):
        """Corrective finding 1: a constructed decision must stay attached
        to stable source lineage; run/snapshot/revision stay excluded."""
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolApplicabilityDecision(
                subject_ref=SUBJECT, site_ref=SITE_REF,
                decision_time_anchor=p.ANCHOR_SCREENING,
                decision_time_anchor_date="2026-03-01",
                decision_status=p.APPLICABILITY_UNIQUE_ACTIVE,
                protocol_id="P", protocol_version="V1",
                amendment_id_or_hash="",
                feasible_version_fingerprints=("fp-1",))

    def test_policy_hash_is_canonical_content_address(self):
        """Corrective finding 4: policy_content_hash is the verified
        canonical content address of the semantic payload (excluding the
        hash itself); a tampered hash fails closed."""
        s = p.SUBTYPE_INCLUSION_NOT_MET
        ch = p.policy_content_hash_value(
            policy_id="pol-1", version="v1", rationale="r",
            subtype_priorities=((s, "high"),),
            subtype_critical=((s, True),),
            subtype_machine_close_forbidden=((s, True),))
        pol = p.D04PriorityPolicy(
            policy_id="pol-1", version="v1", policy_content_hash=ch,
            rationale="r",
            subtype_priorities=((s, "high"),),
            subtype_critical=((s, True),),
            subtype_machine_close_forbidden=((s, True),))
        assert pol.policy_content_hash == ch
        assert ch.startswith("d04-policy-")
        # Semantic payload change -> different hash.
        ch2 = p.policy_content_hash_value(
            policy_id="pol-1", version="v1", rationale="r2",
            subtype_priorities=((s, "high"),),
            subtype_critical=((s, True),),
            subtype_machine_close_forbidden=((s, True),))
        assert ch2 != ch
        with pytest.raises(p.ProtocolSliceError):
            p.D04PriorityPolicy(
                policy_id="pol-1", version="v1",
                policy_content_hash="0" * 64, rationale="r",
                subtype_priorities=((s, "high"),),
                subtype_critical=((s, True),),
                subtype_machine_close_forbidden=((s, True),))

    def test_policy_flag_literal_bool_and_duplicate_rejected(self):
        """Corrective finding 4: flags must be literal bools; duplicate
        subtype entries and mutable aliases fail closed."""
        s = p.SUBTYPE_INCLUSION_NOT_MET

        def valid_hash(entries):
            return p.policy_content_hash_value(
                policy_id="pol-1", version="v1", rationale="r",
                subtype_priorities=((s, "high"),),
                subtype_critical=entries,
                subtype_machine_close_forbidden=((s, True),))

        with pytest.raises(p.ProtocolSliceError):
            # int 1 is not a literal bool.
            p.D04PriorityPolicy(
                policy_id="pol-1", version="v1",
                policy_content_hash=valid_hash(((s, 1),)), rationale="r",
                subtype_priorities=((s, "high"),),
                subtype_critical=((s, 1),),
                subtype_machine_close_forbidden=((s, True),))
        with pytest.raises(p.ProtocolSliceError):
            # Nested list pair is a mutable alias -> fail closed.
            p.D04PriorityPolicy(
                policy_id="pol-1", version="v1",
                policy_content_hash=valid_hash(([s, True],)), rationale="r",
                subtype_priorities=((s, "high"),),
                subtype_critical=([s, True],),
                subtype_machine_close_forbidden=((s, True),))
        with pytest.raises(p.ProtocolSliceError):
            # Duplicate subtype entries rejected.
            ch = p.policy_content_hash_value(
                policy_id="pol-1", version="v1", rationale="r",
                subtype_priorities=((s, "high"), (s, "low")),
                subtype_critical=((s, True),),
                subtype_machine_close_forbidden=((s, True),))
            p.D04PriorityPolicy(
                policy_id="pol-1", version="v1", policy_content_hash=ch,
                rationale="r",
                subtype_priorities=((s, "high"), (s, "low")),
                subtype_critical=((s, True),),
                subtype_machine_close_forbidden=((s, True),))

    def test_routed_record_exactly_one_of_producer_or_gap(self):
        """Corrective finding 5: resolved routing requires exactly one of
        producer_unit_id or routing_gap -- never both, never neither."""
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolControlRoutingRecord(
                control_point_id="CP-1", owner_domain=p.OWNER_D02,
                owner_signal_type="D02_cm", routing_rule_version="v",
                routing_rule_hash="h", producer_unit_id="u", routing_gap="g")
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolControlRoutingRecord(
                control_point_id="CP-1", owner_domain=p.OWNER_D02,
                owner_signal_type="D02_cm", routing_rule_version="v",
                routing_rule_hash="h")

    def test_unresolved_routing_gap_without_producer(self):
        """Corrective finding 5: unresolved routing carries a gap and no
        producer unit."""
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolControlRoutingRecord(
                control_point_id="CP-1", owner_domain=p.OWNER_UNRESOLVED,
                owner_signal_type="x", routing_rule_version="v",
                routing_rule_hash="h",
                candidate_owners=(p.OWNER_D02, p.OWNER_D04),
                producer_unit_id="u")

    def test_delegated_exactly_one_and_producer_owner(self):
        """Corrective finding 5: delegated items require exactly one of
        producer/gap and a producer owner domain."""
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolDelegatedControlPoint(
                control_point_id="CP-1", owner_domain=p.OWNER_D02,
                owner_signal_type="D02_cm", producer_unit_id="u",
                routing_gap="g")
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolDelegatedControlPoint(
                control_point_id="CP-1", owner_domain=p.OWNER_UNRESOLVED,
                owner_signal_type="x", routing_gap="g")
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolDelegatedControlPoint(
                control_point_id="CP-1", owner_domain=p.OWNER_D04,
                owner_signal_type="x", routing_gap="g")

    def test_producer_reference_producer_owner_only(self):
        """Corrective finding 5: ProtocolProducerReference accepts only
        producer owner domains, never D04/self or owner_unresolved."""
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolProducerReference(
                ref_id="r", owner_domain=p.OWNER_D04,
                producer_unit_id="u")
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolProducerReference(
                ref_id="r", owner_domain=p.OWNER_UNRESOLVED,
                producer_unit_id="u")
        ref = p.ProtocolProducerReference(
            ref_id="r", owner_domain=p.OWNER_D02,
            producer_unit_id="u")
        assert ref.owner_domain == p.OWNER_D02

    def test_expected_set_hash_rejects_duplicates(self):
        """Corrective finding 5: duplicate unit ids are rejected, never
        silently deduplicated."""
        with pytest.raises(p.ProtocolSliceError):
            p.expected_set_hash(["u1", "u1"])
        # Distinct ids still hash deterministically, order-independent.
        assert p.expected_set_hash(["u1", "u2"]) == p.expected_set_hash(
            ["u2", "u1"])


# ===========================================================================
# 1. Applicability (§2.3, §5) -- challenges 11-15, 60, 65, 71, 77, 78, 83
# ===========================================================================

class TestApplicability:
    def test_unique_active_version_selected(self):
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "2025-12-31", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version()
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2026-01-20",
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_UNIQUE_ACTIVE
        assert appl.protocol_version == "V2.0"

    def test_old_version_applies_when_site_has_not_adopted_new(self):
        """Challenge 11: latest amendment not yet enabled at the site ->
        evaluate by the old version."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version(site_adoption_start="2026-06-01")
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2025-02-15",  # site adopted the protocol
            stable_source_content_key="k")
        # V2 amendment not yet enabled at the site -> V1 only.
        # V2 not yet adopted -> only V1 feasible
        assert appl.decision_status == p.APPLICABILITY_UNIQUE_ACTIVE
        assert appl.protocol_version == "V1.0"

    def test_two_feasible_versions_boundary(self):
        """Challenge 13: two versions both feasible with source support ->
        applicability gate boundary, no N medical units."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version()
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2026-01-01",
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY
        assert appl.protocol_applicability_id.startswith("d04-appl-")

    def test_missing_approval_date_not_evaluable(self):
        """Challenge 14: key approval/site dates missing -> not_evaluable."""
        v1 = p.ProtocolVersionRecord(
            protocol_id="PROTO-1", protocol_version="V1.0",
            amendment_id_or_hash="", approval_date="",
            effective_start="2025-02-01", effective_end="",
            rule_content_hash="rc1", extraction_hash="ex1",
            transition_scope=p.TRANSITION_ALL_SWITCH)
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1,),
            site_adoption_start="",  # missing
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_NOT_EVALUABLE

    def test_same_day_adoption_endpoint_undefined_boundary(self):
        """Challenge 12: same-day enablement with undefined endpoint ->
        boundary."""
        v1 = make_version()
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-01-20", versions=(v1,),
            site_adoption_start="2026-01-20",
            adoption_start_inclusive=None,
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY

    def test_new_enrollment_only_amendment_does_not_apply_to_existing(self):
        """Challenge 77: V2 enabled at site but transition only for new
        enrollment -> existing subject's past eligibility stays on V1."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version(
            transition_scope=p.TRANSITION_NEW_ENROLLMENT_ONLY,
            new_enrollment_only=True)
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2026-01-20",
            subject_enrollment_date="2025-06-01",  # enrolled before V2
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_UNIQUE_ACTIVE
        assert appl.protocol_version == "V1.0"

    def test_event_time_not_run_time_selects_version(self):
        """Challenge 65: V1 enrollment criterion evaluated at enrollment
        time; V2 treatment rules by new window; Run date never back-dates
        V2 onto V1 events."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "2025-12-31", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version()
        # Enrollment-time event: 2025-06-01 -> V1
        appl_enroll = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_RANDOMIZATION,
            event_anchor_date="2025-06-01", versions=(v1, v2),
            site_adoption_start="2025-02-15",
            stable_source_content_key="k")
        assert appl_enroll.protocol_version == "V1.0"
        # Treatment-time event: 2026-03-01 -> V2
        appl_tx = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_ON_TREATMENT,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2026-01-20",
            stable_source_content_key="k")
        assert appl_tx.protocol_version == "V2.0"

    def test_reconsent_switch_missing_timing_single_gate(self):
        """Challenge 78: re-consent/next-visit switch with missing timing
        -> single applicability gate, no version x control-point units."""
        appl = make_applicability(
            status=p.APPLICABILITY_NOT_EVALUABLE,
            fingerprints=("fp-1", "fp-2"))
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",))
        expansion = expand_one(cp, plan, applicability=appl)
        assert expansion.count == 1
        assert expansion.units[0].evaluation_node_id == p.NODE_APPLICABILITY_GATE
        result = evaluate_unit(expansion.units[0])
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert len(result.coverage_gap_notices) == 1
        assert not result.r2_candidates and not result.query_refs

    def test_gate_unit_id_input_order_independent(self):
        """Challenges 60/83: two feasible versions in opposite input order
        -> same gate unit id, same expected-set hash."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",))
        a1 = make_applicability(
            status=p.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
            fingerprints=("fp-a", "fp-b"))
        a2 = make_applicability(
            status=p.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
            fingerprints=("fp-b", "fp-a"))
        assert a1.protocol_applicability_id == a2.protocol_applicability_id
        e1 = expand_one(cp, plan, applicability=a1)
        e2 = expand_one(cp, plan, applicability=a2)
        assert e1.expected_set_hash == e2.expected_set_hash
        assert (e1.units[0].build_unit(PROJECT_ID).unit_id
                == e2.units[0].build_unit(PROJECT_ID).unit_id)

    def test_multiple_control_points_still_one_gate(self):
        """Challenge 71: two feasible versions x multiple control points ->
        one subject-level gate; affected ids stay in context, L1
        denominator is 1."""
        cp1 = make_control_point(
            control_point_id="CP-A", structured_rule=make_numeric_rule())
        cp2 = make_control_point(
            control_point_id="CP-B", official_criterion_id="5.1.4",
            structured_rule=make_numeric_rule(threshold="5"))
        plan = make_plan(root_ids=("CP-A", "CP-B"))
        appl = make_applicability(
            status=p.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
            fingerprints=("fp-1", "fp-2"))
        expansion = p.expand_protocol_expected_set(
            project_id=PROJECT_ID, applicability=appl,
            control_points=(cp1, cp2), plan=plan)
        assert expansion.count == 1
        assert expansion.units[0].evaluation_node_id == p.NODE_APPLICABILITY_GATE
        assert set(expansion.units[0].affected_control_point_ids) == {
            "CP-A", "CP-B"}

    def test_no_version_covers_event_not_evaluable(self):
        """Corrective finding 1: zero feasible versions with complete
        day-precision inputs is an inability to identify an applicable
        version -- not_evaluable (not boundary), one applicability gate,
        zero candidate/risk/Query."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "2025-12-31", "rc1", p.TRANSITION_ALL_SWITCH)
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1,),
            site_adoption_start="2025-01-15",
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_NOT_EVALUABLE
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",))
        expansion = expand_one(cp, plan, applicability=appl)
        assert expansion.count == 1
        assert (expansion.units[0].evaluation_node_id
                == p.NODE_APPLICABILITY_GATE)
        result = evaluate_unit(expansion.units[0])
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert len(result.coverage_gap_notices) == 1
        assert not result.r2_candidates and not result.query_refs

    def test_resolver_leaves_affected_control_point_ids_empty(self):
        """Corrective finding 1: the resolver never writes protocol-version
        strings into affected_control_point_ids; expansion owns the actual
        affected root ids."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version()
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2026-01-01",
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY
        assert appl.affected_control_point_ids == ()
        appl_na = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1,),
            site_adoption_start="", stable_source_content_key="k")
        assert appl_na.decision_status == p.APPLICABILITY_NOT_EVALUABLE
        assert appl_na.affected_control_point_ids == ()

    def test_resolver_requires_stable_source_content_key(self):
        """Corrective finding 1: the resolver refuses to detach a decision
        from stable source lineage."""
        with pytest.raises(p.ProtocolSliceError):
            p.resolve_protocol_applicability(
                subject_ref=SUBJECT, site_ref=SITE_REF,
                event_anchor_kind=p.ANCHOR_SCREENING,
                event_anchor_date="2026-03-01",
                versions=(make_version(),),
                site_adoption_start="2026-01-20")

    def test_regulatory_guidance_switches_at_boundary(self):
        """Challenge 15: China GCP 2020 -> 2026 switch at 2026-09-01 is
        data-driven; the kernel hardcodes no regulatory calendar."""
        gcp2020 = p.RegulatoryGuidanceVersion(
            version_id="gcp-2020", effective_start="2020-07-01",
            effective_end="2026-08-31", content_reference="2020年第57号")
        gcp2026 = p.RegulatoryGuidanceVersion(
            version_id="gcp-2026", effective_start="2026-09-01",
            content_reference="2026年第50号")
        recs = (gcp2020, gcp2026)
        v_before, _ = p.resolve_regulatory_guidance(
            evaluation_time="2026-08-01", guidance_records=recs)
        v_after, _ = p.resolve_regulatory_guidance(
            evaluation_time="2026-10-01", guidance_records=recs)
        assert v_before.version_id == "gcp-2020"
        assert v_after.version_id == "gcp-2026"
        unresolved, reason = p.resolve_regulatory_guidance(
            evaluation_time="2019-01-01", guidance_records=recs)
        assert unresolved is None and reason

    # -- corrective 03: §2.3 transition-resolution order (fail closed) ----

    def test_all_switch_determinate_unique_latest(self):
        """Corrective 03/1: all_switch with no re-consent dependency keeps
        the interval/adoption behaviour -- one feasible version -> unique."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "2025-12-31", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version()  # all_switch
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2026-01-20",
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_UNIQUE_ACTIVE
        assert appl.protocol_version == "V2.0"

    def test_new_enrollment_only_existing_subject_stays_old(self):
        """Corrective 03/2: new-enrollment-only with a day-comparable
        pre-amendment enrollment date keeps the existing subject on the
        old version."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version(
            transition_scope=p.TRANSITION_NEW_ENROLLMENT_ONLY,
            new_enrollment_only=True)
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2026-01-20",
            subject_enrollment_date="2025-06-01",
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_UNIQUE_ACTIVE
        assert appl.protocol_version == "V1.0"

    def test_new_enrollment_only_missing_enrollment_date_one_gate(self):
        """Corrective 03/3: new-enrollment-only with a missing enrollment
        date is a single not_evaluable gate -- never a unique version --
        with zero candidate/risk/Query downstream."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "2025-12-31", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version(
            transition_scope=p.TRANSITION_NEW_ENROLLMENT_ONLY,
            new_enrollment_only=True)
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2026-01-20",
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_NOT_EVALUABLE
        assert appl.protocol_version == ""
        assert appl.new_enrollment_only is True
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",))
        expansion = expand_one(cp, plan, applicability=appl)
        assert expansion.count == 1
        assert (expansion.units[0].evaluation_node_id
                == p.NODE_APPLICABILITY_GATE)
        result = evaluate_unit(expansion.units[0])
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert len(result.coverage_gap_notices) == 1
        assert not result.r2_candidates and not result.query_refs

    def test_existing_continue_old_unique_predecessor_after_effective_start(self):
        """Corrective 03/4: existing_continue_old with exactly one
        predecessor supported at the enrollment time keeps the old
        version even after the amendment's project effective start; the
        predecessor's own effective_end never forces the subject onto
        the amendment."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "2025-12-31", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version(
            transition_scope=p.TRANSITION_EXISTING_CONTINUE_OLD)
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2025-02-15",
            subject_enrollment_date="2025-06-01",
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_UNIQUE_ACTIVE
        assert appl.protocol_version == "V1.0"
        assert appl.amendment_transition_scope == (
            p.TRANSITION_EXISTING_CONTINUE_OLD)

    def test_existing_continue_old_missing_enrollment_or_ambiguous(self):
        """Corrective 03/5: existing_continue_old without a day-comparable
        enrollment date is one not_evaluable gate; with two supported
        predecessors it is one boundary gate -- never the amendment."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "2025-12-31", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version(
            transition_scope=p.TRANSITION_EXISTING_CONTINUE_OLD)
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2026-01-20",
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_NOT_EVALUABLE
        # Two predecessors supported at the enrollment time -> boundary.
        v1a = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                           "2026-01-31", "rc1", p.TRANSITION_ALL_SWITCH)
        v1b = make_version("V1.5", "am1b", "2025-05-01", "2025-09-01",
                           "", "rc1b", p.TRANSITION_ALL_SWITCH)
        v2b = make_version("V2.0", "am2", "2026-01-01", "2026-02-01",
                           "", "rc2", p.TRANSITION_EXISTING_CONTINUE_OLD)
        appl2 = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1a, v1b, v2b),
            site_adoption_start="2025-02-15",
            subject_enrollment_date="2025-10-01",
            stable_source_content_key="k")
        assert appl2.decision_status == (
            p.APPLICABILITY_MULTI_FEASIBLE_BOUNDARY)
        assert appl2.protocol_version == ""

    def test_next_visit_or_reconsent_missing_trigger_one_gate(self):
        """Corrective 03/6: next_visit_or_reconsent (or any
        re_consent_required=True) with the current inputs is one
        not_evaluable gate with zero candidate/risk/Query -- the schema
        carries no versioned next-visit/re-consent trigger policy and
        subject_consent_date is never reinterpreted as re-consent."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "2025-12-31", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version(
            transition_scope=p.TRANSITION_NEXT_VISIT_OR_RECONSENT)
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2026-01-20",
            subject_consent_date="2025-06-01",
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_NOT_EVALUABLE
        assert appl.re_consent_requirement is True
        assert appl.amendment_transition_scope == (
            p.TRANSITION_NEXT_VISIT_OR_RECONSENT)
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",))
        expansion = expand_one(cp, plan, applicability=appl)
        assert expansion.count == 1
        assert (expansion.units[0].evaluation_node_id
                == p.NODE_APPLICABILITY_GATE)
        result = evaluate_unit(expansion.units[0])
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert len(result.coverage_gap_notices) == 1
        assert not result.r2_candidates and not result.query_refs
        assert not result.risk_instance_refs
        # all_switch with an explicit re-consent dependency also fails
        # closed instead of adopting the amendment.
        v3 = p.ProtocolVersionRecord(
            protocol_id="PROTO-1", protocol_version="V3.0",
            amendment_id_or_hash="am3", approval_date="2026-01-01",
            effective_start="2026-02-01", effective_end="",
            rule_content_hash="rc3", extraction_hash="ex-V3.0",
            transition_scope=p.TRANSITION_ALL_SWITCH,
            re_consent_required=True)
        appl3 = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v3),
            site_adoption_start="2026-01-20",
            stable_source_content_key="k")
        assert appl3.decision_status == p.APPLICABILITY_NOT_EVALUABLE
        assert appl3.re_consent_requirement is True

    def test_undetermined_transition_one_gate(self):
        """Corrective 03/7: an amendment with an undetermined transition
        scope is one not_evaluable gate, never a unique version."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "2025-12-31", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = p.ProtocolVersionRecord(
            protocol_id="PROTO-1", protocol_version="V2.0",
            amendment_id_or_hash="am2", approval_date="2026-01-01",
            effective_start="2026-02-01", effective_end="",
            rule_content_hash="rc2", extraction_hash="ex-V2.0",
            transition_scope=p.TRANSITION_UNDETERMINED)
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2026-01-20",
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_NOT_EVALUABLE
        assert appl.protocol_version == ""
        assert appl.amendment_transition_scope == (
            p.TRANSITION_UNDETERMINED)

    def test_transition_gate_id_input_order_independent(self):
        """Corrective 03/8: reversing the version input order preserves
        the same applicability gate id / expected-set hash for the new
        transition gates (deterministic fingerprint sorting)."""
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "2025-12-31", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version(
            transition_scope=p.TRANSITION_NEW_ENROLLMENT_ONLY,
            new_enrollment_only=True)
        kw = dict(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01",
            site_adoption_start="2026-01-20",
            stable_source_content_key="k")
        a_ab = p.resolve_protocol_applicability(versions=(v1, v2), **kw)
        a_ba = p.resolve_protocol_applicability(versions=(v2, v1), **kw)
        assert a_ab.decision_status == p.APPLICABILITY_NOT_EVALUABLE
        assert (a_ab.protocol_applicability_id
                == a_ba.protocol_applicability_id)
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",))
        e1 = expand_one(cp, plan, applicability=a_ab)
        e2 = expand_one(cp, plan, applicability=a_ba)
        assert e1.expected_set_hash == e2.expected_set_hash
        assert (e1.units[0].build_unit(PROJECT_ID).unit_id
                == e2.units[0].build_unit(PROJECT_ID).unit_id)
        # existing-continue-old unique path is order-independent too.
        v1c = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                           "2025-12-31", "rc1", p.TRANSITION_ALL_SWITCH)
        v2c = make_version(
            transition_scope=p.TRANSITION_EXISTING_CONTINUE_OLD)
        kwc = dict(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01",
            site_adoption_start="2025-02-15",
            subject_enrollment_date="2025-06-01",
            stable_source_content_key="k")
        c_ab = p.resolve_protocol_applicability(versions=(v1c, v2c), **kwc)
        c_ba = p.resolve_protocol_applicability(versions=(v2c, v1c), **kwc)
        assert c_ab.decision_status == p.APPLICABILITY_UNIQUE_ACTIVE
        assert c_ab.protocol_version == "V1.0"
        assert (c_ab.protocol_applicability_id
                == c_ba.protocol_applicability_id)


# ===========================================================================
# 2. Routing (§3.2) -- challenges 29, 33, 56, 57, 67, 69
# ===========================================================================

class TestRouting:
    def _cm_cp(self) -> p.ProtocolControlPoint:
        return make_control_point(
            control_point_id="CP-CM-1",
            control_point_type=p.CONTROL_PROHIBITED_OR_RESTRICTED_TREATMENT,
            official_section_id="6.2", official_criterion_id="6.2.1",
            heading="禁限用要求",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_EXISTS, exists_target_role="concomitant_medication",
                required_evidence_roles=("concomitant_medication",)))

    def test_prohibited_treatment_routes_to_d02_not_in_expected_set(self):
        """Challenge 29/56: D02-owned CM control point is excluded from
        the D04 medical expected-set; no D04 unit/risk/Query."""
        cp = self._cm_cp()
        plan = make_plan(root_ids=("CP-CM-1",))
        expansion = expand_one(cp, plan)
        assert expansion.count == 0
        assert len(expansion.delegated_control_points) == 1
        assert expansion.delegated_control_points[0].owner_domain == p.OWNER_D02

    def test_ip_dosing_routes_to_d03(self):
        """Challenge 57: D03 IP action control points route to D03."""
        cp = make_control_point(
            control_point_id="CP-IP-1",
            control_point_type=p.CONTROL_DOSE_OR_TREATMENT_MANAGEMENT,
            official_section_id="6.3", official_criterion_id="6.3.1",
            heading="给药管理",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_EXISTS, exists_target_role="ip_exposure",
                required_evidence_roles=("ip_exposure",)))
        plan = make_plan(root_ids=("CP-IP-1",))
        expansion = expand_one(cp, plan)
        assert expansion.count == 0
        assert expansion.delegated_control_points[0].owner_domain == p.OWNER_D03

    def test_visit_window_routes_to_d05_stub(self):
        """Challenge 33/69: planned visit/assessment/sample windows route
        to the D05 synthetic producer stub; D04 does not copy the window
        algorithm."""
        cp = make_control_point(
            control_point_id="CP-VIS-1",
            control_point_type=p.CONTROL_REQUIRED_PROCEDURE_OR_ASSESSMENT,
            official_section_id="8.1", official_criterion_id="8.1.1",
            heading="计划访视",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_EXISTS, exists_target_role="visit",
                required_evidence_roles=("visit",)))
        plan = make_plan(root_ids=("CP-VIS-1",))
        route = p.ProtocolControlRoutingRecord(
            control_point_id="CP-VIS-1", owner_domain=p.OWNER_D05,
            owner_signal_type="D05_visit_window",
            routing_rule_version="rv1", routing_rule_hash="rh1",
            producer_unit_id="d05-stub-unit-1",
            decision_rationale="D05 合成 producer stub 仅验证路由/typed ref")
        expansion = expand_one(cp, plan, routing=(route,))
        assert expansion.count == 0
        delegated = expansion.delegated_control_points[0]
        assert delegated.owner_domain == p.OWNER_D05
        assert delegated.producer_unit_id == "d05-stub-unit-1"

    def test_owner_competition_single_routing_gate(self):
        """Challenge 67: owner routing competition -> exactly one
        protocol_routing not_evaluable gate; no duplicate expected units."""
        cp = self._cm_cp()
        plan = make_plan(root_ids=("CP-CM-1",))
        route = p.ProtocolControlRoutingRecord(
            control_point_id="CP-CM-1", owner_domain=p.OWNER_UNRESOLVED,
            owner_signal_type="owner_unresolved",
            routing_rule_version="rv1", routing_rule_hash="rh1",
            routing_gap="无法按 component 拆分",
            candidate_owners=(p.OWNER_D02, p.OWNER_D04),
            decision_rationale="跨 owner 且无法拆分")
        expansion = expand_one(cp, plan, routing=(route,))
        assert expansion.count == 1
        result = evaluate_unit(expansion.units[0])
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert result.signal_type == p.SIGNAL_PROTOCOL_ROUTING
        assert not result.r2_candidates and not result.query_refs
        assert len(result.coverage_gap_notices) == 1

    def test_delegated_item_requires_producer_unit_or_gap(self):
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolDelegatedControlPoint(
                control_point_id="CP-1", owner_domain=p.OWNER_D02,
                owner_signal_type="D02_cm")

    def test_duplicate_routing_records_rejected(self):
        """Corrective finding 5: two routing records for one control point
        are rejected -- never last-write-wins."""
        cp = self._cm_cp()
        plan = make_plan(root_ids=("CP-CM-1",))
        route = p.ProtocolControlRoutingRecord(
            control_point_id="CP-CM-1", owner_domain=p.OWNER_D02,
            owner_signal_type="D02_cm",
            routing_rule_version="rv1", routing_rule_hash="rh1",
            producer_unit_id="d02-unit-9",
            decision_rationale="单一 owner 路由")
        with pytest.raises(p.ProtocolSliceError):
            expand_one(cp, plan, routing=(route, route))

    def test_duplicate_expected_unit_ids_rejected(self):
        """Corrective finding 5: duplicate expected unit ids fail closed
        at expansion -- never silently deduplicated."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",))
        with pytest.raises(p.ProtocolSliceError):
            p.expand_protocol_expected_set(
                project_id=PROJECT_ID, applicability=make_applicability(),
                control_points=(cp, cp), plan=plan)

    def test_slice_delegation_and_producer_refs_separate_counts(self):
        cp = self._cm_cp()
        plan = make_plan(root_ids=("CP-CM-1",))
        producer = p.ProtocolProducerReference(
            ref_id="ref-1", owner_domain=p.OWNER_D02,
            producer_unit_id="d02-unit-9",
            producer_marker_or_query_id="marker-d02-1",
            producer_risk_identity_id="risk-id-d02-1",
            audience_label="禁限用要求", monitoring_priority="medium",
            control_point_id="CP-CM-1")
        sr = p.evaluate_protocol_slice(
            project_id=PROJECT_ID, applicability=make_applicability(),
            control_points=(cp,), plan=plan,
            producer_references=(producer,), snapshot_id=SNAPSHOT_ID)
        assert sr.expected_units == 0
        assert len(sr.delegated_control_points) == 1
        assert len(sr.producer_references) == 1
        assert sr.positive_count == 0 and sr.query_draft_count == 0
        sr.verify_count_invariants()


# ===========================================================================
# 3. Atomic evaluation: inclusion / exclusion (challenges 1-4, 16-21, 34)
# ===========================================================================

class TestInclusionExclusion:
    def test_inclusion_determinately_not_met_positive(self):
        """Challenges 1/16: unique active version, value below threshold ->
        inclusion_requirement_not_met positive with one candidate/Query."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        result = atomic_single(cp, [make_binding("b1", value="8")],
                               {"laboratory": True},
                               enrollment=make_enrollment(),
                               policy=make_policy())
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert result.positive_subtype == p.SUBTYPE_INCLUSION_NOT_MET
        assert result.audience_label == "入选条件待核实"
        assert result.monitoring_priority == "high"
        assert len(result.r2_candidates) == 1
        assert len(result.query_refs) == 1
        assert result.l0_status == "covered"

    def test_inclusion_met_negative(self):
        """Challenge 2: full evidence satisfies the inclusion criterion."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        result = atomic_single(cp, [make_binding("b2", value="12")],
                               {"laboratory": True})
        assert result.l1_disposition == L1Disposition.NEGATIVE
        assert not result.r2_candidates and not result.query_refs

    def test_exclusion_present_positive(self):
        """Challenge 3: exclusion condition determinately present."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_EXISTS, exists_target_role="concomitant_medication",
            required_evidence_roles=("concomitant_medication",),
            evaluation_window_start="2026-02-01",
            evaluation_window_end="2026-02-28",
            window_start_inclusive=True, window_end_inclusive=True)
        cp = make_control_point(
            control_point_id="CP-EXC-1",
            control_point_type=p.CONTROL_EXCLUSION,
            official_criterion_id="5.2.3", heading="排除标准",
            structured_rule=rule)
        result = atomic_single(
            cp,
            [make_binding("cm1", component_id="CP-EXC-1",
                          control_point_id="CP-EXC-1",
                          role="concomitant_medication",
                          value="drugX", date_raw="2026-02-10")],
            {"concomitant_medication": True},
            enrollment=make_enrollment(p.QUERY_CONTEXT_ENROLLED),
            policy=make_policy(p.SUBTYPE_EXCLUSION_PRESENT))
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert result.positive_subtype == p.SUBTYPE_EXCLUSION_PRESENT
        assert result.audience_label == "排除条件待核实"

    def test_exclusion_absent_with_complete_coverage_negative(self):
        """Challenge 4: exclusion condition clearly absent with complete
        source coverage -> negative (no DV zero-row inference)."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_EXISTS, exists_target_role="concomitant_medication",
            required_evidence_roles=("concomitant_medication",),
            evaluation_window_start="2026-02-01",
            evaluation_window_end="2026-02-28",
            window_start_inclusive=True, window_end_inclusive=True)
        cp = make_control_point(
            control_point_id="CP-EXC-2",
            control_point_type=p.CONTROL_EXCLUSION,
            official_criterion_id="5.2.4", heading="排除标准",
            structured_rule=rule)
        result = atomic_single(
            cp, [], {"concomitant_medication": True})
        assert result.l1_disposition == L1Disposition.NEGATIVE

    def test_exclusion_zero_records_without_coverage_is_not_evaluable(self):
        """Challenge 6: IE table no failed rows / DV zero rows alone can
        never prove negative."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_NOT_EXISTS,
            exists_target_role="concomitant_medication",
            required_evidence_roles=("concomitant_medication",))
        cp = make_control_point(
            control_point_id="CP-EXC-3",
            control_point_type=p.CONTROL_EXCLUSION,
            official_criterion_id="5.2.5", heading="排除标准",
            structured_rule=rule)
        result = atomic_single(cp, [], {})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert not result.r2_candidates and not result.query_refs
        assert len(result.coverage_gap_notices) == 1

    def test_ie_summary_only_is_not_evaluable(self):
        """Challenge 5: IEYN=Yes without per-criterion evidence."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        ie_binding = make_binding(
            "ie-1", role="aggregate_ie_status", value="Yes")
        result = atomic_single(cp, [ie_binding], {"laboratory": False})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_IE_SUMMARY_ONLY
                   for n in result.coverage_gap_notices)

    def test_value_exactly_at_threshold_with_explicit_inclusive(self):
        """Challenge 17: value exactly at threshold with explicit
        inclusivity -> determinate."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        result = atomic_single(cp, [make_binding("b3", value="10")],
                               {"laboratory": True})
        assert result.l1_disposition == L1Disposition.NEGATIVE
        cp2 = make_control_point(
            control_point_id="CP-INC-2", official_criterion_id="5.1.4",
            structured_rule=make_numeric_rule(
                comparison="above", lower_inclusive=None))
        result2 = atomic_single(
            cp2, [make_binding("b4", control_point_id="CP-INC-2",
                               value="10")], {"laboratory": True})
        assert result2.l1_disposition == L1Disposition.POSITIVE

    def test_unstated_equality_is_boundary(self):
        """Challenge 18: equality undefined -> boundary (clue, no Query)."""
        cp = make_control_point(
            control_point_id="CP-INC-3", official_criterion_id="5.1.5",
            structured_rule=make_numeric_rule(lower_inclusive=None))
        result = atomic_single(cp, [make_binding(
            "b5", control_point_id="CP-INC-3", value="10")],
            {"laboratory": True})
        assert result.l1_disposition == L1Disposition.BOUNDARY
        assert "CP-INC-3" in result.control_point_id
        assert len(result.r2_candidates) == 1
        assert not result.query_refs
        assert result.audience_label.endswith("（边界）")

    def test_compare_before_vs_after_rounding_differ(self):
        """Challenge 21: compare-before-rounding and compare-after-rounding
        produce predictably different results."""
        rule_before = make_numeric_rule(threshold="1.1")
        cp_before = make_control_point(
            control_point_id="CP-R1", official_criterion_id="5.1.6",
            structured_rule=rule_before)
        result_before = atomic_single(
            cp_before, [make_binding("b6", control_point_id="CP-R1",
                                     value="1.05")],
            {"laboratory": True})
        assert result_before.l1_disposition == L1Disposition.POSITIVE

        rule_after = make_numeric_rule(
            threshold="1.1", rounding_policy=p.ROUNDING_AFTER, precision=1)
        cp_after = make_control_point(
            control_point_id="CP-R2", official_criterion_id="5.1.7",
            structured_rule=rule_after)
        result_after = atomic_single(
            cp_after, [make_binding("b7", control_point_id="CP-R2",
                                    value="1.05")],
            {"laboratory": True})
        assert result_after.l1_disposition == L1Disposition.NEGATIVE

    def test_unit_conversion_determinate(self):
        """Challenge 19: versioned unit conversion -> determinate."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        binding = make_binding("b8", value="0.8", unit="mmol/L")
        conversion = p.UnitConversionRule(
            conversion_id="cv-1", from_unit="mmol/L", to_unit="U/L",
            factor="12.5", content_hash_value="cvh1")
        result = atomic_single(
            cp, [binding], {"laboratory": True}, conversions=(conversion,))
        # 0.8 * 12.5 = 10 -> exactly at threshold, inclusive -> negative
        assert result.l1_disposition == L1Disposition.NEGATIVE

    def test_unknown_unit_not_evaluable(self):
        """Challenge 20: unknown unit or two feasible conversions ->
        not_evaluable/boundary."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        binding = make_binding("b9", value="0.8", unit="ng/mL")
        result = atomic_single(cp, [binding], {"laboratory": True})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_UNIT_UNCONVERTIBLE
                   for n in result.coverage_gap_notices)

        conv_a = p.UnitConversionRule(
            conversion_id="ca", from_unit="ng/mL", to_unit="U/L",
            factor="2", content_hash_value="h")
        conv_b = p.UnitConversionRule(
            conversion_id="cb", from_unit="ng/mL", to_unit="U/L",
            factor="3", content_hash_value="h2")
        result2 = atomic_single(
            cp, [binding], {"laboratory": True},
            conversions=(conv_a, conv_b))
        assert result2.l1_disposition in (L1Disposition.BOUNDARY,
                                          L1Disposition.NOT_EVALUABLE)

    def test_alternate_source_only_when_rule_allows(self):
        """Challenge 34: alternate lab/diagnostic source only when the
        rule explicitly allows it."""
        rule = make_numeric_rule(
            roles=("laboratory",), alternate_roles=("lab_finding_alt",))
        cp = make_control_point(structured_rule=rule)
        alt_binding = make_binding(
            "b10", role="lab_finding_alt", value="12")
        result = atomic_single(
            cp, [alt_binding], {"laboratory": True})
        assert result.l1_disposition == L1Disposition.NEGATIVE

        cp2 = make_control_point(structured_rule=make_numeric_rule())
        result2 = atomic_single(
            cp2, [make_binding("b11", role="lab_finding_alt", value="12")],
            {"laboratory": True})
        assert result2.l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_wrong_role_binding_fails_closed(self):
        cp = make_control_point(structured_rule=make_numeric_rule())
        result = atomic_single(
            cp, [make_binding("b12", role="vital_sign", value="12")],
            {"laboratory": True})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE


# ===========================================================================
# 4. Retest / exception / judgment (challenges 22-28, 61, 81)
# ===========================================================================

class TestRetestAndExceptions:
    def test_retest_in_window_covers_initial(self):
        """Challenge 22: rule allows retest; qualifying retest in window
        covers the initial -> negative + counterevidence."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_NUMERIC_AT_LEAST,
            comparison=p.RuleComparison(
                comparison="at_least", threshold="10",
                lower_inclusive=True, canonical_unit="U/L"),
            required_evidence_roles=("laboratory",),
            temporal_anchor=p.ANCHOR_SCREENING,
            retest_or_confirmation_policy="retest-v1")
        cp = make_control_point(structured_rule=rule)
        retest = p.RetestOutcome(
            has_retest=True, retest_value="11", retest_unit="U/L",
            retest_date_raw="2026-03-05",
            retest_in_allowed_window=True, retest_authority_ok=True,
            retest_count_ok=True, meets_criterion=True,
            rationale="复测合格")
        result = atomic_single(
            cp, [make_binding("b13", value="8")],
            {"laboratory": True}, retests={"CP-INC-1": retest})
        assert result.l1_disposition == L1Disposition.NEGATIVE
        assert any(ev.polarity == "counterevidence" for ev in result.evidence)

    def test_retest_outside_allowed_window_cannot_cover(self):
        """Challenge 81: retest qualifies but outside the allowed retest
        window -> original determinate problem stays positive."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_NUMERIC_AT_LEAST,
            comparison=p.RuleComparison(
                comparison="at_least", threshold="10",
                lower_inclusive=True, canonical_unit="U/L"),
            required_evidence_roles=("laboratory",),
            temporal_anchor=p.ANCHOR_SCREENING,
            retest_or_confirmation_policy="retest-v1")
        cp = make_control_point(structured_rule=rule)
        retest = p.RetestOutcome(
            has_retest=True, retest_value="11", retest_unit="U/L",
            retest_date_raw="2026-05-01",
            retest_in_allowed_window=False, retest_authority_ok=True,
            retest_count_ok=True, meets_criterion=True,
            rationale="复测在允许窗之外")
        result = atomic_single(
            cp, [make_binding("b14", value="8")],
            {"laboratory": True}, retests={"CP-INC-1": retest})
        assert result.l1_disposition == L1Disposition.POSITIVE

    def test_retest_window_or_count_unconfirmed_not_evaluable(self):
        """Challenge 23: retest window/count/authority not satisfied ->
        not_evaluable."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_NUMERIC_AT_LEAST,
            comparison=p.RuleComparison(
                comparison="at_least", threshold="10",
                lower_inclusive=True, canonical_unit="U/L"),
            required_evidence_roles=("laboratory",),
            temporal_anchor=p.ANCHOR_SCREENING,
            retest_or_confirmation_policy="retest-v1")
        cp = make_control_point(structured_rule=rule)
        retest = p.RetestOutcome(
            has_retest=True, retest_value="11", retest_unit="U/L",
            retest_date_raw="2026-03-05",
            retest_in_allowed_window=None, retest_authority_ok=None,
            retest_count_ok=None, meets_criterion=True)
        result = atomic_single(
            cp, [make_binding("b15", value="8")],
            {"laboratory": True}, retests={"CP-INC-1": retest})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_RETEST_UNCONFIRMED
                   for n in result.coverage_gap_notices)

    def test_conflicting_retests_boundary(self):
        """Challenge 24: two equally authoritative retests with no rule
        priority -> boundary."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_NUMERIC_AT_LEAST,
            comparison=p.RuleComparison(
                comparison="at_least", threshold="10",
                lower_inclusive=True, canonical_unit="U/L"),
            required_evidence_roles=("laboratory",),
            temporal_anchor=p.ANCHOR_SCREENING,
            retest_or_confirmation_policy="retest-v1")
        cp = make_control_point(structured_rule=rule)
        retest = p.RetestOutcome(
            has_retest=True, retest_value="11", retest_unit="U/L",
            retest_date_raw="2026-03-05",
            retest_in_allowed_window=True, retest_authority_ok=True,
            retest_count_ok=True, meets_criterion=True,
            conflict_with_initial=True,
            rationale="两个同等权威复测结果冲突")
        result = atomic_single(
            cp, [make_binding("b16", value="8")],
            {"laboratory": True}, retests={"CP-INC-1": retest})
        assert result.l1_disposition == L1Disposition.BOUNDARY

    def test_protocol_defined_exception_flips_to_negative(self):
        """Challenge 25: active-protocol pre-allowed exception precisely
        bound -> counterevidence/negative."""
        rule = make_numeric_rule(exception_policy="protocol_exception_allowed")
        cp = make_control_point(structured_rule=rule)
        exc = p.ProtocolExceptionBinding(
            exception_id="exc-1", subject_ref=SUBJECT, site_ref=SITE_REF,
            control_point_id="CP-INC-1", component_id="CP-INC-1",
            window_start="2026-02-01", window_end="2026-03-31",
            exception_effect=p.EXCEPTION_PROTOCOL_DEFINED,
            approved_or_confirmed=True,
            source_locator=make_locator("exc-1", "protocol_exception"))
        result = atomic_single(
            cp, [make_binding("b17", value="8")],
            {"laboratory": True}, exceptions=(exc,))
        assert result.l1_disposition == L1Disposition.NEGATIVE
        assert any(ev.polarity == "counterevidence" for ev in result.evidence)

    def test_waiver_wording_alone_cannot_flip(self):
        """Challenge 26: '已批准豁免' wording, retrospective/unapproved,
        wrong rule/subject/site/window cannot rewrite to negative."""
        rule = make_numeric_rule(exception_policy="protocol_exception_allowed")
        cp = make_control_point(structured_rule=rule)
        # Unapproved record -> context only -> stays positive
        exc_unapproved = p.ProtocolExceptionBinding(
            exception_id="exc-u", subject_ref=SUBJECT, site_ref=SITE_REF,
            control_point_id="CP-INC-1", component_id="CP-INC-1",
            window_start="2026-02-01", window_end="2026-03-31",
            exception_effect=p.EXCEPTION_PROTOCOL_DEFINED,
            approved_or_confirmed=False,
            source_locator=make_locator("exc-u", "protocol_exception"))
        r1 = atomic_single(
            cp, [make_binding("b18", value="8")],
            {"laboratory": True}, exceptions=(exc_unapproved,))
        assert r1.l1_disposition == L1Disposition.POSITIVE
        # Retrospective acknowledgement -> context only
        exc_retro = p.ProtocolExceptionBinding(
            exception_id="exc-r", subject_ref=SUBJECT, site_ref=SITE_REF,
            control_point_id="CP-INC-1", component_id="CP-INC-1",
            window_start="2026-02-01", window_end="2026-03-31",
            exception_effect=p.EXCEPTION_RETROSPECTIVE,
            approved_or_confirmed=True,
            source_locator=make_locator("exc-r", "protocol_exception"))
        r2 = atomic_single(
            cp, [make_binding("b19", value="8")],
            {"laboratory": True}, exceptions=(exc_retro,))
        assert r2.l1_disposition == L1Disposition.POSITIVE
        # Wrong subject -> context only
        exc_wrong_subj = p.ProtocolExceptionBinding(
            exception_id="exc-w", subject_ref="SYN-999", site_ref=SITE_REF,
            control_point_id="CP-INC-1", component_id="CP-INC-1",
            window_start="2026-02-01", window_end="2026-03-31",
            exception_effect=p.EXCEPTION_PROTOCOL_DEFINED,
            approved_or_confirmed=True)
        r3 = atomic_single(
            cp, [make_binding("b20", value="8")],
            {"laboratory": True}, exceptions=(exc_wrong_subj,))
        assert r3.l1_disposition == L1Disposition.POSITIVE
        # Missing approval status -> not_evaluable (effect cannot be judged)
        exc_missing = p.ProtocolExceptionBinding(
            exception_id="exc-m", subject_ref=SUBJECT, site_ref=SITE_REF,
            control_point_id="CP-INC-1", component_id="CP-INC-1",
            window_start="2026-02-01", window_end="2026-03-31",
            exception_effect=p.EXCEPTION_PROTOCOL_DEFINED,
            approved_or_confirmed=None)
        r4 = atomic_single(
            cp, [make_binding("b21", value="8")],
            {"laboratory": True}, exceptions=(exc_missing,))
        assert r4.l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_urgent_hazard_is_context_not_auto_negative(self):
        """Challenge 28: urgent-hazard exception fully documented explains
        the disposition but does not erase the deviation fact."""
        rule = make_numeric_rule(exception_policy="protocol_exception_allowed")
        cp = make_control_point(structured_rule=rule)
        exc = p.ProtocolExceptionBinding(
            exception_id="exc-h", subject_ref=SUBJECT, site_ref=SITE_REF,
            control_point_id="CP-INC-1", component_id="CP-INC-1",
            window_start="2026-02-01", window_end="2026-03-31",
            exception_effect=p.EXCEPTION_URGENT_HAZARD,
            approved_or_confirmed=True)
        result = atomic_single(
            cp, [make_binding("b22", value="8")],
            {"laboratory": True}, exceptions=(exc,))
        assert result.l1_disposition == L1Disposition.POSITIVE

    def test_investigator_judgment_missing_not_evaluable(self):
        """Challenge 27: investigator judgment is a required input but not
        recorded -> not_evaluable; never inferred from clinical common
        sense."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_INVESTIGATOR_JUDGMENT,
            investigator_judgment_required=True,
            required_evidence_roles=("investigator_judgment",),
            temporal_anchor=p.ANCHOR_OTHER)
        cp = make_control_point(structured_rule=rule)
        result = atomic_single(cp, [], {})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_INVESTIGATOR_JUDGMENT_MISSING
                   for n in result.coverage_gap_notices)

    def test_n1_pre_allowed_exception_reevaluates_negative(self):
        """Challenge 61: N positive; N+1 adds pre-allowed exception evidence
        in effect -> re-evaluated negative + counterevidence.  Historical
        evaluation is not rewritten (same identity, new disposition)."""
        rule = make_numeric_rule(exception_policy="protocol_exception_allowed")
        cp = make_control_point(structured_rule=rule)
        binding = make_binding("b23", value="8")
        r_n = atomic_single(cp, [binding], {"laboratory": True})
        assert r_n.l1_disposition == L1Disposition.POSITIVE
        exc = p.ProtocolExceptionBinding(
            exception_id="exc-n1", subject_ref=SUBJECT, site_ref=SITE_REF,
            control_point_id="CP-INC-1", component_id="CP-INC-1",
            window_start="2026-02-01", window_end="2026-03-31",
            exception_effect=p.EXCEPTION_PROTOCOL_DEFINED,
            approved_or_confirmed=True)
        r_n1 = atomic_single(
            cp, [binding], {"laboratory": True}, exceptions=(exc,))
        assert r_n1.l1_disposition == L1Disposition.NEGATIVE
        # Same unit id: the identity is the stable control point + window,
        # not the disposition.
        assert r_n.unit_id == r_n1.unit_id


# ===========================================================================
# 5. Sequence / discontinuation / age / temporal (challenges 37-42, 80)
# ===========================================================================

class TestSequenceDiscontinuationAge:
    def test_consent_before_randomization_ok(self):
        rule = p.ProtocolStructuredRule(
            operator=p.OP_SEQUENCE, order_direction="before",
            anchor_role_a="consent", anchor_role_b="randomization",
            required_evidence_roles=("consent", "randomization"),
            temporal_anchor=p.ANCHOR_RANDOMIZATION)
        cp = make_control_point(
            control_point_id="CP-SEQ-1",
            control_point_type=p.CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT,
            official_criterion_id="4.2.1", heading="知情与入组时序",
            structured_rule=rule)
        result = atomic_single(cp, [
            make_binding("c1", component_id="CP-SEQ-1",
                         control_point_id="CP-SEQ-1", role="consent",
                         date_raw="2026-01-10"),
            make_binding("r1", component_id="CP-SEQ-1",
                         control_point_id="CP-SEQ-1", role="randomization",
                         date_raw="2026-01-20"),
        ], {})
        assert result.l1_disposition == L1Disposition.NEGATIVE

    def test_consent_after_first_protocol_procedure_conflict(self):
        """Challenge 38: consent after the first protocol-required
        procedure -> determinate sequence conflict (positive)."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_SEQUENCE, order_direction="not_after",
            anchor_role_a="consent", anchor_role_b="first_protocol_procedure",
            required_evidence_roles=("consent", "first_protocol_procedure"),
            temporal_anchor=p.ANCHOR_FIRST_DOSE)
        cp = make_control_point(
            control_point_id="CP-SEQ-2",
            control_point_type=p.CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT,
            official_criterion_id="4.2.2", heading="知情与入组时序",
            structured_rule=rule)
        result = atomic_single(cp, [
            make_binding("c2", component_id="CP-SEQ-2",
                         control_point_id="CP-SEQ-2", role="consent",
                         date_raw="2026-02-01"),
            make_binding("p2", component_id="CP-SEQ-2",
                         control_point_id="CP-SEQ-2",
                         role="first_protocol_procedure",
                         date_raw="2026-01-20"),
        ], {})
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert result.positive_subtype == (
            p.SUBTYPE_CONSENT_SEQUENCE_INCONSISTENT)

    def test_anchors_not_interchangeable(self):
        """Challenge 39: screening/randomization/first-dose anchors are
        distinct roles; a screening record cannot satisfy the
        randomization role."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_SEQUENCE, order_direction="before",
            anchor_role_a="consent", anchor_role_b="randomization",
            required_evidence_roles=("consent", "randomization"),
            temporal_anchor=p.ANCHOR_RANDOMIZATION)
        cp = make_control_point(
            control_point_id="CP-SEQ-3",
            control_point_type=p.CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT,
            official_criterion_id="4.2.3", heading="知情与入组时序",
            structured_rule=rule)
        result = atomic_single(cp, [
            make_binding("c3", component_id="CP-SEQ-3",
                         control_point_id="CP-SEQ-3", role="consent",
                         date_raw="2026-01-10"),
            make_binding("s3", component_id="CP-SEQ-3",
                         control_point_id="CP-SEQ-3", role="screening",
                         date_raw="2026-01-20"),
        ], {})
        # Randomization role missing -> not_evaluable, never satisfied by
        # the screening record.
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_partial_date_order_boundary(self):
        """Challenge 37: partial date possibly hitting/missing -> boundary."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_SEQUENCE, order_direction="before",
            anchor_role_a="consent", anchor_role_b="randomization",
            required_evidence_roles=("consent", "randomization"),
            temporal_anchor=p.ANCHOR_RANDOMIZATION)
        cp = make_control_point(
            control_point_id="CP-SEQ-4",
            control_point_type=p.CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT,
            official_criterion_id="4.2.4", heading="知情与入组时序",
            structured_rule=rule)
        result = atomic_single(cp, [
            make_binding("c4", component_id="CP-SEQ-4",
                         control_point_id="CP-SEQ-4", role="consent",
                         date_raw="2026-01"),
            make_binding("r4", component_id="CP-SEQ-4",
                         control_point_id="CP-SEQ-4", role="randomization",
                         date_raw="2026-01-20"),
        ], {})
        assert result.l1_disposition == L1Disposition.BOUNDARY

    def test_discontinuation_trigger_inconsistent_positive(self):
        """Challenge 41: trigger reached but disposition determinately
        inconsistent -> D04 positive."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_DISCONTINUATION_TRIGGER,
            trigger_comparison=p.RuleComparison(
                comparison="above", threshold="5", canonical_unit="xULN"),
            expected_disposition_values=("withdrawn", "terminated"),
            required_evidence_roles=("laboratory",),
            temporal_anchor=p.ANCHOR_ON_TREATMENT)
        cp = make_control_point(
            control_point_id="CP-DISC-1",
            control_point_type=p.CONTROL_DISCONTINUATION_OR_WITHDRAWAL,
            official_criterion_id="7.3.1", heading="退出标准",
            structured_rule=rule)
        result = atomic_single(cp, [
            make_binding("l1", component_id="CP-DISC-1",
                         control_point_id="CP-DISC-1", role="laboratory",
                         value="6", unit="xULN", date_raw="2026-03-01"),
            make_binding("d1", component_id="CP-DISC-1",
                         control_point_id="CP-DISC-1", role="disposition",
                         value="active", date_raw="2026-03-10"),
        ], {"laboratory": True})
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert result.positive_subtype == (
            p.SUBTYPE_DISCONTINUATION_INCONSISTENT)
        assert result.audience_label == "退出或终止参与标准待核实"

    def test_discontinuation_trigger_consistent_negative(self):
        rule = p.ProtocolStructuredRule(
            operator=p.OP_DISCONTINUATION_TRIGGER,
            trigger_comparison=p.RuleComparison(
                comparison="above", threshold="5", canonical_unit="xULN"),
            expected_disposition_values=("withdrawn", "terminated"),
            required_evidence_roles=("laboratory",),
            temporal_anchor=p.ANCHOR_ON_TREATMENT)
        cp = make_control_point(
            control_point_id="CP-DISC-2",
            control_point_type=p.CONTROL_DISCONTINUATION_OR_WITHDRAWAL,
            official_criterion_id="7.3.2", heading="退出标准",
            structured_rule=rule)
        result = atomic_single(cp, [
            make_binding("l2", component_id="CP-DISC-2",
                         control_point_id="CP-DISC-2", role="laboratory",
                         value="6", unit="xULN", date_raw="2026-03-01"),
            make_binding("d2", component_id="CP-DISC-2",
                         control_point_id="CP-DISC-2", role="disposition",
                         value="withdrawn", date_raw="2026-03-03"),
        ], {"laboratory": True})
        assert result.l1_disposition == L1Disposition.NEGATIVE

    def test_discontinuation_missing_disposition_not_evaluable(self):
        """Challenge 42: D04-native discontinuation input missing ->
        not_evaluable (IP pause/stop inputs are D03-owned)."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_DISCONTINUATION_TRIGGER,
            trigger_comparison=p.RuleComparison(
                comparison="above", threshold="5", canonical_unit="xULN"),
            expected_disposition_values=("withdrawn", "terminated"),
            required_evidence_roles=("laboratory",),
            temporal_anchor=p.ANCHOR_ON_TREATMENT)
        cp = make_control_point(
            control_point_id="CP-DISC-3",
            control_point_type=p.CONTROL_DISCONTINUATION_OR_WITHDRAWAL,
            official_criterion_id="7.3.3", heading="退出标准",
            structured_rule=rule)
        result = atomic_single(cp, [
            make_binding("l3", component_id="CP-DISC-3",
                         control_point_id="CP-DISC-3", role="laboratory",
                         value="6", unit="xULN", date_raw="2026-03-01"),
        ], {"laboratory": True})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_age_algorithm_unfrozen_not_evaluable(self):
        """Challenge 80: age inclusion with only birth year + consent date
        and no frozen age algorithm -> not_evaluable, never default
        周岁/实足年龄."""
        rule = p.ProtocolStructuredRule(
            operator=p.OP_AGE,
            comparison=p.RuleComparison(
                comparison="at_least", threshold="18",
                lower_inclusive=True, canonical_unit="year"),
            required_evidence_roles=("demographics", "consent"),
            temporal_anchor=p.ANCHOR_CONSENT)
        cp = make_control_point(
            control_point_id="CP-AGE-1", official_criterion_id="5.1.8",
            heading="年龄入选标准", structured_rule=rule)
        result = atomic_single(cp, [
            make_binding("bd", component_id="CP-AGE-1",
                         control_point_id="CP-AGE-1", role="demographics",
                         value="2005", date_raw="2005"),
            make_binding("cs", component_id="CP-AGE-1",
                         control_point_id="CP-AGE-1", role="consent",
                         value="", date_raw="2026-03-01"),
        ], {})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_AGE_ALGORITHM_UNFROZEN
                   for n in result.coverage_gap_notices)

    def test_age_with_frozen_algorithm_boundary_on_threshold_year(self):
        rule = p.ProtocolStructuredRule(
            operator=p.OP_AGE, age_algorithm_id="age-algo-v1",
            comparison=p.RuleComparison(
                comparison="at_least", threshold="18",
                lower_inclusive=True, canonical_unit="year"),
            required_evidence_roles=("demographics", "consent"),
            temporal_anchor=p.ANCHOR_CONSENT)
        cp = make_control_point(
            control_point_id="CP-AGE-2", official_criterion_id="5.1.9",
            heading="年龄入选标准", structured_rule=rule)
        # Born 2008, consent 2026-03-01 -> 18 at year precision but exact
        # birthday unknown -> boundary (may or may not have crossed).
        result = atomic_single(cp, [
            make_binding("bd2", component_id="CP-AGE-2",
                         control_point_id="CP-AGE-2", role="demographics",
                         value="2008", date_raw="2008"),
            make_binding("cs2", component_id="CP-AGE-2",
                         control_point_id="CP-AGE-2", role="consent",
                         value="", date_raw="2026-03-01"),
        ], {})
        assert result.l1_disposition == L1Disposition.BOUNDARY


# ===========================================================================
# 6. Package expressions (challenges 8, 9, 58, 72-74, 82)
# ===========================================================================

class TestPackageExpressions:
    def _pkg_cp(
        self, expression: p.IssueExpression, component_ids: Sequence[str],
        cp_id: str = "CP-PKG-1", heading: str = "入选标准（组合）",
    ) -> p.ProtocolControlPoint:
        return make_control_point(
            control_point_id=cp_id,
            official_criterion_id="5.1.10",
            heading=heading,
            root_kind=p.NODE_PACKAGE,
            issue_expression=expression,
            component_ids=component_ids)

    def _rules(self):
        return {
            "C1": make_component("C1", "CP-PKG-1", make_numeric_rule(threshold="10")),
            "C2": make_component("C2", "CP-PKG-1", make_numeric_rule(threshold="5")),
        }

    def test_any_of_one_met_one_not_evaluable_negative(self):
        """Challenge 72: '满足以下任一项' one met + one not_evaluable ->
        package L1 negative, L0/domain incomplete, no candidate/Query."""
        cp = self._pkg_cp(
            p.IssueExpression(operator=p.EXPR_AND, component_ids=("C1", "C2")),
            ("C1", "C2"))
        plan = make_plan(root_ids=("CP-PKG-1",))
        result = evaluate_single(
            cp, plan, self._rules(),
            bindings=[make_binding("b1", component_id="C1", control_point_id="CP-PKG-1", value="12")],
            roles={})
        assert result.l1_disposition == L1Disposition.NEGATIVE
        assert result.l0_status == "partial"
        assert len(result.coverage_gap_notices) == 1
        assert not result.r2_candidates and not result.query_refs
        assert "C2" in result.unresolved_component_ids
        # Component assessments never enter the expected-set/lifecycle.
        assert len(result.component_assessments) == 2
        assert all(not a.assessment_id.startswith("unit-")
                   for a in result.component_assessments)

    def test_all_of_one_unmet_one_not_evaluable_positive(self):
        """Challenge 73: '需同时满足全部' one unmet + one not_evaluable ->
        package L1 positive, L0/domain incomplete, one risk/Query listing
        decisive and unresolved components."""
        cp = self._pkg_cp(
            p.IssueExpression(operator=p.EXPR_OR, component_ids=("C1", "C2")),
            ("C1", "C2"))
        plan = make_plan(root_ids=("CP-PKG-1",))
        result = evaluate_single(
            cp, plan, self._rules(),
            bindings=[make_binding("b2", component_id="C1", control_point_id="CP-PKG-1", value="8")],
            roles={},
            enrollment=make_enrollment(p.QUERY_CONTEXT_ENROLLED),
            policy=make_policy())
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert result.l0_status == "partial"
        assert len(result.r2_candidates) == 1
        assert len(result.query_refs) == 1
        assert "C1" in result.decisive_component_ids
        assert "C2" in result.unresolved_component_ids
        assert len(result.coverage_gap_notices) == 1

    def test_at_least_n_constant_true_positive(self):
        """Challenge 74: AT_LEAST_N constant true -> positive."""
        rules = {
            "C1": make_component("C1", "CP-ATL", make_numeric_rule(threshold="10")),
            "C2": make_component("C2", "CP-ATL", make_numeric_rule(threshold="5")),
            "C3": make_component("C3", "CP-ATL", make_numeric_rule(threshold="1")),
        }
        cp = self._pkg_cp(
            p.IssueExpression(operator=p.EXPR_AT_LEAST_N,
                              component_ids=("C1", "C2", "C3"), at_least_n=2),
            ("C1", "C2", "C3"), cp_id="CP-ATL")
        plan = make_plan(root_ids=("CP-ATL",))
        result = evaluate_single(
            cp, plan, rules,
            bindings=[make_binding("b1", component_id="C1", control_point_id="CP-ATL", value="8"),
                      make_binding("b2", component_id="C2", control_point_id="CP-ATL", value="3")],
            roles={},
            enrollment=make_enrollment(), policy=make_policy())
        # Two unmet (issue_true) + one not_evaluable -> count>=2 always
        # true -> positive; L0 partial.
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert result.l0_status == "partial"
        assert len(result.r2_candidates) == 1

    def test_at_least_n_variable_not_evaluable(self):
        rules = {
            "C1": make_component("C1", "CP-ATL2", make_numeric_rule(threshold="10")),
            "C2": make_component("C2", "CP-ATL2", make_numeric_rule(threshold="5")),
            "C3": make_component("C3", "CP-ATL2", make_numeric_rule(threshold="1")),
        }
        cp = self._pkg_cp(
            p.IssueExpression(operator=p.EXPR_AT_LEAST_N,
                              component_ids=("C1", "C2", "C3"), at_least_n=2),
            ("C1", "C2", "C3"), cp_id="CP-ATL2")
        plan = make_plan(root_ids=("CP-ATL2",))
        result = evaluate_single(
            cp, plan, rules,
            bindings=[make_binding("b1", component_id="C1", control_point_id="CP-ATL2", value="8"),
                      make_binding("b2", component_id="C2", control_point_id="CP-ATL2", value="12")],
            roles={})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert not result.r2_candidates and not result.query_refs

    def test_at_least_n_constant_false_negative(self):
        rules = {
            "C1": make_component("C1", "CP-ATL3", make_numeric_rule(threshold="10")),
            "C2": make_component("C2", "CP-ATL3", make_numeric_rule(threshold="5")),
            "C3": make_component("C3", "CP-ATL3", make_numeric_rule(threshold="1")),
        }
        cp = self._pkg_cp(
            p.IssueExpression(operator=p.EXPR_AT_LEAST_N,
                              component_ids=("C1", "C2", "C3"), at_least_n=2),
            ("C1", "C2", "C3"), cp_id="CP-ATL3")
        plan = make_plan(root_ids=("CP-ATL3",))
        result = evaluate_single(
            cp, plan, rules,
            bindings=[make_binding("b1", component_id="C1", control_point_id="CP-ATL3", value="12"),
                      make_binding("b2", component_id="C2", control_point_id="CP-ATL3", value="8"),
                      make_binding("b3", component_id="C3", control_point_id="CP-ATL3", value="2")],
            roles={})
        assert result.l1_disposition == L1Disposition.NEGATIVE

    def test_input_order_does_not_change_expression_result(self):
        """Challenge 74: input order of components does not change the
        package outcome (AND/OR/AT_LEAST_N are commutative)."""
        rules = {
            "C1": make_component("C1", "CP-PKG-O", make_numeric_rule(threshold="10")),
            "C2": make_component("C2", "CP-PKG-O", make_numeric_rule(threshold="5")),
        }
        e1 = p.IssueExpression(operator=p.EXPR_OR, component_ids=("C1", "C2"))
        e2 = p.IssueExpression(operator=p.EXPR_OR, component_ids=("C2", "C1"))
        cp1 = self._pkg_cp(e1, ("C1", "C2"), cp_id="CP-PKG-O")
        cp2 = self._pkg_cp(e2, ("C2", "C1"), cp_id="CP-PKG-O2")
        plan = make_plan(root_ids=("CP-PKG-O", "CP-PKG-O2"))
        bindings = [make_binding("b1", component_id="C1", control_point_id="CP-PKG-O", value="8"),
                    make_binding("b2", component_id="C2", control_point_id="CP-PKG-O", value="3")]
        bindings2 = [make_binding("b1", component_id="C1",
                                      control_point_id="CP-PKG-O2", value="8"),
                     make_binding("b2", component_id="C2",
                                  control_point_id="CP-PKG-O2", value="3")]
        r1 = evaluate_single(cp1, plan, rules, bindings=bindings, roles={})
        r2 = evaluate_single(cp2, plan, rules, bindings=bindings2, roles={})
        assert r1.l1_disposition == r2.l1_disposition
        assert r1.l1_disposition == L1Disposition.POSITIVE

    def test_ambiguous_any_all_never_defaults_and_or(self):
        """Challenge 82: original text only says '需满足下列标准' with no
        determinable 任一/全部/至少 N -> package not_evaluable; AND/OR is
        never defaulted."""
        rules = self._rules()
        cp = self._pkg_cp(
            p.IssueExpression(operator=p.EXPR_AND, component_ids=("C1", "C2")),
            ("C1", "C2"))
        plan = make_plan(root_ids=("CP-PKG-1",), verification="unverified")
        result = evaluate_single(
            cp, plan, rules,
            bindings=[make_binding("b1", component_id="C1", control_point_id="CP-PKG-1", value="8"),
                      make_binding("b2", component_id="C2", control_point_id="CP-PKG-1", value="3")],
            roles={})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_RULE_NOT_VERIFIED
                   for n in result.coverage_gap_notices)
        assert not result.r2_candidates

    def test_expression_incomplete_not_evaluable(self):
        """Challenge 82/9: an expression referencing an unknown component
        fails closed to not_evaluable (never silent AND/OR)."""
        rules = self._rules()
        cp = self._pkg_cp(
            p.IssueExpression(operator=p.EXPR_AND,
                              component_ids=("C1", "C2", "C9")),
            ("C1", "C2"))
        plan = make_plan(root_ids=("CP-PKG-1",))
        result = evaluate_single(cp, plan, rules, bindings=[], roles={})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert "表达式引用未知子条件" in result.not_evaluable_reason

    def test_package_one_unit_per_root_and_assessment_ids_distinct(self):
        """Challenges 8/59: '以下任一' and '以下全部' each generate one
        package EvaluationUnit; assessment ids never equal unit ids."""
        rules = self._rules()
        cp_any = self._pkg_cp(
            p.IssueExpression(operator=p.EXPR_AND, component_ids=("C1", "C2")),
            ("C1", "C2"))
        cp_all = self._pkg_cp(
            p.IssueExpression(operator=p.EXPR_OR, component_ids=("C1", "C2")),
            ("C1", "C2"), cp_id="CP-PKG-ALL")
        plan = make_plan(root_ids=("CP-PKG-1", "CP-PKG-ALL"))
        expansion = p.expand_protocol_expected_set(
            project_id=PROJECT_ID, applicability=make_applicability(),
            control_points=(cp_any, cp_all), plan=plan, components=rules)
        assert expansion.count == 2
        assert len(set(expansion.unit_ids)) == 2
        r_any = evaluate_single(
            cp_any, plan, rules,
            bindings=[make_binding("b1", component_id="C1", control_point_id="CP-PKG-1", value="8"),
                      make_binding("b2", component_id="C2", control_point_id="CP-PKG-1", value="3")],
            roles={})
        r_all = evaluate_single(
            cp_all, plan, rules,
            bindings=[make_binding("b1", component_id="C1", value="8"),
                      make_binding("b2", component_id="C2", value="3")],
            roles={})
        # 任一 (AND of issue_true) both unmet -> positive; 全部 (OR) both
        # unmet -> positive as well here; different unit ids though.
        assert r_any.unit_id != r_all.unit_id
        for r in (r_any, r_all):
            for assessment in r.component_assessments:
                assert assessment.assessment_id != r.unit_id
                assert assessment.assessment_id.startswith("d04-ca-")


# ===========================================================================
# 7. Query contexts (challenges 43-44, 75-76)
# ===========================================================================

class TestQueryContexts:
    def _positive_inclusion(self, query_context: str) -> p.ProtocolUnitResult:
        cp = make_control_point(structured_rule=make_numeric_rule())
        return atomic_single(
            cp, [make_binding("bq", value="8")], {"laboratory": True},
            enrollment=make_enrollment(query_context),
            policy=make_policy())

    def test_three_part_query_format(self):
        """Challenge 43: three-part Query contains version, clause, facts
        and action; enrolled context requests PD evaluation."""
        result = self._positive_inclusion(p.QUERY_CONTEXT_ENROLLED)
        q = result.query_refs[0]
        assert q.basis.startswith("依据：")
        assert q.finding.startswith("发现：")
        assert q.action.startswith("行动项：")
        assert "V2.0" in q.basis
        assert "5.1" in q.basis and "5.1.3" in q.basis
        assert "SYN-001" in q.finding
        assert "如确认不符合方案，请评估是否构成方案偏离并按相应流程处理" in q.action
        assert q.linked_candidate_id == result.r2_candidates[0].candidate_id

    def test_not_enrolled_query_never_asks_pd(self):
        """Challenge 75: screening not met, determinately not
        randomized/enrolled -> Query only verifies screening
        conclusion/records; no '评估是否构成方案偏离'."""
        result = self._positive_inclusion(p.QUERY_CONTEXT_NOT_OCCURRED)
        q = result.query_refs[0]
        assert "方案偏离" not in q.action
        assert "请核实入排结果、筛选结论或数据记录" in q.action

    def test_unresolved_enrollment_query_asks_state_first(self):
        """Challenge 76: randomization/enrollment state unresolved -> Query
        first asks to verify the state and states insufficient data."""
        result = self._positive_inclusion(p.QUERY_CONTEXT_UNRESOLVED)
        q = result.query_refs[0]
        assert "请先核实是否已随机/入组/接受研究干预及事件时序" in q.action
        assert "资料不足" in q.action
        assert "方案偏离" not in q.action

    def test_query_forbids_confirmed_pd_language(self):
        """Challenge 44: Query must not contain confirmed/major PD,
        reported or closed language."""
        for ctx in p.QUERY_CONTEXTS:
            result = self._positive_inclusion(ctx)
            for q in result.query_refs:
                for token in ("已确认", "重大方案偏离", "已报送", "已关闭",
                              "positive", "candidate", "候选信号", "正式事实",
                              "只读投影", "规则引擎命中"):
                    assert token not in q.basis, token
                    assert token not in q.finding, token
                    assert token not in q.action, token

    def test_boundary_has_no_query(self):
        cp = make_control_point(
            control_point_id="CP-BND", official_criterion_id="5.1.11",
            structured_rule=make_numeric_rule(lower_inclusive=None))
        result = atomic_single(
            cp, [make_binding("bb", control_point_id="CP-BND", value="10")],
            {"laboratory": True})
        assert result.l1_disposition == L1Disposition.BOUNDARY
        assert not result.query_refs
        assert len(result.r2_candidates) == 1

    def test_query_locators_reachable_and_deduped(self):
        result = self._positive_inclusion(p.QUERY_CONTEXT_ENROLLED)
        q = result.query_refs[0]
        assert q.source_locator_ids
        assert len(set(q.source_locator_ids)) == len(q.source_locator_ids)
        available = set(result.all_source_locator_ids())
        assert set(q.source_locator_ids) <= available


# ===========================================================================
# 8. Coverage notices and counts (challenges 45, 54, 58)
# ===========================================================================

class TestCoverageNoticesAndCounts:
    def test_not_evaluable_zero_candidate_query_with_notice(self):
        """Challenge 45: not_evaluable unit generates a coverage-gap notice
        bound to unit/reason/protocol locators/reachable sources; no
        candidate/risk/L2 Query; never writes determinate non-compliance."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        result = atomic_single(cp, [], {})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert len(result.coverage_gap_notices) == 1
        notice = result.coverage_gap_notices[0]
        assert notice.unit_id == result.unit_id
        assert notice.reason_code == p.GAP_SOURCE_ROLE_NOT_COVERED
        assert notice.protocol_locator_ids
        # Corrective finding 2: missing_evidence_roles holds the real
        # semantic role required by the rule and absent here -- never a
        # reason code or component id.
        assert notice.missing_evidence_roles == ("laboratory",)
        assert set(notice.missing_evidence_roles) & set(
            p.GAP_REASON_CODES) == set()
        assert not result.r2_candidates
        assert not result.query_refs
        assert not result.risk_instance_refs
        assert "确定不符合" not in result.not_evaluable_reason

    def test_notice_id_stable_across_reruns(self):
        cp = make_control_point(structured_rule=make_numeric_rule())
        r1 = atomic_single(cp, [], {})
        r2 = atomic_single(cp, [], {})
        assert (r1.coverage_gap_notices[0].notice_id
                == r2.coverage_gap_notices[0].notice_id)

    def test_determinate_with_gap_generates_notice_and_partial_l0(self):
        """Challenge 58: package issue_true + not_evaluable -> determinate
        positive with one candidate/Query; L0 partial + notice block
        domain completeness."""
        rules = {
            "C1": make_component("C1", "CP-PKG-1", make_numeric_rule(threshold="10")),
            "C2": make_component("C2", "CP-PKG-1", make_numeric_rule(threshold="5")),
        }
        cp = make_control_point(
            control_point_id="CP-PKG-1",
            official_criterion_id="5.1.12", heading="入选标准（需同时满足全部）",
            root_kind=p.NODE_PACKAGE,
            issue_expression=p.IssueExpression(
                operator=p.EXPR_OR, component_ids=("C1", "C2")),
            component_ids=("C1", "C2"))
        plan = make_plan(root_ids=("CP-PKG-1",))
        result = evaluate_single(
            cp, plan, rules,
            bindings=[make_binding("b1", component_id="C1",
                                   control_point_id="CP-PKG-1", value="8")],
            roles={},
            enrollment=make_enrollment(), policy=make_policy())
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert result.l0_status == "partial"
        assert len(result.r2_candidates) == 1
        assert len(result.query_refs) == 1
        assert len(result.coverage_gap_notices) == 1
        assert result.coverage_gap_notices[0].reason_code == (
            p.GAP_COMPONENT_GAP_DETERMINATE)
        # Corrective finding 2: the unresolved component's required role
        # (not the component id) lands in missing_evidence_roles.
        assert (result.coverage_gap_notices[0].missing_evidence_roles
                == ("laboratory",))

    def test_missing_evidence_roles_are_semantic_roles_only(self):
        """Corrective finding 2: gap notices carry real semantic evidence
        roles (absent/uncovered per unit), never reason codes or
        component ids; a gap with no missing role uses an empty tuple."""
        # Ambiguous-expression not_evaluable (unverified plan) -> no
        # missing roles, reason code preserved separately.
        cp = make_control_point(
            control_point_id="CP-PKG-2",
            official_criterion_id="5.1.30", heading="需满足下列标准",
            root_kind=p.NODE_PACKAGE,
            issue_expression=p.IssueExpression(
                operator=p.EXPR_AND, component_ids=("C1",)),
            component_ids=("C1",))
        plan = make_plan(root_ids=("CP-PKG-2",),
                         verification="unverified")
        result = evaluate_single(
            cp, plan, {"C1": make_component(
                "C1", "CP-PKG-2", make_numeric_rule(threshold="10"))},
            roles={"laboratory": True})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        notice = result.coverage_gap_notices[0]
        assert notice.reason_code == p.GAP_RULE_NOT_VERIFIED
        assert notice.missing_evidence_roles == ()
        # not_evaluable from a role-covered but binding-free unit still
        # reports the absent semantic role.
        r2 = atomic_single(make_control_point(
            structured_rule=make_numeric_rule()), [], {})
        n2 = r2.coverage_gap_notices[0]
        assert n2.missing_evidence_roles == ("laboratory",)
        assert set(n2.missing_evidence_roles) & set(p.GAP_REASON_CODES) == set()

    def test_source_records_include_evidence_locators(self):
        """Corrective finding 3: every unique accepted evidence locator
        becomes a SourceRecordRef (deduplicated by locator id) while the
        protocol locator is retained; Query locators stay reachable."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        result = atomic_single(
            cp, [make_binding("b1", value="8")], {"laboratory": True},
            enrollment=make_enrollment(), policy=make_policy())
        ids = [ref.locator.locator_id()
               for ref in result.source_record_refs]
        assert cp.source_locator.locator_id() in ids
        ev_ids = {ev.locator.locator_id() for ev in result.evidence}
        assert ev_ids <= set(ids)
        assert len(ids) == len(set(ids))  # deterministic dedup
        assert ids == sorted(ids)
        q = result.query_refs[0]
        assert set(q.source_locator_ids) <= set(ids)
        ue = result.to_unit_evaluation(
            provenance_snapshot_id=SNAPSHOT_ID,
            provenance_rule_lineage="rc2")
        assert ue.count_l2("source_record") == len(ids)

    def test_counts_never_contaminate(self):
        """Challenge 54: source/evidence/candidate/risk/Query counts stay
        separate; coverage-gap notices never enter Query count."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        result = atomic_single(
            cp, [make_binding("b1", value="8")], {"laboratory": True},
            enrollment=make_enrollment(), policy=make_policy())
        assert len(result.source_record_refs) >= 1
        assert len(result.r2_candidates) == 1
        assert len(result.query_refs) == 1
        # UnitEvaluation join invariants hold for the positive unit.
        ue = result.to_unit_evaluation(
            provenance_snapshot_id=SNAPSHOT_ID,
            provenance_rule_lineage="rc2")
        assert isinstance(ue, UnitEvaluation)
        assert ue.count_l2("risk_candidate") == 1
        assert ue.count_l2("query_draft") == 1

    def test_satisfies_risk_domain_unit_result(self):
        cp = make_control_point(structured_rule=make_numeric_rule())
        result = atomic_single(cp, [], {})
        assert isinstance(result, RiskDomainUnitResult)
        assert result.not_evaluable_reason

    def test_to_unit_evaluation_positive_requires_provenance(self):
        cp = make_control_point(structured_rule=make_numeric_rule())
        result = atomic_single(
            cp, [make_binding("b1", value="8")], {"laboratory": True},
            enrollment=make_enrollment(), policy=make_policy())
        with pytest.raises(UnitJoinError):
            result.to_unit_evaluation()
        ue = result.to_unit_evaluation(
            provenance_snapshot_id=SNAPSHOT_ID,
            provenance_rule_lineage="rc2")
        assert ue.l1_disposition == L1Disposition.POSITIVE

    def test_not_applicable_control_point(self):
        """§6.5: control point authoritatively not applicable -> unit
        not_applicable bound to the applicability decision."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        appl = make_applicability()
        appl = p.ProtocolApplicabilityDecision(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            decision_time_anchor=p.ANCHOR_ON_TREATMENT,
            decision_time_anchor_date="2026-03-01",
            decision_status=p.APPLICABILITY_UNIQUE_ACTIVE,
            protocol_id="PROTO-1", protocol_version="V2.0",
            amendment_id_or_hash="am2",
            feasible_version_fingerprints=("fp-1",),
            stable_source_content_key="k",
            not_applicable_control_point_ids=("CP-INC-1",))
        result = evaluate_single(cp, make_plan(root_ids=("CP-INC-1",)),
                                 applicability=appl)
        assert result.l1_disposition == L1Disposition.NOT_APPLICABLE
        assert result.l0_status == "not_applicable"
        assert not result.r2_candidates and not result.query_refs


# ===========================================================================
# 9. Identity and determinism (challenges 48, 52, 59, 62, 68)
# ===========================================================================

class TestIdentityAndDeterminism:
    def test_rerun_produces_identical_ids_and_hashes(self):
        """Challenge 48: same input rerun -> unit/candidate/payload hashes
        stable."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",))
        bindings = [make_binding("b1", value="8")]
        r1 = evaluate_single(cp, plan, bindings=bindings,
                             roles={"laboratory": True},
                             enrollment=make_enrollment(),
                             policy=make_policy())
        r2 = evaluate_single(cp, plan, bindings=bindings,
                             roles={"laboratory": True},
                             enrollment=make_enrollment(),
                             policy=make_policy())
        assert r1.unit_id == r2.unit_id
        assert (r1.r2_candidates[0].candidate_id
                == r2.r2_candidates[0].candidate_id)
        assert (r1.r2_candidates[0].detail["risk_identity_id"]
                == r2.r2_candidates[0].detail["risk_identity_id"])
        assert r1.query_refs[0].query_id == r2.query_refs[0].query_id
        expansion1 = expand_one(cp, plan)
        expansion2 = expand_one(cp, plan)
        assert expansion1.expected_set_hash == expansion2.expected_set_hash

    def test_snapshot_revision_change_keeps_identity(self):
        """N and N+1 use different snapshot/revision but the same stable
        control point + window + lineage -> identical risk identity."""
        loc_a = make_locator("cp-1", snapshot_id="snap-N")
        loc_b = make_locator("cp-1", snapshot_id="snap-N1")
        rule = make_numeric_rule()
        cp_a = make_control_point(source_locator=loc_a, structured_rule=rule)
        cp_b = make_control_point(source_locator=loc_b, structured_rule=rule)
        plan = make_plan(root_ids=("CP-INC-1",))
        r1 = evaluate_single(cp_a, plan, bindings=[make_binding("b1", value="8")],
                             roles={"laboratory": True},
                             enrollment=make_enrollment(),
                             policy=make_policy())
        r2 = evaluate_single(cp_b, plan, bindings=[make_binding("b1", value="8")],
                             roles={"laboratory": True},
                             enrollment=make_enrollment(),
                             policy=make_policy())
        assert r1.unit_id == r2.unit_id
        assert (r1.r2_candidates[0].detail["risk_identity_id"]
                == r2.r2_candidates[0].detail["risk_identity_id"])

    def test_classifier_excludes_lineage_and_version(self):
        """§5: classifier/stable-core never contains protocol version or
        lineage; version only lives in the scope/lineage."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",), rule_hash="rcA")
        r = evaluate_single(cp, plan, bindings=[make_binding("b1", value="8")],
                            roles={"laboratory": True},
                            enrollment=make_enrollment(), policy=make_policy())
        detail = r.r2_candidates[0].detail
        assert "rcA" not in detail["classifier"]
        assert "V2.0" not in detail["classifier"]
        assert "rcA" in detail["lineage_fingerprint"]

    def test_lineage_change_keeps_classifier_but_changes_identity(self):
        """Challenge 52/62: rule/mapping lineage change keeps the
        classifier stable but changes the identity (supersede path, never
        resolved_by_data)."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan_a = make_plan(root_ids=("CP-INC-1",), rule_hash="rcA")
        plan_b = make_plan(root_ids=("CP-INC-1",), rule_hash="rcB")
        r1 = evaluate_single(cp, plan_a, bindings=[make_binding("b1", value="8")],
                             roles={"laboratory": True},
                             enrollment=make_enrollment(), policy=make_policy())
        r2 = evaluate_single(cp, plan_b, bindings=[make_binding("b1", value="8")],
                             roles={"laboratory": True},
                             enrollment=make_enrollment(), policy=make_policy())
        assert r1.unit_id != r2.unit_id
        assert (r1.r2_candidates[0].detail["classifier"]
                == r2.r2_candidates[0].detail["classifier"])
        assert (r1.r2_candidates[0].detail["risk_identity_id"]
                != r2.r2_candidates[0].detail["risk_identity_id"])

    def test_identity_uses_public_make_risk_identity(self):
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",))
        r = evaluate_single(cp, plan, bindings=[make_binding("b1", value="8")],
                            roles={"laboratory": True},
                            enrollment=make_enrollment(), policy=make_policy())
        cand = r.r2_candidates[0]
        expected = make_risk_identity(
            project_id=PROJECT_ID, subject_ref=SUBJECT,
            domain=p.D04_DOMAIN, scope=cand.detail["scope"],
            classifier=cand.detail["classifier"])
        assert expected.risk_identity_id == cand.detail["risk_identity_id"]
        assert expected.risk_identity_id == cand.detail["risk_identity_id"]

    def test_pipe_in_control_point_id_still_distinct_identity(self):
        """Challenge 59: control point/component ids containing '|' still
        produce distinct canonical unit/assessment ids; package unit ids
        never mix with assessment ids."""
        cp1 = make_control_point(
            control_point_id="CP|A|1", official_criterion_id="5.1.13",
            structured_rule=make_numeric_rule())
        cp2 = make_control_point(
            control_point_id="CP|B|1", official_criterion_id="5.1.14",
            structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP|A|1", "CP|B|1"))
        expansion = p.expand_protocol_expected_set(
            project_id=PROJECT_ID, applicability=make_applicability(),
            control_points=(cp1, cp2), plan=plan)
        assert expansion.count == 2
        assert len(set(expansion.unit_ids)) == 2
        r1 = evaluate_unit(
            expansion.units[0],
            bindings=[make_binding("b1", component_id="CP|A|1",
                                   control_point_id="CP|A|1", value="8")],
            roles={"laboratory": True}, enrollment=make_enrollment(),
            policy=make_policy())
        r2 = evaluate_unit(
            expansion.units[1],
            bindings=[make_binding("b1", component_id="CP|B|1",
                                   control_point_id="CP|B|1", value="8")],
            roles={"laboratory": True}, enrollment=make_enrollment(),
            policy=make_policy())
        assert r1.l1_disposition == L1Disposition.POSITIVE
        assert r1.unit_id != r2.unit_id
        assert (r1.r2_candidates[0].detail["risk_identity_id"]
                != r2.r2_candidates[0].detail["risk_identity_id"])
        assert r1.unit_id.startswith("unit-")
        for a in r1.component_assessments:
            assert a.assessment_id != r1.unit_id

    def test_two_windows_same_anchor_distinct_identity(self):
        """Challenge 68: same control point, same on_treatment anchor, two
        disjoint evaluation windows -> different unit ids and risk
        identities; a linked-negative on window A never closes window B."""
        cp = make_control_point(
            control_point_id="CP-W1", official_criterion_id="5.1.15",
            structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-W1",))
        w1 = p.EvaluationWindowSpec(
            eval_anchor_kind=p.ANCHOR_ON_TREATMENT,
            window_start="2026-03-01", window_end="2026-03-31",
            precision=p.PRECISION_DAY,
            endpoint_inclusivity=p.INCLUSIVITY_INCLUSIVE)
        w2 = p.EvaluationWindowSpec(
            eval_anchor_kind=p.ANCHOR_ON_TREATMENT,
            window_start="2026-05-01", window_end="2026-05-31",
            precision=p.PRECISION_DAY,
            endpoint_inclusivity=p.INCLUSIVITY_INCLUSIVE)
        e1 = p.expand_protocol_expected_set(
            project_id=PROJECT_ID, applicability=make_applicability(
                anchor=p.ANCHOR_ON_TREATMENT, anchor_date="2026-03-15"),
            control_points=(cp,), plan=plan,
            window_by_control_point={"CP-W1": w1})
        e2 = p.expand_protocol_expected_set(
            project_id=PROJECT_ID, applicability=make_applicability(
                anchor=p.ANCHOR_ON_TREATMENT, anchor_date="2026-05-15"),
            control_points=(cp,), plan=plan,
            window_by_control_point={"CP-W1": w2})
        u1 = e1.units[0].build_unit(PROJECT_ID).unit_id
        u2 = e2.units[0].build_unit(PROJECT_ID).unit_id
        assert u1 != u2
        bindings = [make_binding("b1", control_point_id="CP-W1", value="8")]
        roles = {"laboratory": True}
        r1 = evaluate_unit(e1.units[0], bindings=bindings, roles=roles,
                           enrollment=make_enrollment(),
                           policy=make_policy())
        r2 = evaluate_unit(e2.units[0], bindings=bindings, roles=roles,
                           enrollment=make_enrollment(),
                           policy=make_policy())
        assert r1.l1_disposition == L1Disposition.POSITIVE
        assert r2.l1_disposition == L1Disposition.POSITIVE
        assert (r1.r2_candidates[0].detail["risk_identity_id"]
                != r2.r2_candidates[0].detail["risk_identity_id"])
        assert r1.evaluation_window_id != r2.evaluation_window_id

    def test_evaluation_window_id_excludes_run_revision(self):
        wid = p._evaluation_window_id(
            eval_anchor_kind=p.ANCHOR_ON_TREATMENT,
            window_start="2026-03-01", window_end="2026-03-31",
            precision=p.PRECISION_DAY,
            endpoint_inclusivity=p.INCLUSIVITY_INCLUSIVE)
        assert "snap" not in wid and "run" not in wid and "rev" not in wid


# ===========================================================================
# 10. Cross-domain gates (challenges 32, 35, 36, 63, 79)
# ===========================================================================

class TestCrossDomain:
    def _exclusion_cp(self) -> p.ProtocolControlPoint:
        rule = p.ProtocolStructuredRule(
            operator=p.OP_EXISTS, exists_target_role="concomitant_medication",
            required_evidence_roles=("concomitant_medication",),
            evaluation_window_start="2026-02-01",
            evaluation_window_end="2026-02-28",
            window_start_inclusive=True, window_end_inclusive=True)
        return make_control_point(
            control_point_id="CP-EXC-CM",
            control_point_type=p.CONTROL_EXCLUSION,
            official_criterion_id="5.2.7", heading="排除标准",
            structured_rule=rule)

    def test_cm_fact_as_eligibility_evidence_positive(self):
        """Challenge 79: exclusion 'X drug within window' consumes a CM
        record as a fact; D04 builds one exclusion_condition_present risk;
        no independent D02 risk is created here."""
        cp = self._exclusion_cp()
        plan = make_plan(root_ids=("CP-EXC-CM",))
        ref = _cd_ref(record_id="CM#9", producer_unit="d02-unit-9")
        binding = make_binding(
            "cm-1", component_id="CP-EXC-CM", control_point_id="CP-EXC-CM",
            role="concomitant_medication", value="drugX",
            date_raw="2026-02-10", cross_domain_ref=ref)
        result = evaluate_single(
            cp, plan, bindings=[binding],
            roles={"concomitant_medication": True},
            enrollment=make_enrollment(p.QUERY_CONTEXT_ENROLLED),
            policy=make_policy(p.SUBTYPE_EXCLUSION_PRESENT))
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert result.positive_subtype == p.SUBTYPE_EXCLUSION_PRESENT
        assert len(result.r2_candidates) == 1
        assert result.r2_candidates[0].domain == p.D04_DOMAIN

    def test_same_record_id_different_subject_fails_closed(self):
        """Challenges 36/63: same record id on a different subject cannot
        establish the cross-domain link."""
        cp = self._exclusion_cp()
        plan = make_plan(root_ids=("CP-EXC-CM",))
        ref = _cd_ref(record_id="CM#9", subject_ref="SYN-002",
                      producer_unit="d02-unit-9")
        binding = make_binding(
            "cm-2", component_id="CP-EXC-CM", control_point_id="CP-EXC-CM",
            role="concomitant_medication", value="drugX",
            date_raw="2026-02-10", cross_domain_ref=ref)
        result = evaluate_single(
            cp, plan, bindings=[binding],
            roles={"concomitant_medication": True})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_RELATION_UNCONFIRMED
                   for n in result.coverage_gap_notices)

    def test_unconfirmed_relation_fails_closed(self):
        cp = self._exclusion_cp()
        plan = make_plan(root_ids=("CP-EXC-CM",))
        ref = _cd_ref(record_id="CM#10", producer_unit="d02-unit-10")
        binding = make_binding(
            "cm-3", component_id="CP-EXC-CM", control_point_id="CP-EXC-CM",
            role="concomitant_medication", value="drugX",
            date_raw="2026-02-10", cross_domain_ref=ref,
            confirmed=False)
        result = evaluate_single(
            cp, plan, bindings=[binding],
            roles={"concomitant_medication": True})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_wrong_site_fails_closed(self):
        cp = self._exclusion_cp()
        plan = make_plan(root_ids=("CP-EXC-CM",))
        ref = _cd_ref(record_id="CM#11", site_ref="SITE99",
                      producer_unit="d02-unit-11")
        binding = make_binding(
            "cm-4", component_id="CP-EXC-CM", control_point_id="CP-EXC-CM",
            role="concomitant_medication", value="drugX",
            date_raw="2026-02-10", cross_domain_ref=ref)
        result = evaluate_single(
            cp, plan, bindings=[binding],
            roles={"concomitant_medication": True})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE

    def test_producer_unit_mismatch_fails_closed(self):
        cp = self._exclusion_cp()
        plan = make_plan(root_ids=("CP-EXC-CM",))
        ref = _cd_ref(record_id="CM#12", producer_unit="d02-unit-12")
        binding = make_binding(
            "cm-5", component_id="CP-EXC-CM", control_point_id="CP-EXC-CM",
            role="concomitant_medication", value="drugX",
            date_raw="2026-02-10", cross_domain_ref=ref)
        # The D04 consumer expects producer unit d02-unit-X from routing;
        # the ref carries d02-unit-12 -> mismatch fails closed.
        binding = p.RuleEvidenceBinding(
            binding_id="cm-5", control_point_id="CP-EXC-CM",
            component_id="CP-EXC-CM", subject_ref=SUBJECT,
            site_ref=SITE_REF, source_role="concomitant_medication",
            stable_source_event_key="recorded_cm:CM#12",
            source_locator=make_locator("CM#12", "recorded_cm"),
            value="drugX", date_raw="2026-02-10",
            cross_domain_ref=ref, expected_producer_unit_id="d02-unit-X")
        result = evaluate_single(
            cp, plan, bindings=[binding],
            roles={"concomitant_medication": True})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_RELATION_UNCONFIRMED
                   for n in result.coverage_gap_notices)

    def test_producer_not_evaluable_blocks_dependent_unit(self):
        """Challenge 32: D03 episode/assignment not_evaluable -> dependent
        D04 unit not_evaluable."""
        cp = self._exclusion_cp()
        plan = make_plan(root_ids=("CP-EXC-CM",))
        ref = _cd_ref(record_id="CM#13", producer_unit="d03-ep-13")
        binding = make_binding(
            "cm-6", component_id="CP-EXC-CM", control_point_id="CP-EXC-CM",
            role="concomitant_medication", value="drugX",
            date_raw="2026-02-10", cross_domain_ref=ref,
            blocked=True, blocked_reason="D03 上游评价暂无法评价")
        result = evaluate_single(
            cp, plan, bindings=[binding],
            roles={"concomitant_medication": True})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_PRODUCER_DEPENDENCY
                   for n in result.coverage_gap_notices)

    def test_wrong_subject_binding_excluded_not_evaluable(self):
        """Challenge 35 + corrective finding 6: wrong-subject evidence in
        a multi-subject accepted listing is ordinary non-matching
        evidence -- excluded, never a kernel crash; with no valid
        required evidence the unit fails closed to not_evaluable with a
        missing-role coverage notice and zero candidate/risk/Query."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",))
        wrong = make_binding("wb", subject_ref="SYN-999")
        result = evaluate_single(cp, plan, bindings=[wrong],
                                 roles={"laboratory": True})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert not result.r2_candidates and not result.query_refs
        assert len(result.coverage_gap_notices) == 1
        notice = result.coverage_gap_notices[0]
        assert notice.reason_code == p.GAP_SOURCE_ROLE_NOT_COVERED
        assert notice.missing_evidence_roles == ("laboratory",)
        # A matching binding for the unit's own subject still evaluates
        # normally in the same listing.
        mixed = evaluate_single(
            cp, plan,
            bindings=[wrong, make_binding("b1", value="8")],
            roles={"laboratory": True},
            enrollment=make_enrollment(), policy=make_policy())
        assert mixed.l1_disposition == L1Disposition.POSITIVE


# ===========================================================================
# 11. Lifecycle integration (challenges 49-51, 66, 70)
# ===========================================================================

class TestLifecycleIntegration:
    def _adapter(self):
        svc = make_acceptance_service()
        make_baseline_snapshot(svc, snapshot_id=SNAPSHOT_ID,
                               revision_id="rev-1")
        lc = make_lifecycle()
        return R4LifecycleAdapter(
            lifecycle=lc, acceptance_service=svc,
            project_id=PROJECT_ID, actor="system_policy"), svc, lc

    def _positive_result(self, policy=None, **kw) -> p.ProtocolUnitResult:
        cp = make_control_point(structured_rule=make_numeric_rule())
        return atomic_single(
            cp, [make_binding("b1", value="8")], {"laboratory": True},
            enrollment=make_enrollment(), policy=policy or make_policy())

    def test_critical_subtype_fails_closed_at_policy_construction(self):
        """Challenges 66/70 + corrective finding 4: the frozen producer
        invariant is enforced at policy construction -- critical=true
        requires machine_close_forbidden=true and effective priority
        high.  The shared adapter's either-flag normalization is no
        longer the only guard."""
        with pytest.raises(p.ProtocolSliceError):
            make_policy(priority="medium", critical=True)
        with pytest.raises(p.ProtocolSliceError):
            make_policy(priority="high", critical=True)
        policy = make_policy(priority="high", critical=True,
                             close_forbidden=True)
        ur = self._positive_result(policy)
        cand = ur.r2_candidates[0]
        assert ur.monitoring_priority == "high"
        assert cand.detail["rights_or_safety_critical"] is True
        assert cand.detail["machine_close_forbidden"] is True
        adapter, _, lc = self._adapter()
        outcome = adapter.promote_unit_result(ur)
        assert len(outcome.established_risk_ids) == 1
        inst = lc.instances_for_project(PROJECT_ID)[0]
        assert inst.severity == "high"
        assert adapter.must_carry_forward(inst)

    def test_machine_close_forbidden_forces_high_and_blocks_close(self):
        policy = make_policy(priority="medium", close_forbidden=True)
        ur = self._positive_result(policy)
        adapter, _, _ = self._adapter()
        outcome = adapter.promote_unit_result(ur)
        inst = adapter.lifecycle.get(outcome.established_risk_ids[0][0])
        assert inst.severity == "high"
        # High severity is the durable machine-close ban.
        from mm_r4.lifecycle import LifecycleAdapterError
        with pytest.raises(LifecycleAdapterError, match="low/medium"):
            adapter.machine_close_by_data(
                inst, coverage_snapshot_id=SNAPSHOT_ID)

    def test_machine_close_requires_linked_negative_and_closed_ledger(self):
        """Challenges 49/51: low/medium machine close requires exact
        linked negative + complete coverage; data correction with unchanged
        lineage is resolved_by_data."""
        policy = make_policy(priority="low")
        ur = self._positive_result(policy)
        adapter, svc, _ = self._adapter()
        outcome = adapter.promote_unit_result(ur)
        inst = adapter.lifecycle.get(outcome.established_risk_ids[0][0])
        assert inst.severity == "low"
        # Without a closed ledger -> no close.
        from mm_r4.lifecycle import LifecycleAdapterError
        with pytest.raises(LifecycleAdapterError):
            adapter.machine_close_by_data(
                inst, coverage_snapshot_id=SNAPSHOT_ID)
        # Build the N+1 linked-negative proof via the public adapter path.
        neg = self._negative_result(inst)
        make_subsequent_snapshot(svc, snapshot_id="snap-N1",
                                 revision_id="rev-N1")
        ledger = self._closed_ledger_for(neg, snapshot_id="snap-N1")
        result = adapter.reconcile_n_to_n1(
            [inst], [neg], coverage_snapshot_id="snap-N1",
            coverage_ledger=ledger)
        assert len(result.closed) == 1
        assert result.closed[0].current_state == "closed"

    def test_high_user_confirmed_and_identity_ambiguous_never_machine_close(self):
        """Challenge 50 + corrective 03 lifecycle proof: (a) a high risk
        refuses machine close; (b) a previously user-confirmed risk stays
        protected after reopen/reconcile and refuses machine close even
        with the exact linked-negative + closed-ledger proof; (c) an
        identity_ambiguous risk refuses machine close.  Every refusal
        comes from the protected state, never a missing prerequisite."""
        from mm_r4.lifecycle import LifecycleAdapterError
        from mm_r2.risk import AdjudicationError
        adapter, svc, _ = self._adapter()

        # (a) high risk refuses machine close (severity guard, pre-proof).
        high = self._positive_result(make_policy(priority="high"))
        outcome = adapter.promote_unit_result(high)
        high_inst = adapter.lifecycle.get(outcome.established_risk_ids[0][0])
        assert high_inst.severity == "high"
        with pytest.raises(LifecycleAdapterError, match="low/medium"):
            adapter.machine_close_by_data(
                high_inst, coverage_snapshot_id=SNAPSHOT_ID)

        # (b) user-confirmed risk stays protected after reopen/reconcile.
        low = self._positive_result(make_policy(priority="low"))
        outcome2 = adapter.promote_unit_result(low)
        inst = adapter.lifecycle.get(outcome2.established_risk_ids[0][0])
        assert inst.severity == "low"
        make_subsequent_snapshot(svc, snapshot_id="snap-N0",
                                 revision_id="rev-N0")
        adapter.user_close_by_data(
            inst, coverage_snapshot_id="snap-N0")
        closed = adapter.lifecycle.get(inst.risk_instance_id)
        assert closed.current_state == "closed"
        assert closed.ever_user_confirmed
        reopened = adapter.reopen(closed)
        assert reopened.current_state == "reopened"
        assert reopened.ever_user_confirmed
        # Full linked-negative + closed-ledger proof is supplied: any
        # refusal is caused by the protected state, not the proof.
        make_subsequent_snapshot(svc, snapshot_id="snap-N1",
                                 revision_id="rev-N1")
        neg = self._negative_result(reopened)
        ledger = self._closed_ledger_for(neg, snapshot_id="snap-N1")
        reconciled = adapter.reconcile_n_to_n1(
            [reopened], [neg], coverage_snapshot_id="snap-N1",
            coverage_ledger=ledger)
        assert reconciled.closed == ()
        assert reopened.risk_instance_id in {
            i.risk_instance_id for i in reconciled.carry_forward}
        with pytest.raises(AdjudicationError):
            adapter.machine_close_by_data(
                reopened, coverage_snapshot_id="snap-N1",
                next_unit_results=[neg], coverage_ledger=ledger)

        # (c) identity_ambiguous refuses machine close (state guard).
        amb_cp = make_control_point(
            control_point_id="CP-INC-2",
            official_criterion_id="5.1.4",
            structured_rule=make_numeric_rule())
        amb = atomic_single(
            amb_cp, [make_binding(
                "bC", control_point_id="CP-INC-2", value="9")],
            {"laboratory": True},
            enrollment=make_enrollment(),
            policy=make_policy(priority="low"))
        outcome3 = adapter.promote_unit_result(amb)
        amb_inst = adapter.lifecycle.get(outcome3.established_risk_ids[0][0])
        adapter.mark_identity_ambiguous(amb_inst)
        ambiguous = adapter.lifecycle.get(amb_inst.risk_instance_id)
        assert ambiguous.current_state == "identity_ambiguous"
        with pytest.raises(LifecycleAdapterError,
                           match="identity_ambiguous"):
            adapter.machine_close_by_data(
                ambiguous, coverage_snapshot_id=SNAPSHOT_ID)

    def _closed_ledger_for(
        self, result: p.ProtocolUnitResult, snapshot_id: str,
    ) -> CoverageLedger:
        cp = make_control_point(structured_rule=make_numeric_rule())
        expansion = expand_one(cp, make_plan(root_ids=("CP-INC-1",)))
        unit = expansion.units[0].build_unit(PROJECT_ID)
        expected = ExpectedSet.from_units(
            [unit], domain_id=p.D04_DOMAIN, run_id="run-1")
        ledger = CoverageLedger(expected_set=expected)
        ledger.assign(result.to_unit_evaluation(
            provenance_snapshot_id=snapshot_id,
            provenance_rule_lineage="rc2"))
        ledger.close()
        return ledger

    def _negative_result(self, instance) -> p.ProtocolUnitResult:
        """An N+1 negative unit explicitly linking the prior risk
        (RiskInstanceRef) -- the exact linked-negative proof."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        result = atomic_single(
            cp, [make_binding("bN", value="12")], {"laboratory": True})
        from dataclasses import replace
        return replace(
            result,
            risk_instance_refs=(
                p.RiskInstanceRef(
                    risk_instance_id=instance.risk_instance_id,
                    risk_identity_id=instance.risk_identity_id,
                    risk_state=instance.current_state),))

    def test_high_risk_carries_forward(self):
        """Challenge 50: high risks never machine-close."""
        policy = make_policy(priority="high")
        ur = self._positive_result(policy)
        adapter, _, _ = self._adapter()
        outcome = adapter.promote_unit_result(ur)
        inst = adapter.lifecycle.get(outcome.established_risk_ids[0][0])
        assert adapter.must_carry_forward(inst)
        assert inst.severity == "high"

    def test_same_identity_persists_across_snapshots(self):
        """Challenge 48/49: N and N+1 same stable identity -> persists
        (carry-forward, no duplicate risk)."""
        ur1 = self._positive_result()
        ur2 = self._positive_result()
        assert (ur1.r2_candidates[0].detail["risk_identity_id"]
                == ur2.r2_candidates[0].detail["risk_identity_id"])
        assert ur1.unit_id == ur2.unit_id
        adapter, _, lc = self._adapter()
        adapter.promote_unit_result(ur1)
        assert len(lc.instances_for_project(PROJECT_ID)) == 1


# ===========================================================================
# 12. Slice aggregation (§11) and user language
# ===========================================================================

class TestSliceAggregation:
    def test_slice_counts_and_invariants(self):
        cp1 = make_control_point(structured_rule=make_numeric_rule())
        rule_exc = p.ProtocolStructuredRule(
            operator=p.OP_NOT_EXISTS,
            exists_target_role="concomitant_medication",
            required_evidence_roles=("concomitant_medication",))
        cp2 = make_control_point(
            control_point_id="CP-EXC-1",
            control_point_type=p.CONTROL_EXCLUSION,
            official_criterion_id="5.2.1", heading="排除标准",
            structured_rule=rule_exc)
        plan = make_plan(root_ids=("CP-INC-1", "CP-EXC-1"))
        sr = p.evaluate_protocol_slice(
            project_id=PROJECT_ID, applicability=make_applicability(),
            control_points=(cp1, cp2), plan=plan,
            bindings=[make_binding("b1", value="8")],
            coverage_complete_roles={"laboratory": True},
            enrollment_context=make_enrollment(),
            priority_policy=make_policy(), snapshot_id=SNAPSHOT_ID)
        assert sr.expected_units == 2
        assert sr.positive_count == 1
        assert sr.not_evaluable_count == 1
        assert (sr.positive_count + sr.negative_count + sr.boundary_count
                + sr.not_applicable_count + sr.not_evaluable_count
                == sr.expected_units)
        sr.verify_count_invariants()
        assert sr.query_draft_count == 1
        assert sr.coverage_gap_count == 1
        assert sr.candidate_count == 1

    def test_delegated_items_excluded_from_l1_denominator(self):
        cm_cp = make_control_point(
            control_point_id="CP-CM-1",
            control_point_type=p.CONTROL_PROHIBITED_OR_RESTRICTED_TREATMENT,
            official_section_id="6.2", official_criterion_id="6.2.1",
            heading="禁限用要求",
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_EXISTS,
                exists_target_role="concomitant_medication",
                required_evidence_roles=("concomitant_medication",)))
        inc_cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-CM-1", "CP-INC-1"))
        sr = p.evaluate_protocol_slice(
            project_id=PROJECT_ID, applicability=make_applicability(),
            control_points=(cm_cp, inc_cp), plan=plan,
            bindings=[make_binding("b1", value="8")],
            coverage_complete_roles={"laboratory": True},
            enrollment_context=make_enrollment(),
            priority_policy=make_policy(), snapshot_id=SNAPSHOT_ID)
        assert sr.expected_units == 1
        assert sr.positive_count == 1
        assert len(sr.delegated_control_points) == 1
        sr.verify_count_invariants()

    def test_closed_ledger_domain_complete_blocked_by_not_evaluable(self):
        cp1 = make_control_point(structured_rule=make_numeric_rule())
        sr = p.evaluate_protocol_slice(
            project_id=PROJECT_ID, applicability=make_applicability(),
            control_points=(cp1,), plan=make_plan(root_ids=("CP-INC-1",)),
            bindings=[], coverage_complete_roles={}, snapshot_id=SNAPSHOT_ID)
        units = [r.to_unit_evaluation(
            provenance_snapshot_id=SNAPSHOT_ID,
            provenance_rule_lineage="rc2") for r in sr.unit_results]
        expected = ExpectedSet.from_units(
            [u for u in units],
            domain_id=p.D04_DOMAIN, run_id="run-1")
        ledger = CoverageLedger(expected_set=expected)
        for u in units:
            ledger.assign(u)
        summary = ledger.close_and_summarize()
        complete, reasons = is_domain_complete(summary)
        assert not complete
        assert any("not_evaluable" in r for r in reasons)

    def test_positive_unit_evaluation_joins_are_valid(self):
        sr = p.evaluate_protocol_slice(
            project_id=PROJECT_ID, applicability=make_applicability(),
            control_points=(make_control_point(
                structured_rule=make_numeric_rule()),),
            plan=make_plan(root_ids=("CP-INC-1",)),
            bindings=[make_binding("b1", value="8")],
            coverage_complete_roles={"laboratory": True},
            enrollment_context=make_enrollment(),
            priority_policy=make_policy(), snapshot_id=SNAPSHOT_ID)
        ue = sr.unit_results[0].to_unit_evaluation(
            provenance_snapshot_id=SNAPSHOT_ID,
            provenance_rule_lineage="rc2")
        assert isinstance(ue, UnitEvaluation)


class TestUserLanguage:
    """User-visible strings must never carry engineering jargon."""

    PROHIBITED = ("正式事实", "候选信号", "只读", "未知风险",
                  "positive", "candidate", "backend", "模型置信度")

    def test_no_prohibited_jargon(self):
        cp = make_control_point(structured_rule=make_numeric_rule())
        results = [
            atomic_single(cp, [make_binding("b1", value="8")],
                          {"laboratory": True},
                          enrollment=make_enrollment(),
                          policy=make_policy()),
            atomic_single(cp, [], {}),
            atomic_single(
                make_control_point(
                    control_point_id="CP-B",
                    official_criterion_id="5.1.20",
                    structured_rule=make_numeric_rule(
                        lower_inclusive=None)),
                [make_binding("b2", value="10")], {"laboratory": True}),
        ]
        for r in results:
            strings = [r.not_evaluable_reason, r.boundary_reason,
                       r.audience_label]
            strings.extend(n.audience_text for n in r.coverage_gap_notices)
            for q in r.query_refs:
                strings.extend((q.basis, q.finding, q.action))
            for s in strings:
                if not s:
                    continue
                for token in self.PROHIBITED:
                    assert token not in s, f"{token!r} in {s!r}"

    def test_positive_label_mapping_matches_contract(self):
        assert (p.positive_subtype_audience_label(
            p.SUBTYPE_INCLUSION_NOT_MET) == "入选条件待核实")
        assert (p.positive_subtype_audience_label(
            p.SUBTYPE_EXCLUSION_PRESENT) == "排除条件待核实")
        assert (p.positive_subtype_audience_label(
            p.SUBTYPE_REQUIRED_ACTION_NOT_MET) == "方案要求执行情况待核实")
        assert (p.positive_subtype_audience_label(
            p.SUBTYPE_DISCONTINUATION_INCONSISTENT)
            == "退出或终止参与标准待核实")
        assert (p.positive_subtype_audience_label(
            p.SUBTYPE_CONSENT_SEQUENCE_INCONSISTENT)
            == "知情与入组时序待核实")
        assert (p.positive_subtype_audience_label(
            p.SUBTYPE_OTHER_REQUIREMENT_INCONSISTENT)
            == "方案执行情况待核实")
        with pytest.raises(p.ProtocolSliceError):
            p.positive_subtype_audience_label("bogus")

    def test_audience_payloads_never_carry_engineering_tokens(self):
        """Corrective 03: audience-facing uncertainty_summary / rationale
        strings use native Chinese (无法评价, 任一/全部/至少 N 关系) --
        raw ``not_evaluable`` and ``AND/OR`` tokens never leak into
        generated payloads; internal enums stay untouched."""
        import re as _re
        import mm_r4.protocol_projection as pp
        raw_tokens = ("not_evaluable", "AND", "OR")
        payloads: list = []

        def collect(result: p.ProtocolUnitResult) -> None:
            payloads.extend([result.not_evaluable_reason,
                             result.boundary_reason, result.audience_label])
            payloads.extend(
                n.audience_text for n in result.coverage_gap_notices)
            for q in result.query_refs:
                payloads.extend((q.basis, q.finding, q.action))

        # (1) resolver-driven not_evaluable gate: missing enrollment date
        # for a new-enrollment-only amendment.
        v1 = make_version("V1.0", "am1", "2025-01-01", "2025-02-01",
                          "2025-12-31", "rc1", p.TRANSITION_ALL_SWITCH)
        v2 = make_version(
            transition_scope=p.TRANSITION_NEW_ENROLLMENT_ONLY,
            new_enrollment_only=True)
        appl = p.resolve_protocol_applicability(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            event_anchor_kind=p.ANCHOR_SCREENING,
            event_anchor_date="2026-03-01", versions=(v1, v2),
            site_adoption_start="2026-01-20",
            stable_source_content_key="k")
        assert appl.decision_status == p.APPLICABILITY_NOT_EVALUABLE
        assert "无法评价" in appl.rationale
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",))
        expansion = expand_one(cp, plan, applicability=appl)
        gate = evaluate_unit(expansion.units[0])
        collect(gate)
        assert "无法评价" in gate.not_evaluable_reason

        # (2) unverified package plan -> 任一/全部/至少 N 关系 wording.
        pkg_cp = make_control_point(
            control_point_id="CP-PKG-U",
            root_kind=p.NODE_PACKAGE,
            issue_expression=p.IssueExpression(
                operator=p.EXPR_AND, component_ids=("C1", "C2")),
            component_ids=("C1", "C2"))
        pkg_plan = make_plan(root_ids=("CP-PKG-U",),
                             verification="unverified")
        pkg = evaluate_single(
            pkg_cp, pkg_plan,
            components={
                "C1": make_component(
                    "C1", "CP-PKG-U",
                    make_numeric_rule(threshold="10")),
                "C2": make_component(
                    "C2", "CP-PKG-U",
                    make_numeric_rule(threshold="5"))},
            bindings=[make_binding("b1", value="8")],
            roles={"laboratory": True})
        collect(pkg)
        assert "任一/全部/至少 N 关系" in pkg.not_evaluable_reason

        # (3) package with a boundary + not_evaluable component ->
        # forced reason keeps 无法评价 wording.
        expr_cp = make_control_point(
            control_point_id="CP-PKG-E",
            root_kind=p.NODE_PACKAGE,
            issue_expression=p.IssueExpression(
                operator=p.EXPR_AND, component_ids=("C1", "C2")),
            component_ids=("C1", "C2"))
        expr = evaluate_single(
            expr_cp, make_plan(root_ids=("CP-PKG-E",)),
            components={
                "C1": make_component(
                    "C1", "CP-PKG-E",
                    make_numeric_rule(
                        threshold="10", lower_inclusive=None)),
                "C2": make_component(
                    "C2", "CP-PKG-E",
                    make_numeric_rule(threshold="5"))},
            bindings=[make_binding(
                "b1", control_point_id="CP-PKG-E", value="10")],
            roles={"laboratory": True})
        collect(expr)
        assert "无法评价" in expr.not_evaluable_reason

        # (4) slice + projection: the audience uncertainty_summary carries
        # only native Chinese, never the engineering tokens.
        sr = p.evaluate_protocol_slice(
            project_id=PROJECT_ID, applicability=appl,
            control_points=(cp,), plan=plan,
            bindings=[], coverage_complete_roles={},
            snapshot_id=SNAPSHOT_ID)
        proj = pp.project_protocol_subject_journey(
            sr, expansions=expansion)
        assert proj.uncertainty_summary
        payloads.append(proj.uncertainty_summary)
        for text in payloads:
            if not text:
                continue
            for token in raw_tokens:
                assert not _re.search(rf"\b{token}\b", text), (
                    f"{token!r} leaked into {text!r}")


# ===========================================================================
# 13. Remaining challenge semantics (7, 10, 40, 58, 64)
# ===========================================================================

class TestRemainingSemantics:
    def test_derived_id_never_masquerades_as_official(self):
        """Challenge 10: no official criterion id -> stable derived id that
        is visibly derived and never presented as official numbering."""
        cp = p.ProtocolControlPoint(
            control_point_id="CP-DERIVED",
            control_point_type=p.CONTROL_INCLUSION,
            official_section_id="5.1", official_criterion_id="",
            official_heading="入选标准",
            evaluation_root_kind=p.NODE_ATOMIC,
            display_order="9", nesting_path="5",
            verbatim_text="未编号条件",
            source_locator=make_locator("cp-derived"),
            source_revision_hash="h",
            extraction_status="verified", verification_status="verified",
            structured_rule=make_numeric_rule())
        assert cp.official_criterion_id.startswith("d04-")
        assert cp.derived_id_note
        assert "无官方编号" in cp.derived_id_note

    def test_official_hierarchy_preserved(self):
        """Challenge 7: official numbering, parent rule, component
        hierarchy and display order are preserved verbatim."""
        rule = make_numeric_rule()
        cp = make_control_point(
            control_point_id="CP-PARENT",
            official_section_id="5.1", official_criterion_id="5.1.3",
            heading="入选标准（包级）",
            root_kind=p.NODE_PACKAGE,
            issue_expression=p.IssueExpression(
                operator=p.EXPR_AND, component_ids=("C1", "C2")),
            component_ids=("C1", "C2"))
        c1 = make_component("C1", "CP-PARENT", rule, "5.1.3-1")
        c2 = make_component("C2", "CP-PARENT", rule, "5.1.3-2")
        assert cp.official_section_id == "5.1"
        assert cp.official_criterion_id == "5.1.3"
        assert c1.official_criterion_id == "5.1.3-1"
        assert c2.official_criterion_id == "5.1.3-2"
        assert c1.parent_rule_id == "CP-PARENT"
        assert c1.control_point_id == "CP-PARENT"
        assert cp.display_order == "1"

    def test_dv_listing_cannot_override_itemized_ie_evidence(self):
        """Challenge 40: pre-enrollment IE semantics are separate from
        post-enrollment DV; DV/deviation listings never override IE
        evidence."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        dv_binding = make_binding(
            "dv-1", role="deviation_listing", value="no_deviation")
        result = atomic_single(cp, [dv_binding], {"laboratory": False})
        assert result.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_FREE_TEXT_ONLY
                   for n in result.coverage_gap_notices)

    def test_site_ref_stays_in_lineage(self):
        """Challenge 64: site stays in the risk lineage scope; a
        centre-transfer cannot silently merge identities."""
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",))
        r = evaluate_single(cp, plan, bindings=[make_binding("b1", value="8")],
                            roles={"laboratory": True},
                            enrollment=make_enrollment(),
                            policy=make_policy())
        scope = r.r2_candidates[0].detail["scope"]
        assert any("site:SITE01" in s for s in scope)
        # A different centre -> different lineage fingerprint -> different
        # identity (never auto-merged).
        appl2 = make_applicability()
        appl2 = p.ProtocolApplicabilityDecision(
            subject_ref=SUBJECT, site_ref="SITE02",
            decision_time_anchor=p.ANCHOR_SCREENING,
            decision_time_anchor_date="2026-03-01",
            decision_status=p.APPLICABILITY_UNIQUE_ACTIVE,
            protocol_id="PROTO-1", protocol_version="V2.0",
            amendment_id_or_hash="am2",
            feasible_version_fingerprints=("fp-1",),
            stable_source_content_key="k")
        r2 = evaluate_single(cp, plan,
                             applicability=appl2,
                             bindings=[make_binding(
                                 "b1", site_ref="SITE02", value="8")],
                             roles={"laboratory": True},
                             enrollment=make_enrollment(),
                             policy=make_policy())
        assert (r.r2_candidates[0].detail["risk_identity_id"]
                != r2.r2_candidates[0].detail["risk_identity_id"])

    def test_at_most_one_candidate_and_query_per_positive_root(self):
        """Challenge 58: positive package root builds at most one
        candidate/risk/Query even with several components."""
        rules = {
            "C1": make_component("C1", "CP-PKG-1", make_numeric_rule(threshold="10")),
            "C2": make_component("C2", "CP-PKG-1", make_numeric_rule(threshold="5")),
        }
        cp = make_control_point(
            control_point_id="CP-PKG-1",
            official_criterion_id="5.1.13", heading="入选标准（需同时满足全部）",
            root_kind=p.NODE_PACKAGE,
            issue_expression=p.IssueExpression(
                operator=p.EXPR_OR, component_ids=("C1", "C2")),
            component_ids=("C1", "C2"))
        plan = make_plan(root_ids=("CP-PKG-1",))
        result = evaluate_single(
            cp, plan, rules,
            bindings=[make_binding("b1", component_id="C1",
                                   control_point_id="CP-PKG-1", value="8"),
                      make_binding("b2", component_id="C2",
                                   control_point_id="CP-PKG-1", value="3")],
            roles={},
            enrollment=make_enrollment(), policy=make_policy())
        assert result.l1_disposition == L1Disposition.POSITIVE
        assert len(result.r2_candidates) == 1
        assert len(result.query_refs) == 1
        assert len(result.risk_candidate_refs) == 1


# ===========================================================================
# 14. RuleEvidenceRequirement expansion and consumption (§4.2, corrective
#     findings 7/8: requirement generated per atomic root/package component,
#     carried on ProtocolUnitExpanded, consumed as the authoritative
#     evidence-role contract; components mapping deep-frozen)
# ===========================================================================

class TestRuleEvidenceRequirement:
    def test_atomic_root_generates_exactly_one_requirement(self):
        cp = make_control_point(structured_rule=make_numeric_rule(
            roles=("laboratory",), alternate_roles=("lab_finding_alt",)))
        plan = make_plan(root_ids=(cp.control_point_id,))
        unit = expand_one(cp, plan).units[0]
        reqs = unit.evidence_requirements
        assert len(reqs) == 1
        req = reqs[0]
        assert req.control_point_id == cp.control_point_id
        assert req.component_id == cp.control_point_id
        assert req.required_evidence_roles == ("laboratory",)
        assert req.alternate_evidence_roles == ("lab_finding_alt",)
        assert req.coverage_complete_required is True
        assert req.retest_or_confirmation_policy == ""
        assert req.rule_lineage == plan.rule_content_hash
        assert req.requirement_id.startswith("d04-req-")

    def test_package_generates_one_requirement_per_component_in_order(self):
        cp = make_control_point(
            control_point_id="CP-PKG-REQ",
            root_kind=p.NODE_PACKAGE,
            issue_expression=p.IssueExpression(
                operator=p.EXPR_OR, component_ids=("C1", "C2")),
            component_ids=("C1", "C2"))
        rules = {
            "C1": make_component(
                "C1", "CP-PKG-REQ", make_numeric_rule(roles=("laboratory",))),
            "C2": make_component(
                "C2", "CP-PKG-REQ", make_numeric_rule(roles=("vital_sign",))),
        }
        unit = expand_one(cp, make_plan(root_ids=("CP-PKG-REQ",)),
                          rules).units[0]
        reqs = unit.evidence_requirements
        assert [r.component_id for r in reqs] == ["C1", "C2"]
        assert {r.control_point_id for r in reqs} == {"CP-PKG-REQ"}
        by_id = {r.component_id: r for r in reqs}
        assert by_id["C1"].required_evidence_roles == ("laboratory",)
        assert by_id["C2"].required_evidence_roles == ("vital_sign",)
        assert by_id["C1"].requirement_id != by_id["C2"].requirement_id

    def test_gates_and_delegated_fabricate_no_requirements(self):
        # Applicability gate carries zero requirements.
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=(cp.control_point_id,))
        appl = make_applicability(status=p.APPLICABILITY_NOT_EVALUABLE)
        expansion = expand_one(cp, plan, applicability=appl)
        gate = expansion.units[0]
        assert gate.evaluation_node_id == p.NODE_APPLICABILITY_GATE
        assert gate.evidence_requirements == ()
        # Routing gate carries zero requirements.
        route = p.ProtocolControlRoutingRecord(
            control_point_id="CP-INC-1", owner_domain=p.OWNER_UNRESOLVED,
            owner_signal_type="owner_unresolved",
            routing_rule_version="rv1", routing_rule_hash="rh1",
            routing_gap="无法按 component 拆分",
            candidate_owners=(p.OWNER_D02, p.OWNER_D04),
            decision_rationale="跨 owner 且无法拆分")
        expansion2 = expand_one(cp, plan, routing=(route,))
        rgate = expansion2.units[0]
        assert rgate.evaluation_node_id == p.NODE_ROUTING_GATE
        assert rgate.evidence_requirements == ()
        # Delegated producer-owned control point: no unit at all, so no
        # D04 requirements are ever fabricated for it.
        cm_cp = make_control_point(
            control_point_id="CP-CM-1",
            control_point_type=p.CONTROL_PROHIBITED_OR_RESTRICTED_TREATMENT,
            structured_rule=p.ProtocolStructuredRule(
                operator=p.OP_EXISTS, exists_target_role="concomitant_medication",
                required_evidence_roles=("concomitant_medication",)))
        expansion3 = expand_one(cm_cp, make_plan(root_ids=("CP-CM-1",)))
        assert expansion3.count == 0
        assert len(expansion3.delegated_control_points) == 1

    def test_requirement_id_content_addressed_and_replay_stable(self):
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=(cp.control_point_id,))
        e1 = expand_one(cp, plan)
        e2 = expand_one(cp, plan)
        assert (e1.units[0].evidence_requirements[0].requirement_id
                == e2.units[0].evidence_requirements[0].requirement_id)
        assert (e1.units[0].evidence_requirements[0]
                == e2.units[0].evidence_requirements[0])

    def test_semantic_change_alters_requirement_id_but_not_unit_identity(self):
        """A semantic evidence-requirement change re-addresses the
        requirement id while the frozen EvaluationUnit identity (the eight
        §5 hash dimensions) stays untouched."""
        cp1 = make_control_point(
            structured_rule=make_numeric_rule(roles=("laboratory",)))
        cp2 = make_control_point(
            structured_rule=make_numeric_rule(
                roles=("laboratory", "vital_sign")))
        plan = make_plan(root_ids=("CP-INC-1",))
        r1 = expand_one(cp1, plan).units[0].evidence_requirements[0]
        r2 = expand_one(cp2, plan).units[0].evidence_requirements[0]
        assert r1.requirement_id != r2.requirement_id
        assert (expand_one(cp1, plan).units[0].build_unit(PROJECT_ID).unit_id
                == expand_one(cp2, plan).units[0].build_unit(PROJECT_ID).unit_id)

    def test_retest_policy_and_lineage_are_preserved_and_addressed(self):
        rule_a = p.ProtocolStructuredRule(
            operator=p.OP_NUMERIC_AT_LEAST,
            comparison=p.RuleComparison(
                comparison="at_least", threshold="10", lower_inclusive=True,
                canonical_unit="U/L", rounding_policy=p.ROUNDING_BEFORE,
                rounding_precision=0),
            required_evidence_roles=("laboratory",),
            retest_or_confirmation_policy="retest-v1")
        rule_b = p.ProtocolStructuredRule(
            operator=p.OP_NUMERIC_AT_LEAST,
            comparison=p.RuleComparison(
                comparison="at_least", threshold="10", lower_inclusive=True,
                canonical_unit="U/L", rounding_policy=p.ROUNDING_BEFORE,
                rounding_precision=0),
            required_evidence_roles=("laboratory",),
            retest_or_confirmation_policy="")
        req_a = expand_one(make_control_point(structured_rule=rule_a),
                           make_plan(root_ids=("CP-INC-1",))
                           ).units[0].evidence_requirements[0]
        req_b = expand_one(make_control_point(structured_rule=rule_b),
                           make_plan(root_ids=("CP-INC-1",))
                           ).units[0].evidence_requirements[0]
        assert req_a.retest_or_confirmation_policy == "retest-v1"
        assert req_a.requirement_id != req_b.requirement_id
        # Rule lineage participates in the content address.
        plan_rc2 = make_plan(root_ids=("CP-INC-1",), rule_hash="rc2")
        plan_rcx = make_plan(root_ids=("CP-INC-1",), rule_hash="rcX")
        req_rc2 = expand_one(make_control_point(structured_rule=rule_a),
                             plan_rc2).units[0].evidence_requirements[0]
        req_rcx = expand_one(make_control_point(structured_rule=rule_a),
                             plan_rcx).units[0].evidence_requirements[0]
        assert req_rc2.rule_lineage == "rc2"
        assert req_rc2.requirement_id != req_rcx.requirement_id
        # Empty plan hash falls back to the frozen default lineage.
        req_def = expand_one(make_control_point(structured_rule=rule_a),
                             make_plan(root_ids=("CP-INC-1",), rule_hash="")
                             ).units[0].evidence_requirements[0]
        assert req_def.rule_lineage == p.D04_RULE_LINEAGE_DEFAULT

    def test_builder_validates_identity_and_literal_bool_fail_closed(self):
        with pytest.raises(p.ProtocolSliceError):
            p.build_rule_evidence_requirement(
                control_point_id="", component_id="C1",
                required_evidence_roles=("laboratory",))
        with pytest.raises(p.ProtocolSliceError):
            p.build_rule_evidence_requirement(
                control_point_id="CP-1", component_id="",
                required_evidence_roles=("laboratory",))
        with pytest.raises(p.ProtocolSliceError):
            p.build_rule_evidence_requirement(
                control_point_id="CP-1", component_id="C1",
                required_evidence_roles=())
        with pytest.raises(p.ProtocolSliceError):
            p.build_rule_evidence_requirement(
                control_point_id="CP-1", component_id="C1",
                required_evidence_roles=("laboratory",),
                coverage_complete_required=1)
        with pytest.raises(p.ProtocolSliceError):
            p.RuleEvidenceRequirement(
                requirement_id="r1", control_point_id="CP-1",
                component_id="C1", required_evidence_roles=("laboratory",),
                coverage_complete_required="yes")

    def test_unit_requires_generated_requirements_fail_closed(self):
        cp = make_control_point(structured_rule=make_numeric_rule())
        plan = make_plan(root_ids=("CP-INC-1",))
        # Atomic/package units without requirements fail at construction.
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolUnitExpanded(
                subject_ref=SUBJECT, site_ref=SITE_REF,
                applicability=make_applicability(),
                evaluation_node_id=p.NODE_ATOMIC,
                signal_type=cp.signal_type(), plan=plan, control_point=cp)
        # Gate units must not fabricate requirements.
        req = p.build_rule_evidence_requirement(
            control_point_id="CP-INC-1", component_id="CP-INC-1",
            required_evidence_roles=("laboratory",))
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolUnitExpanded(
                subject_ref=SUBJECT, site_ref=SITE_REF,
                applicability=make_applicability(),
                evaluation_node_id=p.NODE_APPLICABILITY_GATE,
                signal_type=p.SIGNAL_PROTOCOL_APPLICABILITY, plan=plan,
                affected_control_point_ids=("CP-INC-1",),
                evidence_requirements=(req,))
        # Requirement bound to a different control point fails closed.
        with pytest.raises(p.ProtocolSliceError):
            p.ProtocolUnitExpanded(
                subject_ref=SUBJECT, site_ref=SITE_REF,
                applicability=make_applicability(),
                evaluation_node_id=p.NODE_ATOMIC,
                signal_type=cp.signal_type(), plan=plan, control_point=cp,
                evidence_requirements=(p.build_rule_evidence_requirement(
                    control_point_id="CP-OTHER", component_id="CP-OTHER",
                    required_evidence_roles=("laboratory",)),))

    def test_missing_and_uncovered_roles_reported_from_requirement(self):
        # No bindings at all -> every required role is missing.
        r = atomic_single(make_control_point(structured_rule=make_numeric_rule(
            roles=("laboratory", "vital_sign"))), [], {})
        assert r.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert (r.coverage_gap_notices[0].missing_evidence_roles
                == ("laboratory", "vital_sign"))
        # Package positive with an unresolved component: the notice's
        # missing roles come from that component's requirement only.
        cp = make_control_point(
            control_point_id="CP-PKG-MR",
            root_kind=p.NODE_PACKAGE,
            issue_expression=p.IssueExpression(
                operator=p.EXPR_OR, component_ids=("C1", "C2")),
            component_ids=("C1", "C2"))
        rules = {
            "C1": make_component(
                "C1", "CP-PKG-MR", make_numeric_rule(roles=("laboratory",))),
            "C2": make_component(
                "C2", "CP-PKG-MR",
                make_numeric_rule(roles=("vital_sign", "ecg"))),
        }
        rp = evaluate_single(
            cp, make_plan(root_ids=("CP-PKG-MR",)), rules,
            bindings=[make_binding("b1", component_id="C1",
                                   control_point_id="CP-PKG-MR", value="8")],
            roles={})
        assert rp.l1_disposition == L1Disposition.POSITIVE
        assert len(rp.coverage_gap_notices) == 1
        assert (rp.coverage_gap_notices[0].missing_evidence_roles
                == ("ecg", "vital_sign"))

    def test_evaluation_consumes_expanded_requirement_not_inferred_roles(self):
        """The requirement is the authoritative role contract: a binding
        with a role only the requirement declares is accepted, and a
        binding with a role only the rule declares is rejected -- the
        evaluator never re-derives a second divergent role list."""
        rule = make_numeric_rule(roles=("laboratory",))
        cp = make_control_point(structured_rule=rule)
        plan = make_plan(root_ids=("CP-INC-1",))
        req = p.build_rule_evidence_requirement(
            control_point_id="CP-INC-1", component_id="CP-INC-1",
            required_evidence_roles=("laboratory", "extra_source"))
        unit = p.ProtocolUnitExpanded(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            applicability=make_applicability(),
            evaluation_node_id=p.NODE_ATOMIC, signal_type=cp.signal_type(),
            plan=plan, control_point=cp, evidence_requirements=(req,))
        result = p.evaluate_protocol_unit(
            project_id=PROJECT_ID, expanded=unit,
            bindings=[make_binding("bx", role="extra_source", value="12")],
            coverage_complete_roles={"extra_source": True},
            snapshot_id=SNAPSHOT_ID)
        assert result.l1_disposition == L1Disposition.NEGATIVE

        # Reverse: requirement omits a rule-declared role -> that binding
        # cannot satisfy the requirement (fail closed, role-not-allowed).
        req2 = p.build_rule_evidence_requirement(
            control_point_id="CP-INC-1", component_id="CP-INC-1",
            required_evidence_roles=("demographics",))
        unit2 = p.ProtocolUnitExpanded(
            subject_ref=SUBJECT, site_ref=SITE_REF,
            applicability=make_applicability(),
            evaluation_node_id=p.NODE_ATOMIC, signal_type=cp.signal_type(),
            plan=plan, control_point=cp, evidence_requirements=(req2,))
        result2 = p.evaluate_protocol_unit(
            project_id=PROJECT_ID, expanded=unit2,
            bindings=[make_binding("by", role="laboratory", value="12")],
            coverage_complete_roles={"demographics": True},
            snapshot_id=SNAPSHOT_ID)
        assert result2.l1_disposition == L1Disposition.NOT_EVALUABLE
        assert any(n.reason_code == p.GAP_SOURCE_ROLE_NOT_COVERED
                   for n in result2.coverage_gap_notices)
        # Missing-role reporting follows the requirement too.
        assert result2.coverage_gap_notices[0].missing_evidence_roles \
            == ("demographics",)


class TestProtocolUnitExpandedFreezing:
    def _pkg(self):
        cp = make_control_point(
            control_point_id="CP-PKG-FZ",
            root_kind=p.NODE_PACKAGE,
            issue_expression=p.IssueExpression(
                operator=p.EXPR_OR, component_ids=("C1", "C2")),
            component_ids=("C1", "C2"))
        rules = {
            "C1": make_component(
                "C1", "CP-PKG-FZ", make_numeric_rule(roles=("laboratory",))),
            "C2": make_component(
                "C2", "CP-PKG-FZ", make_numeric_rule(roles=("vital_sign",))),
        }
        return expand_one(cp, make_plan(root_ids=("CP-PKG-FZ",)), rules).units[0]

    def test_components_is_read_only_mapping(self):
        unit = self._pkg()
        assert isinstance(unit.components, Mapping)
        assert set(unit.components) == {"C1", "C2"}
        assert unit.components["C1"].component_id == "C1"
        with pytest.raises(TypeError):
            unit.components["C3"] = make_component(
                "C3", "CP-PKG-FZ", make_numeric_rule())
        with pytest.raises(TypeError):
            del unit.components["C1"]

    def test_caller_alias_mutation_impossible_and_evaluation_deterministic(self):
        cp = make_control_point(
            control_point_id="CP-PKG-FZ",
            root_kind=p.NODE_PACKAGE,
            issue_expression=p.IssueExpression(
                operator=p.EXPR_OR, component_ids=("C1", "C2")),
            component_ids=("C1", "C2"))
        rules = {
            "C1": make_component(
                "C1", "CP-PKG-FZ", make_numeric_rule(roles=("laboratory",))),
            "C2": make_component(
                "C2", "CP-PKG-FZ", make_numeric_rule(roles=("vital_sign",))),
        }
        unit = expand_one(cp, make_plan(root_ids=("CP-PKG-FZ",)), rules).units[0]
        bindings = [
            make_binding("b1", component_id="C1",
                         control_point_id="CP-PKG-FZ", value="8"),
            make_binding("b2", component_id="C2",
                         control_point_id="CP-PKG-FZ", value="3"),
        ]
        before = evaluate_unit(unit, bindings, {}).l1_disposition
        # Caller mutates its own dict after expansion: the unit is immune.
        rules["C3"] = make_component("C3", "CP-PKG-FZ", make_numeric_rule())
        rules["C1"] = make_component(
            "C1", "CP-PKG-FZ", make_numeric_rule(threshold="999"))
        assert "C3" not in unit.components
        assert unit.components["C1"].structured_rule.comparison.threshold == "10"
        after = evaluate_unit(unit, bindings, {}).l1_disposition
        assert before == after == L1Disposition.POSITIVE

    def test_component_map_key_value_identity_validated(self):
        cp = make_control_point(
            control_point_id="CP-PKG-FZ",
            root_kind=p.NODE_PACKAGE,
            issue_expression=p.IssueExpression(
                operator=p.EXPR_OR, component_ids=("C1",)),
            component_ids=("C1",))
        plan = make_plan(root_ids=("CP-PKG-FZ",))
        bad = {"C1": make_component("C2", "CP-PKG-FZ", make_numeric_rule())}
        with pytest.raises(p.ProtocolSliceError):
            p.expand_protocol_expected_set(
                project_id=PROJECT_ID, applicability=make_applicability(),
                control_points=(cp,), plan=plan, components=bad)
        not_a_component = {"C1": "not-a-component"}
        with pytest.raises(p.ProtocolSliceError):
            p.expand_protocol_expected_set(
                project_id=PROJECT_ID, applicability=make_applicability(),
                control_points=(cp,), plan=plan,
                components=not_a_component)

    def test_evidence_requirements_are_immutable(self):
        unit = self._pkg()
        with pytest.raises(AttributeError):
            unit.evidence_requirements += unit.evidence_requirements
        with pytest.raises(AttributeError):
            unit.evidence_requirements = ()
