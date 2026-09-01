"""D06 efficacy constants, fixture contracts and run context."""

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


class _GateRaised(RuntimeError):
    """Internal signal indicating that a gate already decided the outcome."""
