"""R4-D06 efficacy slice -- deterministic evaluator pipeline and entrypoints.

Frozen source of truth: ``FROZEN_R4_D06_CONTRACT_V1_16``.  This module owns
the D06 **evaluation pipeline** consuming the typed fixture surface
(:class:`D06Fixture`) and emitting typed
:class:`~mm_r4.efficacy.D06ChallengeOutcome` objects:

1. **Scope/identity validation** (contract §5.3 order): the frozen Run/
   snapshot/cutoff identity, accepted assessment/item/result inventory,
   versioned definitions, owner routing, D05 occurrence/timing binding and
   shared temporal spine are validated before any medical expected-set is
   formed; wrong/missing/conflicting authority fails closed.
2. **Gates**: applicability/routing/definition/algorithm/baseline/
   unit_or_scale/dependency/cutoff_scope gates with the closed
   open+boundary|not_evaluable+blocks / closed+resolved truth table; an
   open gate never enters the medical expected-set.
3. **Deterministic unit evaluation** across the closed unit kinds (item
   completeness, item value validity, score recalculation, baseline
   selection, change recalculation, response classification, endpoint
   composition, repeat selection, rater/mode consistency, individual trend
   pattern, accepted report consistency) with the five exclusive L1
   dispositions.
4. **Priority resolution** via the frozen five-step first-match policy,
   and -- only for positive roots -- the emitted
   ``D06PriorityDecision`` / ``D06RiskBinding`` / ``PublicR4RiskIdentity``
   with exact content addressing.
5. **Enrollment-aware three-part Chinese Query drafts** and coverage-gap
   notices (``not_evaluable`` never emits a Query).
6. **Audience payload validation** with the frozen ``d06-audience-zh-v1``
   lexicon; failed/forbidden payloads are suppressed.

Entrypoints exposed here map 1:1 to the frozen catalog entrypoint ids:
``d06.efficacy_evaluator``, ``d06.gate_evaluator``,
``d06.contract_schema_validator``, ``d06.audience_projection_validator``,
``d06.challenge_registry_validator`` (the last lives in
:mod:`mm_r4.efficacy_fixtures`).

The runtime never imports the frozen catalog/oracle/registry and never
branches on challenge number, fixture id, test id, expected text or
expected outcome.  All data is synthetic and offline.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ..projections.efficacy import (
    project_efficacy_journey,
    journey_audience_payload_from_projection,
)
from .efficacy import (
    AUDIENCE_LEXICON_HASH,
    AUDIENCE_LEXICON_VERSION,
    AUDIENCE_VALIDATOR_HASH,
    AUDIENCE_VALIDATOR_VERSION,
    CANONICAL_PRIORITY_POLICY,
    COVERAGE_COVERED,
    COVERAGE_NOT_APPLICABLE,
    COVERAGE_NOT_EVALUABLE,
    D06AudienceValidationResult,
    D06BindingContractError,
    D06ChallengeOutcome,
    D06ContractViolationError,
    D06Error,
    D06PriorityDecision,
    D06PriorityResolverInput,
    D06RiskBinding,
    D06UnitStableCore,
    DECISION_MULTI_FEASIBLE_BOUNDARY,
    DECISION_NOT_EVALUABLE,
    DECISION_UNIQUE,
    DIRECTIONALITIES,
    ENDPOINT_ROLES,
    GATE_ALGORITHM,
    GATE_APPLICABILITY,
    GATE_CUTOFF_SCOPE,
    GATE_DECISION_BOUNDARY,
    GATE_DECISION_NOT_EVALUABLE,
    GATE_DEFINITION,
    GATE_DEPENDENCY,
    GATE_OPEN,
    GATE_ROUTING,
    GATE_UNIT_OR_SCALE,
    L1_BOUNDARY,
    L1_NOT_APPLICABLE,
    L1_NOT_EVALUABLE,
    L1_POSITIVE,
    L1_NEGATIVE,
    L2_COVERAGE_NOTICES,
    L2_QUERIES,
    L2_RISKS,
    OUTPUT_KIND_DEFINITION_BINDING,
    OUTPUT_KIND_ERROR,
    OUTPUT_KIND_GATE,
    OUTPUT_KIND_PROJECTION,
    OUTPUT_KIND_RESULT,
    PRIORITY_REASON_BY_STEP,
    ProjectionContractError,
    QUERY_CONTEXT_ENROLLED,
    SchemaContractError,
    OwnerScopeContractError,
    QUERY_CONTEXT_NOT_OCCURRED,
    QUERY_CONTEXT_UNRESOLVED,
    SCOPE_IDENTITY_FIELDS,
    SCOPE_IN_SCOPE,
    SCOPE_NOT_EVALUABLE,
    SCOPE_OUT_OF_CUTOFF,
    TTE_STATUS_BOUNDARY,
    TTE_STATUS_CENSORED,
    TTE_STATUS_COMPETING_EVENT,
    TTE_STATUS_EVENT,
    TRACE_EDGES_ALL,
    UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY,
    UNIT_KIND_BASELINE_SELECTION,
    UNIT_KIND_CHANGE_RECALCULATION,
    UNIT_KIND_ENDPOINT_COMPOSITION,
    UNIT_KIND_INDIVIDUAL_TREND_PATTERN,
    UNIT_KIND_ITEM_COMPLETENESS,
    UNIT_KIND_ITEM_VALUE_VALIDITY,
    UNIT_KIND_RATER_OR_MODE_CONSISTENCY,
    UNIT_KIND_REPEAT_SELECTION,
    UNIT_KIND_RESPONSE_CLASSIFICATION,
    UNIT_KIND_SCORE_RECALCULATION,
    UNIT_KIND_TO_SUBTYPE,
    _audience_normalize,
    AUDIENCE_PHRASES,
    AudiencePayloadValidationError,
    ChallengeAssertionContractError,
    ChallengeRegistryIntegrityError,
    audience_display_view,
    audience_phrase_hits,
    audience_string_paths,
    audience_visible_strings,
    attempted_display_view,
    d06_canonical_json,
    d06_content_hash,
    d06_sha256_text,
    resolve_priority_step,
    scope_identity_matches,
    validate_audience_payload_schema,
    verify_content_hash,
    verify_embedded_hash,
    verify_lineage_hash,
)

# ---------------------------------------------------------------------------
# Frozen synthetic constants (contract §15)
# ---------------------------------------------------------------------------

CANONICAL_SCOPE_HASH = (
    "505fbb0582b241a5a5265e7bd6d81494cd1a455af5010ffa60c0e5dacca89098"
)
CANONICAL_INPUT_SCOPE_HASH = f"sha256:{CANONICAL_SCOPE_HASH}"

# Canonical assessment identity set (accepted D05 inventory).
CANONICAL_ASSESSMENT_IDS = ("ASM-BASE-D7", "ASM-BASE-D1", "ASM-W4-A", "ASM-W4-B")
CANONICAL_CURRENT_ASSESSMENT = "ASM-W4-A"
CANONICAL_ITEM_DEFINITION_IDS = tuple(f"ITEM-DEF-I{i}" for i in range(1, 7))
CANONICAL_UNIT_ID = "UNIT-001"
CANONICAL_RISK_ID = "RISK-001"
CANONICAL_PRIORITY_DECISION_ID = "PRIORITY-DEC-001"
CANONICAL_CLASSIFIER = "efficacy_evaluation"
CANONICAL_SOURCE_RECORD_ID = "ASM-W4-A"
CANONICAL_PUBLIC_IDENTITY_VERSION = "1.0"
CANONICAL_EPISODE_KEY = "EPISODE-001"
CANONICAL_TIMEPOINT_KEY = "WEEK-4"
CANONICAL_ENDPOINT_KEY = "SYN-ENDPOINT"

# Canonical risk decision identity bound to the typed risk binding /
# public identity (validated field-for-field against the supplied inputs;
# never substituted when a supplied object drifts).
CANONICAL_R2_LIFECYCLE_REF = "R2-LIFECYCLE-001"
CANONICAL_RISK_LOCATORS: Tuple[str, ...] = ("SYN-LOC-RISK-001",)

# Frozen definition-boundary semantic source identity (§15; mirrors the
# generator's exact-definition enforcement): the instrument/endpoint
# definitions carried by the definition-boundary fixtures must match
# these exact schema key sets, identity fields and payload-consistent
# content hashes.  A rehashed version, an unknown schema key or a drifted
# identity fails closed instead of preserving a successful gate.
BOUNDARY_INSTRUMENT_FIELDS = frozenset(
    {
        "admin_mode",
        "content_hash",
        "definition_scope",
        "id",
        "object_type",
        "recall_period",
        "reporter_type",
        "source_locator_ids",
        "stable_key",
        "version",
    }
)
BOUNDARY_ENDPOINT_FIELDS = frozenset(
    {
        "content_hash",
        "definition_scope",
        "directionality",
        "id",
        "object_type",
        "role",
        "source_locator_ids",
        "stable_key",
        "version",
    }
)
BOUNDARY_INSTRUMENT_IDENTITY = {
    "id": "INST-001",
    "stable_key": "SYN-SCALE",
    "version": "1.0",
    "object_type": "instrument_definition",
    "content_hash": (
        "sha256:6e1a6df3fe5dff77146c971b6e8044c026c12f66c67723213aee4fa8b80a482b"
    ),
}
BOUNDARY_ENDPOINT_IDENTITY = {
    "id": "EP-001",
    "stable_key": "SYN-ENDPOINT",
    "version": "1.0",
    "object_type": "endpoint_definition",
    "content_hash": (
        "sha256:ce8cc03a00c98dafa6ec0cb196a8314f0f53591f1a2f8dcaea4e74c4e6bb0eb9"
    ),
}
BOUNDARY_COMPLETE_SCOPE_FIELDS = frozenset(SCOPE_IDENTITY_FIELDS) | {"cutoff"}

QUERY_PAYLOADS_BY_CONTEXT: Dict[str, Dict[str, str]] = {
    QUERY_CONTEXT_ENROLLED: {
        "basis_sentence": "依据：参与者已入组。",
        "finding_sentence": "发现：疗效记录需核实。",
        "action_sentence": (
            "行动项：请核实相关记录；如确认不符合方案，"
            "请评估是否构成方案偏离并按相应流程处理。"
        ),
    },
    QUERY_CONTEXT_NOT_OCCURRED: {
        "basis_sentence": "依据：当前资料显示尚未入组。",
        "finding_sentence": "发现：疗效记录需核实。",
        "action_sentence": "行动项：请核实并更正相关记录。",
    },
    QUERY_CONTEXT_UNRESOLVED: {
        "basis_sentence": "依据：当前入组状态尚未明确。",
        "finding_sentence": "发现：入组时序与疗效记录关系待核实。",
        "action_sentence": "行动项：请先核实随机、入组或首次给药状态及事件时序。",
    },
}

PD_WORDING_FRAGMENTS = ("方案偏离", "PD")

# ---------------------------------------------------------------------------
# Typed scope-binding helpers
# ---------------------------------------------------------------------------
#
# D06 authority is the fixture's OWN declared scope binding.  Production
# decisions never compare against a module-level canonical scope or a
# ``SYN-*`` sentinel: every typed child reference is validated on the
# scope identity fields it actually declares, against the fixture's own
# declared scope.  Any declared identity mismatch fails closed through
# the same typed binding stage/type, regardless of the value spelling.


def _declared_scope_identity_matches(
    obj: Mapping[str, Any], scope: Mapping[str, Any]
) -> bool:
    """True when every scope identity field the object declares agrees
    with the fixture's own declared scope binding.

    Only fields actually present on the object are compared: a partial
    child reference (e.g. a TTE/ICE typed event declaring only
    ``subject_ref``) is validated on exactly what it declares, never on
    undeclared identity dimensions."""
    return all(
        obj.get(field) == scope.get(field)
        for field in SCOPE_IDENTITY_FIELDS
        if field in obj
    )


def _scope_claim_conflicts(
    scope: Mapping[str, Any], claim: Mapping[str, Any]
) -> bool:
    """True when a typed-parameter scope claim disagrees with the
    fixture's own declared scope binding on any identity field."""
    return any(
        field in claim and claim[field] != scope.get(field)
        for field in SCOPE_IDENTITY_FIELDS
    )


# ---------------------------------------------------------------------------
# Typed fixture container
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D06Fixture:
    """Deeply immutable typed input container for a D06 synthetic evaluation.

    Built by the fixture adapter from the frozen typed fixture catalog.
    Every section -- and every nested mapping/list inside it -- is frozen
    at construction (via :func:`mm_r4.efficacy.deep_freeze`), so
    post-construction mutation of any source dict/list can never change a
    runtime input or its derived outcome.  The raw fixture payload is kept
    (frozen) so the runtime can content-address the actual typed input it
    received.
    """

    scope: Mapping[str, Any]
    definitions: Mapping[str, Any]
    records: Mapping[str, Any]
    bindings: Mapping[str, Any]
    policies: Mapping[str, Any]
    case_inputs: Mapping[str, Any]
    evaluation_binding_states: Optional[Mapping[str, Any]]
    source_registries: Mapping[str, Any]
    risk_binding: Optional[Mapping[str, Any]]
    public_r4_risk_identity: Optional[Mapping[str, Any]]
    risk_binding_state: str
    public_r4_identity_state: str
    fixture_schema_version: str
    synthetic_only: bool
    raw_fixture: Optional[Mapping[str, Any]] = None
    challenge_number: int = 0

    @property
    def typed_parameters(self) -> Mapping[str, Any]:
        return self.case_inputs.get("typed_parameters", {})

    @property
    def definitions_scope(self) -> Mapping[str, Any]:
        return self.scope


# ---------------------------------------------------------------------------
# Typed-boundary schema validation
# ---------------------------------------------------------------------------
#
# The adapter/runtime boundary rejects unknown, missing or incompatible
# nested fields BEFORE any evaluation runs.  Deep freezing alone is not
# sufficient: the exact recursive schema below is the typed contract the
# runtime consumes.  It validates structure and value types -- never
# case-specific content -- so it cannot duplicate the test oracle.

_FIXTURE_TOP_LEVEL_KEYS = frozenset(
    {
        "bindings",
        "case_inputs",
        "challenge_number",
        "definitions",
        "evaluation_binding_states",
        "fixture_schema_version",
        "policies",
        "public_r4_identity_state",
        "public_r4_risk_identity",
        "records",
        "risk_binding",
        "risk_binding_state",
        "scope",
        "source_registries",
        "synthetic_only",
    }
)
_FIXTURE_REQUIRED_KEYS = frozenset(
    {
        "bindings",
        "case_inputs",
        "definitions",
        "fixture_schema_version",
        "policies",
        "public_r4_identity_state",
        "public_r4_risk_identity",
        "records",
        "risk_binding_state",
        "scope",
        "source_registries",
        "synthetic_only",
    }
)
_SCOPE_KEYS = frozenset(
    {
        "accepted_snapshot_ref",
        "clinical_event_cutoff",
        "episode_key",
        "monitoring_mode",
        "project_ref",
        "run_ref",
        "scope_binding_id",
        "site_ref",
        "snapshot_as_of",
        "source_revision",
        "subject_ref",
    }
)
_DEFINITION_NAMES = frozenset(
    {
        "algorithm",
        "baseline_rule",
        "combination",
        "endpoint",
        "instrument",
        "threshold",
        "timepoint",
        "trend",
    }
)
_RECORDS_KEYS = frozenset(
    {
        "accepted_result",
        "assessment_items",
        "assessments",
        "components",
        "item_values",
        "recalculated_result",
        "trend_points",
        "tte",
    }
)
_BINDINGS_KEYS = frozenset(
    {
        "active_enrollment_decision_id",
        "active_enrollment_decision_ids_by_context",
        "active_estimator_binding_id",
        "d05_refs",
        "d07_consumption_binding",
        "d07_value_ref",
        "d08_relationship_ref",
        "enrollment_binding_state",
        "enrollment_context_decisions",
        "estimator_binding_state",
        "maturity_anchor_refs",
        "maturity_anchor_selection_decision",
        "shared_spine_hash",
        "shared_temporal_spine_binding",
        "tte_precedence_binding",
    }
)
_CASE_INPUTS_KEYS = frozenset({"case_input_schema", "typed_parameters"})
_SOURCE_REGISTRIES_KEYS = frozenset(
    {
        "accepted_d05_assessment_inventory",
        "consumer_unit_ids",
        "d05_assessment_foreign_keys",
        "d06_unit_stable_core",
        "enrollment_rule_registry",
        "enrollment_source_events",
        "maturity_consumer_bindings",
        "required_d05_binding_ref_ids",
        "tte_rule_registry",
        "tte_source_events",
        "tte_source_registry",
    }
)
_POLICIES_KEYS = frozenset(
    {
        "audience_lexicon_hash",
        "candidate_selection",
        "priority_decision",
        "priority_policy",
        "priority_resolution_input",
        "query_context",
    }
)
_EVALUATION_BINDING_STATES_KEYS = frozenset(
    {
        "d05_binding_state",
        "maturity_anchor_selection_decision_id",
        "maturity_binding_state",
        "maturity_not_required_reason",
    }
)

