"""R4-D04 protocol compliance slice -- domain model, applicability gates,
rule-expression evaluation, evidence gates, Chinese Query drafts and
coverage-gap notices.

Frozen source of truth: ``FROZEN_R4_D04_CONTRACT_V1_1`` (§§1-13).  This
module implements the D04 protocol domain on top of the shared
``RiskDomainUnitResult`` protocol, reusing the accepted R1 coverage, R2
identity/lifecycle and R3 normalization public contracts.  It does not
copy lifecycle, identity, Query or coverage implementations.

Design constraints enforced here (frozen D04 contract):

1. Immutable value objects with fail-closed invariant validation; closed
   owner-domain and signal-type enums; no ``|``-joined free signal types.
2. Deterministic canonical identities: the eight frozen EvaluationUnit hash
   dimensions, sorted applicability-gate fingerprints, canonical
   ``protocol_applicability_id`` and N->N+1-compatible R2 risk identities.
3. One EvaluationUnit per atomic/package evaluation root; component
   assessments are separate stable ids and never enter expected-set/L1/L2/
   lifecycle.
4. AND/OR/NOT/AT_LEAST_N parent issue-expression evaluation over feasible
   truth assignments of boundary/not_evaluable components; L0/L1
   orthogonality with coverage-gap notices blocking domain completeness.
5. Exact cross-domain evidence gates (subject/site/producer unit/stable
   source event/content hash/rule+component/comparable window/relation
   type); producer-owned control points are routed out and only surface as
   typed producer references.
6. not_evaluable units carry zero candidate/risk/Query; three-part Chinese
   Query wording is conditional on the enrollment context.
7. Deterministic counts (expected = five L1 buckets; coverage-gap notices
   are separate from Query counts) and delegated routing lists.

All data is synthetic/offline.  No real project, provider, threshold,
listing layout, visit window, medication rule or service.
"""

from __future__ import annotations

from .protocol_contracts import *
from .protocol_applicability import *
from .protocol_evidence import *
from .protocol_component_evaluation import *
from .protocol_risk_projection import *
from .protocol_risk_projection import _evaluation_window_id
from .protocol_materialization import *

__all__ = [
    # Domain identity
    "D04_DOMAIN",
    "D04_UNIT_ALGO_VERSION",
    "D04_RULE_LINEAGE_DEFAULT",
    # Closed enums
    "OWNER_DOMAINS",
    "OWNER_D02",
    "OWNER_D03",
    "OWNER_D04",
    "OWNER_D05",
    "OWNER_D08",
    "OWNER_UNRESOLVED",
    "CONTROL_TYPES",
    "SIGNAL_TYPES",
    "NODE_IDS",
    "ANCHOR_KINDS",
    "PRECISIONS",
    "INCLUSIVITIES",
    "APPLICABILITY_STATUSES",
    "ISSUE_RESULTS",
    "EXPR_OPERATORS",
    "OPERATORS",
    "EXCEPTION_EFFECTS",
    "RELATION_TYPES",
    "JOIN_REASONS",
    "GAP_REASON_CODES",
    "POSITIVE_SUBTYPES",
    "SUBTYPE_LABELS",
    "QUERY_CONTEXTS",
    "TRANSITION_SCOPES",
    "ROUNDING_POLICIES",
    "CLAIM_KINDS",
    # Errors
    "ProtocolSliceError",
    # Value objects
    "ProtocolControlPoint",
    "ProtocolComponent",
    "RuleComparison",
    "ProtocolStructuredRule",
    "IssueExpression",
    "ProtocolRuleEvaluationPlan",
    "ProtocolVersionRecord",
    "ProtocolApplicabilityDecision",
    "ProtocolControlRoutingRecord",
    "ProtocolDelegatedControlPoint",
    "RuleEvidenceRequirement",
    "RuleEvidenceBinding",
    "ProtocolExceptionBinding",
    "UnitConversionRule",
    "RetestOutcome",
    "ProtocolComponentAssessment",
    "ProtocolCoverageGapNotice",
    "D04PriorityPolicy",
    "EnrollmentContext",
    "EvaluationWindowSpec",
    "CrossDomainGateOutcome",
    "RegulatoryGuidanceVersion",
    "ProtocolJourneyEvent",
    "ProtocolRiskMarker",
    "ProtocolEventMarkerJoin",
    "ProtocolProducerReference",
    "ProtocolUnitExpanded",
    "ProtocolExpectedSetExpansion",
    "ProtocolUnitResult",
    "ProtocolSliceResult",
    # Functions
    "positive_subtype_audience_label",
    "policy_content_hash_value",
    "protocol_applicability_id",
    "feasible_version_fingerprint",
    "build_protocol_unit",
    "expected_set_hash",
    "expand_protocol_expected_set",
    "build_rule_evidence_requirement",
    "expand_rule_evidence_requirements",
    "route_control_point",
    "resolve_protocol_applicability",
    "resolve_regulatory_guidance",
    "resolve_enrollment_context",
    "verify_cross_domain_ref",
    "component_issue_predicate",
    "evaluate_issue_expression",
    "evaluate_component_condition",
    "evaluate_protocol_unit",
    "evaluate_protocol_slice",
]