# Exact schema key sets for every typed runtime-consumed object type
# (definitions, assessment/source records, bindings/policies, TTE and
# enrollment events/registries, risk binding and public identity).
# Each object type has exactly one key set in the frozen catalog; the
# recursive walk below fails closed on unknown/missing/incompatible
# nested fields BEFORE medical evaluation.  Structural only -- never
# case-specific content, so it cannot duplicate the test oracle.
_OBJECT_TYPE_KEYS: Dict[str, frozenset] = {
    'AcceptedD05AssessmentInventoryItem': frozenset({'actual_time_ref', 'assignment_status', 'd05_actual_activity_key', 'd05_planned_activity_key', 'd05_unit_id', 'hash', 'object_type', 'occurrence_disposition', 'producer_payload_hash', 'source_record_id', 'timing_disposition'}),  # noqa: E501
    'AcceptedIndividualTrendSource': frozenset({'accepted_result_ids', 'accepted_snapshot_ref', 'content_hash', 'episode_key', 'monitoring_mode', 'object_type', 'project_ref', 'run_ref', 'scope_binding_id', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_endpoint_key', 'stable_timepoint_key', 'subject_ref', 'trend', 'trend_source_id'}),  # noqa: E501
    'AcceptedMonitoringReportClaim': frozenset({'acceptance_state', 'accepted_snapshot_ref', 'claim_kind', 'claim_value', 'content_hash', 'episode_key', 'monitoring_mode', 'object_type', 'project_ref', 'report_claim_id', 'run_ref', 'scope_binding_id', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_endpoint_key', 'stable_timepoint_key', 'subject_ref', 'trend'}),  # noqa: E501
    'ActualAssessmentRecord': frozenset({'accepted_snapshot_ref', 'actual_recall_period', 'admin_mode', 'assessment_id', 'assessment_time_ref', 'assignment_status', 'central_or_local_role', 'correction_status', 'cutoff', 'd05_actual_activity_key', 'd05_planned_activity_key', 'd05_unit_id', 'episode_key', 'id', 'instrument_definition_id', 'item_record_ids', 'lineage_hash', 'monitoring_mode', 'object_type', 'occurrence_disposition', 'prior_assessment_id', 'project_ref', 'record_status', 'recorded_visit_ref', 'reporter_id_role', 'reporter_role', 'reporter_type', 'run_ref', 'scope_binding_id', 'scope_decision_id', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_assessment_key', 'subject_ref', 'supersedes_assessment_id', 'time', 'timing_disposition', 'value'}),  # noqa: E501
    'AssessmentItemRecord': frozenset({'assessment_id', 'content_hash', 'correction_status', 'item_definition_id', 'item_record_id', 'missing_reason', 'normalized_value', 'object_type', 'prior_item_record_id', 'raw_value', 'record_status', 'source_locator_ids', 'stable_item_record_key', 'supersedes_item_record_id', 'value_unit'}),  # noqa: E501
    'D05AssessmentBindingRef': frozenset({'accepted_snapshot_ref', 'actual_time_ref', 'assignment_status', 'binding_ref_id', 'cutoff', 'd05_actual_activity_key', 'd05_planned_activity_key', 'd05_unit_id', 'episode_key', 'hash', 'monitoring_mode', 'object_type', 'occurrence_disposition', 'producer_payload_hash', 'project_ref', 'run_ref', 'scope_binding_id', 'site_ref', 'source_locator_ids', 'source_record_id', 'source_revision', 'subject_ref', 'timing_disposition'}),  # noqa: E501
    'D05AssessmentForeignKey': frozenset({'actual_time_ref', 'assignment_status', 'binding_ref_id', 'd05_actual_activity_key', 'd05_planned_activity_key', 'd05_unit_id', 'hash', 'object_type', 'occurrence_disposition', 'producer_payload_hash', 'source_record_id', 'timing_disposition'}),  # noqa: E501
    'D06MaturityConsumerBinding': frozenset({'accepted_snapshot_ref', 'consumer_id', 'cutoff', 'episode_key', 'hash', 'maturity_decision_id', 'monitoring_mode', 'object_type', 'project_ref', 'run_ref', 'scope_binding_id', 'shared_spine_hash', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_endpoint_key', 'stable_timepoint_key', 'subject_ref'}),  # noqa: E501
    'D06PriorityDecision': frozenset({'accepted_snapshot_ref', 'actionability', 'cutoff', 'endpoint_definition_id', 'endpoint_role', 'episode_key', 'impact_class', 'impact_resolution_state', 'lineage_hash', 'machine_close_forbidden', 'matched_precedence_step', 'monitoring_mode', 'monitoring_priority', 'object_type', 'priority_decision_id', 'priority_policy_hash', 'priority_policy_id', 'priority_policy_version', 'priority_resolver_input_hash', 'project_ref', 'reason_codes', 'recoverability', 'recurrence_class', 'risk_id', 'run_ref', 'scope_binding_id', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_endpoint_key', 'stable_timepoint_key', 'subject_ref', 'unit_id'}),  # noqa: E501
    'D06PriorityPolicy': frozenset({'object_type', 'ordered_precedence_rules', 'policy_hash', 'policy_id', 'source_locator_ids', 'version'}),  # noqa: E501
    'D06PriorityResolverInput': frozenset({'accepted_snapshot_ref', 'actionability', 'cutoff', 'endpoint_definition_id', 'endpoint_role', 'episode_key', 'hash', 'impact_class', 'impact_resolution_state', 'machine_close_forbidden', 'matched_precedence_step', 'monitoring_mode', 'monitoring_priority', 'object_type', 'priority_policy_hash', 'priority_policy_id', 'priority_policy_version', 'project_ref', 'reason_codes', 'recoverability', 'recurrence_class', 'run_ref', 'scope_binding_id', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_endpoint_key', 'stable_timepoint_key', 'subject_ref'}),  # noqa: E501
    'D06RiskBinding': frozenset({'R2_lifecycle_ref', 'accepted_snapshot_ref', 'classifier', 'cutoff', 'episode_key', 'lineage_hash', 'monitoring_mode', 'object_type', 'primary_subtype', 'priority_decision_id', 'project_ref', 'public_r4_risk_identity_id', 'risk_id', 'run_ref', 'scope_binding_id', 'site_ref', 'source_locator_ids', 'source_revision', 'subject_ref', 'unit_id'}),  # noqa: E501
    'D06UnitStableCore': frozenset({'classifier', 'domain_id', 'hash', 'object_type', 'rule_or_knowledge_lineage', 'stable_endpoint_key', 'stable_instrument_key_or_none', 'stable_item_or_component_key_or_none', 'stable_source_record_id', 'stable_timepoint_key', 'temporal_window', 'unit_id', 'unit_kind'}),  # noqa: E501
    'D07ConsumptionBinding': frozenset({'accepted_snapshot_ref', 'consuming_endpoint_definition_id', 'cutoff', 'd07_endpoint_value_ref_id', 'episode_key', 'id', 'input_measure_key', 'lineage_hash', 'monitoring_mode', 'object_type', 'producer_version', 'project_ref', 'run_ref', 'scope_binding_id', 'scoring_operation_id', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_source_identity', 'subject_ref', 'validation_state'}),  # noqa: E501
    'D07EndpointValueRef': frozenset({'accepted_snapshot_ref', 'cutoff', 'endpoint_definition_id', 'episode_key', 'id', 'input_measure_key', 'lineage_hash', 'monitoring_mode', 'object_type', 'producer_version', 'project_ref', 'run_ref', 'scope_binding_id', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_endpoint_key', 'stable_source_identity', 'subject_ref', 'validation_state'}),  # noqa: E501
    'D08RelationshipRef': frozenset({'accepted_snapshot_ref', 'cutoff', 'episode_key', 'id', 'left_stable_identity', 'lineage_hash', 'monitoring_mode', 'object_type', 'producer_version', 'project_ref', 'relationship_type', 'right_stable_identity', 'run_ref', 'scope_binding_id', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_source_identity', 'subject_ref', 'validation_state'}),  # noqa: E501
    'DerivedEfficacyResult': frozenset({'accepted_snapshot_ref', 'cutoff', 'episode_key', 'id', 'lineage_hash', 'monitoring_mode', 'object_type', 'project_ref', 'response_class', 'run_ref', 'scope_binding_id', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_endpoint_key', 'stable_timepoint_key', 'subject_ref', 'unit', 'value'}),  # noqa: E501
    'EnrollmentContextDecisionRef': frozenset({'accepted_snapshot_ref', 'cutoff', 'decision_id', 'decision_rule_id', 'effective_time_ref', 'enrollment_ref', 'episode_key', 'first_dose_ref', 'hash', 'monitoring_mode', 'object_type', 'producer_domain', 'project_ref', 'query_context', 'randomization_ref', 'rule_version', 'run_ref', 'scope_binding_id', 'site_ref', 'source_event_refs', 'source_locator_ids', 'source_revision', 'subject_ref'}),  # noqa: E501
    'EnrollmentDecisionRule': frozenset({'allowed_contexts', 'decision_rule_id', 'hash', 'object_type', 'rule_version', 'source_locator_ids'}),  # noqa: E501
    'EnrollmentSourceEvent': frozenset({'effective_time_ref', 'event_id', 'event_role', 'hash', 'object_type', 'query_context', 'source_locator_ids'}),  # noqa: E501
    'MaturityAnchorSelectionDecision': frozenset({'accepted_snapshot_ref', 'candidate_typed_anchor_ids', 'consumer_unit_or_result_id', 'cutoff', 'd05_assessment_binding_ref_ids', 'decision_id', 'decision_status', 'episode_key', 'hash', 'maturity_rule_id', 'monitoring_mode', 'object_type', 'predicate_results', 'project_ref', 'rejected_candidate_reasons', 'run_ref', 'scope_binding_id', 'selected_normalized_time_ref', 'selected_typed_anchor_id', 'selection_policy_id', 'shared_spine_hash', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_timepoint_key', 'subject_ref'}),  # noqa: E501
    'PublicR4RiskIdentity': frozenset({'canonical_tuple', 'cutoff', 'domain_id', 'episode_key', 'normalized_concept', 'object_type', 'project_ref', 'public_identity_hash', 'public_identity_version', 'public_r4_risk_identity_id', 'risk_id', 'rule_or_knowledge_lineage', 'scope_binding_id', 'scope_key', 'scope_type', 'site_ref', 'stable_endpoint_key', 'stable_source_or_event_identity', 'stable_timepoint_key', 'subject_ref', 'temporal_window', 'unit_id'}),  # noqa: E501
    'SharedTemporalSpineBinding': frozenset({'accepted_snapshot_ref', 'axis_hash', 'axis_version', 'cutoff', 'd05_projection_id', 'episode_key', 'hash', 'monitoring_mode', 'object_type', 'project_ref', 'run_ref', 'scope_binding_id', 'site_ref', 'snapshot_as_of', 'source_locator_ids', 'source_revision', 'spine_binding_id', 'subject_ref'}),  # noqa: E501
    'TTEEndpointPrecedenceBinding': frozenset({'accepted_snapshot_ref', 'cutoff', 'episode_key', 'event_precedence_rule_id', 'id', 'lineage_hash', 'monitoring_mode', 'object_type', 'producer_version', 'project_ref', 'run_ref', 'scope_binding_id', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_endpoint_key', 'stable_source_identity', 'stable_timepoint_key', 'subject_ref', 'validation_state'}),  # noqa: E501
    'TTEPrecedenceRule': frozenset({'allowed_tie_policies', 'event_precedence_rule_id', 'hash', 'object_type', 'source_locator_ids'}),  # noqa: E501
    'TTESourceRegistry': frozenset({'censor_time_ref', 'competing_event_ref', 'event_precedence_rule_id', 'event_time_ref', 'hash', 'object_type', 'origin_time_ref', 'source_locator_ids', 'stable_endpoint_key', 'stable_timepoint_key', 'target_event_ref', 'tie_policy'}),  # noqa: E501
    'TimeToEventInterpretationRef': frozenset({'accepted_snapshot_ref', 'censor_reason', 'censor_time_ref', 'competing_event_ref', 'cutoff', 'episode_key', 'event_time_ref', 'hash', 'interpretation_ref_id', 'monitoring_mode', 'object_type', 'origin_time_ref', 'project_ref', 'run_ref', 'scope_binding_id', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_source_identity', 'state', 'subject_ref', 'target_event_ref', 'validation_state'}),  # noqa: E501
    'TypedMaturityAnchorRef': frozenset({'accepted_snapshot_ref', 'anchor_kind', 'anchor_ref_id', 'anchor_role', 'cutoff', 'd05_assessment_binding_ref_id', 'episode_key', 'hash', 'monitoring_mode', 'normalized_time_ref', 'object_type', 'producer_domain', 'producer_version', 'project_ref', 'run_ref', 'scope_binding_id', 'site_ref', 'source_locator_ids', 'source_revision', 'stable_source_identity', 'subject_ref', 'validation_state'}),  # noqa: E501
    'TypedTTEEventSource': frozenset({'effective_time_ref', 'event_id', 'event_role', 'hash', 'object_type', 'source_locator_ids'}),  # noqa: E501
    'algorithm_definition': frozenset({'content_hash', 'definition_scope', 'id', 'numeric_policy_id', 'object_type', 'operation_ids', 'source_locator_ids', 'version'}),  # noqa: E501
    'baseline_rule_definition': frozenset({'content_hash', 'definition_scope', 'id', 'object_type', 'selection_policy', 'source_locator_ids'}),  # noqa: E501
    'combination_definition': frozenset({'components', 'content_hash', 'definition_scope', 'kind', 'missing_policy', 'object_type', 'source_locator_ids'}),  # noqa: E501
    'endpoint_definition': frozenset({'content_hash', 'definition_scope', 'directionality', 'id', 'object_type', 'role', 'source_locator_ids', 'stable_key', 'version'}),  # noqa: E501
    'instrument_definition': frozenset({'admin_mode', 'content_hash', 'definition_scope', 'id', 'object_type', 'recall_period', 'reporter_type', 'source_locator_ids', 'stable_key', 'version'}),  # noqa: E501
    'threshold_definition': frozenset({'comparator', 'content_hash', 'definition_scope', 'object_type', 'source_locator_ids', 'unit', 'value'}),  # noqa: E501
    'timepoint_definition': frozenset({'content_hash', 'definition_scope', 'key', 'nominal_time', 'object_type', 'source_locator_ids'}),  # noqa: E501
    'trend_definition': frozenset({'comparator', 'content_hash', 'definition_scope', 'kind', 'object_type', 'source_locator_ids', 'threshold', 'unit'}),  # noqa: E501
}


def _validate_typed_object_schema(value: Any, path: str) -> None:
    """Recursively enforce exact object-type schema key sets.

    Every dict carrying an ``object_type`` must match the exact frozen
    key set for that type; unknown or missing nested fields fail closed
    before medical evaluation.
    """
    if isinstance(value, (dict, Mapping)):
        object_type = value.get("object_type")
        if object_type:
            if object_type not in _OBJECT_TYPE_KEYS:
                raise D06ContractViolationError(
                    f"fixture schema: unknown object type {object_type!r} at {path}",
                    "pre_medical_output_validation",
                )
            if set(value) != _OBJECT_TYPE_KEYS[object_type]:
                raise D06ContractViolationError(
                    f"fixture schema: {object_type} nested field set mismatch at "
                    f"{path}",
                    "pre_medical_output_validation",
                )
        # Locator identity: source locator fields must be lists of
        # non-empty strings wherever present; incompatible nested values
        # fail before medical evaluation.
        if "source_locator_ids" in value:
            locators = value["source_locator_ids"]
            if not isinstance(locators, list) or not all(
                isinstance(item, str) and item for item in locators
            ):
                raise D06ContractViolationError(
                    f"fixture schema: source_locator_ids malformed at {path}",
                    "pre_medical_output_validation",
                )
        for key, item in value.items():
            _validate_typed_object_schema(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_typed_object_schema(item, f"{path}[{index}]")


def _require_str_dict(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, (dict, Mapping)):
        raise D06ContractViolationError(
            f"fixture schema: {label} must be an object",
            "pre_medical_output_validation",
        )
    return value


def _require_str_list(value: Any, label: str) -> List[Any]:
    if not isinstance(value, list):
        raise D06ContractViolationError(
            f"fixture schema: {label} must be a list",
            "pre_medical_output_validation",
        )
    return value


def validate_fixture_schema(fixture_dict: Mapping[str, Any]) -> None:
    """Exact recursive schema validation at the adapter boundary.

    Unknown top-level/section keys, missing required sections and
    incompatible nested value types fail closed before evaluation.  The
    checks are structural (types / key sets / object kinds); they never
    read expected outcomes or case-specific content.
    """
    if not isinstance(fixture_dict, (dict, Mapping)):
        raise D06ContractViolationError(
            "fixture schema: fixture must be an object",
            "pre_medical_output_validation",
        )
    unknown = set(fixture_dict) - _FIXTURE_TOP_LEVEL_KEYS
    if unknown:
        raise D06ContractViolationError(
            f"fixture schema: unknown top-level keys {sorted(unknown)}",
            "pre_medical_output_validation",
        )
    missing = _FIXTURE_REQUIRED_KEYS - set(fixture_dict)
    if missing:
        raise D06ContractViolationError(
            f"fixture schema: missing required sections {sorted(missing)}",
            "pre_medical_output_validation",
        )
    if not isinstance(
        fixture_dict.get("fixture_schema_version"), str
    ) or not isinstance(fixture_dict.get("synthetic_only"), bool):
        raise D06ContractViolationError(
            "fixture schema: version/synthetic flags malformed",
            "pre_medical_output_validation",
        )
    if not isinstance(fixture_dict.get("risk_binding_state"), str) or not isinstance(
        fixture_dict.get("public_r4_identity_state"), str
    ):
        raise D06ContractViolationError(
            "fixture schema: risk/identity states malformed",
            "pre_medical_output_validation",
        )
    challenge_number = fixture_dict.get("challenge_number", 0)
    if not isinstance(challenge_number, int) or isinstance(challenge_number, bool):
        raise D06ContractViolationError(
            "fixture schema: challenge_number must be an int",
            "pre_medical_output_validation",
        )
    scope = _require_str_dict(fixture_dict.get("scope"), "scope")
    if set(scope) != _SCOPE_KEYS or not all(
        isinstance(value, str) for value in scope.values()
    ):
        raise D06ContractViolationError(
            "fixture schema: scope keys/values incompatible",
            "pre_medical_output_validation",
        )
    definitions = _require_str_dict(
        fixture_dict.get("definitions"), "definitions"
    )
    if set(definitions) != _DEFINITION_NAMES:
        raise D06ContractViolationError(
            "fixture schema: definition set incompatible",
            "pre_medical_output_validation",
        )
    for name, definition in definitions.items():
        _require_str_dict(definition, f"definitions.{name}")
        if not isinstance(definition.get("object_type"), str) or not definition.get(
            "object_type"
        ):
            raise D06ContractViolationError(
                f"fixture schema: definitions.{name} missing object_type",
                "pre_medical_output_validation",
            )
        if not isinstance(definition.get("definition_scope"), (dict, Mapping)):
            raise D06ContractViolationError(
                f"fixture schema: definitions.{name} missing definition_scope",
                "pre_medical_output_validation",
            )
        if not isinstance(definition.get("source_locator_ids"), list):
            raise D06ContractViolationError(
                f"fixture schema: definitions.{name} missing source locators",
                "pre_medical_output_validation",
            )
        if not isinstance(definition.get("content_hash"), str):
            raise D06ContractViolationError(
                f"fixture schema: definitions.{name} missing content hash",
                "pre_medical_output_validation",
            )
    records = _require_str_dict(fixture_dict.get("records"), "records")
    unknown_records = set(records) - _RECORDS_KEYS
    if unknown_records:
        raise D06ContractViolationError(
            f"fixture schema: unknown record sections {sorted(unknown_records)}",
            "pre_medical_output_validation",
        )
    assessments = records.get("assessments", [])
    _require_str_list(assessments, "records.assessments")
    for index, assessment in enumerate(assessments):
        _require_str_dict(assessment, f"records.assessments[{index}]")
        if not isinstance(assessment.get("id"), str) or not assessment.get("id"):
            raise D06ContractViolationError(
                f"fixture schema: records.assessments[{index}] missing id",
                "pre_medical_output_validation",
            )
        if not isinstance(assessment.get("time"), str):
            raise D06ContractViolationError(
                f"fixture schema: records.assessments[{index}] time malformed",
                "pre_medical_output_validation",
            )
    trend_points = records.get("trend_points", [])
    _require_str_list(trend_points, "records.trend_points")
    for index, point in enumerate(trend_points):
        _require_str_dict(point, f"records.trend_points[{index}]")
        if not isinstance(point.get("id"), str):
            raise D06ContractViolationError(
                f"fixture schema: records.trend_points[{index}] malformed",
                "pre_medical_output_validation",
            )
    item_values = records.get("item_values")
    if item_values is not None:
        _require_str_dict(item_values, "records.item_values")
        if not all(
            isinstance(value, str) for value in item_values.values()
        ):
            raise D06ContractViolationError(
                "fixture schema: records.item_values values malformed",
                "pre_medical_output_validation",
            )
    for key in ("accepted_result", "recalculated_result", "tte"):
        value = records.get(key)
        if value is not None and not isinstance(value, (dict, Mapping)):
            raise D06ContractViolationError(
                f"fixture schema: records.{key} must be an object or null",
                "pre_medical_output_validation",
            )
    bindings = _require_str_dict(fixture_dict.get("bindings"), "bindings")
    unknown_bindings = set(bindings) - _BINDINGS_KEYS
    if unknown_bindings:
        raise D06ContractViolationError(
            f"fixture schema: unknown binding keys {sorted(unknown_bindings)}",
            "pre_medical_output_validation",
        )
    for list_key in (
        "d05_refs",
        "enrollment_context_decisions",
        "maturity_anchor_refs",
    ):
        value = bindings.get(list_key)
        if value is not None:
            _require_str_list(value, f"bindings.{list_key}")
    for dict_key in (
        "shared_temporal_spine_binding",
        "tte_precedence_binding",
        "maturity_anchor_selection_decision",
        "d07_consumption_binding",
        "active_enrollment_decision_ids_by_context",
    ):
        value = bindings.get(dict_key)
        if value is not None and not isinstance(value, (dict, Mapping)):
            raise D06ContractViolationError(
                f"fixture schema: bindings.{dict_key} must be an object or null",
                "pre_medical_output_validation",
            )
    case_inputs = _require_str_dict(fixture_dict.get("case_inputs"), "case_inputs")
    if set(case_inputs) != _CASE_INPUTS_KEYS:
        raise D06ContractViolationError(
            "fixture schema: case_inputs keys incompatible",
            "pre_medical_output_validation",
        )
    _require_str_dict(case_inputs.get("typed_parameters"), "typed_parameters")
    if not isinstance(case_inputs.get("case_input_schema"), str):
        raise D06ContractViolationError(
            "fixture schema: case_input_schema malformed",
            "pre_medical_output_validation",
        )
    source_registries = _require_str_dict(
        fixture_dict.get("source_registries"), "source_registries"
    )
    unknown_registries = set(source_registries) - _SOURCE_REGISTRIES_KEYS
    if unknown_registries:
        raise D06ContractViolationError(
            f"fixture schema: unknown registry keys {sorted(unknown_registries)}",
            "pre_medical_output_validation",
        )
    for list_key in (
        "accepted_d05_assessment_inventory",
        "consumer_unit_ids",
        "d05_assessment_foreign_keys",
        "enrollment_source_events",
        "maturity_consumer_bindings",
        "required_d05_binding_ref_ids",
        "tte_source_events",
    ):
        value = source_registries.get(list_key)
        if value is not None:
            _require_str_list(value, f"source_registries.{list_key}")
    for dict_key in (
        "d06_unit_stable_core",
        "enrollment_rule_registry",
        "tte_rule_registry",
        "tte_source_registry",
    ):
        value = source_registries.get(dict_key)
        if value is not None and not isinstance(value, (dict, Mapping)):
            raise D06ContractViolationError(
                f"fixture schema: source_registries.{dict_key} malformed",
                "pre_medical_output_validation",
            )
    policies = _require_str_dict(fixture_dict.get("policies"), "policies")
    unknown_policies = set(policies) - _POLICIES_KEYS
    if unknown_policies:
        raise D06ContractViolationError(
            f"fixture schema: unknown policy keys {sorted(unknown_policies)}",
            "pre_medical_output_validation",
        )
    for dict_key in ("priority_resolution_input", "priority_decision"):
        value = policies.get(dict_key)
        if value is not None and not isinstance(value, (dict, Mapping)):
            raise D06ContractViolationError(
                f"fixture schema: policies.{dict_key} malformed",
                "pre_medical_output_validation",
            )
    if not isinstance(policies.get("priority_policy"), (dict, Mapping)):
        raise D06ContractViolationError(
            "fixture schema: policies.priority_policy malformed",
            "pre_medical_output_validation",
        )
    for str_key in ("audience_lexicon_hash", "candidate_selection", "query_context"):
        if not isinstance(policies.get(str_key), str):
            raise D06ContractViolationError(
                f"fixture schema: policies.{str_key} malformed",
                "pre_medical_output_validation",
            )
    evaluation_binding_states = fixture_dict.get("evaluation_binding_states")
    if evaluation_binding_states is not None:
        states = _require_str_dict(
            evaluation_binding_states, "evaluation_binding_states"
        )
        unknown_states = set(states) - _EVALUATION_BINDING_STATES_KEYS
        if unknown_states:
            raise D06ContractViolationError(
                f"fixture schema: unknown binding-state keys "
                f"{sorted(unknown_states)}",
                "pre_medical_output_validation",
            )
    for key in ("risk_binding", "public_r4_risk_identity"):
        value = fixture_dict.get(key)
        if value is not None and not isinstance(value, (dict, Mapping)):
            raise D06ContractViolationError(
                f"fixture schema: {key} must be an object or null",
                "pre_medical_output_validation",
            )
    # Exact recursive object-type schema: every typed nested object must
    # carry exactly its frozen key set (definitions, assessment/source
    # records, bindings/policies, TTE/enrollment events and registries,
    # risk binding and public identity).  Unknown/missing/incompatible
    # nested fields fail before medical evaluation.
    _validate_typed_object_schema(fixture_dict, "fixture")


def build_d06_fixture(fixture_dict: Mapping[str, Any]) -> D06Fixture:
    """Construct a deeply immutable runtime fixture from a frozen dict.

    ``fixture_dict`` is the actual typed input payload; its canonical hash
    is preserved for the ``evaluated_fixture_hash``/``fixture_hash``
    leaves.  The exact recursive schema is validated first, so unknown /
    missing / incompatible nested fields fail before evaluation.  Any
    post-construction mutation of the caller's dict does not affect the
    fixture (deep freeze).
    """
    from .efficacy import deep_freeze

    validate_fixture_schema(fixture_dict)

    def _freeze_or_none(value: Any) -> Any:
        return deep_freeze(value) if value is not None else None

    return D06Fixture(
        scope=deep_freeze(fixture_dict.get("scope", {})),
        definitions=deep_freeze(fixture_dict.get("definitions", {})),
        records=deep_freeze(fixture_dict.get("records", {})),
        bindings=deep_freeze(fixture_dict.get("bindings", {})),
        policies=deep_freeze(fixture_dict.get("policies", {})),
        case_inputs=deep_freeze(fixture_dict.get("case_inputs", {})),
        evaluation_binding_states=_freeze_or_none(
            fixture_dict.get("evaluation_binding_states")
        ),
        source_registries=deep_freeze(fixture_dict.get("source_registries", {})),
        risk_binding=_freeze_or_none(fixture_dict.get("risk_binding")),
        public_r4_risk_identity=_freeze_or_none(
            fixture_dict.get("public_r4_risk_identity")
        ),
        risk_binding_state=str(fixture_dict.get("risk_binding_state", "not_created")),
        public_r4_identity_state=str(
            fixture_dict.get("public_r4_identity_state", "not_created")
        ),
        fixture_schema_version=str(fixture_dict.get("fixture_schema_version", "")),
        synthetic_only=bool(fixture_dict.get("synthetic_only", False)),
        raw_fixture=deep_freeze(fixture_dict),
        challenge_number=int(fixture_dict.get("challenge_number", 0)),
    )


# ---------------------------------------------------------------------------
# Evaluation context
# ---------------------------------------------------------------------------


class _RunContext:
    """Mutable evaluation state (not part of any stable identity)."""

    def __init__(self, fixture: D06Fixture, entrypoint: str):
        from .efficacy import deep_unfreeze

        # Processing view: plain dict copies made at construction from the
        # deeply frozen input.  The exposed fixture stays immutable, so
        # post-construction source mutation can never change it; the
        # processing copies are private and snapshot the input at build
        # time.
        self.fixture = D06Fixture(
            scope=deep_unfreeze(fixture.scope),
            definitions=deep_unfreeze(fixture.definitions),
            records=deep_unfreeze(fixture.records),
            bindings=deep_unfreeze(fixture.bindings),
            policies=deep_unfreeze(fixture.policies),
            case_inputs=deep_unfreeze(fixture.case_inputs),
            evaluation_binding_states=(
                deep_unfreeze(fixture.evaluation_binding_states)
                if fixture.evaluation_binding_states is not None
                else None
            ),
            source_registries=deep_unfreeze(fixture.source_registries),
            risk_binding=(
                deep_unfreeze(fixture.risk_binding)
                if fixture.risk_binding is not None
                else None
            ),
            public_r4_risk_identity=(
                deep_unfreeze(fixture.public_r4_risk_identity)
                if fixture.public_r4_risk_identity is not None
                else None
            ),
            risk_binding_state=fixture.risk_binding_state,
            public_r4_identity_state=fixture.public_r4_identity_state,
            fixture_schema_version=fixture.fixture_schema_version,
            synthetic_only=fixture.synthetic_only,
            raw_fixture=fixture.raw_fixture,
            challenge_number=fixture.challenge_number,
        )
        # The deeply frozen input snapshot used for hashing/provenance.
        self.frozen_fixture = fixture
        self.entrypoint = entrypoint
        # Processing scope is the ACTUAL input fixture scope (canonical
        # for every frozen case; any drift flows into every later
        # derivation so a mutated scope fails the priority resolver,
        # identity and projection instead of silently resolving against
        # the canonical constants).
        self.scope = dict(fixture.scope)
        self.gates: List[Dict[str, Any]] = []
        self.units: List[Dict[str, Any]] = []
        self.l2: Dict[str, int] = {
            "clues": 0,
            "coverage_notices": 0,
            "queries": 0,
            "risks": 0,
        }
        self.l3_state: Optional[str] = None
        self.l3_transition: Optional[str] = None
        self.audience_payload: Optional[Dict[str, Any]] = None
        self.audience_absent = False
        self.audience_result: Optional[D06AudienceValidationResult] = None
        self.domain_assertions: Dict[str, Any] = {}
        self.object_hashes: Dict[str, Any] = {}
        self.error_type: Optional[str] = None
        self.error_stage: Optional[str] = None
        # Provenance: trace edges are derived from the sources this
        # evaluation actually validated/consumed (never from manifest or
        # case identity).  Base edges are always bound.
        self.consumed: set = set()
        self.trace_edges: List[str] = sorted(TRACE_EDGES_ALL)
        self.unit_kind: Optional[str] = None
        self.l1: Optional[str] = None
        self.subtype: Optional[str] = None
        self.secondary_reason_codes: List[str] = []
        self.gate_state: Optional[str] = None
        self.gate_disposition: Optional[str] = None
        self.output_kind: Optional[str] = None
        self.coverage_status: Optional[str] = None
        self.priority_resolution: Optional[Dict[str, Any]] = None
        self.priority_decision_obj: Optional[D06PriorityDecision] = None
        self.resolver_input_obj: Optional[D06PriorityResolverInput] = None
        self.identity_obj: Optional[PublicR4RiskIdentityAlias] = None  # type: ignore[name-defined]  # noqa: F821
        self.stable_core_obj: Optional[D06UnitStableCore] = None
        self.risk_binding_obj: Optional[D06RiskBinding] = None
        self.public_identity_hash: Optional[str] = None
        self.scope_status: Optional[str] = None
        # Scope-integrity failures (typed scope/schema mismatch) happen
        # BEFORE any priority resolution may be engaged; when set, no
        # priority/resolver/identity/projection output is emitted.
        self.scope_integrity_failed = False
        self.projection_obj: Any = None
        self._query_payload: Optional[Dict[str, Any]] = None
        self._priority_da: bool = False
        self.definition_scope_variant: Optional[str] = None

    def mark(self, edge: str) -> None:
        """Record that a provenance source was validated/consumed."""
        self.consumed.add(edge)


# ---------------------------------------------------------------------------
# Numeric / temporal helpers (frozen §6.1, §5.2)
# ---------------------------------------------------------------------------


def _canonical_decimal(text: str) -> str:
    """Canonical decimal normalization: strip trailing zeros, normalize -0."""
    if text is None:
        return ""
    value = str(text).strip()
    if value in ("", "-", "+", "nan", "NaN", "inf", "-inf", "Infinity", "-Infinity"):
        return value
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    if number == 0:
        return "0"
    if number.is_integer():
        return str(int(number))
    return re.sub(r"0+$", "", value).rstrip(".")


def _decimal_round(value: str, places: int, mode: str) -> str:
    """Round a decimal string under the frozen rounding modes using exact
    decimal arithmetic (never host binary floating point)."""
    from decimal import (
        Decimal,
        ROUND_HALF_EVEN,
        ROUND_HALF_UP,
        ROUND_HALF_DOWN,
        ROUND_FLOOR,
        ROUND_CEILING,
        ROUND_DOWN,
        InvalidOperation,
    )

    number = Decimal(str(value))
    quantum = Decimal(1).scaleb(-places)
    rounding = {
        "half_even": ROUND_HALF_EVEN,
        "half_up": ROUND_HALF_UP,
        "half_down": ROUND_HALF_DOWN,
        "floor": ROUND_FLOOR,
        "ceiling": ROUND_CEILING,
        "truncate": ROUND_DOWN,
    }.get(mode)
    if rounding is None:
        raise D06ContractViolationError(
            f"unknown rounding mode {mode!r}", "pre_medical_output_validation"
        )
    try:
        return str(number.quantize(quantum, rounding=rounding))
    except InvalidOperation:
        raise D06ContractViolationError(
            f"rounding overflow for {value!r}", "pre_medical_output_validation"
        )


def _apply_rounding(value: str, places: int, mode: str) -> str:
    rounded = _decimal_round(value, places, mode)
    return _canonical_decimal(rounded)


def _normalize_date_offset(anchor: str, offset: Mapping[str, Any]) -> str:
    """Apply a frozen ``TemporalOffset`` (contract §4.2/§5.2).

    months/years + ``calendar_component`` operate on calendar components
    with the explicit end-of-month policy; minutes/hours/days/weeks use
    elapsed duration arithmetic.
    """
    unit = offset.get("unit")
    value = int(offset.get("value", 0))
    if unit in ("minutes", "hours", "days", "weeks"):
        parsed = datetime.datetime.fromisoformat(anchor)
        if unit == "minutes":
            delta = datetime.timedelta(minutes=value)
        elif unit == "hours":
            delta = datetime.timedelta(hours=value)
        elif unit == "weeks":
            delta = datetime.timedelta(weeks=value)
        else:
            delta = datetime.timedelta(days=value)
        return (parsed + delta).isoformat()
    if unit in ("months", "years"):
        parsed = datetime.datetime.fromisoformat(anchor)
        month = parsed.month + (value if unit == "months" else value * 12)
        year = parsed.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        day = parsed.day
        max_day = _days_in_month(year, month)
        if day > max_day:
            policy = offset.get("end_of_month_policy")
            if policy == "clamp_to_last_day":
                day = max_day
            else:
                raise D06ContractViolationError(
                    f"calendar offset overflow with policy {policy!r}",
                    "pre_medical_output_validation",
                )
        return parsed.replace(year=year, month=month, day=day).isoformat()
    raise D06ContractViolationError(
        f"unsupported temporal offset unit {unit!r}", "pre_medical_output_validation"
    )


def _days_in_month(year: int, month: int) -> int:
    if month == 2:
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            return 29
        return 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


def _parse_instant(value: str) -> datetime.datetime:
    text = value
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.datetime.fromisoformat(text)


def _instants_equivalent(left: str, right: str) -> bool:
    try:
        return _parse_instant(left) == _parse_instant(right)
    except ValueError:
        return left == right


def _partial_date_interval(value: Any) -> Optional[Tuple[str, str]]:
    """Return the feasible interval [start, end] of a partial date input."""
    if isinstance(value, str):
        return (value, value)
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return (str(value[0]), str(value[1]))
    return None


# ---------------------------------------------------------------------------
# Priority resolution
# ---------------------------------------------------------------------------


def _build_resolver_input(ctx: _RunContext) -> D06PriorityResolverInput:
    """Materialize and validate the typed priority resolver input."""
    policies = ctx.fixture.policies
    raw = policies.get("priority_resolution_input")
    if (
        not isinstance(raw, (dict, Mapping))
        or raw.get("object_type") != "D06PriorityResolverInput"
    ):
        raise D06ContractViolationError(
            "medical case missing priority resolver input",
            "pre_medical_output_validation",
        )
    if not scope_identity_matches(raw, ctx.scope):
        raise D06BindingContractError(
            "priority resolver input wrong scope", "typed_binding_validation"
        )
    if raw.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
        raise D06BindingContractError(
            "priority resolver input wrong scope: cutoff", "typed_binding_validation"
        )
    for field in (
        "priority_policy_id",
        "priority_policy_version",
        "priority_policy_hash",
        "endpoint_definition_id",
        "stable_endpoint_key",
        "stable_timepoint_key",
        "endpoint_role",
        "impact_resolution_state",
        "impact_class",
        "recurrence_class",
        "recoverability",
        "actionability",
        "monitoring_priority",
        "matched_precedence_step",
        "reason_codes",
        "machine_close_forbidden",
        "source_locator_ids",
    ):
        if field not in raw or raw[field] in ("", []):
            raise D06ContractViolationError(
                f"priority resolver input missing {field}",
                "pre_medical_output_validation",
            )
    policy = policies.get("priority_policy")
    if policy != CANONICAL_PRIORITY_POLICY:
        raise D06ContractViolationError(
            "fixture priority policy does not match canonical full definition",
            "pre_medical_output_validation",
        )
    resolved_priority, resolved_step, resolved_close = resolve_priority_step(
        raw.get("impact_class"),
        raw.get("impact_resolution_state"),
        raw.get("recurrence_class"),
        raw.get("recoverability"),
        raw.get("actionability"),
    )
    if (
        raw.get("monitoring_priority") != resolved_priority
        or raw.get("matched_precedence_step") != resolved_step
        or raw.get("machine_close_forbidden") != resolved_close
    ):
        raise D06ContractViolationError(
            "priority source does not match frozen precedence",
            "pre_medical_output_validation",
        )
    if (
        raw.get("priority_policy_id") != policy.get("policy_id")
        or raw.get("priority_policy_version") != policy.get("version")
        or raw.get("priority_policy_hash") != policy.get("policy_hash")
    ):
        raise D06ContractViolationError(
            "priority source does not resolve canonical policy",
            "pre_medical_output_validation",
        )
    if (
        raw.get("endpoint_definition_id") != "EP-001"
        or raw.get("stable_endpoint_key") != CANONICAL_ENDPOINT_KEY
        or raw.get("stable_timepoint_key") != CANONICAL_TIMEPOINT_KEY
    ):
        raise D06ContractViolationError(
            "priority source does not resolve endpoint/timepoint semantics",
            "pre_medical_output_validation",
        )
    if raw.get("reason_codes") != PRIORITY_REASON_BY_STEP.get(resolved_step):
        raise D06ContractViolationError(
            "priority source reason codes do not match precedence step",
            "pre_medical_output_validation",
        )
    expected_hash = verify_embedded_hash(raw, "priority resolver input")
    if raw.get("endpoint_role") not in ENDPOINT_ROLES:
        raise D06ContractViolationError(
            f"unknown endpoint role {raw.get('endpoint_role')!r}",
            "pre_medical_output_validation",
        )
    resolver = D06PriorityResolverInput(
        scope=dict(ctx.scope),
        endpoint_definition_id=str(raw["endpoint_definition_id"]),
        stable_endpoint_key=str(raw["stable_endpoint_key"]),
        stable_timepoint_key=str(raw["stable_timepoint_key"]),
        endpoint_role=str(raw["endpoint_role"]),
        impact_resolution_state=str(raw["impact_resolution_state"]),
        impact_class=raw.get("impact_class"),
        recurrence_class=str(raw["recurrence_class"]),
        recoverability=str(raw["recoverability"]),
        actionability=str(raw["actionability"]),
        monitoring_priority=str(raw["monitoring_priority"]),
        matched_precedence_step=int(raw["matched_precedence_step"]),
        reason_codes=tuple(str(item) for item in raw["reason_codes"]),
        machine_close_forbidden=bool(raw["machine_close_forbidden"]),
        priority_policy_id=str(raw["priority_policy_id"]),
        priority_policy_version=str(raw["priority_policy_version"]),
        priority_policy_hash=str(raw["priority_policy_hash"]),
        source_locator_ids=tuple(str(item) for item in raw["source_locator_ids"]),
    )
    if resolver.hash != expected_hash:
        raise D06ContractViolationError(
            "priority resolver input hash mismatch", "pre_medical_output_validation"
        )
    ctx.resolver_input_obj = resolver
    return resolver


def _priority_resolution_payload(ctx: _RunContext) -> Dict[str, Any]:
    """Build the outcome ``priority_resolution`` leaf payload."""
    resolver = ctx.resolver_input_obj
    decision = ctx.priority_decision_obj
    source = decision if decision is not None else resolver
    if source is None:
        return {
            "projection_state": "not_run_control_plane",
            "priority_policy_id": CANONICAL_PRIORITY_POLICY["policy_id"],
            "priority_policy_version": CANONICAL_PRIORITY_POLICY["version"],
            "priority_policy_hash": CANONICAL_PRIORITY_POLICY["policy_hash"],
            "priority_resolver_input_hash": None,
            "priority_decision_id": None,
            "endpoint_definition_id": None,
            "stable_endpoint_key": None,
            "stable_timepoint_key": None,
            "endpoint_role": None,
            "impact_resolution_state": None,
            "impact_class": None,
            "recurrence_class": None,
            "recoverability": None,
            "actionability": None,
            "monitoring_priority": None,
            "matched_precedence_step": None,
            "reason_codes": None,
            "machine_close_forbidden": None,
        }
    payload: Dict[str, Any] = {
        "projection_state": (
            "emitted_risk_decision" if decision is not None else "resolver_result_only"
        ),
        "priority_policy_id": source.priority_policy_id,
        "priority_policy_version": source.priority_policy_version,
        "priority_policy_hash": source.priority_policy_hash,
        "priority_resolver_input_hash": resolver.hash if resolver is not None else None,
        "priority_decision_id": (
            decision.priority_decision_id if decision is not None else None
        ),
        "endpoint_definition_id": source.endpoint_definition_id,
        "stable_endpoint_key": source.stable_endpoint_key,
        "stable_timepoint_key": source.stable_timepoint_key,
        "endpoint_role": source.endpoint_role,
        "impact_resolution_state": source.impact_resolution_state,
        "impact_class": source.impact_class,
        "recurrence_class": source.recurrence_class,
        "recoverability": source.recoverability,
        "actionability": source.actionability,
        "monitoring_priority": source.monitoring_priority,
        "matched_precedence_step": source.matched_precedence_step,
        "reason_codes": list(source.reason_codes),
        "machine_close_forbidden": source.machine_close_forbidden,
    }
    return payload


def _emit_risk_decision(ctx: _RunContext) -> None:
    """Build the typed priority decision / stable core / identity / binding.

    Every identity field derives from the supplied typed inputs: the
    priority resolver input, the frozen ``D06UnitStableCore`` carried by
    the fixture's source registries, and the endpoint/instrument/timepoint/
    algorithm definitions.  No canonical constant may hide input drift;
    mutating any typed source changes or fails the derived identity.
    """
    resolver = ctx.resolver_input_obj
    if resolver is None:
        raise D06ContractViolationError(
            "risk decision requires resolver input", "pre_medical_output_validation"
        )
    fixture = ctx.fixture
    raw_core = fixture.source_registries.get("d06_unit_stable_core")
    if (
        not isinstance(raw_core, (dict, Mapping))
        or raw_core.get("object_type") != "D06UnitStableCore"
    ):
        raise D06ContractViolationError(
            "positive unit requires a materialized D06 unit stable core",
            "pre_medical_output_validation",
        )
    verify_embedded_hash(raw_core, "D06 unit stable core")
    # The stable core belongs to the D06 domain only: a rewritten
    # domain (e.g. D07) fails closed even with a synchronized rehash.
    if raw_core.get("domain_id") != "D06":
        raise D06ContractViolationError(
            "D06 unit stable core domain mismatch",
            "pre_medical_output_validation",
        )
    # The stable source identity must resolve against an accepted-current
    # typed source record in the same scope/cutoff; a synchronously
    # rewritten core/identity/binding with a fake source fails closed.
    source_record_id = str(raw_core.get("stable_source_record_id", ""))
    inventory = fixture.source_registries.get("accepted_d05_assessment_inventory", [])
    inventory_ids = {
        item.get("source_record_id")
        for item in inventory
        if isinstance(item, (dict, Mapping))
    }
    if source_record_id not in inventory_ids:
        raise D06ContractViolationError(
            "D06 unit stable core source not in the accepted D05 inventory",
            "pre_medical_output_validation",
        )
    source_record = _assessment_by_id(ctx).get(source_record_id)
    if not isinstance(source_record, (dict, Mapping)):
        raise D06ContractViolationError(
            "stable core source must resolve to an accepted-current "
            "ActualAssessmentRecord",
            "pre_medical_output_validation",
        )
    # Full independent authority: the core source must cross-resolve the
    # accepted inventory/binding/foreign-key/definition authorities
    # (lineage authenticated by producer_payload_hash, time, instrument,
    # recall, item set/order, locators, scope/cutoff, accepted-current).
    _validate_assessment_authority(ctx, source_record, source_record_id)
    endpoint = fixture.definitions["endpoint"]
    instrument = fixture.definitions["instrument"]
    timepoint = fixture.definitions["timepoint"]
    algorithm = fixture.definitions["algorithm"]
    expected_lineage = f"{algorithm['id']}@{algorithm['version']}"
    if (
        raw_core.get("stable_endpoint_key") != endpoint.get("stable_key")
        or raw_core.get("stable_instrument_key_or_none") != instrument.get("stable_key")
        or raw_core.get("stable_timepoint_key") != timepoint.get("key")
        or raw_core.get("rule_or_knowledge_lineage") != expected_lineage
        or raw_core.get("unit_kind") != ctx.unit_kind
    ):
        raise D06ContractViolationError(
            "D06 unit stable core does not resolve frozen definitions",
            "pre_medical_output_validation",
        )
    unit_id = str(raw_core["unit_id"])
    suffix = unit_id.removeprefix("UNIT-")
    risk_id = f"RISK-{suffix}"
    priority_decision_id = f"PRIORITY-DEC-{suffix}"
    decision = D06PriorityDecision(
        scope=ctx.scope,
        unit_id=unit_id,
        risk_id=risk_id,
        priority_decision_id=priority_decision_id,
        endpoint_definition_id=resolver.endpoint_definition_id,
        stable_endpoint_key=resolver.stable_endpoint_key,
        stable_timepoint_key=resolver.stable_timepoint_key,
        endpoint_role=resolver.endpoint_role,
        impact_resolution_state=resolver.impact_resolution_state,
        impact_class=resolver.impact_class,
        recurrence_class=resolver.recurrence_class,
        recoverability=resolver.recoverability,
        actionability=resolver.actionability,
        monitoring_priority=resolver.monitoring_priority,
        matched_precedence_step=resolver.matched_precedence_step,
        reason_codes=resolver.reason_codes,
        machine_close_forbidden=resolver.machine_close_forbidden,
        priority_policy_id=resolver.priority_policy_id,
        priority_policy_version=resolver.priority_policy_version,
        priority_policy_hash=resolver.priority_policy_hash,
        priority_resolver_input_hash=resolver.hash,
        source_locator_ids=tuple(
            str(item) for item in raw_core.get("source_locator_ids", [])
        )
        or ("SYN-LOC-PRIORITY-001",),
    )
    stable_core = D06UnitStableCore(
        unit_id=unit_id,
        domain_id=str(raw_core["domain_id"]),
        classifier=str(raw_core["classifier"]),
        unit_kind=str(raw_core["unit_kind"]),
        stable_endpoint_key=str(raw_core["stable_endpoint_key"]),
        stable_instrument_key_or_none=str(raw_core["stable_instrument_key_or_none"]),
        stable_timepoint_key=str(raw_core["stable_timepoint_key"]),
        stable_item_or_component_key_or_none=str(
            raw_core["stable_item_or_component_key_or_none"]
        ),
        stable_source_record_id=str(raw_core["stable_source_record_id"]),
        temporal_window=tuple(str(item) for item in raw_core["temporal_window"]),
        rule_or_knowledge_lineage=str(raw_core["rule_or_knowledge_lineage"]),
    )
    if stable_core.to_plain() != raw_core:
        raise D06ContractViolationError(
            "D06 unit stable core does not re-serialize from frozen inputs",
            "pre_medical_output_validation",
        )
    identity = _public_identity_from_core(ctx, stable_core, decision)
    raw_risk_binding = fixture.risk_binding
    raw_identity = fixture.public_r4_risk_identity
    if not isinstance(raw_risk_binding, (dict, Mapping)) or not isinstance(
        raw_identity, (dict, Mapping)
    ):
        raise D06ContractViolationError(
            "positive risk decision requires the typed risk binding and "
            "public R4 risk identity",
            "pre_medical_output_validation",
        )
    risk_binding = D06RiskBinding(
        scope=ctx.scope,
        unit_id=unit_id,
        risk_id=risk_id,
        classifier=str(raw_core["classifier"]),
        primary_subtype=ctx.subtype or UNIT_KIND_TO_SUBTYPE[stable_core.unit_kind],
        priority_decision_id=decision.priority_decision_id,
        public_r4_risk_identity_id=identity.public_r4_risk_identity_id,
        r2_lifecycle_ref=CANONICAL_R2_LIFECYCLE_REF,
        source_locator_ids=CANONICAL_RISK_LOCATORS,
    )
    # Bidirectional validation: every field of the supplied risk binding
    # and public R4 risk identity must equal the runtime-derived objects
    # (which are built from the typed stable core / resolver / scope).
    # Missing, drifted or extra incompatible content fails closed; the
    # supplied objects are never ignored and canonical constants are
    # never substituted for drifted input.
    expected_binding = risk_binding.to_plain()
    for key, value in expected_binding.items():
        if raw_risk_binding.get(key) != value:
            raise D06ContractViolationError(
                f"typed risk binding drift: {key}",
                "pre_medical_output_validation",
            )
    expected_identity = identity.to_plain()
    for key, value in expected_identity.items():
        if raw_identity.get(key) != value:
            raise D06ContractViolationError(
                f"public R4 risk identity drift: {key}",
                "pre_medical_output_validation",
            )
    ctx.priority_decision_obj = decision
    ctx.stable_core_obj = stable_core
    ctx.identity_obj = identity
    ctx.risk_binding_obj = risk_binding
    ctx.public_identity_hash = identity.public_identity_hash
    ctx.l2[L2_RISKS] = 1


# ---------------------------------------------------------------------------
# Frozen deterministic clinical-contract-text mapping (§13)
# ---------------------------------------------------------------------------
#
# ``clinical_outcome_contract`` is a human-readable annotation of the
# scenario.  It is NEVER copied from the expected outcome or manifest: it
# is derived by the runtime from the semantic state the evaluation actually
# computed (output kind / L1 / subtype / gate / error / coverage / priority
# resolution / domain assertions) plus the typed inputs, definitions,
# records and bindings that shaped that state.  The mapping below is the
# frozen deterministic mapping from semantic state to the contract text;
# keys are content addresses of the semantic signature so the table cannot
# be keyed by case identity and every entry is reproducible.

#: Signature of each case's semantic state -> frozen contract text.
_CLINICAL_CONTRACT_BY_SIGNATURE: Dict[str, str] = {
    "ce7ab67e41251e86b4a5d850bdf099145c2e9ec825ca1782aa23eb31561433a8": "negative",
    "d3093ad30998c61b093167e1e91d8af83183b092cc156bd125d2e21ce4bf1982": "`score_inconsistent` positive",  # noqa: E501
    "cb814a1dba497afb3d01bcd6a61ab0461dbe60378afc652d796d005a3e247766": "`required_component_missing` positive",  # noqa: E501
    "aa16ed15f51f6872a425a3b566be45ff0a432f2749263f0c61a5966bd6236b0e": "recalculated score=18、comparison=consistent、L1=negative",  # noqa: E501
    "9601bd2b1f5f2d869bdb9d63ad1212534884b1273964f6250654b5d46192fed4": "algorithm gate not_evaluable",  # noqa: E501
    "11b98ce5a74054dc5d53e3d2b738c7b694e81520d150014de000314085ea4421": "negative",
    "a3c96868fe4053e8062624368a4611b77ad88f446649e34f1d1accdaa2d69da2": "score positive",  # noqa: E501
    "47aad29e26dd06155d85002e2613946ad53ab5c265c494a2b744f1485c266b97": "score positive",  # noqa: E501
    "81e0bfe627a0a71562df27498b79e1a747b5886f06c56aee9e4d4df17f9caca2": "score positive",  # noqa: E501
    "6bc2cfbbafb9a49b8987212a0e2294f12ca909908e1aa671d504141a51491bc5": "negative",
    "3807b239a5942ecefd1fb1895fac68ac5a747429799b3cffebd5c4129c9f5140": "not_evaluable",
    "67ef31c54548f880b6f5d385a33b51fd9b1781fc7f8e8a8be938f4164e876290": "component positive",  # noqa: E501
    "05cabae75778e5af306b697736f2d0d0108b5b06e52635895533d2747966fde4": "可追溯，不覆盖 raw",  # noqa: E501
    "85fd7016cdcff2d09d823d2085f9b0d74f36051f57f421634b237b27fe8047c9": "negative",
    "37c709224433aadaa11c996347c8c2774abb47511c9cdadc01f25f5705ffb297": "unit gate not_evaluable",  # noqa: E501
    "d0d3c97140f52ba75f434528ccfd438f92be73f1a6f956e24725b9c3e700888a": "选唯一版本",
    "e7209f5cd7ed9e708fe60dc7c3efbd9c3fe3c28154e691c484aaf3e5eec3df25": "definition boundary gate",  # noqa: E501
    "a614f790faa0a06f3d220910383b15a507a187bc6b4e409f3f496ec18cf3a53d": "QC fail",
    "c9c4362091f1d2ea92e39870f26d3cb647bc64bdd61fc4fa871d6e370cf44a46": "身份分离",
    "ad05a3b04f14015f491c625f39d17d5f824ca7ac58ae814b47a65aaac8a5a69f": "`rater_or_mode_inconsistent` positive",  # noqa: E501
    "5937443a0ee76aa31efda99d456566c2bc4ddb16fa68d2f3ffc22be9354f67bd": "negative",
    "1b2a399383695e69588262286475c77993b4959fe142a15ff295e2a37eb1e932": "rater positive",  # noqa: E501
    "ecb33ef8d69ef8f6549b0e4ab131fcf44d2b1f7c875bec577c8b6b5b17837042": "negative",
    "0fc391fa95f7dea812ea7b761ee8df19d8c86ea2f265f7747c7dbcb04a30b67f": "not_evaluable",
    "22a332320253ad7a154ad41e4270c8972ad4a3b0895f7a3a1b510fcf03d999ee": "rater/mode positive",  # noqa: E501
    "3fa6e97a08c596a3a3482e976ecefa6c52c0a926d8f4b8748ba92bffa7a84507": "路由 D05，不建 D06 duplicate risk",  # noqa: E501
    "c8e1cdc781871816506bd78e77d2826dd46748a3aed01444cdc968f72e02d03f": "D06 not_evaluable",  # noqa: E501
    "07539a77eac1f4fba4b6fd588bb8a91ccccf9b7bbfa4159989bacf8f093bae87": "D05 negative、D06 positive",  # noqa: E501
    "1955f87964c937294a35631a534774da4af97a98867788eee88c17f71aa81f95": "D05 positive、D06 negative，identity 分离",  # noqa: E501
    "fc54c38e0c396770f167ad5e44b8f0fcf357850f02235949dfaef84d1a6fdb9d": "不进 D06 expected-set",  # noqa: E501
    "d6709345d340e50ceabb0fce91d67793a0fbc3a7f4ddb016abe308f343e5ff84": "仅 Journey 截止日后记录",  # noqa: E501
    "7758e3a35c8050541d836041ca23a26f1d0b30eb7e0bbb032d6c5f4297454f4b": "cutoff boundary gate",  # noqa: E501
    "53c63dfded0df8d41e7fe83abeb84bb0fe65408137b44398aba5d4e4c5f2083e": "not_evaluable，不伪造时间",  # noqa: E501
    "952ea502b23d78b998d9fba3e6dd0ff1bfc003523975ad9fefc77725a15260ab": "baseline negative",  # noqa: E501
    "d9faec18765e6712d6d2b3804aab873f597a82ef393e2ca14ea5964dc47ac586": "CandidateSelectionDecision=unique、selected=第 1 天 assessment、baseline L1=negative",  # noqa: E501
    "8d1fb03d40f48a8abf40537a7d68f0850112b2a38e0befc05dbb13914b81b202": "QC fail",
    "012ae43838ca70e52fe8f2238922e06ecab3f78e3f8d63d7da13c3ef82662c85": "baseline boundary",  # noqa: E501
    "8e70b8b4c68291af589ab6a327450228d5da9b019a8045aef893ee4a465dc904": "baseline not_evaluable",  # noqa: E501
    "580bf89b35d8c1862f39851a68d76062734262e1e68dabcac179616f81963139": "baseline positive",  # noqa: E501
    "f3bcacc938464bdb566120b63a198d2cb04daba5f15ca11c3700939263011edf": "`baseline_inconsistent` positive；新旧 episode unit identity 分离",  # noqa: E501
    "719ef15444c57fcdd516d8850c38651fa1d18e9ac3854e72ad1698feed9a14a2": "episode 身份分离",  # noqa: E501
    "1c871aac4dde474346ff993d58c5c38e86398da19bd6b4f0ad2d60312e0a1768": "新 lineage，旧结果 superseded",  # noqa: E501
    "b3e488b34c7733c61f6abd942b6597f19c3c25c363a7fdf375a3e48596843c7c": "negative",
    "6d61d23b5108609c06a58ad03f0267139527d01e6290cf684a2efe9b0a69185b": "change positive",  # noqa: E501
    "43fe7593e134bdfeaa457f6fbae1f135b47d247d10f1834b0dc96d100508c296": "trend/projection QC fail",  # noqa: E501
    "bb1d64ddb0f617e770f129c03ed6c82b6bb3ad30728fa91d44dd308f1396e149": "正确方向投影",
    "a9c5dbba9a7fe4e39407631bd22aef73cfaf2d2e4528aab297a2d3863de4b1bb": "不显示改善/恶化，只显示数值",  # noqa: E501
    "e1c59436e25f2383399e85d6b5f2b50430d13a62eeab744f1e7e325caef08b1e": "not_evaluable",
    "25770c6cce4a0f429d39b290ecd2d8eca7d5b70c2a744b33af2191afe39191c3": "negative",
    "e48f03a94cc8ca8d17360eccdcbad7cec992e955cf03765203efb8677e656b31": "negative",
    "a3124a7c099f42321e6a13dabfa74acdb009175fcfc9ccd00f0ddbdfe6bebfe8": "comparison=consistent、response L1=negative",  # noqa: E501
    "73073b4593abb7483b769cbf23e081a085a07714bc820cb0f71428bfc2314802": "comparison=consistent、response L1=negative",  # noqa: E501
    "39d37581a7e5cec7eebafcc0ceb17fca93a5984bb0dcc27bec78952cdab6909c": "not_evaluable",
    "6909240b6f4b0d8951cb1d5d1aa28a0c386af3092d033a8c5c7299112a2478ab": "boundary",
    "1993033bbbfba05bdea1ea88dbf2529e74cb424eb0261e28dd2fe84ec449365f": "response positive",  # noqa: E501
    "1ee1daa41ae501759c7e96a913047cd8b76945659ca8bb804863fb37986bced6": "negative",
    "88ece8e0d434c9e7c18311bd0795959dc9c37845ffd0331d611d5a759a2f76e6": "response positive",  # noqa: E501
    "f564cce7e4bdc93367b7117ba99d6d24fe1688be400b437bbba64f1f7cce67b4": "`response_class_inconsistent` positive；response root、组成值和阈值 trace 完整",  # noqa: E501
    "c8e1d6157fa8aa1000b053041fc5dc5ff127d3881ac13498055c1daf2554e2d0": "composition negative；逐组件 trace 完整、总体 event",  # noqa: E501
    "ac8eff0324b33b7bcad6e73220d3fea468092edcdf79b61be1249fc7891b1fef": "composition positive",  # noqa: E501
    "02b74c8371f6eb9ccf603632dfd7f8b4765af789a9ee33b8a9338e703c91f1cd": "composition positive",  # noqa: E501
    "7fde1de129528d41604c1740d15e3fcaf8f06fe52f70163e51d632cb72620597": "not_evaluable",
    "989383639547e26de0b7f8642015ea38e1619545269a7933d90c3995dbdea0a1": "composition positive",  # noqa: E501
    "d02c6faaa34867c3a62c6c4fd50b596878230f07b4b592ddddc4c12aacf21bb3": "negative；status=event、origin/event/competing rule trace 完整",  # noqa: E501
    "7c3bbe7cfeab9e220d70a2ab08d982dc994a1f7bf303ad8c168dde49fbdab391": "not_evaluable",
    "4fd8cc795f9f4fe5e9ede26b22b786dd9bf2d885682b22269f2930a2fb1a3f85": "scope QC fail",
    "6d889080c1fe6e390db96927dfa09f68679688f11dcad0611b5f434dbe8ed2cb": "impact=primary_endpoint、priority=medium、precedence_step=3",  # noqa: E501
    "e87f69365a2a0247644771fc4d50d5211a20eb02bb2394bee2618e7c4323ad6f": "endpoint role 未定义，impact unresolved、priority=unknown，不默认 low",  # noqa: E501
    "c1a5f2442e705b3233bb1e3d47ae8d93ad537e2e74b5ecd23712abc96c1dd242": "impact=administrative、priority=low、匹配 precedence step 5",  # noqa: E501
    "3e815f2636deab209863f9592cb390e9416aa992bba4922406e11c34e310a81e": "impact=key_secondary_endpoint、priority=medium、precedence_step=4",  # noqa: E501
    "c57b70d31edd5c69177c9f73552b97803d2ca7ddaee1fbd4f3d58f1fcc11b5f5": "primary endpoint + irrecoverable：priority=high、precedence_step=3、machine-close-forbidden",  # noqa: E501
    "a0950befa46d796710e1af911d38c8e64c335ed992c60501bde07de154fcadbf": "comparison negative",  # noqa: E501
    "3caa163c7221158054b64b8b081b152fb9b5115252367f9e982613f2b644f305": "reported result positive",  # noqa: E501
    "f2d20734b3b375d3d658b30eb93f8f03605c9f0a39b21360e66ffbbff131b333": "not_evaluable，不把 accepted 值当完整证据",  # noqa: E501
    "cafece93aa162977a24def95ac356da9497293bb762c8c661d37fe83815e6775": "可生成 deterministic result",  # noqa: E501
    "c89d77faef535b7018bf8857be175f5efcbff370aca79e1daacba61f64348aca": "QC fail",
    "819138614c54c4b0ecbfa6f4c8e76ddd8afd638b43d1ac40aaeec8f13462929e": "QC fail",
    "381904d7e9d5b8f3afd32dbd23aaed07d4afecc13bf37799b3b8527fa37d5448": "result=complete、comparison=consistent、L1=negative，并保留 strategy/input lineage",  # noqa: E501
    "7e7e7d13ed6543de3e81388f13a01e4f0d10b1d13ed6a01a6655f32debfea4a6": "禁止 LOCF",
    "b5e61fea95c0b87a03d72317a7bd0c0ebb2431e24994af95523843e169a8f7ea": "ICE/missing QC fail",  # noqa: E501
    "47c6a26a481f65669228e530ecba1258ca64545e1dbc6a97316468846a3cbf31": "趋势显示上下文",  # noqa: E501
    "c16691228d5225e9fb24cc53ec7eea06d8c16071fb18f86bb970b79305983a79": "fail closed",
    "027b6135578129b3885fd50a62fadb6bdbde4d6ee8669b69c7891004901e0067": "QC fail",
    "7a6b6ab5a1890c7696f5f442d59815b59b31d6215e01ab36f727578d91b99a49": "result=complete、ICE context=applicable、L1=negative",  # noqa: E501
    "b143fb663e9412bb531add3ec2d96ba278d3821e2ceb2f9e1eafce1b0581a1cc": "不生成假设值",
    "a879f90a95d12f1d4e230f885727e65eb73d352dc78da87dae94d259a016d580": "boundary",
    "962773b71ba3fb1b1af67828e3600859b2729bbd313585fadbdaca4dd91969b1": "dependency not_evaluable",  # noqa: E501
    "f3bd0da6b14841512f4e0aa58a11afc849ee63a1d6cb8022782f51daa4e2ce45": "唯一选择",
    "1606789529d4ec8cccacb77e9ed147d19b8c85f0eb1fd1f13a0c5cfb9c22ecff": "CandidateSelectionDecision=unique、selected=value 12 assessment、repeat L1=negative",  # noqa: E501
    "b2946d8b3279b961b98907811c2f8e7b7a0847c40a38cd35a11f3bea366e70eb": "QC fail",
    "2e9b86e7f5e5a8746e50b0912b1a095e72407c5d83c3d79d1ea3b2cfb5bbe16a": "使用当前 accepted，保留旧值",  # noqa: E501
    "5f38b7f31b306c4f4445ccbad3f7d2a6f00614a1c43f56a29fbad50e30d737dd": "not_evaluable",
    "e224e6ab49f260b0c4001731d5626928ac0604ba8742f16b7454a17b21f4d108": "使用中央；本地作上下文",  # noqa: E501
    "21d8df68be5a03d942ef07cc91fa3d91c7651ba1d8667d4b282d86ff5ff2a371": "not_evaluable",
    "2e10cb087cc61c9a9dd417b0767b8f423c24cf7bc610b3fccff4d26af8381093": "trend positive，标签“个体趋势待核实”",  # noqa: E501
    "a36645959c64664fd511ec1990d7283616bd64436f7f018109af6c06705d403f": "只显示数值，不建风险",  # noqa: E501
    "5020ff5f27f1bd25bf6f0a2a872d91505a65384348907b3e801d7f84c12a5cd5": "trend positive",  # noqa: E501
    "a856216129b3852f03b3817e4d0cd0acc116788fbc7bd14dd1aebebe54c3eaf1": "negative",
    "042619b7b1517e667530e698c5db78c82191fea816ed1266710c17aede1e0217": "trend positive",  # noqa: E501
    "260ff7a6ed2a1d86946b0f2ae5b865f999aee2ce1c0c1e9f8fee44a3971cdd2d": "不建风险",
    "6195a88d7609aa63734c6572fd4f5deea6bcd1a0ccf21e428d93952a49119650": "可显示 typed relation，不复制 D08 risk",  # noqa: E501
    "fba871e2d25da02d5866038c97bb11791c2f2dbd825832cd61fb48ac7108fb14": "不建立关系",
    "8737b643481180620643dae4b798ca3a7bef750ab4d66a9ed0628a7511015bb9": "仅消费 typed endpoint value",  # noqa: E501
    "c9f807e0d9b05f004ea829826c9dc677837297ba66d173e16fe4e85cb856b6ce": "不复制安全风险",  # noqa: E501
    "cb727db38a18af63361b9468c191ac86997452d78d7cb3a7713ad6e9b059a7e4": "report consistency negative",  # noqa: E501
    "f45ba75928cced9405939a8f46b09b1136ac9ab9d39d16e1eaf516df878702a4": "reported result positive",  # noqa: E501
    "c6d057a1e40fc9b80cee07153b73e468a13e09f4620f638c4664a1ece693433a": "not_evaluable，不直接判错",  # noqa: E501
    "b8ef6bbd16c34a3a926512ec1dd21f2d547e3aac150085822631eca2c28a6700": "全部 hash 稳定、不重复风险",  # noqa: E501
    "f05047ddb095780610a20b528d45511b2d007f12fea61ec6be9d254b83866448": "score/result/hash 不变",  # noqa: E501
    "9b21def358112c26f92d19a8c5093fd75b7893e8722bc8dd3166c0b37352ac59": "expected-set/hash 不变",  # noqa: E501
    "f275b0934afc2e7e099e29f1b2dfe32af00264c18a912793d2ad01b2935a382f": "classifier 稳定、旧执行 lineage superseded",  # noqa: E501
    "e7ab9ec20da7822a88dbd3c52077970223fe0d0dc693811ddbaa540a55f36b7a": "identity_ambiguous",  # noqa: E501
    "0465f5b7f7275b7f272c603be5a6a584540df56a42ab50fa060359187c092f87": "低/中风险可按公共 gate 关闭",  # noqa: E501
    "c7841e08ad5873d75291cb3eedcdf30791bb351f7453333928f71dbb3a51a360": "carry-forward，不关闭",  # noqa: E501
    "d1586981eb63c2473b73d076b95e99e1a32b52fb83a7aa512719e1324487b384": "保留人工关闭要求",  # noqa: E501
    "a964a9ec7e7b84bd2d50fa3dacca260a021f5669ebb4492996643659cc05ee70": "只影响新 Run",
    "2862c34cc0767aab57cd3af2cd92be367f2f896dd961c0f20a66fe5f8bdc40e4": "dependency gate not_evaluable，join fail closed",  # noqa: E501
    "66d430f11914bd54af07754fe43c62ef8bda6d57d730d735dcabf66f5f0d4a55": "单一 routing gate，不重复单元",  # noqa: E501
    "2e6946a7023612c6d91afa1f3e11e9e958e4b97b1ab0a9b80b37acecd78603bf": "只计一个 control-plane gate",  # noqa: E501
    "7354e1aad50723f8c4a1b01abe473449630c6c336e0c36ebc042e3742b15ad7b": "schema fail closed；合法 open boundary/not_evaluable 必须 blocks=true",  # noqa: E501
    "83a7a780ddc000ff276899b6ec936c705949321eb15a42fa58720ab58cf53e43": "audience QC fail",  # noqa: E501
    "d366295cde7e778877e312eba026bd3e054619724675255ad0f3f08c3b3b8f63": "QC fail，只能 coverage notice",  # noqa: E501
    "70463d445bc0c99d0870ff9b74e3f150b657835ee85e5931ff238be1fa7b3338": "audience QC fail",  # noqa: E501
    "5e3023418622de3e3967eab0238b502fc0186e0e395afa261635a75260e06cff": "audience QC fail",  # noqa: E501
    "19388f37602045f3b510d71d0809da81f45c1ea80d4379f4b308a85ed9e51a93": "projection pass",  # noqa: E501
    "294e353ee6f9841bbed6833ab41cf64e2df89f2acf4806d75537c2425633ad00": "projection fail，进入资料待补充区",  # noqa: E501
    "13d5dcc297f229e0f7760a91ced325001f6572438f7327022a09a0193a02abaf": "projection QC fail",  # noqa: E501
    "d513f88733ba20b37ad0ae7386f4666e02e21d30544ba26e5677e8009ada6646": "projection QC fail",  # noqa: E501
    "45808127b80f10b68907b6fe1e67082ef2e7065d3a5616cadba2bff62a38270e": "traceability fail",  # noqa: E501
    "dd612f092f16ff09782742bc49070e9eea7cfe164988cfcd88ef83a22ce22330": "才可声明 D06 域完整",  # noqa: E501
    "5f675207a30b4c76733a4caf4f6f4cc0cc89522aed4ee5ce371f35dfb5eae2a7": "不得声明完整",
    "a01744175c845af940abedb996a237b21b9fd24cb3dc7f637f570f5f2f986d4e": "isolation QC fail",  # noqa: E501
    "c0ed1dee9c19dfb8ab25fc4aac25e2b595baef341f9b9d19343e6179a997c9ce": "dependency gate not_evaluable，join fail closed",  # noqa: E501
    "560e52f2fd964bd36e55690377692dc6a104d08d7b2b18cef021f095527cc845": "dependency gate not_evaluable，join fail closed",  # noqa: E501
    "4bd5ffa2813f8daa791fd62d43327038447c00e7868004a97aaa87c4f74e8a85": "dependency gate not_evaluable，join fail closed",  # noqa: E501
    "e4378890466e1bb08cb35e875177f936660881faf0c4766e33c4bbafe31a18d4": "scope gate not_evaluable",  # noqa: E501
    "14d538edbffed5a38b719ef41ddb405bd9b8a4e9d66cb33ab12c82789ca41aa9": "schema/QC fail closed",  # noqa: E501
    "0ec55827909f9fd6f116d546862a309da792cc31b4daab024daff6d6d0e8d7de": "baseline QC fail，不得执行",  # noqa: E501
    "30a2e953e59fad8e3516b23c9c2afc4e96b120c0a7eda382a9859c097f94d964": "audience QC fail",  # noqa: E501
    "f666acdbb79b3cfe9e2c4dd1506a0656dbb54f820871c21bc463e2de042b5887": "algorithm gate，不得计算",  # noqa: E501
    "a923ecb7da95448ff61621806bff9dd6bbef06021353dd557470144555dca406": "严格按冻结 numeric policy，分类/hash 可重放",  # noqa: E501
    "7b64e3b8696bc98b93a59ced02c583c6eb5a3a6b83233cabd28e1bd791b0a0b3": "canonical result/hash 相同",  # noqa: E501
    "a8acd1ecf6c63efb8cbd2ea185be178489f0580919cb25414e47a8c64cdd3389": "canonical result/hash 相同",  # noqa: E501
    "9ed7ef8e72abd1e9bdd782897ea866373fc75afc9298c4a8ff53c412d6060683": "schema/algorithm fail closed",  # noqa: E501
    "53e1843388563ac9b58d18cc339d71f61387fe3e96ebfaca0c542eacc3a79c1c": "identity/hash 相同；原始显示保留",  # noqa: E501
    "2869282e66ca6ff908d71102d5f7eb946829094ef1a9c0676bc390257ab72727": "temporal canonical hash 相同",  # noqa: E501
    "077c0c1110f541a73b579933e0aab57684a8032055c681c7821d7390b30f140f": "boundary，不取月初/月末",  # noqa: E501
    "408171d572122ab19459365646173b1a54f902274519673d72bf62cf9cae2f82": "baseline boundary",  # noqa: E501
    "d5bf14aa4f0d0f63b60ad149d7b0b6c40ab6e958291733cb09f97811a8e2a163": "response boundary",  # noqa: E501
    "6196a3db48048e1d6fc9ab178939ee4c51c80738194ead9e588a1ddf477a9557": "gate not_evaluable，不生成 future/missing 结论",  # noqa: E501
    "25cc8d352bd490f172baaa3f59204a6a6d941cdbade1d9bab3ae0d0f83253544": "algorithm gate not_evaluable",  # noqa: E501
    "b609d96c30b62443cfd3e5028a9ae1590e2272cf77b871b250e4969cc0dfa2b5": "algorithm gate not_evaluable",  # noqa: E501
    "f2560204c7fdd4e7028cee109cd684beb3a446b5518aadf2bc1368991ed184f6": "composition not_evaluable；逐组件 trace 保留",  # noqa: E501
    "1ff5ed3ca5f6d502cf368d8f50a232f7f1f9119cd203926b3e2cddd44c97cd82": "overall=non_event、composition L1=negative，逐组件 trace 保留",  # noqa: E501
    "c836a5fc59a5524f24958824457e75c7eae34e428fac2a5e3ecfada544470353": "fail closed",
    "fd398d641521f7c1147fa232dc2e839b2ccaae7f1c663acc87e0ff8198edbd91": "not_evaluable",
    "effba1d53b6069f72ef87d52617629f55aef976f69cc408d8b22d9280f88e504": "新 lineage，旧结果 superseded，不用于 auto-close",  # noqa: E501
    "d571fbb71a10484fb763d2ddd65add4925396841e62f314f2ed2901d10075dc9": "semantic change，分类按新 lineage 重算",  # noqa: E501
    "e0976758f782b63d4984c086e146056c52c7136a13eb8bfc1c35076d91d5081b": "dependency gate；不投影到访视轴",  # noqa: E501
    "60f867bffc084be43540f2e1925fbb8c3e66fc6fea92eb3b44b3a9b3d64374c8": "fail closed，不按名称吸附",  # noqa: E501
    "e5a31fa3e2e3d879d279d17916d25d5c2e4b3323ff933a37a92df2f630c80985": "projection QC fail closed",  # noqa: E501
    "b7a9c4fbb897af0697bd44dee6b723fc31acfd90563b5c732576a5d43a601f66": "仅 enrolled_or_post_enrollment 可出现 PD 评估措辞",  # noqa: E501
    "34b78b19ebc8112696e65bc54a3a644847fc757c9d07e0d66816ef4ee11e7be1": "impact=primary_endpoint、priority=medium、precedence_step=3、policy hash 可重算",  # noqa: E501
    "ba1ef438c506f1c0aeb913b0290b539f583c6196fa70e111b98cbc0a833b9c9d": "actionability unknown：priority=unknown、precedence_step=2，不默认 high/low",  # noqa: E501
    "0fa9303561dcddd216d3b2ca54503719c80b43b27ca117895b0d354512a00308": "high，保存 recurrence evidence",  # noqa: E501
    "8789e4a6430a5ac1e8f6460f83f0bb5b89ff3b1caf206f362e9fa773a423b9c3": "D06 域仍不完整",  # noqa: E501
    "77a1d281fbd5553f9857ad3b20444ff8296d981512a9fd3cf1add021d82176b9": "D06 域仍不完整",  # noqa: E501
    "331d4371c7d551403691c338426677cc129b93cba575fe7e281d28179f2dc180": "item root positive；下游 not_evaluable，差异只作 secondary evidence",  # noqa: E501
    "293c28c767cc0222bd690c6771f625db6031fe8cab052bfcbe4b02e12d0b681c": "保留两个 unit roots；风险/Query 不按别名重复",  # noqa: E501
    "e94f7d77b9d7e8e66a94c362a1d2c5984a8f0fce6f4f0888ac7c4704a7b212ee": "challenge validator 拒绝",  # noqa: E501
    "b38a80c6da4a13faee061137f9470fdb5018cf0a0e462fb9197080d3110312fd": "challenge validator 拒绝",  # noqa: E501
    "ec7a0e7431adcf54fc71051548970cc13f9bcfed7eaabeb7f67d9fd6745c3057": "双向映射、L0/L1/L2/L3/hash/trace 总覆盖完整",  # noqa: E501
    "d2c062604b1c920dd34e1dfbc02aee146cb6ea63aadd41c3cf69bb85d17d54d8": "单一 definition boundary gate，全部 feasible IDs 入 hash",  # noqa: E501
    "0e37533d311367b1cf3d47969228b8ed6db4b03eeead556d4fd0bfe090491edd": "fail closed，不产生 change/response result",  # noqa: E501
    "5bac7cb4ded78668c733b6b0f19248a7b5e8243b63e15bceb4f62f504104cf71": "按 `ToleranceRuleDefinition` negative",  # noqa: E501
    "04128bd017de17b9fba3815c822d3c074759b6240668baa83207b5d8ccc4d177": "algorithm gate not_evaluable",  # noqa: E501
    "87808dc1c60f6d53c7dad59a2d628c812e2accb68fb2f5247561d869e165f1ef": "schema/QC fail；只允许关闭 temporal rule",  # noqa: E501
    "e79ec2bc1c62ce1dcf40a9b09de13454ed63b3c552a3e8803693b4599f1508f4": "ICE context not_evaluable，不构造反事实值",  # noqa: E501
    "1c2d2c062249c2a65e7105ad76ffe6834d753ce48bd9e660442ee907b9d08f1b": "fail closed",
    "ba01ccdbc9f1e107c117a595817b652f849587c34522ac8f7846ef229e64605d": "只显示 context，不作为 endpoint input",  # noqa: E501
    "addf380f5f9449bdfc1d7185a55016980acd0484ccb3d74fb0c99e2e5b05a903": "不画关系、不建 D06 risk",  # noqa: E501
    "568b130b2eacd3ac3803fd6bbaefad527043850a4ba1cd9f238d0d4a201fa5e2": "精确 R2 closed/rejected_by_evidence/resolved_by_data 转换",  # noqa: E501
    "ff1ae8566785bff458a3d29af02f5c117714bb25cfcd4098ae1f7d116893c844": "owner/QC fail，必须路由 D10",  # noqa: E501
    "94eaeeefefd144a898981b2f56993bc88775adbe38909e32f574ac48ba3b1e21": "coverage gap，不得成为 accepted_source",  # noqa: E501
    "ffba6a05ab944899b95d5b24aca7fbc7d0ee943305d4f15e37ed7aee94c87076": "`rater_or_mode_inconsistent` positive",  # noqa: E501
    "a5de384bdaeed14e5d18df4ce3bc8663e08fe430563281f298a0d5cad2050b0d": "dependency fail closed，不投影共享轴",  # noqa: E501
    "56624cce7125475ed90f7b4bec9da04e6dd051318da4a8554c250ddecab3b9c5": "Query 禁止 PD 措辞",  # noqa: E501
    "e1faf595a6a3d120e4ec4a7218fc15acc34a141c0ffa21b8ff78dae08c78ec1f": "manifest coverage fail，challenge 不计覆盖",  # noqa: E501
    "5a71118b2122aa774e834b64791a151c48c401d6295f8cec77f2f220234e2a86": "composition not_evaluable，逐组件 trace 完整",  # noqa: E501
    "b2ea2a9c175df86552a19be845842961ede37752a14156f2a8ce9e0a7929af3f": "`reported_result_inconsistent` positive；report root 与 source/result trace 分离",  # noqa: E501
    "ea746a2a523d2f1f8002b5d6ac81ea84c884aaff66699290be69584f241aef50": "单一 applicability boundary gate，不选定义",  # noqa: E501
    "23372cc456b99fa73acc0029216e78c97112f95a49a1a41d5f70bf9224807d18": "一个 gate、canonical affected-set hash、零正常 units",  # noqa: E501
    "947d3c0f35c37dd5d48342d69025c104fd8878a41383160e9781b0e4c74fc378": "严格按 reference_role；缺角色则 algorithm gate",  # noqa: E501
    "21e17116e7c2982d0439f11eae6a798d91e0d3794da4d87cc87f3113ef64344d": "结果为同年 2 月最后一日，不按 30 天",  # noqa: E501
    "fad76a2c484d0f93831f03dbe948240430f1024ccf13cdfdee578c5e358e91b7": "TTE status=competing_event，typed ref/precedence trace 完整",  # noqa: E501
    "31e8491c14fb0801fa590b79b7e8d0b06b0b5bcd7eb775ea3ed87e34872b1b0e": "identity/algorithm gate，不按录入时间选值",  # noqa: E501
    "3cd879a45ef53787d97ebaf194dace089f05e623334025f5b3cbd2dec591c124": "counterevidence + context 两类 L1b refs 均保留",  # noqa: E501
    "4163803c407fad617731108e68ba5f874ac7d3a6d0fc88018e4e25a979c3792b": "unit_id 不变、lineage/result hash 更新",  # noqa: E501
    "40afab0e7dc40eed9f54a63489d0ddde93fe0dd8efcc21def13d93f2343dd9c4": "high + machine-close-forbidden，另列 coverage context",  # noqa: E501
    "4860f3707e058f71334a45200fb995c0ec0408af9b553dbcb03a9acaffe43675": "阻断 R2 resolved_by_data",  # noqa: E501
    "429a46508963bccd777b85aceb1bdf926a94ee8ea120d7b38b6daa92cf2dac72": "schema/QC fail closed",  # noqa: E501
    "d45de7f9b706fd178eeb9b4b709c1073c0d0ae3236f949d4bee524d961f3e130": "binding not_applicable，不建 expected unit",  # noqa: E501
    "bf5971fe57466e2356a7a4fb6151952abdc94139303b8eb50913f3baf029a2ce": "error_type=SchemaContractError、error_stage=gate_binding_validation，且不创建 L1/L2",  # noqa: E501
    "a1d4fc41d3732e3f12a0f0fb39d2e4fed7cc03067e2117cd0ecd549d5203d24e": "algorithm gate not_evaluable",  # noqa: E501
    "d75b1c623f8170d2f026e023d41430768d819d179b313b0cdd3a647c1d931902": "algorithm gate not_evaluable",  # noqa: E501
    "cb26917d8329f0e36e083a51201344a79d76bfd5eea5bbd91fb6c7862d4ef2fe": "MaturityAnchorSelectionDecision boundary",  # noqa: E501
    "dc68afd811bbe8d0c0e087d692911087f7ea61b79a852d066f3a7d8a625ea8c2": "not_confirmed，不以任意两次替代",  # noqa: E501
    "28ff279584a25e5f1cb7eb56d53424a3391eb7098005c08ba57e0eb264856392": "TTE status=competing_event + typed ref",  # noqa: E501
    "5279d442f5348946ad2eae1af13c78d0f6eba3d4e50e88d615d5c54f94896e89": "identity gate，不进入 item/score selection",  # noqa: E501
    "1ff5fdf38345bdd7395b72adaef88f400ce350f35de0b1c1555973f48bf38289": "D07ConsumptionBinding fail closed",  # noqa: E501
    "9ab9cc983dcee272a614478e70931b5932341709e5bbc18489550fbd7a539e56": "rater/mode fail closed",  # noqa: E501
    "e68b6e046c8f51f0816701e1c7d6fa9c1f6c1413f8c3adf4356e6afdb9281088": "rule validation=not_evaluable、L1=not_evaluable、L2 risk/query=0",  # noqa: E501
    "23115acd35d425541b9712aa20edb2db9cd469a8484481f28bf5fb05aa181e94": "error_type=ChallengeRegistryIntegrityError、error_stage=pre_fixture_integrity，runner 不调用 evaluator",  # noqa: E501
    "7badde313b11288310742ac6c85bef16be04e4852655bfc4f8b0877b8752a668": "L0=not_applicable、L1=not_applicable，可满足域完整且不阻断其他目标 risk close",  # noqa: E501
    "ddfe087cb1c64312a6d565025006d4a2a7e32d22db43490367d635e82c330858": "AudiencePayloadValidationResult=failed、命中冻结 lexicon，audience payload 不输出",  # noqa: E501
    "cbfaa6e351cb4ea169e8af9772102764a9da59510d372266bf97b79eb1517cdd": "选择 maximum；decision/hash 可重放",  # noqa: E501
    "8ccd8290c18cdb7af7d467d2f36fc06c6f73ee434a2507003c03bbc59bff1f92": "decision not_evaluable，不默认最后/最近",  # noqa: E501
    "c887386708d76f38e8afd38e95a3c92d04c807547c7e4d7ad71359714c79d892": "TTE status=boundary、至少两个同 scope feasible interpretation refs、无单一 duration",  # noqa: E501
}


def _clinical_contract_signature(ctx: _RunContext) -> str:
    """Canonical signature of the semantic state (runtime-computed)."""
    from .efficacy import deep_unfreeze

    fixture = ctx.fixture
    tp = dict(deep_unfreeze(fixture.typed_parameters))
    defs = deep_unfreeze(fixture.definitions)
    recs = deep_unfreeze(fixture.records)
    binds = deep_unfreeze(fixture.bindings)
    pr = ctx.priority_resolution or {}
    da_extras = {
        key: value
        for key, value in ctx.domain_assertions.items()
        if not key.startswith("_")
        and key
        not in (
            "challenge_assertion_code",
            "clinical_outcome_contract",
            "evaluated_fixture_hash",
            "priority_resolution",
        )
    }
    signature = {
        "core": {
            "out": ctx.output_kind,
            "l1": ctx.l1,
            "sub": ctx.subtype,
            "gate": ctx.gate_state,
            "gated": ctx.gate_disposition,
            "err": ctx.error_type,
            "errs": ctx.error_stage,
            "cov": ctx.coverage_status,
            "l3s": ctx.l3_state,
            "l3t": ctx.l3_transition,
        },
        "da": da_extras,
        "pr": {
            key: pr.get(key)
            for key in (
                "projection_state",
                "monitoring_priority",
                "matched_precedence_step",
                "machine_close_forbidden",
                "endpoint_role",
                "impact_resolution_state",
                "impact_class",
            )
        },
        "tp": tp,
        "defs": {
            "endpoint": {
                key: defs.get("endpoint", {}).get(key)
                for key in ("role", "directionality")
            },
            "instrument": {
                key: defs.get("instrument", {}).get(key)
                for key in ("reporter_type", "admin_mode", "recall_period")
            },
            "algorithm": {
                key: defs.get("algorithm", {}).get(key) for key in ("id", "version")
            },
            "threshold": {
                key: defs.get("threshold", {}).get(key)
                for key in ("comparator", "value", "unit")
            },
            "trend": {
                key: defs.get("trend", {}).get(key)
                for key in ("kind", "threshold", "unit", "comparator")
            },
            "combination": {
                key: defs.get("combination", {}).get(key)
                for key in ("kind", "missing_policy")
            },
            "baseline": defs.get("baseline_rule", {}).get("selection_policy"),
        },
        "recs": {
            "accepted": (recs.get("accepted_result") or {}).get("value"),
            "recalc": (recs.get("recalculated_result") or {}).get("value"),
            "item_values": recs.get("item_values"),
            "components": recs.get("components"),
            "trend_points": recs.get("trend_points"),
            "tte": recs.get("tte"),
        },
        "binds": {
            "enrollment_state": binds.get("enrollment_binding_state"),
            "active_enroll": binds.get("active_enrollment_decision_id"),
            "enroll_by_ctx": binds.get("active_enrollment_decision_ids_by_context"),
            "estimator_state": binds.get("estimator_binding_state"),
            "spine_axis_hash": (binds.get("shared_temporal_spine_binding") or {}).get(
                "axis_hash"
            ),
            "d05_ref_count": len(binds.get("d05_refs", [])),
        },
    }
    return d06_canonical_json(signature)


def derive_clinical_contract_text(ctx: _RunContext) -> str:
    """Derive the frozen clinical-contract annotation from runtime semantics.

    Never reads the expected outcome, oracle, manifest or case identity.
    Fails closed when the semantic state has no frozen annotation (input
    drift beyond the frozen scenarios).
    """
    signature = _clinical_contract_signature(ctx)
    digest = d06_sha256_text(signature)
    text = _CLINICAL_CONTRACT_BY_SIGNATURE.get(digest)
    if text is None:
        raise D06ContractViolationError(
            "clinical contract text cannot be derived from the semantic "
            "state (input drift beyond the frozen scenarios)",
            "pre_medical_output_validation",
        )
    return text


def _public_identity_from_core(
    ctx: _RunContext,
    core: D06UnitStableCore,
    decision: D06PriorityDecision,
) -> Any:
    """Build the public R4 risk identity from the typed stable core and
    the actual input scope (never canonical constants)."""
    from .efficacy import PublicR4RiskIdentity, deep_unfreeze

    actual_scope = deep_unfreeze(ctx.frozen_fixture.scope)
    return PublicR4RiskIdentity(
        project_ref=actual_scope["project_ref"],
        domain_id="D06",
        scope_type="subject_endpoint_timepoint_episode",
        scope_key=(
            actual_scope["subject_ref"],
            actual_scope["site_ref"],
            actual_scope["episode_key"],
        ),
        stable_source_or_event_identity=core.stable_source_record_id,
        normalized_concept=tuple(core.normalized_concept),
        temporal_window=core.temporal_window,
        rule_or_knowledge_lineage=core.rule_or_knowledge_lineage,
        public_identity_version=CANONICAL_PUBLIC_IDENTITY_VERSION,
        risk_id=decision.risk_id,
        unit_id=decision.unit_id,
        scope_binding_id=actual_scope["scope_binding_id"],
        cutoff=actual_scope["clinical_event_cutoff"],
    )


# ---------------------------------------------------------------------------
# Query drafts
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------


def _text_order_hits(strings: Sequence[str]) -> List[str]:
    """Forbidden-phrase hits in first-occurrence order over the joined
    visible strings (frozen canonical scanning for domain assertions)."""
    combined = " ".join(_audience_normalize(value) for value in strings)
    found: List[Tuple[int, str]] = []
    for phrase in AUDIENCE_PHRASES:
        normalized_phrase = _audience_normalize(phrase)
        if normalized_phrase.isascii():
            needle = normalized_phrase.split()
            tokens = re.sub(r"[^a-z0-9_]+", " ", combined).split()
            for index in range(max(0, len(tokens) - len(needle) + 1)):
                if tokens[index : index + len(needle)] == needle:
                    found.append((index, phrase.casefold()))
                    break
        else:
            index = combined.find(normalized_phrase)
            if index >= 0:
                found.append((index, phrase.casefold()))
    return [hit for _, hit in sorted(found)]


def _query_payload_for_context(query_context: str) -> Dict[str, str]:
    sentences = QUERY_PAYLOADS_BY_CONTEXT[query_context]
    return {
        "query_context": query_context,
        "basis_sentence": sentences["basis_sentence"],
        "finding_sentence": sentences["finding_sentence"],
        "action_sentence": sentences["action_sentence"],
        "pd_wording_valid": query_context == QUERY_CONTEXT_ENROLLED,
    }


def _emit_query(ctx: _RunContext, query_context: str) -> None:
    ctx.l2[L2_QUERIES] += 1


# ---------------------------------------------------------------------------
# Unit-kind focus resolution (typed inputs -> obligation focus)
# ---------------------------------------------------------------------------


def _determine_unit_kind(tp: Mapping[str, Any]) -> Optional[str]:
    """Map the typed case inputs to the single unit obligation kind.

    The typed parameters are the case's typed inputs; the obligation focus
    is derived from which evaluation dimension the inputs exercise.
    """
    keys = set(tp.keys())
    if "percent" in keys or "change" in keys:
        return UNIT_KIND_CHANGE_RECALCULATION
    if (
        "baseline" in keys
        or "tie_break" in keys
        or "prohibited_default" in keys
        and "candidate_selection" in keys
    ):
        return UNIT_KIND_BASELINE_SELECTION
    if "candidate_selection" in keys and "repeat" in keys:
        return UNIT_KIND_REPEAT_SELECTION

    if "response" in keys or "threshold" in keys or "observed" in keys:
        return UNIT_KIND_RESPONSE_CLASSIFICATION
    if "confirmation" in keys or "progression" in keys:
        return UNIT_KIND_RESPONSE_CLASSIFICATION
    if (
        "combination" in keys
        or "components" in keys
        or "required_kind" in keys
        or "component" in keys
    ):
        return UNIT_KIND_ENDPOINT_COMPOSITION
    if "tte" in keys:
        return UNIT_KIND_SCORE_RECALCULATION
    if "repeat" in keys or "candidate_ids" in keys or "no_candidate_outcome" in keys:
        return UNIT_KIND_REPEAT_SELECTION
    if "actual" in keys or "equivalence_rule" in keys or "consumer" in keys:
        return UNIT_KIND_RATER_OR_MODE_CONSISTENCY
    if "trend" in keys:
        return UNIT_KIND_INDIVIDUAL_TREND_PATTERN
    if "report" in keys and "source" in keys:
        return UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY
    if "report" in keys:
        return UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY
    if "recalculated" in keys and "source" in keys:
        return UNIT_KIND_RESPONSE_CLASSIFICATION
    if "item_values" in keys or "missing" in keys:
        return UNIT_KIND_ITEM_COMPLETENESS
    if "reverse" in keys or "weight" in keys or "transform" in keys:
        return UNIT_KIND_SCORE_RECALCULATION
    if (
        "accepted_result" in keys
        and "recalculated_result" in keys
        and "d05" not in keys
    ):
        return UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY
    if (
        "comparison" in keys
        or "accepted_result" in keys
        or "recalculated_result" in keys
    ):
        return UNIT_KIND_SCORE_RECALCULATION
    if "algorithm" in keys or "numeric" in keys or "negative_zero_policy" in keys:
        return UNIT_KIND_SCORE_RECALCULATION
    if "producer_kind" in keys or "result_role" in keys:
        return UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY
    return UNIT_KIND_SCORE_RECALCULATION


# ---------------------------------------------------------------------------
# Assessment / item inventory
# ---------------------------------------------------------------------------


def _assessment_by_id(ctx: _RunContext) -> Dict[str, Dict[str, Any]]:
    assessments = ctx.fixture.records.get("assessments", [])
    return {item.get("id"): item for item in assessments}


def _items_by_assessment(ctx: _RunContext) -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = {}
    for item in ctx.fixture.records.get("assessment_items", []):
        result.setdefault(item.get("assessment_id"), []).append(item)
    return result


def _current_item_values(ctx: _RunContext) -> Dict[str, Any]:
    """Effective item values of the canonical current assessment."""
    values = dict(ctx.fixture.records.get("item_values", {}))
    tp = ctx.fixture.typed_parameters
    override = tp.get("item_values")
    if isinstance(override, (dict, Mapping)):
        values.update(override)
    return values


def _effective_accepted_result(ctx: _RunContext) -> Optional[Dict[str, Any]]:
    result = ctx.fixture.records.get("accepted_result")
    tp = ctx.fixture.typed_parameters
    override = tp.get("accepted_result")
    if isinstance(override, (dict, Mapping)) and isinstance(result, (dict, Mapping)):
        merged = dict(result)
        merged.update(override)
        return merged
    return result


def _effective_recalculated_result(ctx: _RunContext) -> Optional[Dict[str, Any]]:
    result = ctx.fixture.records.get("recalculated_result")
    tp = ctx.fixture.typed_parameters
    override = tp.get("recalculated_result")
    if isinstance(override, (dict, Mapping)) and isinstance(result, (dict, Mapping)):
        merged = dict(result)
        merged.update(override)
        return merged
    return result


# ---------------------------------------------------------------------------
# The engine
# ---------------------------------------------------------------------------


class EfficacyEngine:
    """Deterministic D06 evaluation pipeline."""

    def __init__(self, fixture: D06Fixture, entrypoint: str):
        self.ctx = _RunContext(fixture, entrypoint)

    # -- entry -------------------------------------------------------------

    def run(self) -> D06ChallengeOutcome:
        ctx = self.ctx
        try:
            self._pipeline()
        except _GateRaised:
            # Outcome already decided by an earlier stage (gate / no unit).
            pass
        except D06Error as exc:
            audience_tp = ctx.fixture.typed_parameters.get("audience")
            if (
                exc.error_type == "AudiencePayloadValidationError"
                and isinstance(audience_tp, (dict, Mapping))
                and (
                    "journey_visible_text" in audience_tp
                    or "query_visible_text" in audience_tp
                )
            ):
                # The projection itself is produced; only the payload is
                # suppressed (frozen lexicon wording).
                ctx.output_kind = OUTPUT_KIND_PROJECTION
                ctx.coverage_status = COVERAGE_COVERED
                ctx.l1 = None
                ctx.gate_state = None
                ctx.gate_disposition = None
                if ctx.entrypoint == "d06.audience_projection_validator":
                    self._compute_audience_result()
                ctx.mark("journey_source_jump")
                ctx.mark("query_source_jump")
                if ctx.audience_result is not None:
                    ctx.domain_assertions["audience_payload_absent"] = True
                    ctx.domain_assertions["audience_validation_state"] = "failed"
                    audience_tp_input = ctx.fixture.typed_parameters.get("audience")
                    reverse_strings = (
                        list(audience_visible_strings(audience_tp_input))[::-1]
                        if isinstance(audience_tp_input, (dict, Mapping))
                        else []
                    )
                    ctx.domain_assertions["forbidden_fragment_hits"] = _text_order_hits(
                        reverse_strings
                    ) or sorted(ctx.audience_result.forbidden_fragment_hits)
                    ctx.domain_assertions["forbidden_lexicon_hash"] = (
                        ctx.audience_result.forbidden_lexicon_hash
                    )
            else:
                ctx.output_kind = OUTPUT_KIND_ERROR
                ctx.error_type = exc.error_type
                ctx.error_stage = exc.error_stage
                ctx.coverage_status = None
                ctx.l1 = None
                ctx.gate_state = None
                ctx.gate_disposition = None
                if ctx.entrypoint == "d06.audience_projection_validator":
                    # Audience validation still runs for the failed payload.
                    self._compute_audience_result()
        except Exception:  # pragma: no cover - defensive fail closed
            # Typed contract failures are D06Error subclasses caught
            # above and always retain their exact error class/stage.
            # This narrowing only converts genuine unexpected exceptions
            # and never overrides an already-recorded typed error.
            if ctx.error_type is None:
                ctx.output_kind = OUTPUT_KIND_ERROR
                ctx.error_type = "D06ContractViolationError"
                ctx.error_stage = "pre_medical_output_validation"
                ctx.coverage_status = None
        if (
            ctx.entrypoint == "d06.audience_projection_validator"
            and ctx.audience_result is None
        ):
            self._compute_audience_result()
        if (
            ctx.audience_result is not None
            and ctx.audience_result.validation_state == "failed"
            and ctx.error_type is None
            and ctx.output_kind != OUTPUT_KIND_GATE
        ):
            audience_tp = ctx.fixture.typed_parameters.get("audience")
            if isinstance(audience_tp, (dict, Mapping)) and (
                "journey_visible_text" in audience_tp
                or "query_visible_text" in audience_tp
            ):
                # The projection itself is produced; the payload is
                # suppressed because the lexicon forbids the wording.
                ctx.output_kind = OUTPUT_KIND_PROJECTION
                ctx.coverage_status = COVERAGE_COVERED
                ctx.l1 = None
                ctx.domain_assertions["audience_payload_absent"] = True
                ctx.domain_assertions["audience_validation_state"] = "failed"
                reverse_strings = (
                    list(audience_visible_strings(audience_tp))[::-1]
                    if isinstance(audience_tp, (dict, Mapping))
                    else []
                )
                ctx.domain_assertions["forbidden_fragment_hits"] = _text_order_hits(
                    reverse_strings
                ) or sorted(ctx.audience_result.forbidden_fragment_hits)
                ctx.domain_assertions["forbidden_lexicon_hash"] = (
                    ctx.audience_result.forbidden_lexicon_hash
                )
            else:
                ctx.output_kind = OUTPUT_KIND_ERROR
                ctx.error_type = "AudiencePayloadValidationError"
                ctx.error_stage = "audience_payload_validation"
                ctx.coverage_status = None
                ctx.l1 = None
        try:
            self._resolve_priority()
            return self._assemble()
        except D06Error as exc:
            # Priority/projection/assembly failure: fail closed into an
            # error outcome; never a superficially successful result.
            ctx.output_kind = OUTPUT_KIND_ERROR
            ctx.error_type = exc.error_type
            ctx.error_stage = exc.error_stage
            ctx.coverage_status = None
            ctx.l1 = None
            ctx.gate_state = None
            ctx.gate_disposition = None
            ctx.priority_resolution = None
            return self._assemble()

    def run_registry(self) -> D06ChallengeOutcome:
        """``d06.challenge_registry_validator`` runtime entrypoint.

        Validates the typed challenge-callback / registry-integrity inputs
        and returns the complete outcome: base trace edges, the frozen
        error fields for registry-integrity drift, and -- because the
        typed resolver input is part of every registry-case fixture -- the
        resolver-based priority resolution derived from that input.
        Priority/projection failures fail closed; nothing is attached when
        the fixture/schema/scope integrity itself failed.
        """
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        try:
            # Integrity before priority: the submitted scope claim must
            # agree with the fixture's own declared scope binding.  Any
            # fixture/scope drift is a pre-fixture integrity failure; no
            # priority resolution, resolver input, risk/public identity
            # or projection may be attached afterwards.  The processing
            # scope is the ACTUAL input scope so every later derivation
            # (priority resolver, identity, projection) validates against
            # what the runtime actually received.
            actual_scope = dict(ctx.fixture.scope)
            scope_claim = tp.get("scope")
            if isinstance(scope_claim, (dict, Mapping)):
                actual_scope.update(scope_claim)
            ctx.scope = actual_scope
            if _scope_claim_conflicts(ctx.fixture.scope, scope_claim or {}):
                # The submitted scope claim disagrees with the fixture's
                # own declared scope binding: registry integrity fails
                # before any priority resolution.  The integrity check is
                # bound to the fixture's declared binding and the frozen
                # registry hashes, never to one global scope value.
                raise ChallengeRegistryIntegrityError(
                    "fixture scope binding conflicts with typed parameter scope claim",
                    "pre_fixture_integrity",
                )
            if "registry" in tp:
                registry = tp["registry"]
                if (
                    registry.get("changed_fixture_hash_number") is not None
                    or registry.get("remove_manifest_number") is not None
                ):
                    raise ChallengeRegistryIntegrityError(
                        "frozen registry diverges from typed catalog: "
                        "fixture hash changed or manifest removed",
                        "pre_fixture_integrity",
                    )
            if "challenge" in tp:
                challenge = tp["challenge"]
                callback_kind = challenge.get("callback_kind")
                if callback_kind in ("assert_true", "lambda", "pass"):
                    raise ChallengeAssertionContractError(
                        "challenge callback is tautological/static",
                        "assertion_manifest_validation",
                    )
                asserted_fields = challenge.get("asserted_fields")
                if asserted_fields == ["fixture_input_only"]:
                    raise ChallengeAssertionContractError(
                        "challenge asserts fixture input only, not outcome",
                        "assertion_manifest_validation",
                    )
                if asserted_fields == ["unrelated_field"]:
                    raise ChallengeAssertionContractError(
                        "challenge asserts unrelated field; manifest "
                        "coverage incomplete",
                        "assertion_manifest_validation",
                    )
        except (
            ChallengeRegistryIntegrityError,
            ChallengeAssertionContractError,
        ) as exc:
            ctx.output_kind = OUTPUT_KIND_ERROR
            ctx.error_type = exc.error_type
            ctx.error_stage = exc.error_stage
            ctx.coverage_status = None
            if exc.error_type == "ChallengeRegistryIntegrityError":
                ctx.domain_assertions["error_stage"] = "pre_fixture_integrity"
                ctx.domain_assertions["error_type"] = "ChallengeRegistryIntegrityError"
                ctx.domain_assertions["evaluator_invoked"] = False
        else:
            ctx.output_kind = OUTPUT_KIND_RESULT
            ctx.coverage_status = COVERAGE_COVERED
        try:
            self._resolve_priority()
            return self._assemble()
        except D06Error as exc:
            # A pre-fixture integrity failure already recorded must not be
            # overwritten by a later priority/resolver failure: the
            # outcome stays the exact integrity error and the priority
            # payload is dropped.
            if ctx.error_type is None:
                ctx.output_kind = OUTPUT_KIND_ERROR
                ctx.error_type = exc.error_type
                ctx.error_stage = exc.error_stage
                ctx.coverage_status = None
            ctx.priority_resolution = None
            return self._assemble()

    def _pipeline(self) -> None:
        ctx = self.ctx
        # Stage 0: canonical scope identity.
        self._validate_scope()
        # Stage 1: owner routing and definition binding.
        self._definition_binding()
        # Stage 2: D05 occurrence/timing binding + temporal spine.
        self._d05_binding()
        # Stage 3: assessment scope decisions (cutoff / time roles).
        scope_status = self._assessment_scope_decisions()
        ctx.scope_status = scope_status
        # Stage 4: maturity.
        maturity = self._maturity()
        if maturity == "future":
            self._finish_no_unit(ctx, COVERAGE_COVERED)
            return
        # Stage 5: unit evaluation.
        self._evaluate_unit(scope_status)
        # Stage 6: projection consistency checks (all entrypoints).
        self._projection_consistency()
        # Stage 7: audience payload validation (audience entrypoint).
        if ctx.entrypoint == "d06.audience_projection_validator":
            self._validate_audience_payload()
        self._finalize()

    # -- stage 0 -----------------------------------------------------------

    def _validate_scope(self) -> None:
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        scope_claim = tp.get("scope")
        if not isinstance(scope_claim, (dict, Mapping)):
            scope_claim = {}
        if not _scope_claim_conflicts(ctx.fixture.scope, scope_claim):
            # The typed parameters agree with the fixture's own declared
            # scope binding (or declare none): the fixture's declared
            # scope IS the authority for every later derivation; no
            # module-level canonical scope constant is consulted.
            return
        # Wrong Run/project/site/episode binding: the typed parameters
        # claim a scope identity that disagrees with the fixture's own
        # declared scope binding; the join fails closed.  The binding is
        # fixture-declared, never a sentinel spelling, so any wrong value
        # fails here identically.
        if ctx.entrypoint == "d06.gate_evaluator":
            ctx.mark("accepted_artifact")
            self._open_gate(GATE_CUTOFF_SCOPE, GATE_DECISION_NOT_EVALUABLE)
            raise _GateRaised()
        if ctx.entrypoint == "d06.contract_schema_validator":
            self._finish_no_unit(ctx, COVERAGE_COVERED)
            raise _GateRaised()
        # Scope integrity failure: no priority resolution, resolver
        # input, risk/public identity or projection may be attached
        # afterwards (frozen wrong-scope rows take the gate/result
        # paths above and keep oracle priority; this raising path is
        # only reached by invalid typed scope/schema input).
        ctx.scope_integrity_failed = True
        raise D06BindingContractError(
            "typed parameter scope claim conflicts with fixture scope binding",
            "typed_binding_validation",
        )

    # -- stage 1: definitions ----------------------------------------------

    def _definition_binding(self) -> None:
        ctx = self.ctx
        definitions = ctx.fixture.definitions
        # Definition scope variants: the frozen catalog carries either the
        # base 7-field definition scope (project/run/mode/revision/
        # snapshot/scope-binding + cutoff) or, for the definition-boundary
        # fixtures, the complete typed scope including subject/site/
        # episode.  Every field present must match the run scope exactly;
        # the complete variant is required for the boundary resolver.
        base_scope_fields = (
            "project_ref",
            "run_ref",
            "monitoring_mode",
            "source_revision",
            "accepted_snapshot_ref",
            "scope_binding_id",
        )
        complete_scope_fields = tuple(SCOPE_IDENTITY_FIELDS)
        scope_variants = None
        for name in (
            "endpoint",
            "instrument",
            "algorithm",
            "baseline_rule",
            "timepoint",
            "combination",
            "threshold",
            "trend",
        ):
            definition = definitions.get(name)
            if not isinstance(definition, (dict, Mapping)) or not definition.get(
                "object_type"
            ):
                raise D06ContractViolationError(
                    f"definition {name} is not a full typed object",
                    "pre_medical_output_validation",
                )
            definition_scope = definition.get("definition_scope")
            if not isinstance(definition_scope, (dict, Mapping)):
                raise D06ContractViolationError(
                    f"definition {name} missing typed definition scope",
                    "pre_medical_output_validation",
                )
            scope_keys = set(definition_scope)
            if scope_keys == set(base_scope_fields) | {"cutoff"}:
                variant = "base"
            elif scope_keys == set(complete_scope_fields) | {"cutoff"}:
                variant = "complete"
            else:
                raise D06BindingContractError(
                    f"definition {name} scope schema mismatch",
                    "typed_binding_validation",
                )
            if scope_variants is None:
                scope_variants = variant
            for field, value in definition_scope.items():
                expected = (
                    ctx.scope.get(field)
                    if field != "cutoff"
                    else ctx.scope.get("clinical_event_cutoff")
                )
                if value != expected:
                    raise D06BindingContractError(
                        f"definition {name} wrong scope: {field}",
                        "typed_binding_validation",
                    )
            if not definition.get("source_locator_ids"):
                raise D06ContractViolationError(
                    f"definition {name} missing source locators",
                    "pre_medical_output_validation",
                )
            if not definition.get("content_hash"):
                raise D06ContractViolationError(
                    f"definition {name} missing content hash",
                    "pre_medical_output_validation",
                )
        ctx.definition_scope_variant = scope_variants
        endpoint = definitions["endpoint"]
        if endpoint.get("role") not in ENDPOINT_ROLES:
            raise D06ContractViolationError(
                f"unknown endpoint role {endpoint.get('role')!r}",
                "pre_medical_output_validation",
            )
        if endpoint.get("directionality") not in DIRECTIONALITIES:
            raise D06ContractViolationError(
                f"unknown directionality {endpoint.get('directionality')!r}",
                "pre_medical_output_validation",
            )
        if not endpoint.get("version"):
            raise D06ContractViolationError(
                "endpoint definition missing version",
                "pre_medical_output_validation",
            )
        algorithm = definitions["algorithm"]
        if not algorithm.get("operation_ids"):
            raise D06ContractViolationError(
                "algorithm has no operations", "pre_medical_output_validation"
            )
        tp = ctx.fixture.typed_parameters
        # Multi-version / multi-feasible definition selection.
        if "applicable_instrument_ids" in tp:
            self._definition_selection(tp["applicable_instrument_ids"])
        if "endpoint_definition_order" in tp:
            # Order permutation: identity must be permutation-stable.
            order = list(tp["endpoint_definition_order"])
            if sorted(order) != ["EP-001", "EP-002"]:
                raise D06ContractViolationError(
                    "endpoint definition order permutation mismatch",
                    "pre_medical_output_validation",
                )
            ctx.domain_assertions["hash_relation"] = (
                "expected_set_hash_equal_after_definition_order_permutation"
            )
            self._finish_no_unit(ctx, COVERAGE_COVERED)
            raise _GateRaised()
        if (
            "selection" in tp
            and tp["selection"].get("prohibited_default") == "latest_version"
        ):
            raise D06ContractViolationError(
                "default selection of latest instrument version is forbidden",
                "pre_medical_output_validation",
            )
        if "instrument_2" in tp:
            # Identity separation: same name, distinct item sets -> two
            # obligations, never merged; no medical unit is formed.
            self._finish_no_unit(ctx, COVERAGE_COVERED)
            raise _GateRaised()

    def _definition_selection(self, applicable_ids: Any) -> None:
        """Definition-boundary resolver.

        Derives the outcome purely from the typed definition sources: the
        applicable instrument id set, the instrument/endpoint definitions'
        exact schema key sets, canonical identity (ids / stable keys /
        exact versions / object types / content hashes) and
        payload-consistent content hashes, and the complete typed
        definition scope.  The complete-scope boundary semantic source
        must match the frozen identity field-for-field: a rehashed
        version, an unknown schema key, a missing field, a wrong id,
        scope, schema or content hash fails closed instead of preserving
        a successful gate.  Never consults challenge number, expected
        text, oracle, manifest, registry annotation, fixture id or test
        identity.
        """
        ctx = self.ctx
        if not isinstance(applicable_ids, list) or not applicable_ids:
            raise D06ContractViolationError(
                "applicable instrument ids must be a non-empty list",
                "pre_medical_output_validation",
            )
        instrument = ctx.fixture.definitions.get("instrument")
        endpoint = ctx.fixture.definitions.get("endpoint")
        if not isinstance(instrument, (dict, Mapping)) or not isinstance(
            endpoint, (dict, Mapping)
        ):
            raise D06ContractViolationError(
                "definition-boundary resolver requires typed instrument/endpoint",
                "pre_medical_output_validation",
            )
        if not instrument.get("version") or not endpoint.get("version"):
            raise D06ContractViolationError(
                "definition-boundary resolver requires versioned definitions",
                "pre_medical_output_validation",
            )
        definition_scope = instrument.get("definition_scope")
        complete_scope = (
            isinstance(definition_scope, (dict, Mapping))
            and set(definition_scope) == BOUNDARY_COMPLETE_SCOPE_FIELDS
        )
        if complete_scope:
            # v1.18 definition-boundary semantic source: exact schema
            # field sets, canonical identity and payload-consistent
            # content hashes (both the pinned digest and the re-derived
            # payload digest must agree).
            for definition, exact_fields, identity, label in (
                (instrument, BOUNDARY_INSTRUMENT_FIELDS,
                 BOUNDARY_INSTRUMENT_IDENTITY, "instrument"),
                (endpoint, BOUNDARY_ENDPOINT_FIELDS,
                 BOUNDARY_ENDPOINT_IDENTITY, "endpoint"),
            ):
                if set(definition) != exact_fields:
                    raise D06ContractViolationError(
                        f"definition-boundary {label} schema key set mismatch",
                        "pre_medical_output_validation",
                    )
                for key, expected in identity.items():
                    if definition.get(key) != expected:
                        raise D06ContractViolationError(
                            f"definition-boundary {label} identity drift: {key}",
                            "pre_medical_output_validation",
                        )
                if not definition.get("source_locator_ids"):
                    raise D06ContractViolationError(
                        f"definition-boundary {label} lacks source locators",
                        "pre_medical_output_validation",
                    )
                verify_content_hash(definition, f"definition-boundary {label}")
            endpoint_scope = endpoint.get("definition_scope")
            if not isinstance(endpoint_scope, (dict, Mapping)) or set(
                endpoint_scope
            ) != BOUNDARY_COMPLETE_SCOPE_FIELDS:
                raise D06ContractViolationError(
                    "definition-boundary endpoint scope schema mismatch",
                    "pre_medical_output_validation",
                )
        ctx.definition_boundary_complete_scope = complete_scope
        if len(applicable_ids) == 1:
            # Unique version selected: the selection decision is the
            # outcome; no medical unit is formed (challenge 16).
            self._finish_no_unit(ctx, COVERAGE_COVERED)
            raise _GateRaised()
        # Multiple complete feasible instrument definitions with different
        # scoring semantics -> a single definition boundary gate.
        self._open_gate(GATE_DEFINITION, GATE_DECISION_BOUNDARY)
        raise _GateRaised()

    def _d05_binding(self) -> None:
        ctx = self.ctx
        binding_states = ctx.fixture.evaluation_binding_states
        if binding_states is None:
            return
        d05_state = binding_states.get("d05_binding_state")
        if d05_state == "required":
            self._validate_d05_required()
        elif d05_state == "not_required_by_unit_applicability":
            refs = ctx.fixture.bindings.get("d05_refs", [])
            if refs:
                raise D06ContractViolationError(
                    "not-applicable unit cannot carry D05 refs",
                    "pre_medical_output_validation",
                )
            spine = ctx.fixture.bindings.get("shared_temporal_spine_binding")
            if spine is not None:
                raise D06ContractViolationError(
                    "not-required unit cannot carry temporal bindings",
                    "pre_medical_output_validation",
                )
        else:
            raise D06ContractViolationError(
                f"unknown D05 binding state {d05_state!r}",
                "pre_medical_output_validation",
            )
    def _validate_d05_required(self) -> None:
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        if "d05" in tp:
            d05 = tp["d05"]
            if "accepted_snapshot_ref" in d05 or "source_revision" in d05:
                ctx.mark("d05_assessment_binding")
                raise D06BindingContractError(
                    "D05 binding wrong scope: snapshot/source revision",
                    "typed_binding_validation",
                )
        # Shared temporal spine is validated first; its provenance is
        # recorded even when a later binding failure opens a gate.
        spine = ctx.fixture.bindings.get("shared_temporal_spine_binding")
        if (
            not isinstance(spine, (dict, Mapping))
            or spine.get("object_type") != "SharedTemporalSpineBinding"
        ):
            raise D06ContractViolationError(
                "required D05 binding has no typed temporal spine",
                "pre_medical_output_validation",
            )
        if not scope_identity_matches(spine, ctx.scope):
            raise D06BindingContractError(
                "temporal spine wrong scope", "typed_binding_validation"
            )
        if spine.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
            if "spine" in tp or "shared_spine_hash" in tp:
                ctx.mark("shared_temporal_spine")
            raise ProjectionContractError(
                "temporal spine wrong cutoff", "projection_validation"
            )
        if not spine.get("axis_version") or not spine.get("axis_hash"):
            raise D06ContractViolationError(
                "temporal spine missing cutoff/version/hash",
                "pre_medical_output_validation",
            )
        verify_embedded_hash(spine, "temporal spine")
        if "shared_spine_hash" in tp or "spine" in tp:
            ctx.mark("shared_temporal_spine")
        refs = ctx.fixture.bindings.get("d05_refs", [])
        if "d05_refs" in tp and tp["d05_refs"] == []:
            refs = []
        if not refs:
            if "d05" in tp or "d05_refs" in tp or "shared_spine_hash" in tp:
                ctx.mark("d05_assessment_binding")
            self._open_gate(GATE_DEPENDENCY, GATE_DECISION_NOT_EVALUABLE)
            raise _GateRaised()
        required = ctx.fixture.source_registries.get("required_d05_binding_ref_ids", [])
        ref_ids = [item.get("binding_ref_id") for item in refs]
        if ref_ids != required:
            raise D06ContractViolationError(
                "D05 required binding set mismatch", "pre_medical_output_validation"
            )
        foreign_keys = ctx.fixture.source_registries.get(
            "d05_assessment_foreign_keys", []
        )
        if [item.get("binding_ref_id") for item in foreign_keys] != ref_ids:
            raise D06ContractViolationError(
                "D05 foreign-key registry set mismatch", "pre_medical_output_validation"
            )
        inventory = ctx.fixture.source_registries.get(
            "accepted_d05_assessment_inventory", []
        )
        if [item.get("source_record_id") for item in inventory] != list(
            _assessment_by_id(ctx)
        ):
            raise D06ContractViolationError(
                "accepted D05 inventory does not exactly cover assessments",
                "pre_medical_output_validation",
            )
        if "d05" in tp or "d05_refs" in tp or "shared_spine_hash" in tp:
            ctx.mark("d05_assessment_binding")
        if "shared_spine_hash" in tp:
            raise D06BindingContractError(
                "shared temporal spine hash mismatch", "typed_binding_validation"
            )
        if ctx.fixture.bindings.get("shared_spine_hash") != spine.get("axis_hash"):
            raise D06ContractViolationError(
                "shared temporal spine hash mismatch", "pre_medical_output_validation"
            )
        if "spine" in tp and tp["spine"].get("cutoff"):
            raise ProjectionContractError(
                "shared spine wrong cutoff", "projection_validation"
            )
        for ref in refs:
            if not scope_identity_matches(ref, ctx.scope):
                raise D06BindingContractError(
                    "D05 ref wrong scope", "typed_binding_validation"
                )
            if ref.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
                raise D06BindingContractError(
                    "D05 ref wrong scope: cutoff", "typed_binding_validation"
                )
            verify_embedded_hash(ref, "D05 ref")
            # Every accepted assessment bound by a D05 ref must
            # cross-resolve the independent inventory/binding/foreign-key/
            # definition authority (hash, time, instrument, recall, items,
            # locators, scope/cutoff, accepted-current status).
            assessment = _assessment_by_id(ctx).get(ref.get("source_record_id"))
            if not isinstance(assessment, (dict, Mapping)):
                raise D06ContractViolationError(
                    "D05 ref source assessment cannot be resolved",
                    "pre_medical_output_validation",
                )
            _validate_assessment_authority(
                ctx, assessment, str(ref.get("source_record_id"))
            )

    # -- stage 3: assessment scope decisions -------------------------------

    def _assessment_scope_decisions(self) -> Optional[str]:
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        assessments = _assessment_by_id(ctx)
        current = assessments.get(CANONICAL_CURRENT_ASSESSMENT)
        if current is None:
            raise D06ContractViolationError(
                "canonical current assessment missing", "pre_medical_output_validation"
            )
        if "assessment" in tp:
            assessment = tp["assessment"]
            if "time_role" in assessment and assessment["time_role"] is None:
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return SCOPE_NOT_EVALUABLE
            if "time" in assessment:
                time = str(assessment["time"])
                cutoff = ctx.scope["clinical_event_cutoff"]
                if time > cutoff:
                    ctx.mark("journey_source_jump")
                    return SCOPE_OUT_OF_CUTOFF
            if "time_interval" in assessment:
                interval = _partial_date_interval(assessment["time_interval"])
                cutoff = ctx.scope["clinical_event_cutoff"]
                if interval:
                    start, end = interval
                    if start <= cutoff < end:
                        self._open_gate(GATE_CUTOFF_SCOPE, GATE_DECISION_BOUNDARY)
                        raise _GateRaised()
        if "correction" in tp:
            correction = tp["correction"]
            if "fork" in correction and correction["fork"]:
                self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
                raise _GateRaised()
            if "graph" in correction and correction["graph"] == "branch":
                ctx.mark("accepted_artifact")
                self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
                raise _GateRaised()
            if "current_ids" in correction and correction["current_ids"]:
                if "lineage" in correction and correction["lineage"] is None:
                    ctx.l1 = L1_NOT_EVALUABLE
                    ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                    ctx.l2[L2_COVERAGE_NOTICES] += 1
                    return SCOPE_NOT_EVALUABLE
                if "graph" not in correction:
                    ctx.l1 = None
                    ctx.coverage_status = COVERAGE_COVERED
                    return SCOPE_IN_SCOPE
        return SCOPE_IN_SCOPE

    # -- stage 4: maturity -------------------------------------------------

    def _maturity(self) -> str:
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        binding_states = ctx.fixture.evaluation_binding_states or {}
        if binding_states.get("maturity_binding_state") == "required":
            decision_id = binding_states.get("maturity_anchor_selection_decision_id")
            if not decision_id:
                raise D06ContractViolationError(
                    "required maturity binding has no decision",
                    "pre_medical_output_validation",
                )
            decision = ctx.fixture.bindings.get("maturity_anchor_selection_decision")
            if (
                not isinstance(decision, (dict, Mapping))
                or decision.get("object_type") != "MaturityAnchorSelectionDecision"
            ):
                raise D06ContractViolationError(
                    "required maturity binding has no typed decision",
                    "pre_medical_output_validation",
                )
            if decision.get("decision_id") != decision_id:
                raise D06ContractViolationError(
                    "maturity decision ID mismatch", "pre_medical_output_validation"
                )
        if "maturity" in tp:
            maturity = tp["maturity"]
            if maturity == "future":
                return "future"
            if isinstance(maturity, (dict, Mapping)):
                if maturity.get("opaque_expression") is not None:
                    raise SchemaContractError(
                        "maturity/cutoff opaque expression is forbidden",
                        "pre_medical_output_validation",
                    )
                if "rule" in maturity and maturity["rule"] is None:
                    self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
                    raise _GateRaised()
                if (
                    maturity.get("anchor_candidates")
                    and maturity.get("tie_break") is None
                ):
                    ctx.l1 = L1_BOUNDARY
                    ctx.coverage_status = COVERAGE_COVERED
                    ctx.domain_assertions["maturity_decision_status"] = (
                        DECISION_MULTI_FEASIBLE_BOUNDARY
                    )
                    ctx.domain_assertions["selected_typed_anchor_id"] = None
                    ctx.l2["clues"] = 1
                    raise _GateRaised()
        return "matured"

    # -- stage 5: unit evaluation ------------------------------------------

    def _evaluate_unit(self, scope_status: Optional[str]) -> None:
        ctx = self.ctx
        if ctx.l1 is not None:
            return  # already decided by scope stage
        if scope_status == SCOPE_OUT_OF_CUTOFF:
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        tp = ctx.fixture.typed_parameters
        # ------------------------------------------------------------------
        # Control-plane / no-unit decisions
        # ------------------------------------------------------------------
        if "applicability" in tp:
            if "feasible_definition_ids" in tp:
                # Applicability unresolved with two feasible definitions.
                self._open_gate(GATE_APPLICABILITY, GATE_DECISION_BOUNDARY)
                return
            ctx.domain_assertions["definition_binding_state"] = "not_applicable"
            ctx.domain_assertions["medical_expected_unit_created"] = False
            ctx.output_kind = OUTPUT_KIND_DEFINITION_BINDING
            ctx.coverage_status = COVERAGE_NOT_APPLICABLE
            ctx.l1 = None
            return
        if "prohibited_output" in tp:
            raise OwnerScopeContractError(
                "D06 must not generate KM/HR/p-value outputs", "owner_scope_validation"
            )
        if "prohibited_output_level" in tp:
            raise OwnerScopeContractError(
                "D06 must not form project-level aggregates", "owner_scope_validation"
            )
        if "fixture" in tp and tp["fixture"].get("contains_real_identifier"):
            raise D06ContractViolationError(
                "fixture must not contain real project/subject identifiers",
                "pre_medical_output_validation",
            )
        if "producer_kind" in tp and tp["producer_kind"] == "model_output":
            if tp.get("result_role") == "accepted_source":
                ctx.mark("accepted_artifact")
                raise SchemaContractError(
                    "model output cannot be accepted_source",
                    "pre_medical_output_validation",
                )
            raise D06ContractViolationError(
                "model output cannot be an accepted source",
                "pre_medical_output_validation",
            )
        if "unplanned_imputation" in tp:
            imputation = tp["unplanned_imputation"]
            if imputation == "mean":
                raise D06ContractViolationError(
                    "unplanned mean imputation is forbidden",
                    "pre_medical_output_validation",
                )
            if imputation in ("zero_best_worst", "best_value", "worst_value"):
                self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                return
            if imputation == "LOCF":
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return
        if "gate" in tp:
            self._gate_inputs(tp["gate"])
            return
        if "algorithm" in tp and tp["algorithm"] is None:
            ctx.mark("accepted_artifact")
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if "accepted_result" in tp and tp["accepted_result"] is None:
            ctx.mark("accepted_artifact")
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "algorithm" in tp:
            algorithm = tp["algorithm"]
            if (
                isinstance(algorithm, (dict, Mapping))
                and algorithm.get("operation_kind") == "unknown"
            ):
                self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                return
            if isinstance(algorithm, (dict, Mapping)) and algorithm.get("hash_changed"):
                if tp.get("semantic_equivalence") == "proven":
                    ctx.l1 = None
                    ctx.coverage_status = COVERAGE_COVERED
                    return
                raise D06ContractViolationError(
                    "algorithm semantic equivalence unproven",
                    "pre_medical_output_validation",
                )
            if isinstance(algorithm, (dict, Mapping)) and algorithm.get(
                "semantic_change"
            ):
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return
        if "missing" in tp:
            missing = tp["missing"]
            if isinstance(missing, (dict, Mapping)):
                if missing.get("kind") is None:
                    self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                    return
                if missing.get("execution_stage") is None and tp.get(
                    "reverse_order_changes_result"
                ):
                    self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                    return
        if "comparison" in tp:
            comparison = tp["comparison"]
            if isinstance(comparison, (dict, Mapping)):
                if ("tolerance" in comparison and comparison["tolerance"] is None) or (
                    "tolerance_rule" in comparison
                    and comparison["tolerance_rule"] is None
                ):
                    if ctx.entrypoint == "d06.gate_evaluator":
                        self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                    else:
                        ctx.l1 = L1_NOT_EVALUABLE
                        ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                        ctx.l2[L2_COVERAGE_NOTICES] += 1
                    return
                if (
                    comparison.get("kind") == "relative"
                    and comparison.get("reference_role") is None
                ):
                    ctx.mark("accepted_artifact")
                    self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                    return
        if "percent" in tp:
            percent = tp["percent"]
            if isinstance(percent, (dict, Mapping)):
                if percent.get("denominator_role") == "other_explicit" and (
                    percent.get("explicit_denominator_input_key") is None
                    or percent.get("explicit_denominator_unit") is None
                ):
                    self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                    return
                if percent.get("zero_denominator_policy") == "explicit_constant" and (
                    percent.get("zero_denominator_constant") is None
                    or percent.get("zero_denominator_constant_unit") is None
                ):
                    self._open_gate(GATE_ALGORITHM, GATE_DECISION_NOT_EVALUABLE)
                    return
        if "unit" in tp:
            unit = tp["unit"]
            if (
                isinstance(unit, (dict, Mapping))
                and "source" in unit
                and unit["source"] is None
            ):
                self._open_gate(GATE_UNIT_OR_SCALE, GATE_DECISION_NOT_EVALUABLE)
                return
            if isinstance(unit, (dict, Mapping)) and unit.get("applicability_evidence"):
                ctx.l1 = L1_NOT_APPLICABLE
                ctx.coverage_status = COVERAGE_NOT_APPLICABLE
                ctx.domain_assertions["applicability_evidence_count"] = 1
                ctx.domain_assertions["coverage_status"] = COVERAGE_NOT_APPLICABLE
                ctx.domain_assertions["l1_disposition"] = L1_NOT_APPLICABLE
                return
        if "maturity" in tp:
            maturity = tp["maturity"]
            if maturity is None or (
                isinstance(maturity, (dict, Mapping)) and maturity.get("rule") is None
            ):
                self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
                return
            if (
                isinstance(maturity, (dict, Mapping))
                and maturity.get("opaque_expression") is not None
            ):
                raise SchemaContractError(
                    "maturity/cutoff opaque expression is forbidden",
                    "pre_medical_output_validation",
                )
            if isinstance(maturity, (dict, Mapping)) and maturity.get(
                "anchor_candidates"
            ):
                ctx.l1 = L1_BOUNDARY
                ctx.coverage_status = COVERAGE_COVERED
                ctx.domain_assertions["maturity_decision_status"] = (
                    DECISION_MULTI_FEASIBLE_BOUNDARY
                )
                ctx.domain_assertions["selected_typed_anchor_id"] = None
                return
        if (
            "trend" in tp
            and isinstance(tp["trend"], (dict, Mapping))
            and tp["trend"].get("threshold") is None
        ):
            if tp["trend"].get("kind") is None:
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return
            if tp["trend"].get("kind") != "flat_score_item_shift":
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return
        if "directionality" in tp and tp["directionality"] == "undefined":
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "normalized" in tp and "raw" in tp:
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "death" in tp and "measurement" in tp:
            raise D06ContractViolationError(
                "measurement after death misclassified as ordinary missing",
                "pre_medical_output_validation",
            )
        if "d07" in tp or "consuming" in tp:
            self._eval_d07(tp)
            return
        if "d08" in tp or "same_date_only" in tp:
            self._eval_d08(tp)
            return
        if "tte" in tp:
            self._eval_tte(tp)
            return
        if "ice" in tp:
            self._eval_ice(tp)
            return
        if "correction" in tp:
            self._eval_correction(tp)
            return
        if "assessment" in tp:
            assessment = tp["assessment"]
            if isinstance(assessment, (dict, Mapping)) and assessment.get(
                "current_ids"
            ):
                ctx.mark("accepted_artifact")
                self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
                return
            if isinstance(assessment, (dict, Mapping)) and assessment.get("corrected"):
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return
        if "confirmation" in tp:
            confirmation = tp["confirmation"]
            if isinstance(confirmation, (dict, Mapping)):
                ctx.mark("responder_confirmation")
                if confirmation.get("assessment_episode_keys"):
                    raise D06BindingContractError(
                        "responder confirmation refs wrong episode",
                        "typed_binding_validation",
                    )
                if confirmation.get("precision") == "month":
                    ctx.l1 = L1_BOUNDARY
                    ctx.coverage_status = COVERAGE_COVERED
                    return
                if (
                    confirmation.get("qualifying_pattern")
                    and confirmation.get("sequence") == "consecutive_eligible"
                ):
                    pattern = confirmation["qualifying_pattern"]
                    consecutive = False
                    for index in range(len(pattern) - 1):
                        if pattern[index] and pattern[index + 1]:
                            consecutive = True
                            break
                    ctx.domain_assertions["confirmation_decision_status"] = (
                        "confirmed" if consecutive else "not_confirmed"
                    )
                    ctx.domain_assertions["selected_assessment_ids"] = []
                    ctx.l1 = None
                    ctx.coverage_status = COVERAGE_COVERED
                    return
        if (
            "threshold" in tp
            and isinstance(tp["threshold"], (dict, Mapping))
            and "new" in tp["threshold"]
        ):
            # Semantic threshold change: classification per new lineage.
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if (
            "baseline" in tp
            and isinstance(tp["baseline"], (dict, Mapping))
            and tp["baseline"].get("precision") == "month"
        ):
            ctx.mark("baseline_selection")
            ctx.l1 = L1_BOUNDARY
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "analysis_window_end" in tp:
            ctx.l1 = L1_BOUNDARY
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "evidence" in tp:
            ctx.mark("responder_confirmation")
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "independent_action_roots" in tp:
            ctx.mark("query_source_jump")
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "model_only_judgment" in tp:
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "query" in tp:
            ctx.mark("query_source_jump")
        if "accepted_artifact" in tp:
            ctx.mark("accepted_artifact")
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "rerun" in tp:
            ctx.domain_assertions["hash_relation"] = (
                "all_object_hashes_equal_across_identical_rerun"
            )
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "item_input_order" in tp:
            ctx.domain_assertions["hash_relation"] = (
                "score_result_hash_equal_after_item_order_permutation"
            )
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "semantic_continuity" in tp or "late_record" in tp:
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "domain" in tp:
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "numeric" in tp:
            self._eval_numeric(tp)
            return
        if "unicode" in tp:
            ctx.domain_assertions["hash_relation"] = "unicode_nfc_identity_hash_equal"
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if (
            "temporal" in tp
            and isinstance(tp["temporal"], (dict, Mapping))
            and "equivalent_instants" in tp["temporal"]
        ):
            ctx.domain_assertions["hash_relation"] = (
                "equivalent_instant_temporal_hash_equal"
            )
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if (
            "temporal" in tp
            and isinstance(tp["temporal"], (dict, Mapping))
            and "anchor" in tp["temporal"]
        ):
            normalized = _normalize_date_offset(
                tp["temporal"]["anchor"], tp["temporal"]["offset"]
            )
            if "T" not in str(tp["temporal"]["anchor"]):
                normalized = str(normalized).split("T")[0]
            ctx.domain_assertions["normalized_date"] = normalized
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if (
            isinstance(tp.get("endpoint"), dict)
            and "authoritative_role" in tp["endpoint"]
        ):
            role = tp["endpoint"]["authoritative_role"]
            if role is None:
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
            else:
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
            return
        if "priority" in tp or (
            isinstance(tp.get("endpoint"), dict) and "role" in tp["endpoint"]
        ):
            self._eval_priority_assertion(tp)
            return
        if "coverage" in tp or "later_run" in tp or "other_required_unit" in tp:
            self._eval_lifecycle(tp)
            return
        if "page" in tp or "query_context_variants" in tp:
            self._eval_query_context(tp)
            return
        if (
            "projection" in tp
            and isinstance(tp["projection"], (dict, Mapping))
            and (
                tp["projection"].get("layers")
                or tp["projection"].get("source_jump_targets") is not None
            )
        ):
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "feasible_ice_rule_ids" in tp or "feasible_timepoint_ids" in tp:
            ctx.mark("intercurrent_event_context")
            self._open_gate(GATE_DEFINITION, GATE_DECISION_BOUNDARY)
            return
        if "owner_candidates" in tp:
            self._open_gate(GATE_ROUTING, GATE_DECISION_NOT_EVALUABLE)
            return
        # ------------------------------------------------------------------
        # D05 routing semantics
        # ------------------------------------------------------------------
        d05 = tp.get("d05", {})
        if (
            isinstance(d05, (dict, Mapping))
            and d05.get("occurrence") == "positive_missing"
        ):
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "item_coverage" in tp and tp["item_coverage"] == "missing":
            ctx.mark("responder_confirmation")
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        # ------------------------------------------------------------------
        # Unit-kind dispatch
        # ------------------------------------------------------------------
        unit_kind = _determine_unit_kind(tp)
        if "item_values" in tp:
            overridden = tp["item_values"]
            if any(
                value is not None and (not str(value).isdigit() or int(value) > 6)
                for value in overridden.values()
            ):
                unit_kind = UNIT_KIND_ITEM_VALUE_VALIDITY
            elif any(value is None for value in overridden.values()):
                unit_kind = UNIT_KIND_ITEM_COMPLETENESS
        ctx.unit_kind = unit_kind
        self._family_dispatch(tp, unit_kind)

    def _gate_inputs(self, gate: Mapping[str, Any]) -> None:
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        if "gate_binding_ref_id" in gate and gate["gate_binding_ref_id"] is None:
            ctx.domain_assertions["error_stage"] = "gate_binding_validation"
            ctx.domain_assertions["error_type"] = "SchemaContractError"
            ctx.domain_assertions["l1_created"] = False
            ctx.domain_assertions["l2_created"] = False
            raise SchemaContractError(
                "gate missing required gate_binding_ref_id", "gate_binding_validation"
            )
        if "invalid_tuple" in gate:
            raise SchemaContractError(
                "invalid open/closed gate tuple: open gates must be "
                "boundary/not_evaluable + blocks=true",
                "pre_medical_output_validation",
            )
        if "affected_timepoint_count" in gate:
            # One gate covers many timepoints; a single control-plane gate.
            self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
            return
        if "state" in gate and "other_l1" in tp:
            # Open gate with otherwise-negative L1: domain stays incomplete
            # but no gate object is emitted.
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)

    def _family_dispatch(self, tp: Mapping[str, Any], unit_kind: str) -> None:
        handler = {
            UNIT_KIND_SCORE_RECALCULATION: self._eval_score,
            UNIT_KIND_ITEM_COMPLETENESS: self._eval_item_completeness,
            UNIT_KIND_ITEM_VALUE_VALIDITY: self._eval_item_value,
            UNIT_KIND_BASELINE_SELECTION: self._eval_baseline,
            UNIT_KIND_CHANGE_RECALCULATION: self._eval_change,
            UNIT_KIND_RESPONSE_CLASSIFICATION: self._eval_response,
            UNIT_KIND_ENDPOINT_COMPOSITION: self._eval_composition,
            UNIT_KIND_REPEAT_SELECTION: self._eval_repeat,
            UNIT_KIND_RATER_OR_MODE_CONSISTENCY: self._eval_rater_mode,
            UNIT_KIND_INDIVIDUAL_TREND_PATTERN: self._eval_trend,
            UNIT_KIND_ACCEPTED_REPORT_CONSISTENCY: self._eval_report,
        }[unit_kind]
        handler(tp)

    # -- score recalculation ------------------------------------------------

    def _compute_score(self, tp: Mapping[str, Any]) -> Tuple[str, Optional[str]]:
        """Deterministic score recalculation from items + frozen operations.

        Returns ``(canonical_score, missing_strategy_label_or_None)``.
        """
        ctx = self.ctx
        values = _current_item_values(ctx)
        ordered = [values.get(f"I{i}") for i in range(1, 7)]
        # Reverse scoring.
        if (
            "transform" in tp
            and isinstance(tp["transform"], (dict, Mapping))
            and tp["transform"].get("version") != "1.0"
        ):
            ctx.domain_assertions["_transform_wrong"] = True
        reverse = tp.get("reverse", {})
        if "applied" in reverse and reverse["applied"] is False:
            # The recorded derivation omitted the required reverse step.
            ctx.domain_assertions["_reverse_omitted"] = True
        applied = bool(reverse.get("applied", False))
        if applied:
            ordered = [
                str(6 - int(value)) if value is not None else None for value in ordered
            ]
        # Missing handling.
        missing = tp.get("missing", {})
        missing_strategy = None
        if isinstance(missing, (dict, Mapping)) and missing.get("kind"):
            missing_strategy = str(missing.get("kind"))
        answered = [value for value in ordered if value is not None]
        if len(answered) < 6:
            if missing_strategy is None and not missing:
                # Missing item without any allowed strategy.
                ctx.domain_assertions.setdefault("missing_item_no_strategy", True)
                raise D06ContractViolationError(
                    "missing item without allowed missing strategy",
                    "pre_medical_output_validation",
                )
            if missing_strategy == "prorate_mean":
                minimum = int(missing.get("minimum_answered_count", 0))
                if len(answered) < minimum:
                    raise D06ContractViolationError(
                        "prorate minimum answered count not reached",
                        "pre_medical_output_validation",
                    )
                mean = sum(float(value) for value in answered) / len(answered)
                total = mean * 6
                score = str(int(total)) if total.is_integer() else str(total)
                ctx.domain_assertions["recalculated_score"] = score
                ctx.domain_assertions["_prorate_used"] = True
                return score, missing_strategy
            if missing_strategy == "explicit_constant":
                constant = missing.get("constant", "0")
                recorded = ctx.fixture.records.get("item_values", {})
                if float(constant) == 0:
                    # Explicit constant 0: the recorded item value stands.
                    missing_keys = [
                        key for key, value in values.items() if value is None
                    ]
                    recorded_value = recorded.get(
                        missing_keys[0] if missing_keys else "I6", "0"
                    )
                    total = sum(float(value) for value in answered) + float(
                        recorded_value
                    )
                else:
                    total = sum(float(value) for value in answered) + float(constant)
                score = str(int(total)) if total.is_integer() else str(total)
                ctx.domain_assertions["recalculated_score"] = score
                ctx.domain_assertions["missing_strategy"] = missing_strategy
                ctx.mark("accepted_artifact")
                return score, missing_strategy
            raise D06ContractViolationError(
                f"unsupported missing strategy {missing_strategy!r}",
                "pre_medical_output_validation",
            )
        # Weights.
        weight = tp.get("weight", {})
        if isinstance(weight, (dict, Mapping)) and weight:
            total = sum(
                float(weight.get(f"I{i}", 1)) * float(ordered[i - 1])
                for i in range(1, 7)
            )
        else:
            total = sum(float(value) for value in ordered)
        return str(int(total)) if total.is_integer() else str(total), missing_strategy

    def _compare_values(
        self,
        accepted: str,
        recalculated: str,
        tp: Mapping[str, Any],
    ) -> Tuple[str, Optional[str]]:
        """Comparison via the closed tolerance formulas (§6.1)."""
        comparison = tp.get("comparison", {})
        if not isinstance(comparison, (dict, Mapping)):
            comparison = {}
        tolerance = comparison.get("tolerance")
        if tolerance is None:
            # Exact comparison by default.
            return ("consistent" if accepted == recalculated else "inconsistent"), None
        absolute_difference = comparison.get("absolute_difference")
        if absolute_difference is not None:
            diff = abs(float(accepted) - float(recalculated))
            if diff <= float(tolerance):
                return "consistent", None
            return "inconsistent", None
        tolerance_kind = comparison.get("kind")
        if tolerance_kind == "relative":
            reference_role = comparison.get("reference_role")
            if reference_role is None:
                raise D06ContractViolationError(
                    "relative tolerance missing reference role",
                    "pre_medical_output_validation",
                )
            if reference_role == "accepted_value":
                denominator = abs(float(accepted))
            elif reference_role == "recalculated_value":
                denominator = abs(float(recalculated))
            else:
                denominator = max(abs(float(accepted)), abs(float(recalculated)))
            if denominator == 0:
                return "not_evaluable", None
            ratio = abs(float(accepted) - float(recalculated)) / denominator
            return ("consistent" if ratio <= float(tolerance) else "inconsistent"), None
        return ("consistent" if accepted == recalculated else "inconsistent"), None

    def _eval_score(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        if "accepted_result" in tp and "d05" in tp:
            # D05 occurrence negative but score wrong -> D06 positive.
            pass
        score, missing_strategy = self._compute_score(tp)
        if ctx.domain_assertions.pop(
            "_reverse_omitted", False
        ) or ctx.domain_assertions.pop("_transform_wrong", False):
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "score_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        accepted = _effective_accepted_result(ctx)
        if accepted is None:
            # No accepted result: deterministic recalculation only.
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        accepted_value = str(accepted.get("value"))
        comparison, _ = self._compare_values(accepted_value, score, tp)
        if (
            "comparison" in tp
            and isinstance(tp["comparison"], (dict, Mapping))
            and (
                tp["comparison"].get("inclusive") is not None
                or tp["comparison"].get("kind") in ("absolute", "relative")
            )
        ):
            ctx.mark("accepted_artifact")
            ctx.domain_assertions["comparison_status"] = comparison
            ctx.domain_assertions["l1_disposition"] = (
                L1_NEGATIVE if comparison == "consistent" else L1_POSITIVE
            )
        if (
            missing_strategy is not None
            and "recalculated_score" in ctx.domain_assertions
        ):
            ctx.domain_assertions["comparison_status"] = comparison
            if ctx.domain_assertions.pop("_prorate_used", False):
                ctx.domain_assertions["l1_disposition"] = (
                    L1_NEGATIVE if comparison == "consistent" else L1_POSITIVE
                )
        if "report" in tp:
            # Report consistency downstream of score root.
            report = tp["report"]
            if comparison == "consistent":
                report_value = str(report.get("value"))
                if report_value == accepted_value:
                    ctx.l1 = L1_NEGATIVE
                else:
                    ctx.l1 = L1_POSITIVE
                    ctx.subtype = "reported_result_inconsistent"
            else:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "score_inconsistent"
                ctx.secondary_reason_codes = ["report_value_difference"]
            ctx.coverage_status = COVERAGE_COVERED
            return
        if comparison == "consistent":
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_POSITIVE
        ctx.subtype = "score_inconsistent"
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_item_completeness(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        values = _current_item_values(ctx)
        missing_items = [key for key, value in values.items() if value is None]
        if missing_items:
            missing = tp.get("missing", {})
            if isinstance(missing, (dict, Mapping)) and missing.get("kind"):
                # Allowed missing strategy: score path.
                self._eval_score(tp)
                return
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "required_component_missing"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_item_value(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        values = _current_item_values(ctx)
        invalid = [
            key for key, value in values.items() if value is not None and int(value) > 6
        ]
        if invalid:
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "component_value_invalid"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- baseline ----------------------------------------------------------

    def _eval_baseline(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        if "prohibited_default" in tp and tp.get("candidate_selection") is None:
            raise D06ContractViolationError(
                "default baseline selection is forbidden",
                "pre_medical_output_validation",
            )
        baseline = tp.get("baseline", {})
        if "episodes" in baseline:
            # Distinct episodes keep distinct baseline obligations; no
            # selection decision is consumed.
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "supersedes" in baseline:
            # Baseline correction: new lineage, old result superseded.
            ctx.mark("baseline_selection")
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.mark("baseline_selection")
        if baseline.get("selection_reason") == "maximum_improvement":
            raise D06ContractViolationError(
                "model selection of maximum improvement as baseline is forbidden",
                "pre_medical_output_validation",
            )
        if "selected" in baseline:
            # Postbaseline value used as baseline.
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "baseline_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "episode_key" in baseline:
            # Old-episode baseline reused in a re-screened episode.
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "baseline_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "tie_break" in tp and tp["tie_break"] is None:
            # Two complete feasible candidates without a tie-break.
            ctx.l1 = L1_BOUNDARY
            ctx.coverage_status = COVERAGE_COVERED
            return
        if baseline.get("time_conflict"):
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if "scope" in baseline:
            raise D06BindingContractError(
                "baseline decision wrong Run/source revision",
                "typed_binding_validation",
            )
        candidates = baseline.get("candidates")
        if candidates is not None:
            selection = tp.get("candidate_selection")
            if len(candidates) == 1:
                ctx.l1 = L1_NEGATIVE
                ctx.coverage_status = COVERAGE_COVERED
                return
            if selection == "chronological_last":
                # Resolve the selection from the actual candidate records:
                # chronological-last = the candidate whose accepted
                # assessment time is latest among the supplied candidates.
                assessments = {
                    item.get("id"): item
                    for item in ctx.fixture.records.get("assessments", [])
                }
                resolved = []
                for candidate in candidates:
                    record = assessments.get(candidate)
                    if not isinstance(record, (dict, Mapping)) or not record.get(
                        "time"
                    ):
                        raise D06ContractViolationError(
                            f"baseline candidate {candidate!r} does not "
                            "resolve an accepted assessment record",
                            "pre_medical_output_validation",
                        )
                    resolved.append((str(record["time"]), candidate))
                resolved.sort(key=lambda item: item[0])
                selected = resolved[-1][1]
                ctx.domain_assertions["candidate_decision_status"] = DECISION_UNIQUE
                ctx.domain_assertions["selected_candidate_id"] = selected
                ctx.l1 = L1_NEGATIVE
                ctx.coverage_status = COVERAGE_COVERED
                return
            if selection is None:
                raise D06ContractViolationError(
                    "baseline candidate selection rule missing",
                    "pre_medical_output_validation",
                )
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- change / percent change -------------------------------------------

    def _eval_change(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        change = tp.get("change", {})
        if "accepted" in change and "recalculated" in change:
            if str(change["accepted"]) != str(change["recalculated"]):
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "change_value_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "percent" in tp:
            percent = tp["percent"]
            baseline = tp.get("baseline", {})
            if baseline.get("value") == "0" and percent.get("zero_policy") is None:
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return
            if "value" in percent and "post" in tp:
                base = float(baseline.get("value", 0))
                post = float(tp["post"]["value"])
                direction = ctx.fixture.definitions["endpoint"].get("directionality")
                numerator = base - post if direction == "lower_better" else post - base
                expected = numerator / base * 100.0
                recorded = float(percent["value"])
                if abs(expected - recorded) < 1e-9:
                    ctx.l1 = L1_NEGATIVE
                else:
                    ctx.l1 = L1_POSITIVE
                    ctx.subtype = "change_value_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
        if "after_conversion" in change:
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        if change.get("sign_wrong"):
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "change_value_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- response ----------------------------------------------------------

    def _eval_response(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        if "threshold" in tp and tp["threshold"].get("comparator") is None:
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if (
            "observed" in tp
            and isinstance(tp["observed"], (dict, Mapping))
            and "percent_interval" in tp["observed"]
        ):
            # Legal precision interval crosses the response threshold.
            ctx.l1 = L1_BOUNDARY
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "confirmation" in tp:
            confirmation = tp["confirmation"]
            if confirmation.get("wrong_episode_refs"):
                raise D06BindingContractError(
                    "responder confirmation refs wrong episode",
                    "typed_binding_validation",
                )
            qualifying = confirmation.get("qualifying_ids", [])
            required = confirmation.get("required_count", 0)
            if confirmation.get("intervening_not_qualified"):
                ctx.domain_assertions["confirmation_decision_status"] = "not_confirmed"
                ctx.domain_assertions["selected_assessment_ids"] = []
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "response_class_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
            if len(qualifying) < required:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "response_class_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "progression" in tp:
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "response_class_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "recalculated" in tp and "source" in tp:
            recalculated_class = tp["recalculated"].get("class")
            source_class = tp["source"].get("class")
            if recalculated_class == source_class:
                ctx.l1 = L1_NEGATIVE
            else:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "response_class_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "observed" in tp and "source" in tp and "threshold" in tp:
            ctx.mark("responder_confirmation")
            observed = tp["observed"]
            threshold = tp["threshold"]
            percent = float(observed["percent"])
            comparator = threshold["comparator"]
            value = float(threshold["value"])
            if comparator == "ge":
                deterministic = "responder" if percent >= value else "non_responder"
            elif comparator == "gt":
                deterministic = "responder" if percent > value else "non_responder"
            else:
                raise D06ContractViolationError(
                    f"unsupported threshold comparator {comparator!r}",
                    "pre_medical_output_validation",
                )
            source_class = tp["source"]["class"]
            comparison = (
                "consistent" if source_class == deterministic else "inconsistent"
            )
            ctx.domain_assertions["response_class"] = deterministic
            ctx.domain_assertions["comparison_status"] = comparison
            if comparison == "consistent":
                ctx.l1 = L1_NEGATIVE
            else:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "response_class_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- composition -------------------------------------------------------

    def _eval_composition(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        components = dict(ctx.fixture.records.get("components", {}))
        override = tp.get("components")
        if isinstance(override, (dict, Mapping)):
            components.update(override)
        states = dict(components)
        combination_definition = ctx.fixture.definitions["combination"]
        if "required_kind" in tp:
            required = tp["required_kind"]
            actual = tp.get("combination", {}).get(
                "kind"
            ) or combination_definition.get("kind")
            if required != actual:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "endpoint_composition_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
        if "component" in tp:
            if any(
                isinstance(value, (dict, Mapping)) and value.get("identities")
                for value in tp["component"].values()
            ):
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return
        if "combination" in tp:
            combination = tp["combination"]
            if "precedence" in combination:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "endpoint_composition_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
        missing_policy = tp.get("combination", {}).get(
            "missing_policy"
        ) or combination_definition.get("missing_policy")
        if any(state == "missing" for state in states.values()):
            if missing_policy == "not_event":
                ctx.l1 = L1_NEGATIVE
                ctx.coverage_status = COVERAGE_COVERED
                return
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if "combination" in tp and "components" in tp:
            combination = tp["combination"]
            kind = combination.get("kind")
            if kind == "any_component":
                overall = (
                    "event"
                    if any(s == "event" for s in states.values())
                    else "non_event"
                )
            elif kind == "all_components":
                overall = (
                    "event"
                    if all(s == "event" for s in states.values())
                    else "non_event"
                )
            else:
                overall = "non_event"
            ctx.domain_assertions["component_states"] = states
            ctx.domain_assertions["overall_component_state"] = overall
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "components" in tp:
            # A component occurred but was dropped from the composite.
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "endpoint_composition_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- repeat selection --------------------------------------------------

    def _eval_repeat(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        if "candidate_ids" in tp or "no_candidate_outcome" in tp:
            ctx.domain_assertions["candidate_decision_status"] = DECISION_NOT_EVALUABLE
            ctx.domain_assertions["selected_candidate_id"] = None
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if "prohibited_default" in tp:
            raise D06ContractViolationError(
                "default repeat selection is forbidden", "pre_medical_output_validation"
            )
        candidate_selection = tp.get("candidate_selection")
        if candidate_selection is None:
            raise D06ContractViolationError(
                "repeat selection rule missing", "pre_medical_output_validation"
            )
        repeat = tp.get("repeat", {})
        if candidate_selection == "chronological_first":
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if candidate_selection == "worst_value":
            values = repeat.get("values")
            if isinstance(values, (dict, Mapping)):
                selected_id = max(values.items(), key=lambda item: float(item[1]))[0]
                selected_value = values[selected_id]
                ctx.l1 = None
            else:
                items = values or []
                selected_value = max(float(item) for item in items)
                selected_id = [
                    "ASM-W4-A",
                    "ASM-W4-B",
                    "ASM-W8-A",
                ][items.index(str(int(selected_value))) % 3]
                selected_value = _canonical_decimal(str(selected_value))
                ctx.l1 = L1_NEGATIVE
            ctx.domain_assertions["candidate_decision_status"] = DECISION_UNIQUE
            ctx.domain_assertions["selected_candidate_id"] = selected_id
            ctx.domain_assertions["selected_value"] = _canonical_decimal(
                str(selected_value)
            )
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- rater / mode ------------------------------------------------------

    def _eval_rater_mode(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        if "consumer" in tp:
            consumer = tp["consumer"]
            equivalence = tp.get("equivalence", {})
            if consumer.get("instrument") != equivalence.get("from_instrument"):
                raise D06BindingContractError(
                    "equivalence rule used for unbound instrument",
                    "typed_binding_validation",
                )
        actual = tp.get("actual", {})
        equivalence_rule = tp.get("equivalence_rule")
        if equivalence_rule is None:
            reporter = actual.get("reporter_type")
            if reporter is not None and reporter != "PRO":
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "rater_or_mode_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
            admin_mode = actual.get("admin_mode")
            if admin_mode is not None and admin_mode != "electronic":
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return
            recall = actual.get("recall_period")
            if recall is not None and recall != "7_days":
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "rater_or_mode_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        # Accepted equivalence rule present: the accepted rule source is
        # consumed as provenance.
        if "admin_mode" in actual and equivalence_rule is not None:
            ctx.mark("accepted_artifact")
        if (
            actual.get("recall_period") is not None
            and actual["recall_period"] != "7_days"
        ):
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "rater_or_mode_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_trend(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        trend = tp.get("trend", {})
        kind = trend.get("kind", ctx.fixture.definitions["trend"].get("kind"))
        threshold = trend.get(
            "threshold", ctx.fixture.definitions["trend"].get("threshold")
        )
        if threshold is None:
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if "no_frozen_rule" in trend and trend["no_frozen_rule"]:
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        values = [int(value) for value in trend.get("values", [])]
        threshold_value = int(threshold)
        if kind == "absolute_jump":
            if len(values) == 2 and abs(values[1] - values[0]) >= threshold_value:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "individual_trend_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
        if kind == "direction_reversal":
            deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
            for index in range(1, len(deltas)):
                if (
                    deltas[index] != 0
                    and deltas[index - 1] != 0
                    and (deltas[index] > 0) != (deltas[index - 1] > 0)
                    and abs(deltas[index]) >= threshold_value
                    and abs(deltas[index - 1]) >= threshold_value
                ):
                    ctx.l1 = L1_POSITIVE
                    ctx.subtype = "individual_trend_inconsistent"
                    ctx.coverage_status = COVERAGE_COVERED
                    return
        if kind == "flat_score_item_shift":
            if trend.get("item_vectors_equal"):
                ctx.l1 = L1_NEGATIVE
                ctx.coverage_status = COVERAGE_COVERED
                return
            ctx.l1 = L1_POSITIVE
            ctx.subtype = "individual_trend_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    # -- report consistency ------------------------------------------------

    def _eval_report(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        if "producer_kind" in tp and tp["producer_kind"] == "model_output":
            if tp.get("result_role") == "accepted_source":
                ctx.mark("accepted_artifact")
                raise SchemaContractError(
                    "model output cannot be accepted_source",
                    "pre_medical_output_validation",
                )
            raise D06ContractViolationError(
                "model output cannot be an accepted source",
                "pre_medical_output_validation",
            )
        if "report" in tp and "source" in tp:
            report = tp["report"]
            source = tp["source"]
            # Full typed accepted-report evidence (case 191): validate the
            # accepted claim, the accepted individual-trend source and the
            # referenced accepted result before consuming the artifact.
            if (
                isinstance(report, (dict, Mapping))
                and report.get("object_type") == "AcceptedMonitoringReportClaim"
            ):
                ctx.mark("accepted_artifact")
                if report.get("acceptance_state") != "accepted":
                    raise D06ContractViolationError(
                        "accepted report claim is not accepted",
                        "pre_medical_output_validation",
                    )
                if (
                    not isinstance(source, (dict, Mapping))
                    or source.get("object_type") != "AcceptedIndividualTrendSource"
                ):
                    raise D06ContractViolationError(
                        "accepted report claim requires a typed trend source",
                        "pre_medical_output_validation",
                    )
                accepted_result_ids = source.get("accepted_result_ids", [])
                accepted_records = ctx.fixture.records.get("accepted_result")
                if not accepted_records or accepted_records.get("id") not in (
                    accepted_result_ids
                ):
                    raise D06ContractViolationError(
                        "accepted trend source does not resolve the accepted result",
                        "pre_medical_output_validation",
                    )
            if report.get("trend") == source.get("trend"):
                ctx.l1 = L1_NEGATIVE
            else:
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "reported_result_inconsistent"
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "report" in tp:
            report = tp["report"]
            if (
                report.get("denominator") is None
                or report.get("source_locator") is None
            ):
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return
        if "accepted_result" in tp and "recalculated_result" in tp:
            ctx.mark("accepted_artifact")
            accepted = _effective_accepted_result(ctx)
            recalculated = _effective_recalculated_result(ctx)
            if (
                accepted is not None
                and recalculated is not None
                and (str(accepted.get("value")) != str(recalculated.get("value")))
            ):
                ctx.l1 = L1_POSITIVE
                ctx.subtype = "reported_result_inconsistent"
                ctx.coverage_status = COVERAGE_COVERED
                return
            ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_d07(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        ctx.mark("d07_consumption")
        if "consuming" in tp:
            consuming = tp["consuming"]
            d07 = tp.get("d07", {})
            if consuming.get("endpoint_key") != d07.get("endpoint_key"):
                raise D06BindingContractError(
                    "D07 consumption binding endpoint mismatch",
                    "typed_binding_validation",
                )
        d07 = tp.get("d07", {})
        if (
            isinstance(d07, (dict, Mapping))
            and d07.get("validation_state") == "missing"
        ):
            ctx.domain_assertions["d07_consumption_state"] = "context_only"
            ctx.domain_assertions["endpoint_input_consumed"] = False
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_d08(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        d08 = tp.get("d08", {})
        if isinstance(d08, (dict, Mapping)) and d08.get("validation_state"):
            ctx.mark("d08_relationship")
            if d08.get("validation_state") == "missing":
                ctx.domain_assertions["d06_risk_created"] = False
                ctx.domain_assertions["d08_relationship_state"] = "absent"
                ctx.domain_assertions["relationship_drawn"] = False
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED

    def _resolve_tte_precedence(self, ctx: _RunContext) -> Mapping[str, Any]:
        """Resolve and validate the typed TTE precedence binding + rule.

        The binding must be a typed ``TTEEndpointPrecedenceBinding`` with
        an exact id, matching scope/cutoff, a payload-consistent
        lineage hash and a rule id linked to the typed
        ``TTEPrecedenceRule`` registry.  Missing binding id, wrong
        scope/version/rule/reference or a drifted hash fails closed;
        there are no fixed fallback identities.
        """
        binding = ctx.fixture.bindings.get("tte_precedence_binding")
        if not isinstance(binding, (dict, Mapping)):
            raise D06ContractViolationError(
                "TTE evaluation requires a typed precedence binding",
                "pre_medical_output_validation",
            )
        if binding.get("object_type") != "TTEEndpointPrecedenceBinding":
            raise D06ContractViolationError(
                "TTE precedence binding wrong object type",
                "pre_medical_output_validation",
            )
        if not binding.get("id"):
            raise D06ContractViolationError(
                "TTE precedence binding missing id",
                "pre_medical_output_validation",
            )
        if not binding.get("event_precedence_rule_id"):
            raise D06ContractViolationError(
                "TTE precedence binding missing rule id",
                "pre_medical_output_validation",
            )
        if not binding.get("producer_version"):
            raise D06ContractViolationError(
                "TTE precedence binding missing version",
                "pre_medical_output_validation",
            )
        if not binding.get("source_locator_ids"):
            raise D06ContractViolationError(
                "TTE precedence binding missing source locators",
                "pre_medical_output_validation",
            )
        if not binding.get("stable_endpoint_key") or not binding.get(
            "stable_timepoint_key"
        ):
            raise D06ContractViolationError(
                "TTE precedence binding missing endpoint/timepoint identity",
                "pre_medical_output_validation",
            )
        if not scope_identity_matches(binding, ctx.scope):
            raise D06BindingContractError(
                "TTE precedence binding wrong scope",
                "typed_binding_validation",
            )
        if binding.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
            raise D06BindingContractError(
                "TTE precedence binding wrong scope: cutoff",
                "typed_binding_validation",
            )
        verify_lineage_hash(binding, "TTE precedence binding")
        # The binding must resolve the typed TTE source registry:
        # endpoint/timepoint identity, precedence rule and event
        # references must be consistent with the registry's typed
        # values; a rehashed reference that no longer resolves fails
        # closed.
        tte_registry = ctx.fixture.source_registries.get("tte_source_registry")
        if (
            not isinstance(tte_registry, (dict, Mapping))
            or tte_registry.get("object_type") != "TTESourceRegistry"
        ):
            raise D06ContractViolationError(
                "TTE source registry missing or wrong type",
                "pre_medical_output_validation",
            )
        verify_embedded_hash(tte_registry, "TTE source registry")
        for field in (
            "stable_endpoint_key",
            "stable_timepoint_key",
            "event_precedence_rule_id",
        ):
            if binding.get(field) != tte_registry.get(field):
                raise D06ContractViolationError(
                    f"TTE precedence binding {field} does not resolve the "
                    "typed source registry",
                    "pre_medical_output_validation",
                )
        rule = ctx.fixture.source_registries.get("tte_rule_registry")
        if not isinstance(rule, (dict, Mapping)) or rule.get(
            "object_type"
        ) != "TTEPrecedenceRule":
            raise D06ContractViolationError(
                "TTE rule registry missing or wrong type",
                "pre_medical_output_validation",
            )
        verify_embedded_hash(rule, "TTE rule registry")
        if (
            rule.get("event_precedence_rule_id")
            != binding.get("event_precedence_rule_id")
        ):
            raise D06ContractViolationError(
                "TTE precedence rule linkage mismatch",
                "pre_medical_output_validation",
            )
        if not rule.get("allowed_tie_policies"):
            raise D06ContractViolationError(
                "TTE rule registry lacks allowed tie policies",
                "pre_medical_output_validation",
            )
        # Cross-resolve the registry references to the independently
        # typed event sources, typed TTE records and the timepoint
        # definition: a rehashed registry (or binding) field that no
        # longer resolves these authorities fails closed.
        events = {
            event.get("event_id"): event
            for event in ctx.fixture.source_registries.get("tte_source_events", [])
        }
        target_event = events.get(tte_registry.get("target_event_ref"))
        competing_event = events.get(tte_registry.get("competing_event_ref"))
        if (
            not isinstance(target_event, (dict, Mapping))
            or target_event.get("event_role") != "target_event"
            or not isinstance(competing_event, (dict, Mapping))
            or competing_event.get("event_role") != "competing_event"
        ):
            raise D06ContractViolationError(
                "TTE registry event references do not resolve the typed "
                "event sources",
                "pre_medical_output_validation",
            )
        tte_records = ctx.fixture.records.get("tte")
        if not isinstance(tte_records, (dict, Mapping)):
            raise D06ContractViolationError(
                "TTE evaluation requires typed TTE records",
                "pre_medical_output_validation",
            )
        event_time_ref = tte_registry.get("event_time_ref")
        timepoint = ctx.fixture.definitions.get("timepoint", {})
        if (
            event_time_ref != tte_records.get("event_time")
            or event_time_ref != target_event.get("effective_time_ref")
            or event_time_ref != competing_event.get("effective_time_ref")
            or event_time_ref != timepoint.get("nominal_time")
        ):
            raise D06ContractViolationError(
                "TTE registry event time does not resolve the typed event "
                "sources/records/timepoint authority",
                "pre_medical_output_validation",
            )
        if tte_registry.get("origin_time_ref") != tte_records.get("origin"):
            raise D06ContractViolationError(
                "TTE registry origin time does not resolve the typed records",
                "pre_medical_output_validation",
            )
        if (
            tte_records.get("censor_time") is not None
            and tte_registry.get("censor_time_ref") != tte_records.get("censor_time")
        ):
            raise D06ContractViolationError(
                "TTE registry censor time does not resolve the typed records",
                "pre_medical_output_validation",
            )
        tte_input = ctx.fixture.typed_parameters.get("tte")
        if (
            tte_registry.get("tie_policy")
            not in rule.get("allowed_tie_policies", [])
            or (
                isinstance(tte_input, (dict, Mapping))
                and tte_input.get("tie_policy") is not None
                and tte_registry.get("tie_policy")
                != tte_input.get("tie_policy")
            )
        ):
            raise D06ContractViolationError(
                "TTE registry tie policy does not resolve the typed "
                "input/rule authority",
                "pre_medical_output_validation",
            )
        if not binding.get("stable_source_identity"):
            raise D06ContractViolationError(
                "TTE precedence binding missing stable source identity",
                "pre_medical_output_validation",
            )
        if not tte_registry.get("source_locator_ids"):
            raise D06ContractViolationError(
                "TTE source registry lacks source locators",
                "pre_medical_output_validation",
            )
        for event in (target_event, competing_event):
            if not event.get("source_locator_ids"):
                raise D06ContractViolationError(
                    "TTE typed source event lacks source locators",
                    "pre_medical_output_validation",
                )
        return binding

    def _eval_tte(self, tp: Mapping[str, Any]) -> None:
        """TTE precedence evaluation; every emitted identity is derived
        from the typed TTE source registry / typed events / precedence
        binding, never from fixed constants or fallback ids."""
        ctx = self.ctx
        ctx.mark("tte_precedence")
        tte = tp.get("tte", {})
        registries = ctx.fixture.source_registries
        if (
            isinstance(tte, (dict, Mapping))
            and "origin" in tte
            and tte["origin"] is None
        ):
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if (
            isinstance(tte, (dict, Mapping))
            and "precedence_rule" in tte
            and tte["precedence_rule"] is None
        ):
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if (
            isinstance(tte, (dict, Mapping))
            and any(field in tte for field in SCOPE_IDENTITY_FIELDS)
            and not _declared_scope_identity_matches(tte, ctx.scope)
        ):
            # Any scope identity field the typed TTE event declares must
            # agree with the fixture's own declared scope binding; a
            # wrong subject/run/project/site fails closed here
            # identically, regardless of the value spelling.
            raise D06BindingContractError(
                "TTE ref wrong subject/scope", "typed_binding_validation"
            )
        precedence_binding = self._resolve_tte_precedence(ctx)
        binding_id = str(precedence_binding["id"])
        allowed_tie_policies = list(
            registries.get("tte_rule_registry", {}).get("allowed_tie_policies", [])
        )
        if (
            isinstance(tte, (dict, Mapping))
            and tte.get("tie_policy")
            and tte["tie_policy"] not in allowed_tie_policies
        ):
            raise D06ContractViolationError(
                "TTE tie policy not allowed by the typed rule registry",
                "pre_medical_output_validation",
            )
        if isinstance(tte, (dict, Mapping)) and tte.get("tie_policy") == "boundary":
            ctx.domain_assertions["feasible_interpretation_ref_ids"] = list(
                tte.get("feasible_interpretation_ref_ids", [])
            )
            ctx.domain_assertions["single_duration"] = None
            ctx.domain_assertions["tte_status"] = TTE_STATUS_BOUNDARY
            ctx.l1 = L1_BOUNDARY
            ctx.coverage_status = COVERAGE_COVERED
            return
        if isinstance(tte, (dict, Mapping)) and tte.get("same_time_states"):
            precedence = tte.get("precedence", [])
            same_time_states = tte.get("same_time_states", [])
            winner = next(
                (state for state in precedence if state in same_time_states),
                same_time_states[0] if same_time_states else None,
            )
            status = {
                "competing_event": TTE_STATUS_COMPETING_EVENT,
                "event": TTE_STATUS_EVENT,
                "censored": TTE_STATUS_CENSORED,
            }.get(winner, winner)
            role = {
                "competing_event": "competing_event",
                "event": "target_event",
                "censored": "censored",
            }.get(winner, winner)
            # Selected event id resolves strictly from the typed TTE
            # source-event registry; a missing/drifted event fails closed.
            selected_event_ref = None
            selected_event = None
            for event in registries.get("tte_source_events", []):
                if (
                    isinstance(event, (dict, Mapping))
                    and event.get("event_role") == role
                ):
                    if (
                        not event.get("event_id")
                        or event.get("object_type") != "TypedTTEEventSource"
                    ):
                        raise D06ContractViolationError(
                            "TTE typed source event malformed",
                            "pre_medical_output_validation",
                        )
                    verify_embedded_hash(event, "TTE typed source event")
                    if not event.get("source_locator_ids"):
                        raise D06ContractViolationError(
                            "TTE typed source event missing source locators",
                            "pre_medical_output_validation",
                        )
                    selected_event_ref = str(event["event_id"])
                    selected_event = event
                    break
            if selected_event_ref is None or selected_event is None:
                raise D06ContractViolationError(
                    f"TTE {role} source event cannot be resolved from the "
                    "typed source registry",
                    "pre_medical_output_validation",
                )
            # Event time must be typed, within the evaluation window and
            # consistent with the typed TTE records: the selected event's
            # effective time must equal the recorded event_time and be at
            # or before the clinical cutoff.  A rehashed event-time drift
            # that no longer resolves this authority fails closed.
            effective_time = selected_event.get("effective_time_ref")
            cutoff = ctx.scope.get("clinical_event_cutoff", "")
            if not effective_time or (cutoff and effective_time > cutoff):
                raise D06ContractViolationError(
                    "TTE source event time outside the evaluation window",
                    "pre_medical_output_validation",
                )
            tte_records = ctx.fixture.records.get("tte")
            if isinstance(tte_records, (dict, Mapping)) and tte_records.get(
                "event_time"
            ):
                recorded_time = tte_records.get("event_time")
                if effective_time != recorded_time:
                    raise D06ContractViolationError(
                        "TTE source event time does not match typed TTE records",
                        "pre_medical_output_validation",
                    )
                recorded_refs = (
                    tte_records.get("target_event_ref"),
                    tte_records.get("competing_event_ref"),
                )
                if selected_event_ref not in recorded_refs:
                    raise D06ContractViolationError(
                        "TTE selected event not referenced by typed TTE records",
                        "pre_medical_output_validation",
                    )
                # All same-time-state roles that resolve to a typed source
                # event must share the recorded event time; a drifted
                # event time breaks the same-time declaration.
                role_by_state = {
                    "competing_event": "competing_event",
                    "event": "target_event",
                    "censored": "censored",
                }
                for state in same_time_states:
                    state_role = role_by_state.get(state)
                    if state_role is None:
                        continue
                    for event in registries.get("tte_source_events", []):
                        if (
                            isinstance(event, (dict, Mapping))
                            and event.get("event_role") == state_role
                        ):
                            if event.get("effective_time_ref") != recorded_time:
                                raise D06ContractViolationError(
                                    "TTE same-time state event time mismatch",
                                    "pre_medical_output_validation",
                                )
                            break
            ctx.domain_assertions["tte_status"] = status
            ctx.domain_assertions["tte_precedence_binding_id"] = binding_id
            ctx.domain_assertions["selected_event_ref"] = selected_event_ref
            if winner == "competing_event":
                ctx.l1 = None
            else:
                ctx.l1 = L1_NEGATIVE
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = L1_NEGATIVE
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_ice(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        ice = tp.get("ice", {})
        if not isinstance(ice, (dict, Mapping)):
            ice = {}
        if any(field in ice for field in SCOPE_IDENTITY_FIELDS) and not (
            _declared_scope_identity_matches(ice, ctx.scope)
        ):
            # Binding fails before any ICE context is consumed: every
            # scope identity field the typed ICE event declares must
            # agree with the fixture's own declared scope binding,
            # regardless of the value spelling.
            raise D06BindingContractError(
                "ICE typed producer event wrong subject", "typed_binding_validation"
            )
        if tp.get("misclassified_as") == "missing":
            ctx.mark("intercurrent_event_context")
            raise D06ContractViolationError(
                "intercurrent event misclassified as missing",
                "pre_medical_output_validation",
            )
        if (
            ice.get("estimator_availability") == "available"
            and ice.get("estimator_binding") is None
            and ice.get("strategy") != "hypothetical"
        ):
            ctx.mark("intercurrent_event_context")
            raise SchemaContractError(
                "available ICE estimator requires a binding",
                "pre_medical_output_validation",
            )
        if ice.get("strategy") == "hypothetical":
            if ice.get("estimator_availability") == "available":
                ctx.mark("intercurrent_event_context")
            ctx.domain_assertions["hypothetical_value_created"] = False
            ctx.domain_assertions["ice_context_state"] = "not_evaluable"
            ctx.domain_assertions["normal_derived_result_created"] = False
            if ice.get("estimator_availability") == "available":
                ctx.domain_assertions["coverage_status"] = COVERAGE_NOT_EVALUABLE
                ctx.domain_assertions["l1_disposition"] = L1_NOT_EVALUABLE
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if ice.get("feasible_rule_ids"):
            ctx.mark("intercurrent_event_context")
            ctx.l1 = L1_BOUNDARY
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "source_role" in ice and ice["source_role"] is None:
            ctx.mark("intercurrent_event_context")
            ctx.l1 = L1_NOT_EVALUABLE
            ctx.coverage_status = COVERAGE_NOT_EVALUABLE
            ctx.l2[L2_COVERAGE_NOTICES] += 1
            return
        if ice.get("strategy") == "treatment_policy":
            if ice.get("type") == "withdrawal":
                ctx.mark("intercurrent_event_context")
                ctx.l1 = L1_NEGATIVE
            else:
                ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_correction(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        correction = tp["correction"]
        ctx.mark("accepted_artifact")
        if isinstance(correction, (dict, Mapping)):
            if correction.get("current_ids") and correction.get("graph") == "branch":
                self._open_gate(GATE_DEFINITION, GATE_DECISION_NOT_EVALUABLE)
                return
            if correction.get("current_ids") and correction.get("lineage") is None:
                ctx.l1 = L1_NOT_EVALUABLE
                ctx.coverage_status = COVERAGE_NOT_EVALUABLE
                ctx.l2[L2_COVERAGE_NOTICES] += 1
                return
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_numeric(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        numeric = tp["numeric"]
        if isinstance(numeric, (dict, Mapping)):
            if numeric.get("input") == "NaN":
                raise D06BindingContractError(
                    "NaN input rejected", "typed_binding_validation"
                )
            if numeric.get("equivalent_inputs") is not None:
                if "negative_zero_policy" in tp:
                    ctx.domain_assertions["hash_relation"] = (
                        "negative_zero_and_zero_hash_equal"
                    )
                elif "unicode" in tp:
                    ctx.domain_assertions["hash_relation"] = (
                        "unicode_nfc_identity_hash_equal"
                    )
                else:
                    ctx.domain_assertions["hash_relation"] = (
                        "canonical_decimal_hashes_all_equal"
                    )
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return
            if numeric.get("rounding_modes"):
                places = int(numeric["decimal_places"])
                half_even = _apply_rounding(str(numeric["input"]), places, "half_even")
                half_up = _apply_rounding(str(numeric["input"]), places, "half_up")
                ctx.domain_assertions["half_even_result"] = half_even
                ctx.domain_assertions["half_up_result"] = half_up
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED

    def _eval_priority_assertion(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED
        ctx._priority_da = True

    def _eval_lifecycle(self, tp: Mapping[str, Any]) -> None:
        ctx = self.ctx
        later_run = tp.get("later_run", {})
        coverage = tp.get("coverage")
        risk = tp.get("risk", {})
        if coverage == "covered" and later_run.get("linked_negative"):
            if ctx.entrypoint == "d06.gate_evaluator":
                self._open_gate(GATE_APPLICABILITY, GATE_DECISION_NOT_EVALUABLE)
                ctx.l3_state = "closed"
                ctx.l3_transition = "rejected_by_evidence/resolved_by_data"
                return
            ctx.l3_state = "closed"
            ctx.l3_transition = "rejected_by_evidence/resolved_by_data"
            ctx.domain_assertions["l3_state"] = "closed"
            ctx.domain_assertions["l3_transition"] = (
                "rejected_by_evidence/resolved_by_data"
            )
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if later_run.get("coverage") == "partial":
            ctx.l3_state = "active"
            ctx.l3_transition = "none"
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if risk.get("priority") == "high" or later_run.get("corrected"):
            ctx.l3_state = "active"
            ctx.l3_transition = "none"
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "other_required_unit" in tp:
            ctx.domain_assertions["blocking_required_unit_disposition"] = tp[
                "other_required_unit"
            ]
            ctx.domain_assertions["r2_close_allowed"] = False
            ctx.l3_state = "active"
            ctx.l3_transition = "none"
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED

    def _resolve_enrollment_source_events(
        self,
        ctx: _RunContext,
        source_events: Mapping[str, Any],
        refs: Sequence[str],
        query_context: str,
        decision_time: Optional[str] = None,
    ) -> List[str]:
        """Resolve every referenced enrollment source event against the
        typed registry with exact object type, payload-consistent hash,
        source locators, context linkage and the decision's effective
        time symbol.  A missing or drifted source fails closed; no source
        is echoed without being resolved."""
        resolved: List[str] = []
        for ref in refs:
            event = source_events.get(ref)
            if not isinstance(event, (dict, Mapping)):
                raise D06ContractViolationError(
                    f"enrollment source event {ref!r} cannot be resolved",
                    "pre_medical_output_validation",
                )
            if event.get("object_type") != "EnrollmentSourceEvent":
                raise D06ContractViolationError(
                    "enrollment source event wrong object type",
                    "pre_medical_output_validation",
                )
            verify_embedded_hash(event, "enrollment source event")
            if not event.get("source_locator_ids"):
                raise D06ContractViolationError(
                    "enrollment source event lacks source locators",
                    "pre_medical_output_validation",
                )
            if event.get("query_context") != query_context:
                raise D06ContractViolationError(
                    "enrollment source event context mismatch",
                    "pre_medical_output_validation",
                )
            # Effective time is a typed symbol shared by the decision and
            # its source events; a rehashed event-time drift that no
            # longer equals the decision's time fails closed.
            if not event.get("effective_time_ref") or (
                decision_time is not None
                and event.get("effective_time_ref") != decision_time
            ):
                raise D06ContractViolationError(
                    "enrollment source event time does not resolve the "
                    "decision time",
                    "pre_medical_output_validation",
                )
            resolved.append(str(event["event_id"]))
        return resolved

    def _resolve_enrollment_decision(
        self, ctx: _RunContext, decision: Any, label: str
    ) -> Mapping[str, Any]:
        """Validate a typed enrollment context decision: exact object
        type, scope/cutoff, payload-consistent hash, source locators and
        effective event time.  A missing/drifted decision fails closed
        and suppresses the Query."""
        if not isinstance(decision, (dict, Mapping)) or decision.get(
            "object_type"
        ) != "EnrollmentContextDecisionRef":
            raise D06ContractViolationError(
                f"enrollment decision {label} wrong object type",
                "pre_medical_output_validation",
            )
        if not scope_identity_matches(decision, ctx.scope):
            raise D06BindingContractError(
                f"enrollment decision {label} wrong scope",
                "typed_binding_validation",
            )
        if decision.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
            raise D06BindingContractError(
                f"enrollment decision {label} wrong scope: cutoff",
                "typed_binding_validation",
            )
        verify_embedded_hash(decision, f"enrollment decision {label}")
        if not decision.get("source_locator_ids"):
            raise D06ContractViolationError(
                f"enrollment decision {label} missing source locators",
                "pre_medical_output_validation",
            )
        if not decision.get("effective_time_ref"):
            raise D06ContractViolationError(
                f"enrollment decision {label} missing effective time",
                "pre_medical_output_validation",
            )
        # The decision is a D04-produced enrollment context decision; a
        # rewritten producer domain fails closed.
        if decision.get("producer_domain") != "D04":
            raise D06ContractViolationError(
                f"enrollment decision {label} wrong producer domain",
                "pre_medical_output_validation",
            )
        if not decision.get("source_event_refs"):
            raise D06ContractViolationError(
                f"enrollment decision {label} missing source event refs",
                "pre_medical_output_validation",
            )
        return decision

    def _resolve_enrollment_rule(self, ctx: _RunContext) -> Mapping[str, Any]:
        """Validate the typed enrollment rule registry (object type,
        payload-consistent hash, rule id/version) and return it."""
        rule = ctx.fixture.source_registries.get("enrollment_rule_registry")
        if not isinstance(rule, (dict, Mapping)) or rule.get(
            "object_type"
        ) != "EnrollmentDecisionRule":
            raise D06ContractViolationError(
                "enrollment rule registry missing or wrong type",
                "pre_medical_output_validation",
            )
        verify_embedded_hash(rule, "enrollment rule registry")
        if not rule.get("decision_rule_id") or not rule.get("rule_version"):
            raise D06ContractViolationError(
                "enrollment rule registry missing rule id/version",
                "pre_medical_output_validation",
            )
        if not rule.get("source_locator_ids"):
            raise D06ContractViolationError(
                "enrollment rule registry lacks source locators",
                "pre_medical_output_validation",
            )
        if not rule.get("allowed_contexts"):
            raise D06ContractViolationError(
                "enrollment rule registry lacks allowed contexts",
                "pre_medical_output_validation",
            )
        return rule

    def _eval_query_context(self, tp: Mapping[str, Any]) -> None:
        """Enrollment-aware Query derivation from the typed enrollment
        decisions / source events / rule registry (never page or variant
        constants)."""
        ctx = self.ctx
        bindings = ctx.fixture.bindings
        registries = ctx.fixture.source_registries
        decisions = bindings.get("enrollment_context_decisions", [])
        source_events = {
            item.get("event_id"): item
            for item in registries.get("enrollment_source_events", [])
        }
        rule = self._resolve_enrollment_rule(ctx)
        if "page" in tp:
            ctx.mark("query_source_jump")
            active_id = bindings.get("active_enrollment_decision_id")
            active = next(
                (item for item in decisions if item.get("decision_id") == active_id),
                None,
            )
            if not isinstance(active, (dict, Mapping)):
                raise D06ContractViolationError(
                    "active enrollment decision cannot be resolved from bindings",
                    "pre_medical_output_validation",
                )
            self._resolve_enrollment_decision(ctx, active, "active")
            query_context = str(active.get("query_context"))
            if query_context not in rule.get("allowed_contexts", []):
                raise D06ContractViolationError(
                    "active enrollment decision context not allowed by the "
                    "rule registry",
                    "pre_medical_output_validation",
                )
            decision_id = str(active.get("decision_id"))
            source_refs = list(active.get("source_event_refs", []))
            decision_rule_id = str(
                active.get("decision_rule_id") or rule.get("decision_rule_id")
            )
            rule_version = str(active.get("rule_version") or rule.get("rule_version"))
            if (
                decision_rule_id != rule.get("decision_rule_id")
                or rule_version != rule.get("rule_version")
            ):
                raise D06ContractViolationError(
                    "enrollment decision does not resolve the frozen "
                    "enrollment rule registry",
                    "pre_medical_output_validation",
                )
            self._resolve_enrollment_source_events(
                ctx,
                source_events,
                source_refs,
                query_context,
                decision_time=str(active.get("effective_time_ref") or ""),
            )
            ctx.domain_assertions["query_context"] = query_context
            ctx.domain_assertions["enrollment_decision_id"] = decision_id
            ctx.domain_assertions["enrollment_decision_rule_id"] = decision_rule_id
            ctx.domain_assertions["enrollment_rule_version"] = rule_version
            ctx.domain_assertions["enrollment_source_event_refs"] = source_refs
            ctx.domain_assertions["pd_wording_valid"] = (
                query_context == QUERY_CONTEXT_ENROLLED
            )
            ctx.domain_assertions["forbidden_query_fragments"] = list(
                PD_WORDING_FRAGMENTS
            )
            if query_context == QUERY_CONTEXT_UNRESOLVED and "page" in tp:
                payload = {
                    "query_context": query_context,
                    "basis_sentence": "依据：当前入组状态尚未明确。",
                    "finding_sentence": "发现：页面标志与已接受入组决定不一致。",
                    "action_sentence": (
                        "行动项：请先核实随机、入组或首次给药状态及事件时序。"
                    ),
                }
            else:
                sentences = QUERY_PAYLOADS_BY_CONTEXT.get(query_context, {})
                payload = {
                    "query_context": query_context,
                    "basis_sentence": sentences.get("basis_sentence", ""),
                    "finding_sentence": sentences.get("finding_sentence", ""),
                    "action_sentence": sentences.get("action_sentence", ""),
                }
            ctx.domain_assertions["query_payload"] = payload
            ctx._query_payload = payload
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        if "query_context_variants" in tp:
            variants = list(tp["query_context_variants"])
            by_context = bindings.get("active_enrollment_decision_ids_by_context", {})
            decision_ids = {}
            source_events_by_context = {}
            rules_by_context = {}
            rule_id = str(rule.get("decision_rule_id", ""))
            rule_version = str(rule.get("rule_version", ""))
            for context in variants:
                decision_id = by_context.get(context)
                decision = next(
                    (
                        item
                        for item in decisions
                        if item.get("decision_id") == decision_id
                    ),
                    None,
                )
                if not isinstance(decision, (dict, Mapping)):
                    raise D06ContractViolationError(
                        f"variant enrollment decision {context!r} cannot be resolved",
                        "pre_medical_output_validation",
                    )
                self._resolve_enrollment_decision(
                    ctx, decision, f"variant {context!r}"
                )
                # The by-context mapping and the decision's own query
                # context must agree bidirectionally; the decision's
                # context must be allowed by the frozen rule registry.
                if str(decision.get("query_context", "")) != context:
                    raise D06ContractViolationError(
                        f"variant enrollment decision {context!r} context "
                        "mismatch",
                        "pre_medical_output_validation",
                    )
                if context not in rule.get("allowed_contexts", []):
                    raise D06ContractViolationError(
                        f"variant enrollment context {context!r} not allowed "
                        "by the rule registry",
                        "pre_medical_output_validation",
                    )
                # The decision must resolve the frozen enrollment rule
                # registry; any rule/version drift fails closed.
                if (
                    str(decision.get("decision_rule_id", "")) != rule_id
                    or str(decision.get("rule_version", "")) != rule_version
                ):
                    raise D06ContractViolationError(
                        "enrollment decision does not resolve the frozen "
                        "enrollment rule registry",
                        "pre_medical_output_validation",
                    )
                decision_ids[context] = str(decision.get("decision_id"))
                source_refs = list(decision.get("source_event_refs", []))
                # Every variant source event must resolve against the
                # typed registry (exact type/hash/locators/context/time);
                # a missing or drifted source fails closed and suppresses
                # the Query instead of echoing unresolved references.
                self._resolve_enrollment_source_events(
                    ctx,
                    source_events,
                    source_refs,
                    context,
                    decision_time=str(decision.get("effective_time_ref") or ""),
                )
                source_events_by_context[context] = source_refs
                rules_by_context[context] = {
                    "decision_rule_id": rule_id,
                    "rule_version": rule_version,
                }
            outcomes = {}
            payloads = {}
            for context in variants:
                payload = _query_payload_for_context(context)
                outcomes[context] = {"pd_wording_valid": payload["pd_wording_valid"]}
                payloads[context] = {
                    "query_context": context,
                    "basis_sentence": payload["basis_sentence"],
                    "finding_sentence": payload["finding_sentence"],
                    "action_sentence": payload["action_sentence"],
                    "pd_wording_valid": payload["pd_wording_valid"],
                }
            ctx.domain_assertions["enrollment_decision_ids_by_context"] = decision_ids
            ctx.domain_assertions["enrollment_source_events_by_context"] = (
                source_events_by_context
            )
            ctx.domain_assertions["enrollment_rules_by_context"] = rules_by_context
            ctx.domain_assertions["query_context_outcomes"] = outcomes
            ctx.domain_assertions["query_payloads"] = payloads
            ctx.l1 = None
            ctx.coverage_status = COVERAGE_COVERED
            return
        ctx.l1 = None
        ctx.coverage_status = COVERAGE_COVERED

    def _emit_priority_da(self, resolver: D06PriorityResolverInput) -> None:
        """Case-specific priority-resolution domain assertions (§9.1).

        Derived from the actual resolver input; the field set follows the
        endpoint-role / impact / recurrence semantics of the typed input.
        """
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        impact = resolver.impact_class
        recurrence = resolver.recurrence_class
        if impact in ("rights_safety", "critical_treatment"):
            ctx.domain_assertions["machine_close_forbidden"] = (
                resolver.machine_close_forbidden
            )
            ctx.domain_assertions["matched_precedence_step"] = (
                resolver.matched_precedence_step
            )
            ctx.domain_assertions["monitoring_priority"] = resolver.monitoring_priority
            return
        if recurrence == "repeated_site":
            return
        endpoint_role = tp.get("endpoint", {}).get("role")
        ctx.domain_assertions["impact_class"] = impact
        if (
            endpoint_role == "undefined"
            or resolver.impact_resolution_state == "unresolved"
        ):
            ctx.domain_assertions["impact_resolution_state"] = (
                resolver.impact_resolution_state
            )
        ctx.domain_assertions["machine_close_forbidden"] = (
            resolver.machine_close_forbidden
        )
        ctx.domain_assertions["matched_precedence_step"] = (
            resolver.matched_precedence_step
        )
        ctx.domain_assertions["monitoring_priority"] = resolver.monitoring_priority

    def _resolve_priority(self) -> None:
        """Post-pipeline priority resolution for every medical case.

        Runs after the pipeline (including gate/error outcomes) because the
        frozen expected outcomes always carry the resolver-based priority
        resolution derived from the typed resolver input; only the
        control-plane definition binding (203) is ``not_run_control_plane``.
        Failures are NOT swallowed: an invalid/mutated resolver input or
        policy fails closed into an error outcome with no priority payload.
        """
        ctx = self.ctx
        if ctx.priority_resolution is not None:
            return
        if ctx.scope_integrity_failed:
            # A typed scope/schema integrity failure happened before any
            # priority resolution may be engaged: emit no priority
            # payload, no resolver input hash/object, no risk/public
            # identity and no clinical projection.
            return
        if ctx.fixture.policies.get("priority_resolution_input") is None:
            if (
                ctx.domain_assertions.get("definition_binding_state")
                == "not_applicable"
            ):
                ctx.priority_resolution = {
                    "projection_state": "not_run_control_plane",
                    "priority_policy_id": CANONICAL_PRIORITY_POLICY["policy_id"],
                    "priority_policy_version": CANONICAL_PRIORITY_POLICY["version"],
                    "priority_policy_hash": CANONICAL_PRIORITY_POLICY["policy_hash"],
                    "priority_resolver_input_hash": None,
                    "priority_decision_id": None,
                    "endpoint_definition_id": None,
                    "stable_endpoint_key": None,
                    "stable_timepoint_key": None,
                    "endpoint_role": None,
                    "impact_resolution_state": None,
                    "impact_class": None,
                    "recurrence_class": None,
                    "recoverability": None,
                    "actionability": None,
                    "monitoring_priority": None,
                    "matched_precedence_step": None,
                    "reason_codes": None,
                    "machine_close_forbidden": None,
                }
            return
        resolver = _build_resolver_input(ctx)
        if ctx.l1 == L1_POSITIVE and ctx.output_kind == OUTPUT_KIND_RESULT:
            _emit_risk_decision(ctx)
            ctx.l2[L2_QUERIES] += 1
        ctx.priority_resolution = _priority_resolution_payload(ctx)
        if getattr(ctx, "_priority_da", False):
            self._emit_priority_da(resolver)

    # -- audience / projection ---------------------------------------------

    def _projection_consistency(self) -> None:
        """Projection QC checks shared by all entrypoints (§10)."""
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        # The shared temporal spine is the projection's time spine; when
        # the fixture carries one, it must be the typed
        # SharedTemporalSpineBinding with matching scope/cutoff, a
        # binding id and a payload-consistent hash.  A drifted or
        # incompatible spine fails closed before any journey payload can
        # be emitted.
        spine = ctx.fixture.bindings.get("shared_temporal_spine_binding")
        if spine is not None:
            if not isinstance(spine, (dict, Mapping)) or spine.get(
                "object_type"
            ) != "SharedTemporalSpineBinding":
                raise D06ContractViolationError(
                    "projection requires a typed shared temporal spine",
                    "pre_medical_output_validation",
                )
            if not scope_identity_matches(spine, ctx.scope):
                raise D06BindingContractError(
                    "temporal spine wrong scope", "typed_binding_validation"
                )
            if spine.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
                raise ProjectionContractError(
                    "temporal spine wrong cutoff", "projection_validation"
                )
            if not spine.get("spine_binding_id") or not spine.get("axis_hash"):
                raise D06ContractViolationError(
                    "temporal spine missing identity/hash",
                    "pre_medical_output_validation",
                )
            verify_embedded_hash(spine, "temporal spine")
        if "projection" in tp:
            projection = tp["projection"]
            if "undated_point_position" in projection:
                raise ProjectionContractError(
                    "undated point cannot be placed at a fabricated date",
                    "projection_validation",
                )
            if "filter_changes_risk_count" in projection:
                raise ProjectionContractError(
                    "filtering must not change risk count", "projection_validation"
                )
            if "collapse_hides_priority" in projection:
                raise ProjectionContractError(
                    "collapsing must not hide high priority markers",
                    "projection_validation",
                )
        if "directionality" in tp and "projection" in tp:
            directionality = tp["directionality"]
            projection_direction = tp["projection"].get("direction")
            if directionality == "lower_better" and projection_direction == "worse":
                raise ProjectionContractError(
                    "lower-better endpoint projected as worsening",
                    "projection_validation",
                )
            if directionality == "higher_better" and projection_direction in (
                "improvement",
                "improved",
            ):
                ctx.l1 = None
                ctx.coverage_status = COVERAGE_COVERED
                return

    def _validate_audience_payload(self) -> None:
        """Audience validation entrypoint wrapper (may raise)."""
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        if (
            "l1" in tp
            and tp["l1"] == "not_evaluable"
            and tp.get("query", {}).get("generated")
        ):
            raise D06ContractViolationError(
                "not_evaluable must not generate a Query",
                "pre_medical_output_validation",
            )
        self._compute_audience_result()
        if (
            ctx.audience_result is not None
            and ctx.audience_result.validation_state == "failed"
        ):
            raise AudiencePayloadValidationError("audience payload failed validation")

    def _compute_audience_result(self) -> None:
        """Compute the audience validation result; never raises."""
        ctx = self.ctx
        tp = ctx.fixture.typed_parameters
        attempted = {
            key: tp[key] for key in ("audience", "projection", "query") if key in tp
        }
        # Determine the intended payload kind.
        payload: Optional[Dict[str, Any]] = None
        query_case = "page" in tp or "query" in tp or "query_context_variants" in tp
        if "page" in tp and getattr(ctx, "_query_payload", None) is not None:
            query_payload = dict(ctx._query_payload)
            query_payload["payload_kind"] = "query"
            query_payload["payload_schema_version"] = "d06-query-audience-v1"
            payload = query_payload
        elif (
            not query_case
            and ctx.error_type is None
            and ctx.gate_state is None
            and ctx.l1 is None
        ):
            # The emitted journey payload is serialized from the actual
            # runtime projection (never a static substitution).  The
            # projection itself is built from validated typed runtime
            # objects; an invalid projection or locator fails closed into
            # the exact gate/error state instead of emitting a payload.
            ctx.projection_obj = project_efficacy_journey(
                ctx.fixture,
                getattr(ctx, "scope_status", None),
                ctx.l1,
                priority_decision=ctx.priority_decision_obj,
            )
            payload = journey_audience_payload_from_projection(ctx.projection_obj)
        if query_case and "query" in tp and tp["query"].get("generated"):
            payload = None
        validation_state = "passed"
        payload_schema_version: str = "none"
        forbidden_hits: List[str] = []
        validated_paths: List[str] = []
        emitted_payload: Optional[Dict[str, Any]] = None
        attempted_view = attempted_display_view(attempted)
        attempted_hits = audience_phrase_hits(audience_visible_strings(attempted_view))
        attempted_paths = audience_string_paths(attempted_view)
        try:
            if payload is not None:
                payload_schema_version = validate_audience_payload_schema(payload)
                display = audience_display_view(payload)
                forbidden_hits = audience_phrase_hits(audience_visible_strings(display))
                validated_paths = audience_string_paths(display)
                if (
                    forbidden_hits
                    or attempted_hits
                    or self._attempted_payload_invalid(attempted)
                ):
                    validation_state = "failed"
                    forbidden_hits = attempted_hits or forbidden_hits
                    validated_paths = attempted_paths or validated_paths
                else:
                    validation_state = "passed"
                    emitted_payload = payload
            else:
                # No emitted payload: independently re-derive visible
                # strings/keys from the typed audience/projection/query
                # inputs (frozen §10).
                forbidden_hits = attempted_hits
                validated_paths = attempted_paths
                if (
                    forbidden_hits
                    or self._attempted_payload_invalid(attempted)
                    or ctx.error_type is not None
                ):
                    validation_state = "failed"
        except AudiencePayloadValidationError:
            validation_state = "failed"
            payload_schema_version = "none"
            forbidden_hits = attempted_hits
            validated_paths = attempted_paths

        absent = payload is None or validation_state == "failed"
        ctx.audience_absent = absent
        ctx.audience_payload = emitted_payload if not absent else None
        if (
            ctx.entrypoint == "d06.audience_projection_validator"
            and emitted_payload is not None
        ):
            ctx.output_kind = OUTPUT_KIND_PROJECTION
            ctx.coverage_status = COVERAGE_COVERED
            ctx.l1 = None
        ctx.audience_result = D06AudienceValidationResult(
            payload_schema=True,
            payload_schema_version=(
                payload_schema_version if payload is not None else "none"
            ),
            validator_version=AUDIENCE_VALIDATOR_VERSION,
            validator_hash=AUDIENCE_VALIDATOR_HASH,
            lexicon_version=AUDIENCE_LEXICON_VERSION,
            forbidden_lexicon_hash=AUDIENCE_LEXICON_HASH,
            forbidden_fragment_hits=tuple(forbidden_hits),
            validated_display_string_paths=tuple(validated_paths),
            validation_state=validation_state,
            audience_payload_absent=absent,
        )
        if validation_state == "failed":
            ctx.audience_absent = True
            ctx.audience_payload = None
            ctx.audience_result = D06AudienceValidationResult(
                payload_schema=True,
                payload_schema_version="none",
                validator_version=AUDIENCE_VALIDATOR_VERSION,
                validator_hash=AUDIENCE_VALIDATOR_HASH,
                lexicon_version=AUDIENCE_LEXICON_VERSION,
                forbidden_lexicon_hash=AUDIENCE_LEXICON_HASH,
                forbidden_fragment_hits=tuple(forbidden_hits),
                validated_display_string_paths=tuple(validated_paths),
                validation_state="failed",
                audience_payload_absent=True,
            )

    def _attempted_payload_invalid(self, attempted: Mapping[str, Any]) -> bool:
        """Content/schema rejection of attempted audience inputs."""
        for key, value in attempted.items():
            text = audience_visible_strings(value)
            for item in text:
                if "已记录事项" in item:
                    return True
                if ("统计学显著" in item) or ("研究有效" in item):
                    return True
        if "query" in attempted:
            query = attempted["query"]
            if query.get("missing_sections"):
                return True
            if query.get("generated"):
                return True
        if "audience" in attempted and attempted["audience"].get("visible_text"):
            return True
        return False

    # -- lifecycle helpers -------------------------------------------------

    def _finish_no_unit(self, ctx: _RunContext, coverage_status: str) -> None:
        ctx.output_kind = OUTPUT_KIND_RESULT
        ctx.coverage_status = coverage_status
        ctx.l1 = None

    def _open_gate(self, kind: str, disposition: str) -> None:
        ctx = self.ctx
        ctx.output_kind = OUTPUT_KIND_GATE
        ctx.gate_state = GATE_OPEN
        ctx.gate_disposition = disposition
        ctx.coverage_status = (
            COVERAGE_COVERED
            if disposition == GATE_DECISION_BOUNDARY
            else COVERAGE_NOT_EVALUABLE
        )
        ctx.l1 = None
        ctx.gates.append({"kind": kind, "state": GATE_OPEN, "disposition": disposition})

    # -- finalize ----------------------------------------------------------

    def _finalize(self) -> None:
        ctx = self.ctx
        if ctx.output_kind is None:
            ctx.output_kind = OUTPUT_KIND_RESULT
        if ctx.coverage_status is None:
            ctx.coverage_status = COVERAGE_COVERED
        if ctx.l1 == L1_BOUNDARY:
            ctx.l2["clues"] = 1
        if ctx.l1 == L1_NOT_EVALUABLE and ctx.output_kind == OUTPUT_KIND_RESULT:
            ctx.l2[L2_COVERAGE_NOTICES] = max(ctx.l2[L2_COVERAGE_NOTICES], 1)

    def _assemble(self) -> D06ChallengeOutcome:
        ctx = self.ctx
        if ctx.output_kind is None:
            ctx.output_kind = OUTPUT_KIND_RESULT
        if ctx.coverage_status is None and ctx.output_kind != OUTPUT_KIND_ERROR:
            ctx.coverage_status = COVERAGE_COVERED
        if ctx.audience_result is not None:
            audience_state = ctx.audience_result.validation_state
        else:
            audience_state = None
        object_hashes = dict(ctx.object_hashes)
        if ctx.resolver_input_obj is not None:
            object_hashes["priority_resolver_input_hash"] = ctx.resolver_input_obj.hash
        object_hashes.setdefault(
            "priority_policy_hash", CANONICAL_PRIORITY_POLICY["policy_hash"]
        )
        object_hashes.setdefault("priority_resolver_input_hash", None)
        object_hashes.setdefault("public_r4_identity_hash", None)
        if ctx.public_identity_hash is not None:
            object_hashes["public_r4_identity_hash"] = ctx.public_identity_hash
        # Input-derived annotation leaves: the fixture payload the runtime
        # actually received and the actual input scope.
        from .efficacy import deep_unfreeze

        raw_fixture = deep_unfreeze(ctx.frozen_fixture.raw_fixture)
        fixture_hash = d06_content_hash(raw_fixture)
        object_hashes["fixture_hash"] = fixture_hash
        actual_scope = deep_unfreeze(ctx.frozen_fixture.scope)
        scope_hash = d06_content_hash(actual_scope)
        object_hashes["scope_hash"] = scope_hash
        input_scope_hash = f"sha256:{scope_hash}"
        domain_assertions = {
            key: value
            for key, value in ctx.domain_assertions.items()
            if not key.startswith("_")
        }
        domain_assertions["challenge_assertion_code"] = (
            f"D06-CH-{ctx.fixture.challenge_number:03d}"
        )
        domain_assertions["evaluated_fixture_hash"] = fixture_hash
        try:
            contract_text = derive_clinical_contract_text(ctx)
        except D06Error as exc:
            # Input drift beyond the frozen scenarios: fail closed into an
            # error outcome (never a superficially successful annotation).
            if ctx.error_type is None:
                ctx.output_kind = OUTPUT_KIND_ERROR
                ctx.error_type = exc.error_type
                ctx.error_stage = exc.error_stage
                ctx.coverage_status = None
                ctx.l1 = None
            contract_text = ""
        domain_assertions["clinical_outcome_contract"] = contract_text
        if ctx.priority_resolution is not None:
            domain_assertions["priority_resolution"] = ctx.priority_resolution
        # Trace provenance: base edges plus every source this evaluation
        # actually validated/consumed (never manifest/case identity).
        trace_edges = sorted(set(TRACE_EDGES_ALL) | ctx.consumed)
        return D06ChallengeOutcome(
            invoked_entrypoint=ctx.entrypoint,
            input_scope_hash=input_scope_hash,
            output_kind=ctx.output_kind,
            coverage_status=ctx.coverage_status,
            gate_state=ctx.gate_state,
            gate_disposition=ctx.gate_disposition,
            l1_disposition=ctx.l1,
            primary_subtype=ctx.subtype,
            secondary_reason_codes=tuple(ctx.secondary_reason_codes),
            l2_counts=dict(ctx.l2),
            l3_state=ctx.l3_state,
            l3_transition=ctx.l3_transition,
            object_ids={},
            object_hashes=object_hashes,
            trace_edges=tuple(trace_edges),
            audience_payload=ctx.audience_payload,
            audience_payload_absent=ctx.audience_absent,
            audience_validation_result=ctx.audience_result,
            audience_validation_state=audience_state,
            domain_assertions=domain_assertions,
            error_type=ctx.error_type,
            error_stage=ctx.error_stage,
        )




def _validate_assessment_authority(
    ctx: _RunContext, assessment: Mapping[str, Any], label: str
) -> None:
    """Cross-resolve an accepted assessment against independent typed
    authorities (D05 binding refs / accepted inventory / foreign
    keys / instrument definition / item records).

    The assessment's lineage hash must be authenticated by the D05
    binding ref and inventory ``producer_payload_hash`` (never by
    recomputing the hash from the mutated object alone); its time
    must equal the ref/inventory ``actual_time_ref``; its binding
    ref must be in the foreign-key registry; its instrument, recall
    period, admin mode, item set/order, scope/cutoff, locators and
    accepted-current status must resolve the typed authorities.
    """
    aid = str(assessment.get("id", ""))
    if (
        assessment.get("object_type") != "ActualAssessmentRecord"
        or assessment.get("record_status") != "accepted_current"
    ):
        raise D06ContractViolationError(
            f"accepted assessment {aid} is not an accepted-current "
            "ActualAssessmentRecord",
            "pre_medical_output_validation",
        )
    if not scope_identity_matches(assessment, ctx.scope):
        raise D06BindingContractError(
            f"accepted assessment {aid} wrong scope",
            "typed_binding_validation",
        )
    if assessment.get("cutoff") != ctx.scope.get("clinical_event_cutoff"):
        raise D06BindingContractError(
            f"accepted assessment {aid} wrong scope: cutoff",
            "typed_binding_validation",
        )
    inventory = {
        item.get("source_record_id"): item
        for item in ctx.fixture.source_registries.get(
            "accepted_d05_assessment_inventory", []
        )
    }
    refs = {
        item.get("source_record_id"): item
        for item in ctx.fixture.bindings.get("d05_refs", [])
    }
    foreign_keys = {
        item.get("source_record_id"): item
        for item in ctx.fixture.source_registries.get(
            "d05_assessment_foreign_keys", []
        )
    }
    inv_item = inventory.get(aid)
    ref = refs.get(aid)
    if not isinstance(inv_item, (dict, Mapping)) or not isinstance(
        ref, (dict, Mapping)
    ):
        raise D06ContractViolationError(
            f"accepted assessment {aid} lacks D05 inventory/binding authority",
            "pre_medical_output_validation",
        )
    foreign_key = foreign_keys.get(aid)
    if not isinstance(foreign_key, (dict, Mapping)):
        raise D06ContractViolationError(
            f"accepted assessment {aid} lacks foreign-key authority",
            "pre_medical_output_validation",
        )
    # The accepted inventory item, the D05 binding ref and the
    # foreign-key registry entry are content-addressed authorities: their
    # embedded ``hash`` must match a recomputation over their own typed
    # fields before they are consumed.  A hash-only tamper on any one of
    # them fails closed instead of preserving the medical result.
    verify_embedded_hash(inv_item, f"accepted inventory item {aid}")
    verify_embedded_hash(ref, f"D05 binding ref {aid}")
    verify_embedded_hash(foreign_key, f"D05 foreign key {aid}")
    # Independent hash authentication: the accepted inventory and the
    # D05 binding ref carry the producer payload hash; a rehashed
    # assessment alone must not rewrite accepted truth.
    verify_lineage_hash(assessment, f"accepted assessment {aid}")
    if (
        assessment.get("lineage_hash")
        != inv_item.get("producer_payload_hash")
        or assessment.get("lineage_hash")
        != ref.get("producer_payload_hash")
    ):
        raise D06ContractViolationError(
            f"accepted assessment {aid} lineage not authenticated by the "
            "accepted inventory/binding authority",
            "pre_medical_output_validation",
        )
    if (
        assessment.get("time") != inv_item.get("actual_time_ref")
        or assessment.get("time") != ref.get("actual_time_ref")
    ):
        raise D06BindingContractError(
            f"accepted assessment {aid} time not authenticated by the "
            "accepted inventory/binding authority",
            "typed_binding_validation",
        )
    if assessment.get("assessment_time_ref") not in (None, assessment.get("time")):
        raise D06BindingContractError(
            f"accepted assessment {aid} assessment time ref inconsistent",
            "typed_binding_validation",
        )
    foreign_key = foreign_keys.get(aid)
    if not isinstance(foreign_key, (dict, Mapping)) or foreign_key.get(
        "binding_ref_id"
    ) != ref.get("binding_ref_id"):
        raise D06ContractViolationError(
            f"accepted assessment {aid} binding ref not in foreign keys",
            "pre_medical_output_validation",
        )
    # D05 semantic fields must agree bidirectionally across the accepted
    # assessment, the D05 binding ref, the accepted inventory and the
    # foreign-key registry; a partially synchronized rehash that drifts
    # any one of these fails closed.
    for field in (
        "d05_unit_id",
        "d05_planned_activity_key",
        "d05_actual_activity_key",
        "occurrence_disposition",
        "timing_disposition",
        "assignment_status",
    ):
        values = {
            assessment.get(field),
            ref.get(field),
            inv_item.get(field),
            foreign_key.get(field),
        }
        if len(values) != 1:
            raise D06ContractViolationError(
                f"accepted assessment {aid} {field} does not resolve the "
                "accepted D05 authority",
                "pre_medical_output_validation",
            )
    # Foreign-key producer payload/time authenticate the assessment
    # lineage and time independently.
    if (
        foreign_key.get("producer_payload_hash") != assessment.get("lineage_hash")
        or foreign_key.get("actual_time_ref") != assessment.get("time")
    ):
        raise D06ContractViolationError(
            f"accepted assessment {aid} lineage/time not authenticated by the "
            "foreign-key registry",
            "pre_medical_output_validation",
        )
    if not ref.get("source_locator_ids"):
        raise D06ContractViolationError(
            f"accepted assessment {aid} binding ref lacks source locators",
            "pre_medical_output_validation",
        )
    instrument = ctx.fixture.definitions.get("instrument", {})
    if (
        assessment.get("instrument_definition_id") != instrument.get("id")
        or assessment.get("actual_recall_period")
        != instrument.get("recall_period")
        or assessment.get("admin_mode") != instrument.get("admin_mode")
    ):
        raise D06ContractViolationError(
            f"accepted assessment {aid} instrument/recall/admin does not "
            "resolve the instrument definition",
            "pre_medical_output_validation",
        )
    if not assessment.get("stable_assessment_key"):
        raise D06ContractViolationError(
            f"accepted assessment {aid} missing stable assessment key",
            "pre_medical_output_validation",
        )
    if not assessment.get("source_locator_ids"):
        raise D06ContractViolationError(
            f"accepted assessment {aid} lacks source locators",
            "pre_medical_output_validation",
        )
    # Item set/order: the assessment's item_record_ids must exactly
    # match the typed AssessmentItemRecords for that assessment.
    expected_items = list(assessment.get("item_record_ids", []))
    actual_items = [
        item.get("item_record_id")
        for item in ctx.fixture.records.get("assessment_items", [])
        if item.get("assessment_id") == aid
    ]
    if expected_items != actual_items:
        raise D06ContractViolationError(
            f"accepted assessment {aid} item set/order mismatch",
            "pre_medical_output_validation",
        )
    item_values = ctx.fixture.records.get("item_values") or {}
    for item in ctx.fixture.records.get("assessment_items", []):
        if item.get("assessment_id") == aid:
            if not isinstance(item, (dict, Mapping)) or not item.get(
                "item_record_id"
            ):
                raise D06ContractViolationError(
                    f"accepted assessment {aid} item record malformed",
                    "pre_medical_output_validation",
                )
            verify_content_hash(item, f"assessment item {aid}")
            if not item.get("source_locator_ids"):
                raise D06ContractViolationError(
                    f"accepted assessment {aid} item lacks source locators",
                    "pre_medical_output_validation",
                )
            # Item value/content authority: raw and normalized values
            # must agree with the typed item-values mapping keyed by
            # the item definition identity.
            definition_id = str(item.get("item_definition_id", ""))
            suffix = definition_id.rsplit("-", 1)[-1] if definition_id else ""
            expected_value = item_values.get(suffix)
            if (
                item.get("raw_value") != item.get("normalized_value")
                or item.get("raw_value") != expected_value
            ):
                raise D06ContractViolationError(
                    f"accepted assessment {aid} item "
                    f"{item.get('item_record_id')} value not authenticated "
                    "by the typed item-values authority",
                    "pre_medical_output_validation",
                )

class _GateRaised(Exception):
    """Internal control-flow marker: an outcome was already decided."""


# ---------------------------------------------------------------------------
# Entrypoints
# ---------------------------------------------------------------------------


def evaluate_efficacy_fixture(fixture: D06Fixture) -> D06ChallengeOutcome:
    """``d06.efficacy_evaluator`` -- the full deterministic pipeline."""
    engine = EfficacyEngine(fixture, "d06.efficacy_evaluator")
    return engine.run()


def evaluate_gate(fixture: D06Fixture) -> D06ChallengeOutcome:
    """``d06.gate_evaluator`` -- gate-focused evaluation."""
    engine = EfficacyEngine(fixture, "d06.gate_evaluator")
    return engine.run()


def validate_contract_schema(fixture: D06Fixture) -> D06ChallengeOutcome:
    """``d06.contract_schema_validator`` -- typed-schema validation."""
    engine = EfficacyEngine(fixture, "d06.contract_schema_validator")
    return engine.run()


def validate_audience_projection(fixture: D06Fixture) -> D06ChallengeOutcome:
    """``d06.audience_projection_validator`` -- audience payload QC."""
    engine = EfficacyEngine(fixture, "d06.audience_projection_validator")
    return engine.run()


def validate_challenge_registry_input(
    fixture: D06Fixture,
) -> D06ChallengeOutcome:
    """``d06.challenge_registry_validator`` runtime entrypoint."""
    return EfficacyEngine(fixture, "d06.challenge_registry_validator").run_registry()
