"""R4-D05 visit/assessment/sample timing slice -- domain model, dual cutoff,
gates, encounter bundles and typed schedule anchors (worker_01).

Frozen source of truth: ``FROZEN_R4_D05_CONTRACT_V1_2`` (§§1-15).  This
module owns the D05 **domain objects** and the four frozen object-level
contracts assigned to worker_01:

1. Immutable planned/actual domain objects (§3.1, §3.2) and the value
   objects of §3.3 (assignments, ledger, anchor, gate, interpretation
   ledger, evaluation unit, coverage-gap notice, journey projection
   schemas) with fail-closed invariant validation.
2. The dual time boundaries ``snapshot_as_of`` (what this accepted
   snapshot actually contains) versus ``clinical_event_cutoff`` (which
   events medical monitoring may evaluate) -- frozen separately, never
   interchangeable -- and ``resolve_actual_record_scope`` deciding
   ``in_scope | out_of_cutoff | boundary | not_evaluable`` (§4.2,
   challenges 103/104/26/27).
3. ``ScheduleGate`` with the closed state truth table
   (open+boundary|not_evaluable+blocks_domain_complete / closed+resolved)
   and per-Run accounting (challenge 116, §3.3, §12).
4. ``ActualEncounterBundle`` with canonical member ordering, merge/split
   rules and derived interval provenance (challenges 45/46/47/48/107/108).
5. Exact ``TypedScheduleAnchorRef`` binding from producer
   ``CrossDomainEvidenceRef`` with full-dimension explicit expected-value
   matching -- producer domain, producer unit id, stable source event key,
   content hash, subject, site, phase/episode, anchor interval, date
   precision, timezone and relation type -- any missing, wrong or
   conflicting dimension fails closed to a single
   ``ScheduleGate(gate_kind=anchor)`` (challenges 73/74/112).

Evaluation, expected-set expansion, assignment algorithms, Query wording,
journey projection functions, fixtures and root exports are explicitly out
of scope of this module (worker_02/worker_03/worker_04).

Design constraints enforced here (frozen D05 contract):

* Every object is an immutable frozen dataclass; tuples are canonically
  sorted; every id/hash is a deterministic content address (sorted-key
  canonical JSON + SHA-256) over the object's canonical payload.
* Stable identity (``planned_visit_key``, ``planned_activity_key``,
  ``stable_actual_object_key``, ``stable_core``) never contains Run/
  snapshot/revision ids, display version, free text, dates or evaluation
  results (§3.4).  Content hashes (``definition_hash``, ``content_hash``,
  ``lineage_hash``) do contain full payloads for lineage.
* No silent defaults: no default ±N window, no default Day 0, no default
  timezone, no default endpoint inclusivity, no default latest version,
  no nearest-date/row-order/VISITNUM shortcuts (§4, §5, §6).
* Fail closed on wrong/conflicting identity, cutoff, bundle, assignment
  and typed-anchor combinations (§3.2, §3.3, §5.3, §12).

All data is synthetic/offline.  No real project, provider, fixed visit
number, fixed window, fixed table name, medication rule or service.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, fields, is_dataclass
from typing import (Any, Dict, List, Optional, Sequence, Set, Tuple)

from ..intelligence.normalization import normalize_partial_date

from .contracts import (
    CrossDomainEvidenceRef,
    SourceLocator,
    VALID_MONITORING_PRIORITIES,
    content_hash,
)

__all__ = [
    # Domain identity
    "D05_DOMAIN",
    "D05_UNIT_ALGO_VERSION",
    "D05_RULE_LINEAGE_DEFAULT",
    "D05_SOURCE_IDENTITY_ALGORITHM_VERSION",
    # Closed enums
    "VISIT_KINDS",
    "VISIT_SCHEDULED",
    "VISIT_TRIGGERED",
    "VISIT_CONTINGENT",
    "VISIT_REPEAT_ALLOWED",
    "ACTIVITY_KINDS",
    "ACTIVITY_ASSESSMENT",
    "ACTIVITY_SAMPLE",
    "ACTIVITY_PROCEDURE",
    "ACTIVITY_CONTACT",
    "ENCOUNTER_KINDS",
    "ENCOUNTER_ONSITE",
    "ENCOUNTER_REMOTE",
    "ENCOUNTER_HOSPITAL",
    "ENCOUNTER_HOME",
    "ENCOUNTER_UNSCHEDULED",
    "ENCOUNTER_UNKNOWN",
    "MODALITIES",
    "MODALITY_ONSITE",
    "MODALITY_REMOTE",
    "MODALITY_PHONE",
    "MODALITY_HOME",
    "MODALITY_HOSPITAL",
    "MODALITY_OTHER",
    "MODALITY_UNKNOWN",
    "PRECISIONS",
    "PRECISION_MINUTE",
    "PRECISION_HOUR",
    "PRECISION_DAY",
    "PRECISION_MONTH",
    "PRECISION_YEAR",
    "PRECISION_UNKNOWN",
    "SUB_DAY_PRECISIONS",
    "DATE_ORIGINS",
    "DATE_ORIGIN_RECORDED",
    "DATE_ORIGIN_DERIVED",
    "SCOPE_STATUSES",
    "SCOPE_IN_SCOPE",
    "SCOPE_OUT_OF_CUTOFF",
    "SCOPE_BOUNDARY",
    "SCOPE_NOT_EVALUABLE",
    "APPLICABILITY_STATUSES",
    "APPLICABILITY_UNIQUE_ACTIVE",
    "APPLICABILITY_MULTI_FEASIBLE_BOUNDARY",
    "APPLICABILITY_NOT_EVALUABLE",
    "TRANSITION_RULES",
    "TRANSITION_NEW_ENROLLMENT_ONLY",
    "TRANSITION_EXISTING_CONTINUE_OLD",
    "TRANSITION_ALL_SWITCH",
    "TRANSITION_NEXT_VISIT_SWITCH",
    "TRANSITION_RECONSENT_SWITCH",
    "TRANSITION_OTHER_EXPLICIT",
    "TRANSITION_UNDETERMINED",
    "GATE_KINDS",
    "GATE_APPLICABILITY",
    "GATE_ROUTING",
    "GATE_ANCHOR",
    "GATE_CUTOFF_SCOPE",
    "GATE_STATES",
    "GATE_OPEN",
    "GATE_CLOSED",
    "GATE_DECISION_STATUSES",
    "GATE_DECISION_BOUNDARY",
    "GATE_DECISION_NOT_EVALUABLE",
    "GATE_DECISION_RESOLVED",
    "RELATION_TYPES",
    "RELATION_FIXED_REFERENCE",
    "RELATION_PRIOR_ACTUAL_VISIT",
    "RELATION_FIRST_IP_DOSE",
    "RELATION_RANDOMIZATION",
    "RELATION_CONSENT",
    "RELATION_OTHER_VERIFIED_PROTOCOL_ANCHOR",
    "PRODUCER_RELATION_TYPES",
    "INTERNAL_RELATION_TYPES",
    "UNIT_KINDS",
    "UNIT_VISIT_OCCURRENCE",
    "UNIT_VISIT_TIMING",
    "UNIT_VISIT_ORDER",
    "UNIT_ACTIVITY_OCCURRENCE",
    "UNIT_ACTIVITY_TIMING",
    "UNIT_ACTUAL_ASSIGNMENT",
    "UNIT_SCHEDULE_CONSISTENCY",
    "EPISODE_KINDS",
    "EPISODE_SINGLE_CONTACT",
    "EPISODE_MULTI_CONTACT",
    "EPISODE_HOSPITALIZATION",
    "EPISODE_REMOTE",
    "EPISODE_UNSCHEDULED",
    "EPISODE_UNKNOWN",
    "ASSIGNMENT_SCOPES",
    "ASSIGNMENT_SCOPE_SINGLE",
    "ASSIGNMENT_SCOPE_MULTI",
    "ASSIGNMENT_SCOPE_UNKNOWN",
    "VISIT_ASSIGNMENT_STATUSES",
    "VISIT_ASSIGNMENT_UNIQUE",
    "VISIT_ASSIGNMENT_MULTI_FEASIBLE",
    "VISIT_ASSIGNMENT_UNPLANNED_SUPPORTED",
    "VISIT_ASSIGNMENT_UNASSIGNED_INCONSISTENT",
    "VISIT_ASSIGNMENT_NOT_EVALUABLE",
    "ACTIVITY_ASSIGNMENT_STATUSES",
    "ACTIVITY_ASSIGNMENT_UNIQUE",
    "ACTIVITY_ASSIGNMENT_MULTI_FEASIBLE",
    "ACTIVITY_ASSIGNMENT_UNPLANNED_SUPPORTED",
    "ACTIVITY_ASSIGNMENT_DUPLICATE_CONSUMPTION",
    "ACTIVITY_ASSIGNMENT_NOT_EVALUABLE",
    "REVERSE_COVERAGE_STATUSES",
    "REVERSE_COVERAGE_CLOSED",
    "REVERSE_COVERAGE_OPEN",
    "OWNER_D05",
    "OWNER_D03",
    "OWNER_D04",
    "OWNER_D06",
    "OWNER_D07",
    "OWNER_D08",
    "OWNER_UNRESOLVED",
    "OWNER_DOMAINS",
    "REASON_CODES",
    "REASON_VERSION_MISSING",
    "REASON_VERSION_CONFLICT",
    "REASON_MULTIPLE_FEASIBLE",
    "REASON_SITE_ACTIVATION_MISSING",
    "REASON_COHORT_OR_ARM_CONFLICT",
    "REASON_TRANSITION_TIME_MISSING",
    "REASON_TRANSITION_TIME_CONFLICT",
    "REASON_ROUTING_COMPETITION",
    "REASON_ANCHOR_MISSING",
    "REASON_ANCHOR_CONFLICT",
    "REASON_PRODUCER_NOT_EVALUABLE",
    "REASON_TIME_ROLE_MISSING",
    "REASON_TIME_ROLE_CONFLICT",
    "REASON_INTERVAL_STRADDLES",
    "REASON_PRECISION_INSUFFICIENT",
    "REASON_TIMEZONE_MISSING",
    "REASON_IDENTITY_AMBIGUOUS",
    "REASON_MATURITY_RULE_MISSING",
    "REASON_MAPPING_MISSING",
    "REASON_SCHEDULE_MISSING",
    "REASON_INVALID_RELATION_TYPE",
    "REASON_WRONG_CONSUMER_DOMAIN",
    "REASON_WRONG_PRODUCER_DOMAIN",
    "REASON_SUBJECT_SITE_MISMATCH",
    "REASON_PHASE_OR_EPISODE_MISMATCH",
    "REASON_INTERVAL_MISMATCH",
    "REASON_PRECISION_OR_TIMEZONE_MISMATCH",
    "REASON_COVERAGE_INCOMPLETE",
    "REASON_OTHER",
    "CALENDAR_SEMANTICS",
    "CALENDAR_DATE",
    "ELAPSED_DURATION",
    "STUDY_DAY",
    "PROPAGATION_RULES",
    "PROPAGATION_FIXED_ANCHOR",
    "PROPAGATION_CHAINED_PRIOR_VISIT",
    "PROPAGATION_EXPLICIT_RESCHEDULE",
    "PROPAGATION_UNDEFINED",
    "MISSING_ANCHOR_EFFECT_GATE",
    "ANCHOR_SOURCE_ROLES",
    "ANCHOR_ROLE_VISIT_SCHEDULE",
    "ANCHOR_ROLE_IP_EXPOSURE",
    "ANCHOR_ROLE_RANDOMIZATION",
    "ANCHOR_ROLE_CONSENT",
    "ANCHOR_ROLE_DISPOSITION",
    "ANCHOR_ROLE_OTHER",
    "INTERPRETATION_SCOPES",
    "INTERPRET_SCOPE_MERGE",
    "INTERPRET_SCOPE_SPLIT",
    "INTERPRET_SCOPE_REPEAT",
    "INTERPRET_SCOPE_RESCHEDULE",
    "INTERPRET_SCOPE_TRIGGER",
    "INTERPRET_SCOPE_WINDOW",
    "INTERPRET_SCOPE_OTHER",
    "INTERPRETATION_PREDICATES",
    "PREDICATE_TRUE",
    "PREDICATE_FALSE",
    "PREDICATE_BOUNDARY",
    "PREDICATE_NOT_EVALUABLE",
    "MARKER_STATUS_HINTS",
    "STATUS_UPCOMING",
    "STATUS_DUE",
    "STATUS_EVALUATED",
    "STATUS_PENDING_ASSIGNMENT",
    "STATUS_PENDING_TIME",
    "ANCHOR_STATES",
    "ANCHOR_STATE_DATED",
    "ANCHOR_STATE_PARTIAL",
    "ANCHOR_STATE_PENDING_TIME",
    "ANCHOR_STATE_OUT_OF_CUTOFF",
    # Value objects
    "ScheduleSliceError",
    "SnapshotAsOf",
    "ClinicalEventCutoff",
    "VisitAnchorRule",
    "VisitWindowRule",
    "EvaluationMaturityRule",
    "PlannedVisitDefinition",
    "PlannedActivityDefinition",
    "VisitScheduleApplicabilityDecision",
    "ActualEncounterRecord",
    "ActualActivityRecord",
    "ActualEncounterBundle",
    "ActualRecordScopeDecision",
    "VisitAssignmentDecision",
    "ActivityAssignmentDecision",
    "ActualActivityConsumptionLedger",
    "TypedScheduleAnchorRef",
    "AnchorBindingOutcome",
    "ScheduleGate",
    "GateRunAccounting",
    "ScheduleInterpretationLedger",
    "ScheduleEvaluationUnit",
    "VisitCoverageGapNotice",
    "PlannedVisitMarker",
    "ActualEncounterMarker",
    "VisitRiskMarker",
    "VisitJourneyProjection",
    # Contract functions
    "encounter_stable_object_key",
    "activity_stable_object_key",
    "bundle_stable_object_key",
    "resolve_actual_record_scope",
    "build_actual_encounter_bundle",
    "validate_bundle_membership",
    "bind_typed_schedule_anchor",
    "anchor_binding_matches",
    "validate_gate_run_accounting",
    "all_gates_closed",
    "schedule_evaluation_window_id",
    "schedule_unit_stable_core",
    "schedule_unit_classifier",
]


# ---------------------------------------------------------------------------
# Domain identity
# ---------------------------------------------------------------------------

D05_DOMAIN = "D05_visit_schedule"
D05_UNIT_ALGO_VERSION = "d05_unit_v1"
D05_RULE_LINEAGE_DEFAULT = "d05-visit-schedule-rule-v1"
D05_SOURCE_IDENTITY_ALGORITHM_VERSION = "d05_source_identity_v1"


# ---------------------------------------------------------------------------
# Closed enums (frozen D05 contract §3)
# ---------------------------------------------------------------------------

#: Planned visit kinds (§3.1).
VISIT_SCHEDULED = "scheduled"
VISIT_TRIGGERED = "triggered"
VISIT_CONTINGENT = "contingent"
VISIT_REPEAT_ALLOWED = "repeat_allowed"
VISIT_KINDS: Tuple[str, ...] = (
    VISIT_SCHEDULED, VISIT_TRIGGERED, VISIT_CONTINGENT, VISIT_REPEAT_ALLOWED,
)

#: Planned/actual activity kinds (§3.1, §3.2).
ACTIVITY_ASSESSMENT = "assessment"
ACTIVITY_SAMPLE = "sample"
ACTIVITY_PROCEDURE = "procedure"
ACTIVITY_CONTACT = "contact"
ACTIVITY_KINDS: Tuple[str, ...] = (
    ACTIVITY_ASSESSMENT, ACTIVITY_SAMPLE, ACTIVITY_PROCEDURE, ACTIVITY_CONTACT,
)

#: Actual encounter kinds (§3.2).
ENCOUNTER_ONSITE = "onsite"
ENCOUNTER_REMOTE = "remote"
ENCOUNTER_HOSPITAL = "hospital"
ENCOUNTER_HOME = "home"
ENCOUNTER_UNSCHEDULED = "unscheduled"
ENCOUNTER_UNKNOWN = "unknown"
ENCOUNTER_KINDS: Tuple[str, ...] = (
    ENCOUNTER_ONSITE, ENCOUNTER_REMOTE, ENCOUNTER_HOSPITAL, ENCOUNTER_HOME,
    ENCOUNTER_UNSCHEDULED, ENCOUNTER_UNKNOWN,
)

#: Allowed visit modalities (§5.2) -- a planned visit may be completed
#: remotely/phone/home only when the applicable plan or effective rule
#: allows that modality.
MODALITY_ONSITE = "onsite"
MODALITY_REMOTE = "remote"
MODALITY_PHONE = "phone"
MODALITY_HOME = "home"
MODALITY_HOSPITAL = "hospital"
MODALITY_OTHER = "other"
MODALITY_UNKNOWN = "unknown"
MODALITIES: Tuple[str, ...] = (
    MODALITY_ONSITE, MODALITY_REMOTE, MODALITY_PHONE, MODALITY_HOME,
    MODALITY_HOSPITAL, MODALITY_OTHER, MODALITY_UNKNOWN,
)

#: Date/datetime precision (§6).  ``unknown`` means the effective time
#: role cannot be compared (never silently padded).
PRECISION_MINUTE = "minute"
PRECISION_HOUR = "hour"
PRECISION_DAY = "day"
PRECISION_MONTH = "month"
PRECISION_YEAR = "year"
PRECISION_UNKNOWN = "unknown"
PRECISIONS: Tuple[str, ...] = (
    PRECISION_MINUTE, PRECISION_HOUR, PRECISION_DAY, PRECISION_MONTH,
    PRECISION_YEAR, PRECISION_UNKNOWN,
)
SUB_DAY_PRECISIONS: Tuple[str, ...] = (PRECISION_MINUTE, PRECISION_HOUR)

#: Date origin (§3.2): a derived date must keep algorithm + input rows and
#: never masquerade as a recorded source date.
DATE_ORIGIN_RECORDED = "recorded"
DATE_ORIGIN_DERIVED = "derived"
DATE_ORIGINS: Tuple[str, ...] = (DATE_ORIGIN_RECORDED, DATE_ORIGIN_DERIVED)

#: Actual-record scope status (§3.2, §4.2).
SCOPE_IN_SCOPE = "in_scope"
SCOPE_OUT_OF_CUTOFF = "out_of_cutoff"
SCOPE_BOUNDARY = "boundary"
SCOPE_NOT_EVALUABLE = "not_evaluable"
SCOPE_STATUSES: Tuple[str, ...] = (
    SCOPE_IN_SCOPE, SCOPE_OUT_OF_CUTOFF, SCOPE_BOUNDARY, SCOPE_NOT_EVALUABLE,
)

#: Applicability decision status (§4.1).
APPLICABILITY_UNIQUE_ACTIVE = "unique_active"
APPLICABILITY_MULTI_FEASIBLE_BOUNDARY = "multi_feasible_boundary"
APPLICABILITY_NOT_EVALUABLE = "not_evaluable"
APPLICABILITY_STATUSES: Tuple[str, ...] = (
    APPLICABILITY_UNIQUE_ACTIVE,
    APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
    APPLICABILITY_NOT_EVALUABLE,
)

#: Amendment transition scopes (§4.1).
TRANSITION_NEW_ENROLLMENT_ONLY = "new_enrollment_only"
TRANSITION_EXISTING_CONTINUE_OLD = "existing_continue_old"
TRANSITION_ALL_SWITCH = "all_switch"
TRANSITION_NEXT_VISIT_SWITCH = "next_visit_switch"
TRANSITION_RECONSENT_SWITCH = "reconsent_switch"
TRANSITION_OTHER_EXPLICIT = "other_explicit"
TRANSITION_UNDETERMINED = "undetermined"
TRANSITION_RULES: Tuple[str, ...] = (
    TRANSITION_NEW_ENROLLMENT_ONLY,
    TRANSITION_EXISTING_CONTINUE_OLD,
    TRANSITION_ALL_SWITCH,
    TRANSITION_NEXT_VISIT_SWITCH,
    TRANSITION_RECONSENT_SWITCH,
    TRANSITION_OTHER_EXPLICIT,
    TRANSITION_UNDETERMINED,
)

#: Schedule gate kinds (§3.3).
GATE_APPLICABILITY = "applicability"
GATE_ROUTING = "routing"
GATE_ANCHOR = "anchor"
GATE_CUTOFF_SCOPE = "cutoff_scope"
GATE_KINDS: Tuple[str, ...] = (
    GATE_APPLICABILITY, GATE_ROUTING, GATE_ANCHOR, GATE_CUTOFF_SCOPE,
)

#: Schedule gate states (§3.3).
GATE_OPEN = "open"
GATE_CLOSED = "closed"
GATE_STATES: Tuple[str, ...] = (GATE_OPEN, GATE_CLOSED)

#: Schedule gate decision statuses (§3.3).
GATE_DECISION_BOUNDARY = "boundary"
GATE_DECISION_NOT_EVALUABLE = "not_evaluable"
GATE_DECISION_RESOLVED = "resolved"
GATE_DECISION_STATUSES: Tuple[str, ...] = (
    GATE_DECISION_BOUNDARY, GATE_DECISION_NOT_EVALUABLE, GATE_DECISION_RESOLVED,
)

#: Typed anchor relation types (§3.3, §5.3).
RELATION_FIXED_REFERENCE = "fixed_reference"
RELATION_PRIOR_ACTUAL_VISIT = "prior_actual_visit"
RELATION_FIRST_IP_DOSE = "first_ip_dose"
RELATION_RANDOMIZATION = "randomization"
RELATION_CONSENT = "consent"
RELATION_OTHER_VERIFIED_PROTOCOL_ANCHOR = "other_verified_protocol_anchor"
RELATION_TYPES: Tuple[str, ...] = (
    RELATION_FIXED_REFERENCE,
    RELATION_PRIOR_ACTUAL_VISIT,
    RELATION_FIRST_IP_DOSE,
    RELATION_RANDOMIZATION,
    RELATION_CONSENT,
    RELATION_OTHER_VERIFIED_PROTOCOL_ANCHOR,
)
#: Relation types that must be bound from a producer CrossDomainEvidenceRef.
PRODUCER_RELATION_TYPES: Tuple[str, ...] = (
    RELATION_FIRST_IP_DOSE, RELATION_RANDOMIZATION, RELATION_CONSENT,
    RELATION_OTHER_VERIFIED_PROTOCOL_ANCHOR,
)
#: Relation types resolved inside D05 itself (fixed Day 1 / chained prior
#: actual visit).
INTERNAL_RELATION_TYPES: Tuple[str, ...] = (
    RELATION_FIXED_REFERENCE, RELATION_PRIOR_ACTUAL_VISIT,
)

#: Evaluation unit kinds (§3.3 closed set).
UNIT_VISIT_OCCURRENCE = "visit_occurrence"
UNIT_VISIT_TIMING = "visit_timing"
UNIT_VISIT_ORDER = "visit_order"
UNIT_ACTIVITY_OCCURRENCE = "activity_occurrence"
UNIT_ACTIVITY_TIMING = "activity_timing"
UNIT_ACTUAL_ASSIGNMENT = "actual_assignment"
UNIT_SCHEDULE_CONSISTENCY = "schedule_consistency"
UNIT_KINDS: Tuple[str, ...] = (
    UNIT_VISIT_OCCURRENCE, UNIT_VISIT_TIMING, UNIT_VISIT_ORDER,
    UNIT_ACTIVITY_OCCURRENCE, UNIT_ACTIVITY_TIMING, UNIT_ACTUAL_ASSIGNMENT,
    UNIT_SCHEDULE_CONSISTENCY,
)

#: Encounter bundle episode kinds (§3.2, §5.2).
EPISODE_SINGLE_CONTACT = "single_contact"
EPISODE_MULTI_CONTACT = "multi_contact"
EPISODE_HOSPITALIZATION = "hospitalization"
EPISODE_REMOTE = "remote"
EPISODE_UNSCHEDULED = "unscheduled"
EPISODE_UNKNOWN = "unknown"
EPISODE_KINDS: Tuple[str, ...] = (
    EPISODE_SINGLE_CONTACT, EPISODE_MULTI_CONTACT, EPISODE_HOSPITALIZATION,
    EPISODE_REMOTE, EPISODE_UNSCHEDULED, EPISODE_UNKNOWN,
)

#: Bundle assignment scope (§3.2): a bundle supports one planned visit
#: unless an explicit merge rule allows more.
ASSIGNMENT_SCOPE_SINGLE = "single_planned_visit"
ASSIGNMENT_SCOPE_MULTI = "multi_planned_visit"
ASSIGNMENT_SCOPE_UNKNOWN = "unknown"
ASSIGNMENT_SCOPES: Tuple[str, ...] = (
    ASSIGNMENT_SCOPE_SINGLE, ASSIGNMENT_SCOPE_MULTI, ASSIGNMENT_SCOPE_UNKNOWN,
)

#: Visit assignment decision statuses (§5.1).
VISIT_ASSIGNMENT_UNIQUE = "unique"
VISIT_ASSIGNMENT_MULTI_FEASIBLE = "multi_feasible_boundary"
VISIT_ASSIGNMENT_UNPLANNED_SUPPORTED = "unplanned_supported"
VISIT_ASSIGNMENT_UNASSIGNED_INCONSISTENT = "unassigned_inconsistent"
VISIT_ASSIGNMENT_NOT_EVALUABLE = "not_evaluable"
VISIT_ASSIGNMENT_STATUSES: Tuple[str, ...] = (
    VISIT_ASSIGNMENT_UNIQUE,
    VISIT_ASSIGNMENT_MULTI_FEASIBLE,
    VISIT_ASSIGNMENT_UNPLANNED_SUPPORTED,
    VISIT_ASSIGNMENT_UNASSIGNED_INCONSISTENT,
    VISIT_ASSIGNMENT_NOT_EVALUABLE,
)

#: Activity assignment decision statuses (§7.2).
ACTIVITY_ASSIGNMENT_UNIQUE = "unique"
ACTIVITY_ASSIGNMENT_MULTI_FEASIBLE = "multi_feasible_boundary"
ACTIVITY_ASSIGNMENT_UNPLANNED_SUPPORTED = "unplanned_supported"
ACTIVITY_ASSIGNMENT_DUPLICATE_CONSUMPTION = "duplicate_consumption"
ACTIVITY_ASSIGNMENT_NOT_EVALUABLE = "not_evaluable"
ACTIVITY_ASSIGNMENT_STATUSES: Tuple[str, ...] = (
    ACTIVITY_ASSIGNMENT_UNIQUE,
    ACTIVITY_ASSIGNMENT_MULTI_FEASIBLE,
    ACTIVITY_ASSIGNMENT_UNPLANNED_SUPPORTED,
    ACTIVITY_ASSIGNMENT_DUPLICATE_CONSUMPTION,
    ACTIVITY_ASSIGNMENT_NOT_EVALUABLE,
)

#: Consumption-ledger reverse coverage status (§7.2).
REVERSE_COVERAGE_CLOSED = "closed"
REVERSE_COVERAGE_OPEN = "open"
REVERSE_COVERAGE_STATUSES: Tuple[str, ...] = (
    REVERSE_COVERAGE_CLOSED, REVERSE_COVERAGE_OPEN,
)

#: Owner domains (§2.3 routing).  D05's own real owner token is
#: ``D05_visit_schedule``; D04's protocol.py keeps its historical
#: ``D05_visit_window`` stub untouched (outside this module's write list).
OWNER_D05 = D05_DOMAIN
OWNER_D03 = "D03_ip_exposure"
OWNER_D04 = "D04_protocol_compliance"
OWNER_D06 = "D06_endpoint"
OWNER_D07 = "D07_laboratory"
OWNER_D08 = "D08_multi_table_relation"
OWNER_UNRESOLVED = "owner_unresolved"
OWNER_DOMAINS: Tuple[str, ...] = (
    OWNER_D05, OWNER_D03, OWNER_D04, OWNER_D06, OWNER_D07, OWNER_D08,
    OWNER_UNRESOLVED,
)

#: Closed reason codes used by scope decisions, gates, anchors, ledger and
#: coverage-gap notices.  The frozen D05 contract does not freeze the
#: reason-code vocabulary; this closed set is the implementation's frozen
#: vocabulary (extending it requires a module revision).
REASON_VERSION_MISSING = "version_missing"
REASON_VERSION_CONFLICT = "version_conflict"
REASON_MULTIPLE_FEASIBLE = "multiple_feasible"
REASON_SITE_ACTIVATION_MISSING = "site_activation_missing"
REASON_COHORT_OR_ARM_CONFLICT = "cohort_or_arm_conflict"
REASON_TRANSITION_TIME_MISSING = "transition_time_missing"
REASON_TRANSITION_TIME_CONFLICT = "transition_time_conflict"
REASON_ROUTING_COMPETITION = "routing_competition"
REASON_ANCHOR_MISSING = "anchor_missing"
REASON_ANCHOR_CONFLICT = "anchor_conflict"
REASON_PRODUCER_NOT_EVALUABLE = "producer_not_evaluable"
REASON_TIME_ROLE_MISSING = "time_role_missing"
REASON_TIME_ROLE_CONFLICT = "time_role_conflict"
REASON_INTERVAL_STRADDLES = "interval_straddles_cutoff"
REASON_PRECISION_INSUFFICIENT = "precision_insufficient"
REASON_TIMEZONE_MISSING = "timezone_missing"
REASON_IDENTITY_AMBIGUOUS = "identity_ambiguous"
REASON_MATURITY_RULE_MISSING = "maturity_rule_missing"
REASON_MAPPING_MISSING = "mapping_missing"
REASON_SCHEDULE_MISSING = "schedule_missing"
REASON_INVALID_RELATION_TYPE = "invalid_relation_type"
REASON_WRONG_CONSUMER_DOMAIN = "wrong_consumer_domain"
REASON_WRONG_PRODUCER_DOMAIN = "wrong_producer_domain"
REASON_SUBJECT_SITE_MISMATCH = "subject_site_mismatch"
REASON_PHASE_OR_EPISODE_MISMATCH = "phase_or_episode_mismatch"
REASON_INTERVAL_MISMATCH = "interval_mismatch"
REASON_PRECISION_OR_TIMEZONE_MISMATCH = "precision_or_timezone_mismatch"
REASON_COVERAGE_INCOMPLETE = "coverage_incomplete"
REASON_OTHER = "other"
REASON_CODES: Tuple[str, ...] = (
    REASON_VERSION_MISSING,
    REASON_VERSION_CONFLICT,
    REASON_MULTIPLE_FEASIBLE,
    REASON_SITE_ACTIVATION_MISSING,
    REASON_COHORT_OR_ARM_CONFLICT,
    REASON_TRANSITION_TIME_MISSING,
    REASON_TRANSITION_TIME_CONFLICT,
    REASON_ROUTING_COMPETITION,
    REASON_ANCHOR_MISSING,
    REASON_ANCHOR_CONFLICT,
    REASON_PRODUCER_NOT_EVALUABLE,
    REASON_TIME_ROLE_MISSING,
    REASON_TIME_ROLE_CONFLICT,
    REASON_INTERVAL_STRADDLES,
    REASON_PRECISION_INSUFFICIENT,
    REASON_TIMEZONE_MISSING,
    REASON_IDENTITY_AMBIGUOUS,
    REASON_MATURITY_RULE_MISSING,
    REASON_MAPPING_MISSING,
    REASON_SCHEDULE_MISSING,
    REASON_INVALID_RELATION_TYPE,
    REASON_WRONG_CONSUMER_DOMAIN,
    REASON_WRONG_PRODUCER_DOMAIN,
    REASON_SUBJECT_SITE_MISMATCH,
    REASON_PHASE_OR_EPISODE_MISMATCH,
    REASON_INTERVAL_MISMATCH,
    REASON_PRECISION_OR_TIMEZONE_MISMATCH,
    REASON_COVERAGE_INCOMPLETE,
    REASON_OTHER,
)

#: Window calendar semantics (§6).
CALENDAR_DATE = "calendar_date"
ELAPSED_DURATION = "elapsed_duration"
STUDY_DAY = "study_day"
CALENDAR_SEMANTICS: Tuple[str, ...] = (
    CALENDAR_DATE, ELAPSED_DURATION, STUDY_DAY,
)

#: Window propagation rules (§6): fixed anchors never auto-shift; chained
#: anchors propagate only by explicit rule.
PROPAGATION_FIXED_ANCHOR = "fixed_anchor"
PROPAGATION_CHAINED_PRIOR_VISIT = "chained_prior_visit"
PROPAGATION_EXPLICIT_RESCHEDULE = "explicit_reschedule"
PROPAGATION_UNDEFINED = "undefined"
PROPAGATION_RULES: Tuple[str, ...] = (
    PROPAGATION_FIXED_ANCHOR,
    PROPAGATION_CHAINED_PRIOR_VISIT,
    PROPAGATION_EXPLICIT_RESCHEDULE,
    PROPAGATION_UNDEFINED,
)

#: Missing-anchor effect (§3.1): the only frozen effect is ``gate``.
MISSING_ANCHOR_EFFECT_GATE = "gate"
MISSING_ANCHOR_EFFECTS: Tuple[str, ...] = (MISSING_ANCHOR_EFFECT_GATE,)

#: Anchor source roles (§3.1/§3.3) -- semantic roles, never fixed table
#: names.
ANCHOR_ROLE_VISIT_SCHEDULE = "visit_schedule"
ANCHOR_ROLE_IP_EXPOSURE = "ip_exposure"
ANCHOR_ROLE_RANDOMIZATION = "randomization"
ANCHOR_ROLE_CONSENT = "consent"
ANCHOR_ROLE_DISPOSITION = "disposition"
ANCHOR_ROLE_OTHER = "other"
ANCHOR_SOURCE_ROLES: Tuple[str, ...] = (
    ANCHOR_ROLE_VISIT_SCHEDULE, ANCHOR_ROLE_IP_EXPOSURE,
    ANCHOR_ROLE_RANDOMIZATION, ANCHOR_ROLE_CONSENT, ANCHOR_ROLE_DISPOSITION,
    ANCHOR_ROLE_OTHER,
)

#: Interpretation-ledger decision scopes (§6).
INTERPRET_SCOPE_MERGE = "merge"
INTERPRET_SCOPE_SPLIT = "split"
INTERPRET_SCOPE_REPEAT = "repeat"
INTERPRET_SCOPE_RESCHEDULE = "reschedule"
INTERPRET_SCOPE_TRIGGER = "trigger"
INTERPRET_SCOPE_WINDOW = "window"
INTERPRET_SCOPE_OTHER = "other"
INTERPRETATION_SCOPES: Tuple[str, ...] = (
    INTERPRET_SCOPE_MERGE, INTERPRET_SCOPE_SPLIT, INTERPRET_SCOPE_REPEAT,
    INTERPRET_SCOPE_RESCHEDULE, INTERPRET_SCOPE_TRIGGER, INTERPRET_SCOPE_WINDOW,
    INTERPRET_SCOPE_OTHER,
)

#: Interpretation predicate results (§6): an excluded interpretation must
#: carry a versioned predicate and reason code.
PREDICATE_TRUE = "true"
PREDICATE_FALSE = "false"
PREDICATE_BOUNDARY = "boundary"
PREDICATE_NOT_EVALUABLE = "not_evaluable"
INTERPRETATION_PREDICATES: Tuple[str, ...] = (
    PREDICATE_TRUE, PREDICATE_FALSE, PREDICATE_BOUNDARY,
    PREDICATE_NOT_EVALUABLE,
)

#: Journey planned-visit marker status hints (§10).
STATUS_UPCOMING = "upcoming"
STATUS_DUE = "due"
STATUS_EVALUATED = "evaluated"
STATUS_PENDING_ASSIGNMENT = "pending_assignment"
STATUS_PENDING_TIME = "pending_time"
MARKER_STATUS_HINTS: Tuple[str, ...] = (
    STATUS_UPCOMING, STATUS_DUE, STATUS_EVALUATED, STATUS_PENDING_ASSIGNMENT,
    STATUS_PENDING_TIME,
)

#: Journey encounter/risk marker anchor states (§10).
ANCHOR_STATE_DATED = "dated"
ANCHOR_STATE_PARTIAL = "partial"
ANCHOR_STATE_PENDING_TIME = "pending_time"
ANCHOR_STATE_OUT_OF_CUTOFF = "out_of_cutoff"
ANCHOR_STATES: Tuple[str, ...] = (
    ANCHOR_STATE_DATED, ANCHOR_STATE_PARTIAL, ANCHOR_STATE_PENDING_TIME,
    ANCHOR_STATE_OUT_OF_CUTOFF,
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ScheduleSliceError(Exception):
    """A D05 visit-schedule domain invariant was violated."""


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO_DURATION_RE = re.compile(r"^P(?:\d+(?:\.\d+)?[YMWD])+$|^P$")
_DAY_COUNT_RE = re.compile(r"^[+-]?\d+$")


def _validate_nonempty(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScheduleSliceError(
            f"{field_name} is required and must be a non-empty string")
    return value


def _validate_optional_str(value: Any, field_name: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ScheduleSliceError(f"{field_name} must be a str or None")
    return value


def _freeze_tuple(value: Any, field_name: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raise ScheduleSliceError(
            f"{field_name} must be a sequence of strings, not a single str")
    result: List[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ScheduleSliceError(
                f"{field_name} entries must be non-empty strings")
        result.append(item)
    return tuple(result)


def _canonical_sorted(value: Sequence[str]) -> Tuple[str, ...]:
    """Deduplicated, deterministically sorted tuple of non-empty strings."""
    seen: List[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ScheduleSliceError(
                "tuple entries must be non-empty strings")
        if item not in seen:
            seen.append(item)
    return tuple(sorted(seen))


def _require_member(value: str, closed_set: Sequence[str], field_name: str,
                    allow_empty: bool = False) -> None:
    if not value.strip():
        if allow_empty:
            return
        raise ScheduleSliceError(f"{field_name} is required")
    if value not in closed_set:
        raise ScheduleSliceError(
            f"{field_name}={value!r} is not a member of the closed set "
            f"{tuple(closed_set)}")


def _date_precision(raw: str) -> str:
    """Precision of a raw date string (day/month/year/unknown) using the
    frozen R3 partial-date normalization; never silently padded."""
    if not raw.strip():
        return PRECISION_UNKNOWN
    nv = normalize_partial_date(raw)
    if not nv.normalized:
        return PRECISION_UNKNOWN
    parts = str(nv.normalized).split("-")
    if len(parts) == 3:
        return PRECISION_DAY
    if len(parts) == 2:
        return PRECISION_MONTH
    if len(parts) == 1:
        return PRECISION_YEAR
    return PRECISION_UNKNOWN


def _day_date(raw: str) -> Optional[datetime.date]:
    """Parse a day-precision date, or None when missing/partial/invalid."""
    if not raw.strip():
        return None
    nv = normalize_partial_date(raw)
    if not nv.normalized or _date_precision(raw) != PRECISION_DAY:
        return None
    try:
        return datetime.date.fromisoformat(str(nv.normalized))
    except (ValueError, TypeError):
        return None


def _day_interval(
    raw: str,
) -> Optional[Tuple[Optional[datetime.date], Optional[datetime.date]]]:
    """Earliest/latest day-dates implied by a partial date.

    ``"2026-01-15"`` -> (d, d); ``"2026-01"`` -> (Jan 1, Jan 31);
    ``"2026"`` -> (Jan 1, Dec 31); missing/invalid -> None.
    """
    if not raw.strip():
        return None
    nv = normalize_partial_date(raw)
    if not nv.normalized:
        return None
    parts = str(nv.normalized).split("-")
    try:
        if len(parts) == 3:
            d = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
            return (d, d)
        if len(parts) == 2:
            y, m = int(parts[0]), int(parts[1])
            start = datetime.date(y, m, 1)
            if m == 12:
                end = datetime.date(y, 12, 31)
            else:
                end = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)
            return (start, end)
        if len(parts) == 1:
            y = int(parts[0])
            return (datetime.date(y, 1, 1), datetime.date(y, 12, 31))
    except (ValueError, TypeError):
        return None
    return None


_PRECISION_RANK: Dict[str, int] = {
    PRECISION_MINUTE: 0,
    PRECISION_HOUR: 1,
    PRECISION_DAY: 2,
    PRECISION_MONTH: 3,
    PRECISION_YEAR: 4,
    PRECISION_UNKNOWN: 5,
}


def _coarsest_precision(precisions: Sequence[str]) -> str:
    """Coarsest precision among a set (unknown is the coarsest)."""
    best = PRECISION_UNKNOWN
    best_rank = -1
    for precision in precisions:
        rank = _PRECISION_RANK.get(precision, 5)
        if rank > best_rank:
            best_rank = rank
            best = precision
    return best


def _tzinfo(tz: str) -> Optional[datetime.tzinfo]:
    """Parse a frozen timezone token into a tzinfo.

    Accepts ``UTC``/``Z``, numeric offsets (``+08:00``, ``-05:00``) and
    IANA names via :mod:`zoneinfo`.  Unknown tokens return None so the
    caller fails closed (never silently defaults to local time).
    """
    if not tz or not tz.strip():
        return None
    token = tz.strip()
    if token in ("UTC", "Z", "z"):
        return datetime.timezone.utc
    match = re.fullmatch(
        r"([+-])(\d{2}):(\d{2})", token)
    if match:
        sign = 1 if match.group(1) == "+" else -1
        hours = int(match.group(2))
        minutes = int(match.group(3))
        if hours > 23 or minutes > 59:
            return None
        return datetime.timezone(
            sign * datetime.timedelta(hours=hours, minutes=minutes))
    try:
        from zoneinfo import ZoneInfo  # stdlib >= 3.9
        return ZoneInfo(token)
    except Exception:
        return None


def _parse_instant(raw: str, tz: str) -> Optional[datetime.datetime]:
    """Parse a sub-day datetime instant, normalized to UTC when a
    timezone token resolves.  Returns None on missing/invalid input."""
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    try:
        parsed = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None:
        resolved = _tzinfo(tz)
        if resolved is None:
            return None
        parsed = parsed.replace(tzinfo=resolved)
    return parsed.astimezone(datetime.timezone.utc)


def _day_instant_interval(
    lo: datetime.date, hi: datetime.date,
) -> Tuple[datetime.datetime, datetime.datetime]:
    """Day interval as UTC instants with inclusive end-of-day semantics
    (a day-precision cutoff includes events on the cutoff day)."""
    start = datetime.datetime.combine(lo, datetime.time.min,
                                      tzinfo=datetime.timezone.utc)
    end = datetime.datetime.combine(hi, datetime.time.max,
                                    tzinfo=datetime.timezone.utc)
    return start, end


def _interval_compare(
    lo: datetime.datetime, hi: datetime.datetime,
    cutoff: datetime.datetime,
) -> str:
    """Determinate scope relation of one interval vs one cutoff instant.

    Returns ``in_scope`` (hi <= cutoff), ``out_of_cutoff`` (lo > cutoff)
    or ``boundary`` (interval straddles the cutoff).
    """
    if hi <= cutoff:
        return SCOPE_IN_SCOPE
    if lo > cutoff:
        return SCOPE_OUT_OF_CUTOFF
    return SCOPE_BOUNDARY


def _payload_ids(locators: Sequence[SourceLocator]) -> List[str]:
    return sorted(loc.locator_id() for loc in locators)


def _marker_id_list(
    markers: Sequence[Any], *, expected_type: str, id_prefix: str,
) -> List[str]:
    """Deterministically sorted content-addressed marker ids of a Journey
    marker collection.

    Every Journey marker (planned/actual/activity/pending/out-of-cutoff)
    is a renderer-neutral value object carrying a content-addressed
    ``marker_id`` (``d05-*``).  This helper extracts those ids in a
    canonical order so the projection identity covers the *set* of markers
    - not their input order - and fails closed if a marker lacks a stable
    id (a marker with an empty id could never be content-addressed).
    """
    ids: List[str] = []
    for marker in markers:
        marker_type = type(marker)
        if marker_type.__module__ not in (
                "mm_r4.visit_schedule_projection",
                "packages.medical_monitoring.projections.visit_schedule",
        ) \
                or marker_type.__name__ != expected_type \
                or not is_dataclass(marker):
            raise ScheduleSliceError(
                f"Journey marker collection requires {expected_type}; "
                f"received {marker_type.__module__}."
                f"{marker_type.__name__}")
        marker_id = getattr(marker, "marker_id", "")
        if not isinstance(marker_id, str) or not marker_id.strip():
            raise ScheduleSliceError(
                "Journey marker collection carries a marker without a "
                "content-addressed marker_id")
        payload = {
            field.name: getattr(marker, field.name)
            for field in fields(marker)
            if field.name != "marker_id"
        }
        expected_id = id_prefix + content_hash(payload)
        if marker_id != expected_id:
            raise ScheduleSliceError(
                f"{expected_type}.marker_id {marker_id!r} does not match "
                f"its current content {expected_id!r}")
        ids.append(marker_id)
    return sorted(ids)


# ---------------------------------------------------------------------------
# Dual time boundaries (§4.2) -- frozen separately, never interchangeable
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SnapshotAsOf:
    """The accepted full snapshot boundary: what this Run actually read.

    ``accepted_at`` is the snapshot acceptance/formation timepoint and
    ``source_revision_id`` the source revision.  Together with
    :class:`ClinicalEventCutoff` it forms the frozen dual time boundary of
    one Run (§4.2).
    """

    snapshot_id: str
    accepted_at: str
    source_revision_id: str

    def __post_init__(self) -> None:
        _validate_nonempty(self.snapshot_id, "SnapshotAsOf.snapshot_id")
        _validate_nonempty(self.accepted_at, "SnapshotAsOf.accepted_at")
        _validate_nonempty(self.source_revision_id,
                           "SnapshotAsOf.source_revision_id")
        try:
            datetime.datetime.fromisoformat(
                self.accepted_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            raise ScheduleSliceError(
                f"SnapshotAsOf.accepted_at {self.accepted_at!r} is not an "
                f"ISO-8601 datetime")

    def canonical(self) -> str:
        return content_hash({
            "snapshot_id": self.snapshot_id,
            "accepted_at": self.accepted_at,
            "source_revision_id": self.source_revision_id,
        })


@dataclass(frozen=True)
class ClinicalEventCutoff:
    """The clinical-event cutoff: the effective timepoint through which
    actual events may be evaluated in this Run.

    Only day/hour/minute precision is allowed for a cutoff (a medical
    monitoring cutoff is a day or a timepoint); sub-day cutoffs require a
    timezone (never silently local).  A record is eligible only when its
    comparable event/collection effective interval is entirely not later
    than this cutoff (§4.2).
    """

    cutoff: str
    precision: str = PRECISION_DAY
    timezone: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.cutoff, "ClinicalEventCutoff.cutoff")
        _require_member(self.precision, PRECISIONS,
                        "ClinicalEventCutoff.precision")
        if self.precision not in (PRECISION_DAY, PRECISION_HOUR,
                                  PRECISION_MINUTE):
            raise ScheduleSliceError(
                f"ClinicalEventCutoff precision must be day/hour/minute, "
                f"got {self.precision!r}")
        if self.precision in SUB_DAY_PRECISIONS:
            if not self.timezone.strip():
                raise ScheduleSliceError(
                    "ClinicalEventCutoff requires a timezone at sub-day "
                    "precision (never silently local)")
            if _tzinfo(self.timezone) is None:
                raise ScheduleSliceError(
                    f"ClinicalEventCutoff timezone {self.timezone!r} is "
                    f"not a resolvable UTC/offset/IANA token")
        self._validate_parseable()

    def _validate_parseable(self) -> None:
        if self.precision == PRECISION_DAY:
            if _day_date(self.cutoff) is None:
                raise ScheduleSliceError(
                    f"ClinicalEventCutoff {self.cutoff!r} is not a "
                    f"day-precision date")
        else:
            if _parse_instant(self.cutoff, self.timezone) is None:
                raise ScheduleSliceError(
                    f"ClinicalEventCutoff {self.cutoff!r} is not parseable "
                    f"at {self.precision} precision with timezone "
                    f"{self.timezone!r}")

    def canonical(self) -> str:
        return content_hash({
            "cutoff": self.cutoff,
            "precision": self.precision,
            "timezone": self.timezone,
        })

    def cutoff_instant(self) -> datetime.datetime:
        """The cutoff as a UTC instant; day cutoffs use inclusive
        end-of-day semantics."""
        if self.precision == PRECISION_DAY:
            day = _day_date(self.cutoff)
            assert day is not None
            start, end = _day_instant_interval(day, day)
            return end
        instant = _parse_instant(self.cutoff, self.timezone)
        if instant is None:
            raise ScheduleSliceError(
                f"ClinicalEventCutoff {self.cutoff!r} is not parseable")
        return instant


# ---------------------------------------------------------------------------
# Planned objects (§3.1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VisitAnchorRule:
    """Versioned anchor rule for one planned visit (§3.1, §5.3).

    ``anchor_kind`` is the closed relation-type set; a producer relation
    resolves only through an exact ``TypedScheduleAnchorRef`` binding.
    """

    anchor_kind: str
    anchor_source_role: str
    anchor_ref_id: str = ""
    rule_version: str = D05_RULE_LINEAGE_DEFAULT
    source_locator_ids: Tuple[str, ...] = ()
    content_hash: str = ""

    def __post_init__(self) -> None:
        _require_member(self.anchor_kind, RELATION_TYPES,
                        "VisitAnchorRule.anchor_kind")
        _require_member(self.anchor_source_role, ANCHOR_SOURCE_ROLES,
                        "VisitAnchorRule.anchor_source_role")
        _validate_optional_str(self.anchor_ref_id,
                               "VisitAnchorRule.anchor_ref_id")
        _validate_nonempty(self.rule_version, "VisitAnchorRule.rule_version")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        computed = self.compute_content_hash()
        if self.content_hash and self.content_hash != computed:
            raise ScheduleSliceError(
                f"VisitAnchorRule.content_hash {self.content_hash!r} does "
                f"not match the canonical hash {computed!r}")
        object.__setattr__(self, "content_hash", computed)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "anchor_kind": self.anchor_kind,
            "anchor_source_role": self.anchor_source_role,
            "anchor_ref_id": self.anchor_ref_id,
            "rule_version": self.rule_version,
            "source_locator_ids": list(self.source_locator_ids),
        }

    def compute_content_hash(self) -> str:
        return "d05-anchorrule-" + content_hash(self.canonical_payload())


@dataclass(frozen=True)
class VisitWindowRule:
    """Versioned, locatable window rule (§6) -- the kernel never defaults
    ±N days, Day 0, timezone, endpoint inclusivity or a fixed Day 1 anchor.

    ``study_day_zero_exists``, ``lower_endpoint_inclusive`` and
    ``upper_endpoint_inclusive`` are tri-state: ``None`` explicitly means
    *unfrozen/unstated* and must be evaluated as ``not_evaluable``, never
    silently defaulted.
    """

    window_rule_id: str
    anchor_kind: str
    anchor_source_role: str
    calendar_semantics: str
    propagation_rule: str
    lower_offset: str = ""
    upper_offset: str = ""
    study_day_zero_exists: Optional[bool] = None
    lower_endpoint_inclusive: Optional[bool] = None
    upper_endpoint_inclusive: Optional[bool] = None
    grace_period: str = ""
    date_precision: str = PRECISION_UNKNOWN
    timezone: str = ""
    anchor_ref_id: str = ""
    rule_version: str = D05_RULE_LINEAGE_DEFAULT
    source_locator_ids: Tuple[str, ...] = ()
    content_hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.window_rule_id, "VisitWindowRule.window_rule_id")
        _require_member(self.anchor_kind, RELATION_TYPES,
                        "VisitWindowRule.anchor_kind")
        _require_member(self.anchor_source_role, ANCHOR_SOURCE_ROLES,
                        "VisitWindowRule.anchor_source_role")
        _require_member(self.calendar_semantics, CALENDAR_SEMANTICS,
                        "VisitWindowRule.calendar_semantics")
        _require_member(self.propagation_rule, PROPAGATION_RULES,
                        "VisitWindowRule.propagation_rule")
        _require_member(self.date_precision, PRECISIONS,
                        "VisitWindowRule.date_precision")
        _validate_optional_str(self.lower_offset,
                               "VisitWindowRule.lower_offset")
        _validate_optional_str(self.upper_offset,
                               "VisitWindowRule.upper_offset")
        _validate_optional_str(self.grace_period,
                               "VisitWindowRule.grace_period")
        _validate_optional_str(self.timezone, "VisitWindowRule.timezone")
        _validate_optional_str(self.anchor_ref_id,
                               "VisitWindowRule.anchor_ref_id")
        _validate_nonempty(self.rule_version, "VisitWindowRule.rule_version")
        for name, value in (("lower_offset", self.lower_offset),
                            ("upper_offset", self.upper_offset),
                            ("grace_period", self.grace_period)):
            if value and not (_DAY_COUNT_RE.match(value)
                              or _ISO_DURATION_RE.match(value)):
                raise ScheduleSliceError(
                    f"VisitWindowRule.{name} {value!r} must be a signed "
                    f"day count or ISO-8601 duration (no free text)")
        if self.date_precision in SUB_DAY_PRECISIONS:
            if not self.timezone.strip():
                raise ScheduleSliceError(
                    "VisitWindowRule requires a timezone at sub-day "
                    "precision (never silently local)")
            if _tzinfo(self.timezone) is None:
                raise ScheduleSliceError(
                    f"VisitWindowRule timezone {self.timezone!r} is not "
                    f"resolvable")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        computed = self.compute_content_hash()
        if self.content_hash and self.content_hash != computed:
            raise ScheduleSliceError(
                f"VisitWindowRule.content_hash {self.content_hash!r} does "
                f"not match the canonical hash {computed!r}")
        object.__setattr__(self, "content_hash", computed)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "window_rule_id": self.window_rule_id,
            "anchor_kind": self.anchor_kind,
            "anchor_source_role": self.anchor_source_role,
            "calendar_semantics": self.calendar_semantics,
            "propagation_rule": self.propagation_rule,
            "lower_offset": self.lower_offset,
            "upper_offset": self.upper_offset,
            "study_day_zero_exists": self.study_day_zero_exists,
            "lower_endpoint_inclusive": self.lower_endpoint_inclusive,
            "upper_endpoint_inclusive": self.upper_endpoint_inclusive,
            "grace_period": self.grace_period,
            "date_precision": self.date_precision,
            "timezone": self.timezone,
            "anchor_ref_id": self.anchor_ref_id,
            "rule_version": self.rule_version,
            "source_locator_ids": list(self.source_locator_ids),
        }

    def compute_content_hash(self) -> str:
        return "d05-window-" + content_hash(self.canonical_payload())


@dataclass(frozen=True)
class EvaluationMaturityRule:
    """Frozen maturity rule for one unit kind (§3.1, §4.2).  Only when the
    maturity timepoint computed from this rule is not later than the
    clinical event cutoff may the obligation enter the normal expected-set.
    """

    maturity_rule_id: str
    unit_kind: str
    anchor_kind: str
    anchor_source_role: str
    maturity_expression: str
    cutoff_precision: str
    timezone: str = ""
    missing_anchor_effect: str = MISSING_ANCHOR_EFFECT_GATE
    rule_version: str = D05_RULE_LINEAGE_DEFAULT
    source_locator_ids: Tuple[str, ...] = ()
    hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.maturity_rule_id,
                           "EvaluationMaturityRule.maturity_rule_id")
        _require_member(self.unit_kind, UNIT_KINDS,
                        "EvaluationMaturityRule.unit_kind")
        _require_member(self.anchor_kind, RELATION_TYPES,
                        "EvaluationMaturityRule.anchor_kind")
        _require_member(self.anchor_source_role, ANCHOR_SOURCE_ROLES,
                        "EvaluationMaturityRule.anchor_source_role")
        _validate_nonempty(self.maturity_expression,
                           "EvaluationMaturityRule.maturity_expression")
        _require_member(self.cutoff_precision, PRECISIONS,
                        "EvaluationMaturityRule.cutoff_precision")
        _require_member(self.missing_anchor_effect, MISSING_ANCHOR_EFFECTS,
                        "EvaluationMaturityRule.missing_anchor_effect")
        if self.missing_anchor_effect != MISSING_ANCHOR_EFFECT_GATE:
            raise ScheduleSliceError(
                "EvaluationMaturityRule.missing_anchor_effect must be "
                "'gate' (frozen §3.1)")
        _validate_optional_str(self.timezone,
                               "EvaluationMaturityRule.timezone")
        if self.cutoff_precision in SUB_DAY_PRECISIONS:
            if not self.timezone.strip():
                raise ScheduleSliceError(
                    "EvaluationMaturityRule requires a timezone at sub-day "
                    "cutoff precision (never silently local)")
        _validate_nonempty(self.rule_version,
                           "EvaluationMaturityRule.rule_version")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        computed = self.compute_hash()
        if self.hash and self.hash != computed:
            raise ScheduleSliceError(
                f"EvaluationMaturityRule.hash {self.hash!r} does not match "
                f"the canonical hash {computed!r}")
        object.__setattr__(self, "hash", computed)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "maturity_rule_id": self.maturity_rule_id,
            "unit_kind": self.unit_kind,
            "anchor_kind": self.anchor_kind,
            "anchor_source_role": self.anchor_source_role,
            "maturity_expression": self.maturity_expression,
            "cutoff_precision": self.cutoff_precision,
            "timezone": self.timezone,
            "missing_anchor_effect": self.missing_anchor_effect,
            "rule_version": self.rule_version,
            "source_locator_ids": list(self.source_locator_ids),
        }

    def compute_hash(self) -> str:
        return "d05-maturity-" + content_hash(self.canonical_payload())


@dataclass(frozen=True)
class PlannedVisitDefinition:
    """One versioned planned visit definition (§3.1).

    ``planned_visit_key`` is the cross-revision stable logical obligation;
    ``planned_visit_id`` is the versioned definition id.  ``planned_order``
    and the anchor lineage are explicit; VISITNUM/display order are
    identification evidence, never time authority.
    """

    planned_visit_id: str
    planned_visit_key: str
    schedule_id: str
    protocol_version: str
    official_visit_code: str
    audience_visit_name: str
    planned_order: str
    visit_kind: str
    phase: str
    applicability_expression: str
    anchor_rule: VisitAnchorRule
    window_rule: VisitWindowRule
    allowed_modalities: Tuple[str, ...] = (MODALITY_ONSITE,)
    merge_or_split_rule: str = ""
    source_locator_ids: Tuple[str, ...] = ()
    definition_hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.planned_visit_id,
                           "PlannedVisitDefinition.planned_visit_id")
        _validate_nonempty(self.planned_visit_key,
                           "PlannedVisitDefinition.planned_visit_key")
        _validate_nonempty(self.schedule_id,
                           "PlannedVisitDefinition.schedule_id")
        _validate_nonempty(self.protocol_version,
                           "PlannedVisitDefinition.protocol_version")
        _validate_nonempty(self.official_visit_code,
                           "PlannedVisitDefinition.official_visit_code")
        _validate_nonempty(self.audience_visit_name,
                           "PlannedVisitDefinition.audience_visit_name")
        _validate_nonempty(self.planned_order,
                           "PlannedVisitDefinition.planned_order")
        _require_member(self.visit_kind, VISIT_KINDS,
                        "PlannedVisitDefinition.visit_kind")
        _validate_nonempty(self.phase, "PlannedVisitDefinition.phase")
        _validate_nonempty(self.applicability_expression,
                           "PlannedVisitDefinition.applicability_expression")
        if not isinstance(self.anchor_rule, VisitAnchorRule):
            raise ScheduleSliceError(
                "PlannedVisitDefinition.anchor_rule must be a VisitAnchorRule")
        if not isinstance(self.window_rule, VisitWindowRule):
            raise ScheduleSliceError(
                "PlannedVisitDefinition.window_rule must be a VisitWindowRule")
        _validate_optional_str(self.merge_or_split_rule,
                               "PlannedVisitDefinition.merge_or_split_rule")
        for modality in self.allowed_modalities:
            _require_member(modality, MODALITIES,
                            "PlannedVisitDefinition.allowed_modalities")
        object.__setattr__(self, "allowed_modalities",
                           _canonical_sorted(self.allowed_modalities))
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        computed = self.compute_definition_hash()
        if self.definition_hash and self.definition_hash != computed:
            raise ScheduleSliceError(
                f"PlannedVisitDefinition.definition_hash "
                f"{self.definition_hash!r} does not match the canonical "
                f"hash {computed!r}")
        object.__setattr__(self, "definition_hash", computed)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "planned_visit_id": self.planned_visit_id,
            "planned_visit_key": self.planned_visit_key,
            "schedule_id": self.schedule_id,
            "protocol_version": self.protocol_version,
            "official_visit_code": self.official_visit_code,
            "audience_visit_name": self.audience_visit_name,
            "planned_order": self.planned_order,
            "visit_kind": self.visit_kind,
            "phase": self.phase,
            "applicability_expression": self.applicability_expression,
            "anchor_rule": self.anchor_rule.canonical_payload(),
            "window_rule": self.window_rule.canonical_payload(),
            "allowed_modalities": list(self.allowed_modalities),
            "merge_or_split_rule": self.merge_or_split_rule,
            "source_locator_ids": list(self.source_locator_ids),
        }

    def compute_definition_hash(self) -> str:
        return "d05-visit-" + content_hash(self.canonical_payload())


@dataclass(frozen=True)
class PlannedActivityDefinition:
    """One versioned planned activity (assessment/sample/procedure/contact)
    under a planned visit (§3.1).

    ``planned_activity_key`` is the stable cross-revision obligation; the
    ``owner_domain`` routes the activity to its owner before the D05
    expected-set is built (§2.3).
    """

    planned_activity_id: str
    planned_activity_key: str
    planned_visit_id: str
    activity_kind: str
    clinical_domain: str
    official_activity_code: str
    audience_name: str
    applicability_expression: str
    occurrence_rule: str
    timing_rule: str
    repeat_rule: str = ""
    specimen_or_method_role: str = ""
    owner_domain: str = OWNER_D05
    source_locator_ids: Tuple[str, ...] = ()
    definition_hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.planned_activity_id,
                           "PlannedActivityDefinition.planned_activity_id")
        _validate_nonempty(self.planned_activity_key,
                           "PlannedActivityDefinition.planned_activity_key")
        _validate_nonempty(self.planned_visit_id,
                           "PlannedActivityDefinition.planned_visit_id")
        _require_member(self.activity_kind, ACTIVITY_KINDS,
                        "PlannedActivityDefinition.activity_kind")
        _validate_nonempty(self.clinical_domain,
                           "PlannedActivityDefinition.clinical_domain")
        _validate_nonempty(self.official_activity_code,
                           "PlannedActivityDefinition.official_activity_code")
        _validate_nonempty(self.audience_name,
                           "PlannedActivityDefinition.audience_name")
        _validate_nonempty(self.applicability_expression,
                           "PlannedActivityDefinition.applicability_expression")
        _validate_nonempty(self.occurrence_rule,
                           "PlannedActivityDefinition.occurrence_rule")
        _validate_nonempty(self.timing_rule,
                           "PlannedActivityDefinition.timing_rule")
        _validate_optional_str(self.repeat_rule,
                               "PlannedActivityDefinition.repeat_rule")
        _validate_optional_str(self.specimen_or_method_role,
                               "PlannedActivityDefinition.specimen_or_method_role")
        _require_member(self.owner_domain, OWNER_DOMAINS,
                        "PlannedActivityDefinition.owner_domain")
        if self.activity_kind == ACTIVITY_SAMPLE:
            if not self.specimen_or_method_role.strip():
                raise ScheduleSliceError(
                    "a sample planned activity requires "
                    "specimen_or_method_role")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        computed = self.compute_definition_hash()
        if self.definition_hash and self.definition_hash != computed:
            raise ScheduleSliceError(
                f"PlannedActivityDefinition.definition_hash "
                f"{self.definition_hash!r} does not match the canonical "
                f"hash {computed!r}")
        object.__setattr__(self, "definition_hash", computed)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "planned_activity_id": self.planned_activity_id,
            "planned_activity_key": self.planned_activity_key,
            "planned_visit_id": self.planned_visit_id,
            "activity_kind": self.activity_kind,
            "clinical_domain": self.clinical_domain,
            "official_activity_code": self.official_activity_code,
            "audience_name": self.audience_name,
            "applicability_expression": self.applicability_expression,
            "occurrence_rule": self.occurrence_rule,
            "timing_rule": self.timing_rule,
            "repeat_rule": self.repeat_rule,
            "specimen_or_method_role": self.specimen_or_method_role,
            "owner_domain": self.owner_domain,
            "source_locator_ids": list(self.source_locator_ids),
        }

    def compute_definition_hash(self) -> str:
        return "d05-activity-" + content_hash(self.canonical_payload())


@dataclass(frozen=True)
class VisitScheduleApplicabilityDecision:
    """The per-subject schedule applicability decision (§4.1).

    Only ``unique_active`` may generate a normal medical expected-set;
    ``multi_feasible_boundary``/``not_evaluable`` produce exactly one
    subject-level ``ScheduleGate(gate_kind=applicability)``.  ``decision_id``
    is the stable cross-run decision identity (no cutoff/status/reasons);
    ``hash`` is the full content address including cutoff, status and
    reason codes (lineage).
    """

    decision_id: str
    project_ref: str
    subject_ref: str
    site_ref: str
    protocol_version: str
    arm: str
    cohort: str
    phase: str
    transition_rule: str
    cutoff: ClinicalEventCutoff
    decision_status: str
    feasible_schedule_ids: Tuple[str, ...] = ()
    reason_codes: Tuple[str, ...] = ()
    rule_version: str = D05_RULE_LINEAGE_DEFAULT
    source_locator_ids: Tuple[str, ...] = ()
    hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.project_ref,
                           "VisitScheduleApplicabilityDecision.project_ref")
        _validate_nonempty(self.subject_ref,
                           "VisitScheduleApplicabilityDecision.subject_ref")
        _validate_nonempty(self.site_ref,
                           "VisitScheduleApplicabilityDecision.site_ref")
        _validate_optional_str(self.protocol_version,
                               "VisitScheduleApplicabilityDecision.protocol_version")
        _validate_optional_str(self.arm,
                               "VisitScheduleApplicabilityDecision.arm")
        _validate_optional_str(self.cohort,
                               "VisitScheduleApplicabilityDecision.cohort")
        _validate_optional_str(self.phase,
                               "VisitScheduleApplicabilityDecision.phase")
        _require_member(self.transition_rule, TRANSITION_RULES,
                        "VisitScheduleApplicabilityDecision.transition_rule")
        if not isinstance(self.cutoff, ClinicalEventCutoff):
            raise ScheduleSliceError(
                "VisitScheduleApplicabilityDecision.cutoff must be a "
                "ClinicalEventCutoff")
        _require_member(self.decision_status, APPLICABILITY_STATUSES,
                        "VisitScheduleApplicabilityDecision.decision_status")
        _validate_nonempty(self.rule_version,
                           "VisitScheduleApplicabilityDecision.rule_version")
        feasible = _canonical_sorted(self.feasible_schedule_ids)
        reasons = _canonical_sorted(self.reason_codes)
        for code in reasons:
            _require_member(code, REASON_CODES,
                            "VisitScheduleApplicabilityDecision.reason_codes")
        object.__setattr__(self, "feasible_schedule_ids", feasible)
        object.__setattr__(self, "reason_codes", reasons)
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        if self.decision_status == APPLICABILITY_UNIQUE_ACTIVE:
            if not self.protocol_version.strip():
                raise ScheduleSliceError(
                    "unique_active applicability requires protocol_version")
            if not feasible:
                raise ScheduleSliceError(
                    "unique_active applicability requires at least one "
                    "feasible schedule id")
        elif self.decision_status == APPLICABILITY_MULTI_FEASIBLE_BOUNDARY:
            if len(feasible) < 2:
                raise ScheduleSliceError(
                    "multi_feasible_boundary applicability requires at "
                    "least two feasible schedule ids")
        else:  # not_evaluable
            if not reasons:
                raise ScheduleSliceError(
                    "not_evaluable applicability requires at least one "
                    "reason code")
        stable = "d05-appl-" + content_hash({
            "project_ref": self.project_ref,
            "subject_ref": self.subject_ref,
            "site_ref": self.site_ref,
            "protocol_version": self.protocol_version,
            "arm": self.arm,
            "cohort": self.cohort,
            "phase": self.phase,
            "transition_rule": self.transition_rule,
            "feasible_schedule_ids": list(feasible),
            "rule_version": self.rule_version,
        })
        if self.decision_id and self.decision_id != stable:
            raise ScheduleSliceError(
                f"VisitScheduleApplicabilityDecision.decision_id "
                f"{self.decision_id!r} does not match the stable id "
                f"{stable!r}")
        object.__setattr__(self, "decision_id", stable)
        full = "d05-appl-lineage-" + content_hash({
            "decision_id": stable,
            "cutoff": self.cutoff.canonical(),
            "decision_status": self.decision_status,
            "reason_codes": list(reasons),
            "source_locator_ids": list(self.source_locator_ids),
        })
        if self.hash and self.hash != full:
            raise ScheduleSliceError(
                f"VisitScheduleApplicabilityDecision.hash {self.hash!r} "
                f"does not match {full!r}")
        object.__setattr__(self, "hash", full)


# ---------------------------------------------------------------------------
# Actual objects (§3.2)
# ---------------------------------------------------------------------------

def encounter_stable_object_key(
    *, subject_ref: str, site_ref: str,
    source_record_keys: Sequence[str],
) -> str:
    """Frozen source-identity algorithm v1 for actual encounters.

    ``stable_actual_object_key`` is the content address of the immutable
    business keys (subject + site + canonical sorted source record keys)
    and never contains revisable dates, visit names or free text (§3.2).
    """
    _validate_nonempty(subject_ref, "subject_ref")
    _validate_nonempty(site_ref, "site_ref")
    keys = _canonical_sorted(source_record_keys)
    if not keys:
        raise ScheduleSliceError(
            "stable actual identity requires at least one source record key")
    return "d05-enc-key-" + content_hash({
        "subject_ref": subject_ref,
        "site_ref": site_ref,
        "source_record_keys": list(keys),
        "algorithm_version": D05_SOURCE_IDENTITY_ALGORITHM_VERSION,
    })


def activity_stable_object_key(
    *, subject_ref: str, site_ref: str,
    source_record_keys: Sequence[str],
) -> str:
    """Frozen source-identity algorithm v1 for actual activities."""
    _validate_nonempty(subject_ref, "subject_ref")
    _validate_nonempty(site_ref, "site_ref")
    keys = _canonical_sorted(source_record_keys)
    if not keys:
        raise ScheduleSliceError(
            "stable actual identity requires at least one source record key")
    return "d05-act-key-" + content_hash({
        "subject_ref": subject_ref,
        "site_ref": site_ref,
        "source_record_keys": list(keys),
        "algorithm_version": D05_SOURCE_IDENTITY_ALGORITHM_VERSION,
    })


def bundle_stable_object_key(
    *, subject_ref: str, site_ref: str,
    member_encounter_ids: Sequence[str],
) -> str:
    """Frozen source-identity algorithm v1 for encounter bundles (§3.2).

    The bundle's ``stable_actual_object_key`` is the content address of
    its immutable business keys (subject + site + canonical sorted member
    encounter ids) and never contains derived dates, merge/split rule ids,
    episode kind, locators or free text.  The canonical payload is
    ``{"subject_ref", "site_ref", "member_encounter_ids",
    "algorithm_version"}``; input order never changes the key and the same
    member episode keeps the same key across Runs/snapshots.
    """
    _validate_nonempty(subject_ref, "subject_ref")
    _validate_nonempty(site_ref, "site_ref")
    members = _canonical_sorted(member_encounter_ids)
    if not members:
        raise ScheduleSliceError(
            "bundle stable identity requires at least one member encounter")
    return "d05-bundle-key-" + content_hash({
        "subject_ref": subject_ref,
        "site_ref": site_ref,
        "member_encounter_ids": list(members),
        "algorithm_version": D05_SOURCE_IDENTITY_ALGORITHM_VERSION,
    })


def _validate_record_dates(
    *, start: str, end: str, date_precision: str, timezone: str,
    prefix: str,
) -> None:
    _validate_optional_str(start, f"{prefix}.start")
    _validate_optional_str(end, f"{prefix}.end")
    _require_member(date_precision, PRECISIONS, f"{prefix}.date_precision")
    if start.strip() or end.strip():
        if date_precision == PRECISION_UNKNOWN:
            raise ScheduleSliceError(
                f"{prefix} carries a date but declares precision unknown "
                f"(never silently guessed)")
        if date_precision in SUB_DAY_PRECISIONS:
            if not timezone.strip():
                raise ScheduleSliceError(
                    f"{prefix} requires a timezone at sub-day precision")
            if _parse_instant(start or end, timezone) is None:
                raise ScheduleSliceError(
                    f"{prefix} sub-day date is not parseable with timezone "
                    f"{timezone!r}")
        else:
            for raw in (start, end):
                if raw.strip() and _day_interval(raw) is None:
                    raise ScheduleSliceError(
                        f"{prefix} date {raw!r} is not parseable at "
                        f"{date_precision} precision")


def _record_content_hash(*, kind_prefix: str, payload: Dict[str, Any]) -> str:
    return f"d05-{kind_prefix}-hash-" + content_hash(payload)


@dataclass(frozen=True)
class ActualEncounterRecord:
    """One accepted actual encounter record (§3.2).

    ``stable_actual_object_key`` is the frozen source identity (immutable
    business keys only); ``content_hash`` is the full content address
    (including dates/names, for lineage).  A derived date must carry its
    derivation algorithm and input rows and never masquerade as recorded.
    """

    encounter_id: str
    stable_actual_object_key: str
    subject_ref: str
    site_ref: str
    source_record_keys: Tuple[str, ...]
    encounter_kind: str
    recorded_visit_code: str
    recorded_visit_name: str = ""
    start: str = ""
    end: str = ""
    date_precision: str = PRECISION_UNKNOWN
    timezone: str = ""
    date_origin: str = DATE_ORIGIN_RECORDED
    derivation_algorithm_id: str = ""
    input_locator_ids: Tuple[str, ...] = ()
    source_locator_ids: Tuple[str, ...] = ()
    content_hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.encounter_id, "ActualEncounterRecord.encounter_id")
        _validate_nonempty(self.subject_ref, "ActualEncounterRecord.subject_ref")
        _validate_nonempty(self.site_ref, "ActualEncounterRecord.site_ref")
        _validate_nonempty(self.recorded_visit_code,
                           "ActualEncounterRecord.recorded_visit_code")
        _validate_optional_str(self.recorded_visit_name,
                               "ActualEncounterRecord.recorded_visit_name")
        _require_member(self.encounter_kind, ENCOUNTER_KINDS,
                        "ActualEncounterRecord.encounter_kind")
        _require_member(self.date_origin, DATE_ORIGINS,
                        "ActualEncounterRecord.date_origin")
        _validate_optional_str(self.derivation_algorithm_id,
                               "ActualEncounterRecord.derivation_algorithm_id")
        _validate_optional_str(self.timezone, "ActualEncounterRecord.timezone")
        keys = _canonical_sorted(self.source_record_keys)
        object.__setattr__(self, "source_record_keys", keys)
        if not keys:
            raise ScheduleSliceError(
                "ActualEncounterRecord requires at least one source record key")
        expected_key = encounter_stable_object_key(
            subject_ref=self.subject_ref, site_ref=self.site_ref,
            source_record_keys=keys)
        if self.stable_actual_object_key and \
                self.stable_actual_object_key != expected_key:
            raise ScheduleSliceError(
                f"ActualEncounterRecord.stable_actual_object_key "
                f"{self.stable_actual_object_key!r} does not match the "
                f"frozen source identity {expected_key!r}")
        object.__setattr__(self, "stable_actual_object_key", expected_key)
        _validate_record_dates(
            start=self.start, end=self.end,
            date_precision=self.date_precision, timezone=self.timezone,
            prefix="ActualEncounterRecord")
        if self.date_origin == DATE_ORIGIN_DERIVED:
            if not self.derivation_algorithm_id.strip():
                raise ScheduleSliceError(
                    "a derived encounter date requires "
                    "derivation_algorithm_id and input locators")
            if not self.input_locator_ids:
                raise ScheduleSliceError(
                    "a derived encounter date requires input_locator_ids")
        else:
            if self.derivation_algorithm_id.strip() or self.input_locator_ids:
                raise ScheduleSliceError(
                    "a recorded encounter date must not carry derivation "
                    "algorithm/input ids (derived dates must never "
                    "masquerade as recorded)")
        object.__setattr__(self, "input_locator_ids",
                           _canonical_sorted(self.input_locator_ids))
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        computed = self.compute_content_hash()
        if self.content_hash and self.content_hash != computed:
            raise ScheduleSliceError(
                f"ActualEncounterRecord.content_hash {self.content_hash!r} "
                f"does not match {computed!r}")
        object.__setattr__(self, "content_hash", computed)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "encounter_id": self.encounter_id,
            "stable_actual_object_key": self.stable_actual_object_key,
            "subject_ref": self.subject_ref,
            "site_ref": self.site_ref,
            "source_record_keys": list(self.source_record_keys),
            "encounter_kind": self.encounter_kind,
            "recorded_visit_code": self.recorded_visit_code,
            "recorded_visit_name": self.recorded_visit_name,
            "start": self.start,
            "end": self.end,
            "date_precision": self.date_precision,
            "timezone": self.timezone,
            "date_origin": self.date_origin,
            "derivation_algorithm_id": self.derivation_algorithm_id,
            "input_locator_ids": list(self.input_locator_ids),
            "source_locator_ids": list(self.source_locator_ids),
        }

    def compute_content_hash(self) -> str:
        return _record_content_hash(kind_prefix="enc", payload=self.canonical_payload())


@dataclass(frozen=True)
class ActualActivityRecord:
    """One accepted actual activity record (§3.2)."""

    actual_activity_id: str
    stable_actual_object_key: str
    subject_ref: str
    site_ref: str
    source_record_keys: Tuple[str, ...]
    activity_kind: str
    clinical_domain: str
    recorded_activity_code: str
    start: str = ""
    end: str = ""
    date_precision: str = PRECISION_UNKNOWN
    timezone: str = ""
    encounter_refs: Tuple[str, ...] = ()
    source_locator_ids: Tuple[str, ...] = ()
    content_hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.actual_activity_id,
                           "ActualActivityRecord.actual_activity_id")
        _validate_nonempty(self.subject_ref, "ActualActivityRecord.subject_ref")
        _validate_nonempty(self.site_ref, "ActualActivityRecord.site_ref")
        _require_member(self.activity_kind, ACTIVITY_KINDS,
                        "ActualActivityRecord.activity_kind")
        _validate_nonempty(self.clinical_domain,
                           "ActualActivityRecord.clinical_domain")
        _validate_nonempty(self.recorded_activity_code,
                           "ActualActivityRecord.recorded_activity_code")
        _validate_optional_str(self.timezone, "ActualActivityRecord.timezone")
        keys = _canonical_sorted(self.source_record_keys)
        object.__setattr__(self, "source_record_keys", keys)
        if not keys:
            raise ScheduleSliceError(
                "ActualActivityRecord requires at least one source record key")
        expected_key = activity_stable_object_key(
            subject_ref=self.subject_ref, site_ref=self.site_ref,
            source_record_keys=keys)
        if self.stable_actual_object_key and \
                self.stable_actual_object_key != expected_key:
            raise ScheduleSliceError(
                f"ActualActivityRecord.stable_actual_object_key "
                f"{self.stable_actual_object_key!r} does not match the "
                f"frozen source identity {expected_key!r}")
        object.__setattr__(self, "stable_actual_object_key", expected_key)
        _validate_record_dates(
            start=self.start, end=self.end,
            date_precision=self.date_precision, timezone=self.timezone,
            prefix="ActualActivityRecord")
        object.__setattr__(self, "encounter_refs",
                           _canonical_sorted(self.encounter_refs))
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        computed = self.compute_content_hash()
        if self.content_hash and self.content_hash != computed:
            raise ScheduleSliceError(
                f"ActualActivityRecord.content_hash {self.content_hash!r} "
                f"does not match {computed!r}")
        object.__setattr__(self, "content_hash", computed)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "actual_activity_id": self.actual_activity_id,
            "stable_actual_object_key": self.stable_actual_object_key,
            "subject_ref": self.subject_ref,
            "site_ref": self.site_ref,
            "source_record_keys": list(self.source_record_keys),
            "activity_kind": self.activity_kind,
            "clinical_domain": self.clinical_domain,
            "recorded_activity_code": self.recorded_activity_code,
            "start": self.start,
            "end": self.end,
            "date_precision": self.date_precision,
            "timezone": self.timezone,
            "encounter_refs": list(self.encounter_refs),
            "source_locator_ids": list(self.source_locator_ids),
        }

    def compute_content_hash(self) -> str:
        return _record_content_hash(kind_prefix="act", payload=self.canonical_payload())


@dataclass(frozen=True)
class ActualEncounterBundle:
    """The only actual visit episode referenceable by planned-visit
    assignment (§3.2, §5.2).

    Member ordering is canonicalized by stable actual object key -- never
    input row order (challenge 107).  A bundle supports multiple planned
    visits only under an explicit merge rule; an encounter enters multiple
    bundles only under an explicit split rule (challenges 45/46/47/48/108).
    Derived start/end must be traceable to the member input rows and are
    validated against the declared values (fail closed).

    ``stable_actual_object_key`` (§3.2) is declarable: when declared it is
    verified against the frozen canonical identity payload (subject/site/
    sorted member ids/algorithm version) and any mismatch fails closed;
    when empty it is auto-computed from that same canonical payload.
    """

    bundle_id: str
    stable_actual_object_key: str
    subject_ref: str
    site_ref: str
    member_encounter_ids: Tuple[str, ...]
    episode_kind: str
    assignment_scope: str
    merge_or_split_rule_id: str = ""
    derived_start: str = ""
    derived_end: str = ""
    date_precision: str = PRECISION_UNKNOWN
    timezone: str = ""
    completion_evidence_locator_ids: Tuple[str, ...] = ()
    source_locator_ids: Tuple[str, ...] = ()
    lineage_hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref, "ActualEncounterBundle.subject_ref")
        _validate_nonempty(self.site_ref, "ActualEncounterBundle.site_ref")
        _require_member(self.episode_kind, EPISODE_KINDS,
                        "ActualEncounterBundle.episode_kind")
        _require_member(self.assignment_scope, ASSIGNMENT_SCOPES,
                        "ActualEncounterBundle.assignment_scope")
        _validate_optional_str(self.merge_or_split_rule_id,
                               "ActualEncounterBundle.merge_or_split_rule_id")
        _require_member(self.date_precision, PRECISIONS,
                        "ActualEncounterBundle.date_precision")
        _validate_optional_str(self.timezone, "ActualEncounterBundle.timezone")
        members = _canonical_sorted(self.member_encounter_ids)
        object.__setattr__(self, "member_encounter_ids", members)
        if not members:
            raise ScheduleSliceError(
                "ActualEncounterBundle requires at least one member "
                "encounter (a single contact still forms a single-member "
                "bundle)")
        if len(members) > 1 or self.assignment_scope == ASSIGNMENT_SCOPE_MULTI:
            if not self.merge_or_split_rule_id.strip():
                raise ScheduleSliceError(
                    "a multi-contact or multi-visit bundle requires an "
                    "explicit merge rule (challenge 46)")
        object.__setattr__(self, "completion_evidence_locator_ids",
                           _canonical_sorted(self.completion_evidence_locator_ids))
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        expected_key = bundle_stable_object_key(
            subject_ref=self.subject_ref, site_ref=self.site_ref,
            member_encounter_ids=self.member_encounter_ids)
        if self.stable_actual_object_key and \
                self.stable_actual_object_key != expected_key:
            raise ScheduleSliceError(
                f"ActualEncounterBundle.stable_actual_object_key "
                f"{self.stable_actual_object_key!r} does not match the "
                f"frozen canonical identity payload {expected_key!r}")
        object.__setattr__(self, "stable_actual_object_key", expected_key)
        computed_id = "d05-bundle-id-" + content_hash({
            "stable_actual_object_key": self.stable_actual_object_key,
            "subject_ref": self.subject_ref,
            "site_ref": self.site_ref,
            "member_encounter_ids": list(members),
            "episode_kind": self.episode_kind,
            "assignment_scope": self.assignment_scope,
            "merge_or_split_rule_id": self.merge_or_split_rule_id,
        })
        if self.bundle_id and self.bundle_id != computed_id:
            raise ScheduleSliceError(
                f"ActualEncounterBundle.bundle_id {self.bundle_id!r} does "
                f"not match {computed_id!r}")
        object.__setattr__(self, "bundle_id", computed_id)
        computed = self.compute_lineage_hash()
        if self.lineage_hash and self.lineage_hash != computed:
            raise ScheduleSliceError(
                f"ActualEncounterBundle.lineage_hash {self.lineage_hash!r} "
                f"does not match {computed!r}")
        object.__setattr__(self, "lineage_hash", computed)

    def stable_identity_payload(self) -> Dict[str, Any]:
        """The frozen canonical payload that determines the stable actual
        object key (§3.2): immutable business keys only -- subject/site/
        member encounter ids -- never derived dates, merge rules, episode
        kind, locators or free text."""
        return {
            "subject_ref": self.subject_ref,
            "site_ref": self.site_ref,
            "member_encounter_ids": list(self.member_encounter_ids),
            "algorithm_version": D05_SOURCE_IDENTITY_ALGORITHM_VERSION,
        }

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "stable_actual_object_key": self.stable_actual_object_key,
            "subject_ref": self.subject_ref,
            "site_ref": self.site_ref,
            "member_encounter_ids": list(self.member_encounter_ids),
            "episode_kind": self.episode_kind,
            "assignment_scope": self.assignment_scope,
            "merge_or_split_rule_id": self.merge_or_split_rule_id,
            "derived_start": self.derived_start,
            "derived_end": self.derived_end,
            "date_precision": self.date_precision,
            "timezone": self.timezone,
            "completion_evidence_locator_ids":
                list(self.completion_evidence_locator_ids),
            "source_locator_ids": list(self.source_locator_ids),
        }

    def compute_lineage_hash(self) -> str:
        return "d05-bundle-" + content_hash(self.canonical_payload())


def _member_effective_interval(
    record: Any,
) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime],
           Optional[str], str, str]:
    """(lo, hi, precision, start_raw, end_raw) of one actual record."""
    start = record.start
    end = record.end
    precision = record.date_precision
    timezone = getattr(record, "timezone", "")
    if precision in (PRECISION_DAY, PRECISION_MONTH, PRECISION_YEAR):
        lo_parts: List[datetime.date] = []
        hi_parts: List[datetime.date] = []
        for raw in (start, end):
            if raw.strip():
                interval = _day_interval(raw)
                if interval is not None:
                    lo_parts.append(interval[0] or interval[1])
                    hi_parts.append(interval[1] or interval[0])
        if not lo_parts:
            return None, None, precision, start, end
        lo_day = min(lo_parts)
        hi_day = max(hi_parts)
        lo, hi = _day_instant_interval(lo_day, hi_day)
        return lo, hi, precision, start, end
    if precision in SUB_DAY_PRECISIONS:
        lo = _parse_instant(start, timezone)
        hi = _parse_instant(end, timezone)
        if lo is None and hi is None:
            return None, None, precision, start, end
        if hi is None:
            hi = lo
        if lo is None:
            lo = hi
        if hi < lo:  # cross-midnight (full precision + timezone required)
            hi = hi + datetime.timedelta(days=1)
        return lo, hi, precision, start, end
    return None, None, precision, start, end


@dataclass(frozen=True)
class ActualRecordScopeDecision:
    """One scope decision for one actual object under the frozen dual time
    boundary (§3.2, §4.2).

    ``scope_decision_id`` is the deterministic content address of the
    decision (snapshot + cutoff + interval + status + reasons); the same
    accepted snapshot and facts rerun to the same id, and a later snapshot
    late-arriving the same event-time record produces a *new* decision
    (challenge 104) without rewriting the old Run.
    """

    scope_decision_id: str
    actual_object_id: str
    snapshot_as_of: SnapshotAsOf
    clinical_event_cutoff: ClinicalEventCutoff
    event_effective_start: str
    event_effective_end: str
    date_precision: str
    timezone: str
    scope_status: str
    reason_codes: Tuple[str, ...] = ()
    source_locator_ids: Tuple[str, ...] = ()
    lineage_hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.actual_object_id,
                           "ActualRecordScopeDecision.actual_object_id")
        if not isinstance(self.snapshot_as_of, SnapshotAsOf):
            raise ScheduleSliceError(
                "ActualRecordScopeDecision.snapshot_as_of must be a SnapshotAsOf")
        if not isinstance(self.clinical_event_cutoff, ClinicalEventCutoff):
            raise ScheduleSliceError(
                "ActualRecordScopeDecision.clinical_event_cutoff must be a "
                "ClinicalEventCutoff")
        _require_member(self.scope_status, SCOPE_STATUSES,
                        "ActualRecordScopeDecision.scope_status")
        _require_member(self.date_precision, PRECISIONS,
                        "ActualRecordScopeDecision.date_precision")
        reasons = _canonical_sorted(self.reason_codes)
        for code in reasons:
            _require_member(code, REASON_CODES,
                            "ActualRecordScopeDecision.reason_codes")
        object.__setattr__(self, "reason_codes", reasons)
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        if self.scope_status in (SCOPE_IN_SCOPE, SCOPE_OUT_OF_CUTOFF):
            if reasons:
                raise ScheduleSliceError(
                    f"scope_status={self.scope_status!r} must carry no "
                    f"reason codes")
        elif self.scope_status == SCOPE_NOT_EVALUABLE:
            if not reasons:
                raise ScheduleSliceError(
                    "not_evaluable scope requires at least one reason code")
        else:  # boundary
            if not reasons:
                raise ScheduleSliceError(
                    "boundary scope requires at least one reason code")
        payload = {
            "actual_object_id": self.actual_object_id,
            "snapshot_as_of": self.snapshot_as_of.canonical(),
            "clinical_event_cutoff": self.clinical_event_cutoff.canonical(),
            "event_effective_start": self.event_effective_start,
            "event_effective_end": self.event_effective_end,
            "date_precision": self.date_precision,
            "timezone": self.timezone,
            "scope_status": self.scope_status,
            "reason_codes": list(reasons),
            "source_locator_ids": list(self.source_locator_ids),
        }
        computed = "d05-scope-" + content_hash(payload)
        if self.scope_decision_id and self.scope_decision_id != computed:
            raise ScheduleSliceError(
                f"ActualRecordScopeDecision.scope_decision_id "
                f"{self.scope_decision_id!r} does not match {computed!r}")
        object.__setattr__(self, "scope_decision_id", computed)
        lineage = "d05-scope-lineage-" + content_hash(payload)
        if self.lineage_hash and self.lineage_hash != lineage:
            raise ScheduleSliceError(
                f"ActualRecordScopeDecision.lineage_hash "
                f"{self.lineage_hash!r} does not match {lineage!r}")
        object.__setattr__(self, "lineage_hash", lineage)


def resolve_actual_record_scope(
    *,
    record: Any,
    snapshot_as_of: SnapshotAsOf,
    clinical_event_cutoff: ClinicalEventCutoff,
    source_locators: Sequence[SourceLocator] = (),
    conflicting_time_roles: Sequence[str] = (),
) -> ActualRecordScopeDecision:
    """Decide the scope of one actual record under the frozen dual time
    boundary (§4.2, challenges 26/27/103/104).

    * A record not belonging to the accepted snapshot fails closed
      (raise) -- it must never enter the normal inventory.
    * The record's comparable event/collection effective interval entirely
      not later than the cutoff -> ``in_scope``; entirely after ->
      ``out_of_cutoff`` (Journey future context only); interval straddling
      the cutoff with complete source precision -> ``boundary``
      (``cutoff_scope`` gate); missing/conflicting effective time roles or
      missing sub-day timezone -> ``not_evaluable``.
    """
    if not isinstance(snapshot_as_of, SnapshotAsOf):
        raise ScheduleSliceError("snapshot_as_of must be a SnapshotAsOf")
    if not isinstance(clinical_event_cutoff, ClinicalEventCutoff):
        raise ScheduleSliceError(
            "clinical_event_cutoff must be a ClinicalEventCutoff")
    locators = tuple(source_locators)
    if not locators:
        raise ScheduleSliceError(
            "resolve_actual_record_scope requires the record's source "
            "locators to verify accepted-snapshot membership")
    actual_object_id = (record.actual_object_id if hasattr(
        record, "actual_object_id") else getattr(
            record, "encounter_id", None) or getattr(
                record, "actual_activity_id", ""))
    _validate_nonempty(actual_object_id, "record.actual_object_id")
    if not any(loc.snapshot_id == snapshot_as_of.snapshot_id
               for loc in locators):
        raise ScheduleSliceError(
            f"actual object {actual_object_id!r} does not belong to "
            f"the accepted snapshot {snapshot_as_of.snapshot_id!r}; a "
            f"record outside the accepted snapshot must not be scoped "
            f"(fail closed)")
    locator_ids = _payload_ids(locators)
    conflicts = _canonical_sorted(conflicting_time_roles)
    if conflicts:
        return ActualRecordScopeDecision(
            scope_decision_id="", actual_object_id=actual_object_id,
            snapshot_as_of=snapshot_as_of,
            clinical_event_cutoff=clinical_event_cutoff,
            event_effective_start=record.start, event_effective_end=record.end,
            date_precision=record.date_precision, timezone=record.timezone,
            scope_status=SCOPE_NOT_EVALUABLE,
            reason_codes=(REASON_TIME_ROLE_CONFLICT,),
            source_locator_ids=locator_ids)
    start = record.start or ""
    end = record.end or ""
    if not start.strip() and not end.strip():
        return ActualRecordScopeDecision(
            scope_decision_id="", actual_object_id=actual_object_id,
            snapshot_as_of=snapshot_as_of,
            clinical_event_cutoff=clinical_event_cutoff,
            event_effective_start=start, event_effective_end=end,
            date_precision=record.date_precision, timezone=record.timezone,
            scope_status=SCOPE_NOT_EVALUABLE,
            reason_codes=(REASON_TIME_ROLE_MISSING,),
            source_locator_ids=locator_ids)
    precision = record.date_precision
    if precision == PRECISION_UNKNOWN:
        return ActualRecordScopeDecision(
            scope_decision_id="", actual_object_id=actual_object_id,
            snapshot_as_of=snapshot_as_of,
            clinical_event_cutoff=clinical_event_cutoff,
            event_effective_start=start, event_effective_end=end,
            date_precision=precision, timezone=record.timezone,
            scope_status=SCOPE_NOT_EVALUABLE,
            reason_codes=(REASON_PRECISION_INSUFFICIENT,),
            source_locator_ids=locator_ids)
    if precision in SUB_DAY_PRECISIONS and not record.timezone.strip():
        # Sub-day comparison needs a frozen timezone; never silently local
        # (challenge 27: 跨午夜但时区缺失且可改变结论 -> not_evaluable).
        return ActualRecordScopeDecision(
            scope_decision_id="", actual_object_id=actual_object_id,
            snapshot_as_of=snapshot_as_of,
            clinical_event_cutoff=clinical_event_cutoff,
            event_effective_start=start, event_effective_end=end,
            date_precision=precision, timezone=record.timezone,
            scope_status=SCOPE_NOT_EVALUABLE,
            reason_codes=(REASON_TIMEZONE_MISSING,),
            source_locator_ids=locator_ids)
    if precision == PRECISION_DAY:
        # A day-precision interval whose end precedes its start is a
        # conflicting time role, never a cross-midnight day.
        start_day = _day_date(start) if start.strip() else None
        end_day = _day_date(end) if end.strip() else None
        if (start_day is not None and end_day is not None
                and end_day < start_day):
            return ActualRecordScopeDecision(
                scope_decision_id="", actual_object_id=actual_object_id,
                snapshot_as_of=snapshot_as_of,
                clinical_event_cutoff=clinical_event_cutoff,
                event_effective_start=start, event_effective_end=end,
                date_precision=precision, timezone=record.timezone,
                scope_status=SCOPE_NOT_EVALUABLE,
                reason_codes=(REASON_TIME_ROLE_CONFLICT,),
                source_locator_ids=locator_ids)
    lo, hi, _, _, _ = _member_effective_interval(record)
    if lo is None or hi is None:
        return ActualRecordScopeDecision(
            scope_decision_id="", actual_object_id=actual_object_id,
            snapshot_as_of=snapshot_as_of,
            clinical_event_cutoff=clinical_event_cutoff,
            event_effective_start=start, event_effective_end=end,
            date_precision=precision, timezone=record.timezone,
            scope_status=SCOPE_NOT_EVALUABLE,
            reason_codes=(REASON_TIME_ROLE_MISSING,),
            source_locator_ids=locator_ids)
    relation = _interval_compare(lo, hi, clinical_event_cutoff.cutoff_instant())
    if relation == SCOPE_IN_SCOPE:
        return ActualRecordScopeDecision(
            scope_decision_id="", actual_object_id=actual_object_id,
            snapshot_as_of=snapshot_as_of,
            clinical_event_cutoff=clinical_event_cutoff,
            event_effective_start=start, event_effective_end=end,
            date_precision=precision, timezone=record.timezone,
            scope_status=SCOPE_IN_SCOPE, source_locator_ids=locator_ids)
    if relation == SCOPE_OUT_OF_CUTOFF:
        return ActualRecordScopeDecision(
            scope_decision_id="", actual_object_id=actual_object_id,
            snapshot_as_of=snapshot_as_of,
            clinical_event_cutoff=clinical_event_cutoff,
            event_effective_start=start, event_effective_end=end,
            date_precision=precision, timezone=record.timezone,
            scope_status=SCOPE_OUT_OF_CUTOFF, source_locator_ids=locator_ids)
    return ActualRecordScopeDecision(
        scope_decision_id="", actual_object_id=actual_object_id,
        snapshot_as_of=snapshot_as_of,
        clinical_event_cutoff=clinical_event_cutoff,
        event_effective_start=start, event_effective_end=end,
        date_precision=precision, timezone=record.timezone,
        scope_status=SCOPE_BOUNDARY,
        reason_codes=(REASON_INTERVAL_STRADDLES,),
        source_locator_ids=locator_ids)


def _derived_bundle_interval(
    members: Sequence[ActualEncounterRecord],
) -> Tuple[str, str, str, str]:
    """Derived (start, end, precision, timezone) of a bundle from its
    member rows: earliest member start, latest member end, coarsest
    precision, common timezone (conflict fails closed)."""
    starts: List[str] = []
    ends: List[str] = []
    precisions: List[str] = []
    timezones: Set[str] = set()
    for member in members:
        if member.start.strip():
            starts.append(member.start)
        if member.end.strip():
            ends.append(member.end)
        precisions.append(member.date_precision)
        if member.timezone.strip():
            timezones.add(member.timezone)
    derived_start = min(starts) if starts else ""
    derived_end = max(ends) if ends else ""
    precision = _coarsest_precision(precisions)
    if len(timezones) > 1:
        raise ScheduleSliceError(
            "ActualEncounterBundle members carry conflicting timezones; "
            "the derived interval is ambiguous (fail closed)")
    timezone = next(iter(timezones)) if timezones else ""
    return derived_start, derived_end, precision, timezone


def build_actual_encounter_bundle(
    *,
    member_encounters: Sequence[ActualEncounterRecord],
    subject_ref: str,
    site_ref: str,
    episode_kind: str,
    merge_or_split_rule_id: str = "",
    assignment_scope: str = ASSIGNMENT_SCOPE_SINGLE,
    completion_evidence_locators: Sequence[SourceLocator] = (),
    source_locators: Sequence[SourceLocator] = (),
) -> ActualEncounterBundle:
    """Build one immutable encounter bundle (§3.2, §5.2).

    * Members are canonicalized by stable object key, never input order
      (challenge 107);
    * every member must share the bundle subject/site (fail closed);
    * a multi-contact or multi-visit bundle requires an explicit merge
      rule (challenge 46);
    * derived start/end/precision/timezone are recomputed from the member
      rows and must match the declared ones when supplied.
    """
    members = tuple(member_encounters)
    if not members:
        raise ScheduleSliceError("build_actual_encounter_bundle requires members")
    for member in members:
        if not isinstance(member, ActualEncounterRecord):
            raise ScheduleSliceError(
                "bundle members must be ActualEncounterRecord instances")
        if member.subject_ref != subject_ref or member.site_ref != site_ref:
            raise ScheduleSliceError(
                f"bundle member {member.encounter_id!r} subject/site "
                f"{member.subject_ref!r}/{member.site_ref!r} does not match "
                f"bundle {subject_ref!r}/{site_ref!r} (fail closed)")
    member_ids = _canonical_sorted([m.encounter_id for m in members])
    if len(member_ids) != len({m.encounter_id for m in members}):
        raise ScheduleSliceError(
            "bundle members must have distinct encounter ids")
    derived_start, derived_end, precision, timezone = (
        _derived_bundle_interval(members))
    return ActualEncounterBundle(
        bundle_id="", stable_actual_object_key="",
        subject_ref=subject_ref, site_ref=site_ref,
        member_encounter_ids=member_ids,
        episode_kind=episode_kind,
        assignment_scope=assignment_scope,
        merge_or_split_rule_id=merge_or_split_rule_id,
        derived_start=derived_start, derived_end=derived_end,
        date_precision=precision, timezone=timezone,
        completion_evidence_locator_ids=_payload_ids(
            completion_evidence_locators),
        source_locator_ids=_payload_ids(source_locators))


def validate_bundle_membership(
    *,
    bundles: Sequence[ActualEncounterBundle],
    split_allowed_encounter_ids: Sequence[str] = (),
) -> None:
    """Enforce bundle-membership invariants across one Run's bundles:
    an encounter (by encounter id) may enter multiple bundles only when an
    explicit split rule allows it (challenge 108); duplicate bundles and
    cross-subject/site mixes fail closed."""
    if not bundles:
        return
    allowed = set(split_allowed_encounter_ids)
    subject = bundles[0].subject_ref
    site = bundles[0].site_ref
    seen_bundle_ids: Set[str] = set()
    membership: Dict[str, List[str]] = {}
    for bundle in bundles:
        if bundle.bundle_id in seen_bundle_ids:
            raise ScheduleSliceError(
                f"duplicate bundle {bundle.bundle_id!r} in one Run")
        seen_bundle_ids.add(bundle.bundle_id)
        if bundle.subject_ref != subject or bundle.site_ref != site:
            raise ScheduleSliceError(
                "bundles across different subject/site cannot be validated "
                "together (fail closed)")
        for member_id in bundle.member_encounter_ids:
            membership.setdefault(member_id, []).append(bundle.bundle_id)
    for member_id, bundle_ids in membership.items():
        if len(bundle_ids) > 1 and member_id not in allowed:
            raise ScheduleSliceError(
                f"encounter {member_id!r} enters multiple bundles "
                f"{sorted(bundle_ids)} without an explicit split rule "
                f"(challenge 108)")


# ---------------------------------------------------------------------------
# Assignment / consumption objects (§3.3, §5, §7)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VisitAssignmentDecision:
    """Assignment of one actual encounter bundle to planned visits (§5.1).

    Never a nearest-date/VISITNUM/row-order shortcut: ``decision_status``
    is closed and ``selected_planned_visit_id`` must be a member of the
    candidate set for ``unique``.
    """

    assignment_id: str
    subject_ref: str
    actual_bundle_id: str
    candidate_planned_visit_ids: Tuple[str, ...]
    decision_status: str
    selected_planned_visit_id: str = ""
    evidence_predicate_ids: Tuple[str, ...] = ()
    rejected_candidate_reasons: Tuple[str, ...] = ()
    algorithm_version: str = D05_UNIT_ALGO_VERSION
    source_locator_ids: Tuple[str, ...] = ()
    hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref, "VisitAssignmentDecision.subject_ref")
        _validate_nonempty(self.actual_bundle_id,
                           "VisitAssignmentDecision.actual_bundle_id")
        candidates = _canonical_sorted(self.candidate_planned_visit_ids)
        object.__setattr__(self, "candidate_planned_visit_ids", candidates)
        _require_member(self.decision_status, VISIT_ASSIGNMENT_STATUSES,
                        "VisitAssignmentDecision.decision_status")
        _validate_optional_str(self.selected_planned_visit_id,
                               "VisitAssignmentDecision.selected_planned_visit_id")
        _validate_nonempty(self.algorithm_version,
                           "VisitAssignmentDecision.algorithm_version")
        object.__setattr__(self, "evidence_predicate_ids",
                           _canonical_sorted(self.evidence_predicate_ids))
        reasons = _canonical_sorted(self.rejected_candidate_reasons)
        for code in reasons:
            _require_member(code, REASON_CODES,
                            "VisitAssignmentDecision.rejected_candidate_reasons")
        object.__setattr__(self, "rejected_candidate_reasons", reasons)
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        selected = self.selected_planned_visit_id
        if self.decision_status == VISIT_ASSIGNMENT_UNIQUE:
            if not selected or selected not in candidates:
                raise ScheduleSliceError(
                    "unique visit assignment requires a selected candidate "
                    "visit id from the candidate set")
        else:
            if selected:
                raise ScheduleSliceError(
                    f"visit assignment status {self.decision_status!r} must "
                    f"not carry a selected visit id")
            if self.decision_status == VISIT_ASSIGNMENT_MULTI_FEASIBLE \
                    and len(candidates) < 2:
                raise ScheduleSliceError(
                    "multi_feasible_boundary requires at least two "
                    "candidate visit ids")
        payload = {
            "subject_ref": self.subject_ref,
            "actual_bundle_id": self.actual_bundle_id,
            "candidate_planned_visit_ids": list(candidates),
            "decision_status": self.decision_status,
            "selected_planned_visit_id": selected,
            "evidence_predicate_ids": list(self.evidence_predicate_ids),
            "rejected_candidate_reasons": list(reasons),
            "algorithm_version": self.algorithm_version,
            "source_locator_ids": list(self.source_locator_ids),
        }
        computed = "d05-va-" + content_hash(payload)
        if self.assignment_id and self.assignment_id != computed:
            raise ScheduleSliceError(
                f"VisitAssignmentDecision.assignment_id {self.assignment_id!r} "
                f"does not match {computed!r}")
        object.__setattr__(self, "assignment_id", computed)
        if self.hash and self.hash != computed:
            raise ScheduleSliceError(
                f"VisitAssignmentDecision.hash {self.hash!r} does not match "
                f"{computed!r}")
        object.__setattr__(self, "hash", computed)


@dataclass(frozen=True)
class ActivityAssignmentDecision:
    """Assignment of one actual activity to planned activities (§7.1/7.2).

    Multiple selected planned activities are only legal under
    ``duplicate_consumption``; allowed repeat/resample multi-consumption is
    represented as separate per-obligation unique assignments sharing one
    consumption ledger row with an explicit repeat rule.
    """

    assignment_id: str
    subject_ref: str
    actual_activity_id: str
    candidate_planned_activity_ids: Tuple[str, ...]
    decision_status: str
    selected_planned_activity_ids: Tuple[str, ...] = ()
    repeat_or_resample_parent_id: str = ""
    repeat_rule_id: str = ""
    evidence_predicate_ids: Tuple[str, ...] = ()
    algorithm_version: str = D05_UNIT_ALGO_VERSION
    source_locator_ids: Tuple[str, ...] = ()
    hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref,
                           "ActivityAssignmentDecision.subject_ref")
        _validate_nonempty(self.actual_activity_id,
                           "ActivityAssignmentDecision.actual_activity_id")
        candidates = _canonical_sorted(self.candidate_planned_activity_ids)
        object.__setattr__(self, "candidate_planned_activity_ids", candidates)
        _require_member(self.decision_status, ACTIVITY_ASSIGNMENT_STATUSES,
                        "ActivityAssignmentDecision.decision_status")
        _validate_optional_str(self.repeat_or_resample_parent_id,
                               "ActivityAssignmentDecision.repeat_or_resample_parent_id")
        _validate_optional_str(self.repeat_rule_id,
                               "ActivityAssignmentDecision.repeat_rule_id")
        selected = _canonical_sorted(self.selected_planned_activity_ids)
        object.__setattr__(self, "selected_planned_activity_ids", selected)
        for sid in selected:
            if sid not in candidates:
                raise ScheduleSliceError(
                    f"selected activity {sid!r} not in the candidate set "
                    f"(fail closed)")
        object.__setattr__(self, "evidence_predicate_ids",
                           _canonical_sorted(self.evidence_predicate_ids))
        _validate_nonempty(self.algorithm_version,
                           "ActivityAssignmentDecision.algorithm_version")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        if self.decision_status == ACTIVITY_ASSIGNMENT_UNIQUE:
            if len(selected) != 1:
                raise ScheduleSliceError(
                    "unique activity assignment requires exactly one "
                    "selected activity id")
        elif self.decision_status == ACTIVITY_ASSIGNMENT_DUPLICATE_CONSUMPTION:
            if len(selected) < 2:
                raise ScheduleSliceError(
                    "duplicate_consumption requires at least two selected "
                    "activity ids")
        else:
            if selected:
                raise ScheduleSliceError(
                    f"activity assignment status {self.decision_status!r} "
                    f"must not carry selected activity ids")
            if self.decision_status == ACTIVITY_ASSIGNMENT_MULTI_FEASIBLE \
                    and len(candidates) < 2:
                raise ScheduleSliceError(
                    "multi_feasible_boundary requires at least two "
                    "candidate activity ids")
        payload = {
            "subject_ref": self.subject_ref,
            "actual_activity_id": self.actual_activity_id,
            "candidate_planned_activity_ids": list(candidates),
            "decision_status": self.decision_status,
            "selected_planned_activity_ids": list(selected),
            "repeat_or_resample_parent_id": self.repeat_or_resample_parent_id,
            "repeat_rule_id": self.repeat_rule_id,
            "evidence_predicate_ids": list(self.evidence_predicate_ids),
            "algorithm_version": self.algorithm_version,
            "source_locator_ids": list(self.source_locator_ids),
        }
        computed = "d05-aa-" + content_hash(payload)
        if self.assignment_id and self.assignment_id != computed:
            raise ScheduleSliceError(
                f"ActivityAssignmentDecision.assignment_id "
                f"{self.assignment_id!r} does not match {computed!r}")
        object.__setattr__(self, "assignment_id", computed)
        if self.hash and self.hash != computed:
            raise ScheduleSliceError(
                f"ActivityAssignmentDecision.hash {self.hash!r} does not "
                f"match {computed!r}")
        object.__setattr__(self, "hash", computed)


@dataclass(frozen=True)
class ActualActivityConsumptionLedger:
    """Consumption ledger of one actual activity by planned activities
    (§7.2).  The ledger is the actual->planned index; reverse coverage is
    closed only when the allowed multiplicity covers every consuming
    obligation (with an explicit repeat rule when multiplicity > 1)."""

    ledger_id: str
    subject_ref: str
    site_ref: str
    actual_activity_id: str
    consuming_planned_activity_ids: Tuple[str, ...]
    allowed_multiplicity: int
    repeat_rule_id: str = ""
    assignment_ids: Tuple[str, ...] = ()
    reverse_coverage_status: str = REVERSE_COVERAGE_CLOSED
    source_locator_ids: Tuple[str, ...] = ()
    lineage_hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref,
                           "ActualActivityConsumptionLedger.subject_ref")
        _validate_nonempty(self.site_ref,
                           "ActualActivityConsumptionLedger.site_ref")
        _validate_nonempty(self.actual_activity_id,
                           "ActualActivityConsumptionLedger.actual_activity_id")
        consuming = _canonical_sorted(self.consuming_planned_activity_ids)
        object.__setattr__(self, "consuming_planned_activity_ids", consuming)
        if not consuming:
            raise ScheduleSliceError(
                "consumption ledger requires at least one consuming planned "
                "activity id")
        if not isinstance(self.allowed_multiplicity, int) \
                or self.allowed_multiplicity < 1:
            raise ScheduleSliceError(
                "consumption ledger allowed_multiplicity must be an int >= 1")
        _validate_optional_str(self.repeat_rule_id,
                               "ActualActivityConsumptionLedger.repeat_rule_id")
        assignments = _canonical_sorted(self.assignment_ids)
        object.__setattr__(self, "assignment_ids", assignments)
        if not assignments:
            raise ScheduleSliceError(
                "consumption ledger requires at least one assignment id")
        _require_member(self.reverse_coverage_status,
                        REVERSE_COVERAGE_STATUSES,
                        "ActualActivityConsumptionLedger.reverse_coverage_status")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        if self.reverse_coverage_status == REVERSE_COVERAGE_CLOSED:
            if len(consuming) > self.allowed_multiplicity:
                raise ScheduleSliceError(
                    "reverse coverage cannot be closed when the number of "
                    "consuming planned activities exceeds the allowed "
                    "multiplicity (multi-consumption without a repeat rule "
                    "is a duplicate_consumption positive, not closed)")
            if len(consuming) > 1 and not self.repeat_rule_id.strip():
                raise ScheduleSliceError(
                    "reverse coverage cannot be closed for multi-consumption "
                    "without an explicit repeat rule")
        payload = {
            "subject_ref": self.subject_ref,
            "site_ref": self.site_ref,
            "actual_activity_id": self.actual_activity_id,
            "consuming_planned_activity_ids": list(consuming),
            "allowed_multiplicity": self.allowed_multiplicity,
            "repeat_rule_id": self.repeat_rule_id,
            "assignment_ids": list(assignments),
            "reverse_coverage_status": self.reverse_coverage_status,
            "source_locator_ids": list(self.source_locator_ids),
        }
        computed = "d05-aa-ledger-" + content_hash(payload)
        if self.ledger_id and self.ledger_id != computed:
            raise ScheduleSliceError(
                f"ActualActivityConsumptionLedger.ledger_id {self.ledger_id!r} "
                f"does not match {computed!r}")
        object.__setattr__(self, "ledger_id", computed)
        if self.lineage_hash and self.lineage_hash != computed:
            raise ScheduleSliceError(
                f"ActualActivityConsumptionLedger.lineage_hash "
                f"{self.lineage_hash!r} does not match {computed!r}")
        object.__setattr__(self, "lineage_hash", computed)


# ---------------------------------------------------------------------------
# Typed schedule anchors (§3.3, §5.3)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TypedScheduleAnchorRef:
    """A typed schedule anchor bound to a fixed reference, a chained prior
    actual visit or a producer event (D03 first dose, D04
    randomization/consent) (§3.3, §5.3).

    ``anchor_ref_id`` is the *stable* cross-run identity (producer domain +
    producer unit + stable source event key + subject/site/phase/episode +
    relation type -- no locators, no snapshot); ``lineage_hash`` is the
    full content address including interval, precision, timezone and
    locators.
    """

    anchor_ref_id: str
    producer_domain: str
    producer_unit_id: str
    stable_source_event_key: str
    content_hash: str
    subject_ref: str
    site_ref: str
    phase: str
    episode_id: str
    anchor_start: str
    anchor_end: str
    date_precision: str
    timezone: str
    relation_type: str
    source_locator_ids: Tuple[str, ...] = ()
    lineage_hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref, "TypedScheduleAnchorRef.subject_ref")
        _validate_nonempty(self.site_ref, "TypedScheduleAnchorRef.site_ref")
        _validate_optional_str(self.producer_domain,
                               "TypedScheduleAnchorRef.producer_domain")
        _validate_optional_str(self.producer_unit_id,
                               "TypedScheduleAnchorRef.producer_unit_id")
        _validate_optional_str(self.stable_source_event_key,
                               "TypedScheduleAnchorRef.stable_source_event_key")
        _validate_optional_str(self.phase, "TypedScheduleAnchorRef.phase")
        _validate_optional_str(self.episode_id,
                               "TypedScheduleAnchorRef.episode_id")
        _require_member(self.date_precision, PRECISIONS,
                        "TypedScheduleAnchorRef.date_precision")
        _validate_optional_str(self.timezone, "TypedScheduleAnchorRef.timezone")
        _require_member(self.relation_type, RELATION_TYPES,
                        "TypedScheduleAnchorRef.relation_type")
        if self.relation_type in PRODUCER_RELATION_TYPES:
            if not self.producer_domain.strip() \
                    or not self.producer_unit_id.strip() \
                    or not self.stable_source_event_key.strip() \
                    or not _SHA256_RE.match(self.content_hash or ""):
                raise ScheduleSliceError(
                    "a producer-typed anchor requires producer_domain, "
                    "producer_unit_id, stable_source_event_key and a "
                    "64-hex content_hash")
        else:
            if self.producer_domain.strip() or self.producer_unit_id.strip() \
                    or self.stable_source_event_key.strip() \
                    or self.content_hash.strip():
                raise ScheduleSliceError(
                    "a fixed/chained anchor must not carry producer binding "
                    "fields")
        if not self.anchor_start.strip() and not self.anchor_end.strip():
            raise ScheduleSliceError(
                "a typed anchor requires a comparable time interval "
                "(§5.3); missing anchor time is a gate, never a default")
        _validate_optional_str(self.anchor_start,
                               "TypedScheduleAnchorRef.anchor_start")
        _validate_optional_str(self.anchor_end,
                               "TypedScheduleAnchorRef.anchor_end")
        if self.date_precision in SUB_DAY_PRECISIONS:
            if not self.timezone.strip():
                raise ScheduleSliceError(
                    "a sub-day typed anchor requires a timezone (never "
                    "silently local)")
            for raw in (self.anchor_start, self.anchor_end):
                if raw.strip() and _parse_instant(raw, self.timezone) is None:
                    raise ScheduleSliceError(
                        f"TypedScheduleAnchorRef date {raw!r} is not "
                        f"parseable at {self.date_precision} precision")
        else:
            for raw in (self.anchor_start, self.anchor_end):
                if raw.strip() and _day_interval(raw) is None:
                    raise ScheduleSliceError(
                        f"TypedScheduleAnchorRef date {raw!r} is not "
                        f"parseable at {self.date_precision} precision")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        stable = "d05-anchor-" + content_hash({
            "producer_domain": self.producer_domain,
            "producer_unit_id": self.producer_unit_id,
            "stable_source_event_key": self.stable_source_event_key,
            "subject_ref": self.subject_ref,
            "site_ref": self.site_ref,
            "phase": self.phase,
            "episode_id": self.episode_id,
            "relation_type": self.relation_type,
        })
        if self.anchor_ref_id and self.anchor_ref_id != stable:
            raise ScheduleSliceError(
                f"TypedScheduleAnchorRef.anchor_ref_id {self.anchor_ref_id!r} "
                f"does not match the stable id {stable!r}")
        object.__setattr__(self, "anchor_ref_id", stable)
        lineage = "d05-anchor-lineage-" + content_hash({
            "anchor_ref_id": stable,
            "content_hash": self.content_hash,
            "anchor_start": self.anchor_start,
            "anchor_end": self.anchor_end,
            "date_precision": self.date_precision,
            "timezone": self.timezone,
            "source_locator_ids": list(self.source_locator_ids),
        })
        if self.lineage_hash and self.lineage_hash != lineage:
            raise ScheduleSliceError(
                f"TypedScheduleAnchorRef.lineage_hash {self.lineage_hash!r} "
                f"does not match {lineage!r}")
        object.__setattr__(self, "lineage_hash", lineage)


@dataclass(frozen=True)
class AnchorBindingOutcome:
    """Result of one typed-anchor binding: exactly one of
    ``anchor_ref`` / ``gate`` is set (§5.3)."""

    anchor_ref: Optional[TypedScheduleAnchorRef] = None
    gate: Optional["ScheduleGate"] = None

    def __post_init__(self) -> None:
        if (self.anchor_ref is None) == (self.gate is None):
            raise ScheduleSliceError(
                "AnchorBindingOutcome requires exactly one of anchor_ref / "
                "gate")

    @property
    def is_bound(self) -> bool:
        return self.anchor_ref is not None


def _anchor_gate(
    *, subject_ref: str, site_ref: str, reason_codes: Sequence[str],
    feasible_anchor_ref_ids: Sequence[str] = (),
    affected_planned_visit_keys: Sequence[str] = (),
    affected_planned_activity_keys: Sequence[str] = (),
    missing_evidence_roles: Sequence[str] = (),
    source_locator_ids: Sequence[str] = (),
    decision_status: str = GATE_DECISION_NOT_EVALUABLE,
) -> ScheduleGate:
    return ScheduleGate(
        gate_id="", gate_kind=GATE_ANCHOR, subject_ref=subject_ref,
        site_ref=site_ref, gate_state=GATE_OPEN,
        decision_status=decision_status,
        feasible_anchor_ref_ids=feasible_anchor_ref_ids,
        affected_planned_visit_keys=affected_planned_visit_keys,
        affected_planned_activity_keys=affected_planned_activity_keys,
        missing_evidence_roles=missing_evidence_roles,
        reason_codes=reason_codes,
        source_locator_ids=source_locator_ids)


def _ref_ctx(ref: CrossDomainEvidenceRef) -> Dict[str, str]:
    """Producer ref context payload as a plain string dict."""
    return {str(k): str(v) for k, v in ref.context_payload}


def _producer_stable_event_key(ref: CrossDomainEvidenceRef) -> str:
    """Stable source event key of a producer ref = ``table_semantic:
    record_id`` (excludes snapshot/revision id; shared D02 §3.3)."""
    return f"{ref.source_locator.table_semantic}:{ref.source_locator.record_id}"


def _anchor_binding_verdict(
    *,
    relation_type: str,
    subject_ref: str,
    site_ref: str,
    producer_ref: Optional[CrossDomainEvidenceRef],
    producer_domain: str = "",
    producer_unit_id: str = "",
    stable_source_event_key: str = "",
    content_hash: str = "",
    phase: str = "",
    episode_id: str = "",
    anchor_start: str = "",
    anchor_end: str = "",
    date_precision: str = "",
    timezone: str = "",
) -> Tuple[bool, str, str]:
    """Full-dimension explicit expected-value match of one producer ref
    against the schedule's declared anchor requirements (§5.3).

    No dimension is optional: omission never behaves as a wildcard.  For a
    producer relation the caller MUST declare explicit expected values for
    ``producer_domain``, ``producer_unit_id``, ``stable_source_event_key``,
    ``content_hash``, ``phase``, ``anchor_start``, ``anchor_end`` and
    ``date_precision``; the producer reference context MUST contain and
    exactly equal ``phase``, ``episode_id``, ``anchor_start``,
    ``anchor_end``, ``date_precision``, ``timezone`` and ``relation_type``
    (``episode_id``/``timezone`` may be the explicit empty value only when
    the context contains the key and the expected value is likewise
    empty).  Subject/site and the binding relation type are always
    mandatory.  Any missing, wrong or conflicting dimension returns
    ``(False, reason_code, missing_evidence_role)``; a date-neighbour,
    same visit name, same row number or plain locator can never substitute
    for an exact dimension match.
    """
    if relation_type not in RELATION_TYPES:
        return False, REASON_INVALID_RELATION_TYPE, ANCHOR_ROLE_OTHER
    if producer_ref is None:
        return False, REASON_ANCHOR_MISSING, ANCHOR_ROLE_OTHER
    ref = producer_ref
    if ref.consumer_domain != D05_DOMAIN:
        return False, REASON_WRONG_CONSUMER_DOMAIN, ANCHOR_ROLE_OTHER
    if not ref.verify_content_hash():
        return False, REASON_ANCHOR_CONFLICT, ANCHOR_ROLE_OTHER
    # -- every required expected dimension must be explicit and non-empty --
    for name, value in (
        ("producer_domain", producer_domain),
        ("producer_unit_id", producer_unit_id),
        ("stable_source_event_key", stable_source_event_key),
        ("content_hash", content_hash),
        ("phase", phase),
        ("anchor_start", anchor_start),
        ("anchor_end", anchor_end),
        ("date_precision", date_precision),
    ):
        if not value:
            return False, REASON_ANCHOR_MISSING, ANCHOR_ROLE_OTHER
    # -- exact equality on the ref fields --
    if producer_domain != ref.producer_domain:
        return False, REASON_WRONG_PRODUCER_DOMAIN, ANCHOR_ROLE_OTHER
    if not ref.producer_unit_id.strip():
        return False, REASON_ANCHOR_MISSING, ANCHOR_ROLE_OTHER
    if producer_unit_id != ref.producer_unit_id:
        return False, REASON_ANCHOR_CONFLICT, ANCHOR_ROLE_OTHER
    if stable_source_event_key != _producer_stable_event_key(ref):
        return False, REASON_ANCHOR_CONFLICT, ANCHOR_ROLE_OTHER
    if content_hash != ref.content_hash:
        return False, REASON_ANCHOR_CONFLICT, ANCHOR_ROLE_OTHER
    # -- subject / site: context must carry and exactly match --
    ctx = _ref_ctx(ref)
    ref_subject = ctx.get("subject_ref", "")
    ref_site = ctx.get("site_ref", "")
    if not ref_subject or not ref_site:
        return False, REASON_SUBJECT_SITE_MISMATCH, ANCHOR_ROLE_OTHER
    if ref_subject != subject_ref or ref_site != site_ref:
        return False, REASON_SUBJECT_SITE_MISMATCH, ANCHOR_ROLE_OTHER
    # -- context must contain and exactly equal every typed dimension --
    # ``episode_id``/``timezone`` accept an explicit empty value only when
    # the context contains the key and the expected value is likewise
    # empty; a context key present but empty while the expected value is
    # non-empty is missing evidence, never a wildcard substitute.
    for key, expected in (
        ("phase", phase),
        ("episode_id", episode_id),
        ("anchor_start", anchor_start),
        ("anchor_end", anchor_end),
        ("date_precision", date_precision),
        ("timezone", timezone),
        ("relation_type", relation_type),
    ):
        if key not in ctx:
            return False, REASON_ANCHOR_MISSING, ANCHOR_ROLE_OTHER
        actual = ctx[key]
        if actual == expected:
            continue
        if not actual:
            return False, REASON_ANCHOR_MISSING, ANCHOR_ROLE_OTHER
        if key == "phase" or key == "episode_id":
            return False, REASON_PHASE_OR_EPISODE_MISMATCH, ANCHOR_ROLE_OTHER
        if key == "relation_type":
            return False, REASON_INVALID_RELATION_TYPE, ANCHOR_ROLE_OTHER
        if key in ("anchor_start", "anchor_end"):
            return False, REASON_INTERVAL_MISMATCH, ANCHOR_ROLE_OTHER
        return False, REASON_PRECISION_OR_TIMEZONE_MISMATCH, ANCHOR_ROLE_OTHER
    return True, "", ""


def anchor_binding_matches(
    *,
    relation_type: str,
    subject_ref: str,
    site_ref: str,
    producer_ref: Optional[CrossDomainEvidenceRef],
    producer_domain: str = "",
    producer_unit_id: str = "",
    stable_source_event_key: str = "",
    content_hash: str = "",
    phase: str = "",
    episode_id: str = "",
    anchor_start: str = "",
    anchor_end: str = "",
    date_precision: str = "",
    timezone: str = "",
) -> bool:
    """Full-dimension explicit expected-value matching (§5.3).

    Returns True only when every required dimension -- producer_domain,
    producer_unit_id, stable_source_event_key, content_hash, phase,
    anchor_start/end and date_precision -- is declared explicitly, the
    producer ref context contains and exactly equals phase, episode_id,
    anchor_start/end, date_precision, timezone and relation_type, and
    subject/site and the binding relation type match.  Omission never
    behaves as a wildcard: any missing, wrong or conflicting dimension
    returns False; same-day dates or a plain locator can never substitute
    for an exact dimension match.
    """
    matched, _, _ = _anchor_binding_verdict(
        relation_type=relation_type, subject_ref=subject_ref,
        site_ref=site_ref, producer_ref=producer_ref,
        producer_domain=producer_domain, producer_unit_id=producer_unit_id,
        stable_source_event_key=stable_source_event_key,
        content_hash=content_hash, phase=phase, episode_id=episode_id,
        anchor_start=anchor_start, anchor_end=anchor_end,
        date_precision=date_precision, timezone=timezone)
    return matched


def bind_typed_schedule_anchor(
    *,
    relation_type: str,
    subject_ref: str,
    site_ref: str,
    producer_ref: Optional[CrossDomainEvidenceRef] = None,
    producer_domain: str = "",
    producer_unit_id: str = "",
    stable_source_event_key: str = "",
    content_hash: str = "",
    phase: str = "",
    episode_id: str = "",
    anchor_start: str = "",
    anchor_end: str = "",
    date_precision: str = "",
    timezone: str = "",
    affected_planned_visit_keys: Sequence[str] = (),
    affected_planned_activity_keys: Sequence[str] = (),
    source_locators: Sequence[SourceLocator] = (),
) -> AnchorBindingOutcome:
    """Exact typed-anchor binding (§5.3, challenges 73/74/112).

    A producer relation requires a ``CrossDomainEvidenceRef`` and every
    declared expected dimension (producer domain/unit id, stable source
    event key/content hash, subject, site, phase/episode, anchor interval,
    date precision, timezone, relation type) must match exactly; any
    missing, wrong or conflicting dimension yields one ``ScheduleGate
    (gate_kind=anchor)`` -- never a date-neighbour / same-name / same-row
    shortcut.  Internal fixed/chained relations bind from declared dates
    without a producer ref.
    """
    _validate_nonempty(subject_ref, "subject_ref")
    _validate_nonempty(site_ref, "site_ref")
    locator_ids = _payload_ids(source_locators)
    if relation_type not in RELATION_TYPES:
        return AnchorBindingOutcome(gate=_anchor_gate(
            subject_ref=subject_ref, site_ref=site_ref,
            reason_codes=(REASON_INVALID_RELATION_TYPE,),
            source_locator_ids=locator_ids))
    if relation_type in PRODUCER_RELATION_TYPES:
        matched, reason, missing_role = _anchor_binding_verdict(
            relation_type=relation_type, subject_ref=subject_ref,
            site_ref=site_ref, producer_ref=producer_ref,
            producer_domain=producer_domain, producer_unit_id=producer_unit_id,
            stable_source_event_key=stable_source_event_key,
            content_hash=content_hash, phase=phase, episode_id=episode_id,
            anchor_start=anchor_start, anchor_end=anchor_end,
            date_precision=date_precision, timezone=timezone)
        if not matched:
            return AnchorBindingOutcome(gate=_anchor_gate(
                subject_ref=subject_ref, site_ref=site_ref,
                reason_codes=(reason,),
                missing_evidence_roles=(missing_role,),
                affected_planned_visit_keys=affected_planned_visit_keys,
                affected_planned_activity_keys=affected_planned_activity_keys,
                source_locator_ids=locator_ids))
        ref = producer_ref
        assert ref is not None
        ctx = _ref_ctx(ref)
        resolved_start = anchor_start or ctx.get("anchor_start", "")
        resolved_end = anchor_end or ctx.get("anchor_end", "")
        resolved_precision = date_precision or ctx.get("date_precision", "") \
            or PRECISION_DAY
        resolved_timezone = timezone or ctx.get("timezone", "")
        if resolved_precision in SUB_DAY_PRECISIONS \
                and not resolved_timezone.strip():
            return AnchorBindingOutcome(gate=_anchor_gate(
                subject_ref=subject_ref, site_ref=site_ref,
                reason_codes=(REASON_TIMEZONE_MISSING,),
                missing_evidence_roles=(ANCHOR_ROLE_OTHER,),
                affected_planned_visit_keys=affected_planned_visit_keys,
                affected_planned_activity_keys=affected_planned_activity_keys,
                source_locator_ids=locator_ids))
        anchor = TypedScheduleAnchorRef(
            anchor_ref_id="",
            producer_domain=ref.producer_domain,
            producer_unit_id=ref.producer_unit_id,
            stable_source_event_key=_producer_stable_event_key(ref),
            content_hash=ref.content_hash,
            subject_ref=subject_ref, site_ref=site_ref,
            phase=phase or ctx.get("phase", ""),
            episode_id=episode_id or ctx.get("episode_id", ""),
            anchor_start=resolved_start, anchor_end=resolved_end,
            date_precision=resolved_precision,
            timezone=resolved_timezone,
            relation_type=relation_type,
            source_locator_ids=locator_ids)
        return AnchorBindingOutcome(anchor_ref=anchor)
    # Internal relations: fixed reference / chained prior actual visit.
    if producer_ref is not None:
        raise ScheduleSliceError(
            f"internal anchor relation {relation_type!r} must not carry a "
            f"producer ref (misuse)")
    if not anchor_start.strip() and not anchor_end.strip():
        return AnchorBindingOutcome(gate=_anchor_gate(
            subject_ref=subject_ref, site_ref=site_ref,
            reason_codes=(REASON_ANCHOR_MISSING,),
            affected_planned_visit_keys=affected_planned_visit_keys,
            affected_planned_activity_keys=affected_planned_activity_keys,
            missing_evidence_roles=(ANCHOR_ROLE_VISIT_SCHEDULE,),
            source_locator_ids=locator_ids))
    if date_precision in SUB_DAY_PRECISIONS and not timezone.strip():
        return AnchorBindingOutcome(gate=_anchor_gate(
            subject_ref=subject_ref, site_ref=site_ref,
            reason_codes=(REASON_TIMEZONE_MISSING,),
            affected_planned_visit_keys=affected_planned_visit_keys,
            affected_planned_activity_keys=affected_planned_activity_keys,
            missing_evidence_roles=(ANCHOR_ROLE_VISIT_SCHEDULE,),
            source_locator_ids=locator_ids))
    anchor = TypedScheduleAnchorRef(
        anchor_ref_id="", producer_domain="", producer_unit_id="",
        stable_source_event_key="", content_hash="",
        subject_ref=subject_ref, site_ref=site_ref,
        phase=phase, episode_id=episode_id,
        anchor_start=anchor_start, anchor_end=anchor_end,
        date_precision=date_precision or PRECISION_DAY,
        timezone=timezone,
        relation_type=relation_type,
        source_locator_ids=locator_ids)
    return AnchorBindingOutcome(anchor_ref=anchor)


# ---------------------------------------------------------------------------
# ScheduleGate (§3.3, §12)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScheduleGate:
    """Coverage/control-plane gate (§3.3).

    Closed state truth table (challenge 116):
    ``open + boundary|not_evaluable + blocks_domain_complete=true``
    (no prior/resolved ids), or
    ``closed + resolved + blocks_domain_complete=false``
    (requires prior_gate_id + resolved_by_decision_id).
    Every other combination fails schema/QC closed.  A gate never counts
    in the medical expected-set.
    """

    gate_id: str
    gate_kind: str
    subject_ref: str
    site_ref: str
    gate_state: str
    decision_status: str
    feasible_schedule_ids: Tuple[str, ...] = ()
    feasible_owner_domains: Tuple[str, ...] = ()
    feasible_anchor_ref_ids: Tuple[str, ...] = ()
    affected_planned_visit_keys: Tuple[str, ...] = ()
    affected_planned_activity_keys: Tuple[str, ...] = ()
    missing_evidence_roles: Tuple[str, ...] = ()
    reason_codes: Tuple[str, ...] = ()
    prior_gate_id: str = ""
    resolved_by_decision_id: str = ""
    source_locator_ids: Tuple[str, ...] = ()
    lineage_hash: str = ""
    counts_in_medical_expected_set: bool = False
    blocks_domain_complete: Optional[bool] = None

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref, "ScheduleGate.subject_ref")
        _validate_nonempty(self.site_ref, "ScheduleGate.site_ref")
        _require_member(self.gate_kind, GATE_KINDS, "ScheduleGate.gate_kind")
        _require_member(self.gate_state, GATE_STATES, "ScheduleGate.gate_state")
        _require_member(self.decision_status, GATE_DECISION_STATUSES,
                        "ScheduleGate.decision_status")
        if self.counts_in_medical_expected_set:
            raise ScheduleSliceError(
                "ScheduleGate.counts_in_medical_expected_set must always be "
                "false (gates never enter the medical expected-set, §3.3)")
        if self.blocks_domain_complete is not None \
                and not isinstance(self.blocks_domain_complete, bool):
            raise ScheduleSliceError(
                "ScheduleGate.blocks_domain_complete must be a bool or None")
        for field_name in (
                "feasible_schedule_ids", "feasible_owner_domains",
                "feasible_anchor_ref_ids", "affected_planned_visit_keys",
                "affected_planned_activity_keys", "missing_evidence_roles",
                "reason_codes", "source_locator_ids"):
            object.__setattr__(
                self, field_name, _canonical_sorted(getattr(self, field_name)))
        for code in self.reason_codes:
            _require_member(code, REASON_CODES, "ScheduleGate.reason_codes")
        for domain in self.feasible_owner_domains:
            _require_member(domain, OWNER_DOMAINS,
                            "ScheduleGate.feasible_owner_domains")
        _validate_optional_str(self.prior_gate_id, "ScheduleGate.prior_gate_id")
        _validate_optional_str(self.resolved_by_decision_id,
                               "ScheduleGate.resolved_by_decision_id")
        open_ok = (self.gate_state == GATE_OPEN
                   and self.decision_status in (GATE_DECISION_BOUNDARY,
                                                GATE_DECISION_NOT_EVALUABLE)
                   and not self.prior_gate_id.strip()
                   and not self.resolved_by_decision_id.strip())
        closed_ok = (self.gate_state == GATE_CLOSED
                     and self.decision_status == GATE_DECISION_RESOLVED
                     and bool(self.prior_gate_id.strip())
                     and bool(self.resolved_by_decision_id.strip()))
        if not open_ok and not closed_ok:
            raise ScheduleSliceError(
                f"illegal ScheduleGate state combination: "
                f"gate_state={self.gate_state!r} "
                f"decision_status={self.decision_status!r} "
                f"prior={self.prior_gate_id!r} "
                f"resolved={self.resolved_by_decision_id!r} "
                f"(challenge 116: only open+boundary|not_evaluable or "
                f"closed+resolved are legal)")
        computed_blocks = (self.gate_state == GATE_OPEN)
        if self.blocks_domain_complete is not None \
                and self.blocks_domain_complete != computed_blocks:
            raise ScheduleSliceError(
                f"ScheduleGate.blocks_domain_complete "
                f"{self.blocks_domain_complete!r} must be "
                f"{computed_blocks!r} for gate_state={self.gate_state!r}")
        object.__setattr__(self, "blocks_domain_complete", computed_blocks)
        payload = {
            "gate_kind": self.gate_kind,
            "subject_ref": self.subject_ref,
            "site_ref": self.site_ref,
            "gate_state": self.gate_state,
            "decision_status": self.decision_status,
            "feasible_schedule_ids": list(self.feasible_schedule_ids),
            "feasible_owner_domains": list(self.feasible_owner_domains),
            "feasible_anchor_ref_ids": list(self.feasible_anchor_ref_ids),
            "affected_planned_visit_keys":
                list(self.affected_planned_visit_keys),
            "affected_planned_activity_keys":
                list(self.affected_planned_activity_keys),
            "missing_evidence_roles": list(self.missing_evidence_roles),
            "reason_codes": list(self.reason_codes),
            "prior_gate_id": self.prior_gate_id,
            "resolved_by_decision_id": self.resolved_by_decision_id,
            "source_locator_ids": list(self.source_locator_ids),
        }
        computed = "d05-gate-" + content_hash(payload)
        if self.gate_id and self.gate_id != computed:
            raise ScheduleSliceError(
                f"ScheduleGate.gate_id {self.gate_id!r} does not match the "
                f"canonical hash {computed!r}")
        object.__setattr__(self, "gate_id", computed)
        if self.lineage_hash and self.lineage_hash != computed:
            raise ScheduleSliceError(
                f"ScheduleGate.lineage_hash {self.lineage_hash!r} does not "
                f"match {computed!r}")
        object.__setattr__(self, "lineage_hash", computed)


@dataclass(frozen=True)
class GateRunAccounting:
    """Per-Run gate accounting (§12):
    ``current_run_gates = closed_resolved + open_boundary +
    open_not_evaluable``; any open gate blocks domain completeness."""

    run_id: str
    total: int
    closed_resolved: int
    open_boundary: int
    open_not_evaluable: int
    blocks_domain_complete: bool
    reason: str = ""


def validate_gate_run_accounting(
    *,
    gates: Sequence[ScheduleGate],
    run_id: str = "",
) -> GateRunAccounting:
    """Validate one Run's gate set (§3.3, §12, challenges 105/106/116):

    * no duplicate gate id (each stable decision yields exactly one gate
      per Run; identical content -> identical id -> rejected);
    * the accounting equation holds (every gate lands in exactly one
      bucket);
    * any open gate blocks domain completeness.
    """
    seen: Set[str] = set()
    closed_resolved = 0
    open_boundary = 0
    open_not_evaluable = 0
    for gate in gates:
        if not isinstance(gate, ScheduleGate):
            raise ScheduleSliceError(
                "validate_gate_run_accounting requires ScheduleGate objects")
        if gate.gate_id in seen:
            raise ScheduleSliceError(
                f"duplicate gate {gate.gate_id!r} in one Run: a stable "
                f"decision may produce only one gate per Run (§3.3)")
        seen.add(gate.gate_id)
        if gate.gate_state == GATE_CLOSED:
            closed_resolved += 1
        elif gate.decision_status == GATE_DECISION_BOUNDARY:
            open_boundary += 1
        else:
            open_not_evaluable += 1
    total = len(gates)
    if total != closed_resolved + open_boundary + open_not_evaluable:
        raise ScheduleSliceError(
            "gate accounting equation violated: total != closed_resolved + "
            "open_boundary + open_not_evaluable")
    blocks = open_boundary + open_not_evaluable > 0
    return GateRunAccounting(
        run_id=run_id, total=total, closed_resolved=closed_resolved,
        open_boundary=open_boundary, open_not_evaluable=open_not_evaluable,
        blocks_domain_complete=blocks,
        reason="any open gate blocks domain completeness" if blocks else "")


def all_gates_closed(gates: Sequence[ScheduleGate]) -> bool:
    return all(gate.gate_state == GATE_CLOSED for gate in gates)


# ---------------------------------------------------------------------------
# Interpretation ledger and evaluation unit (§3.3, §3.4, §6)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScheduleInterpretationLedger:
    """Interpretation ledger (§6): all feasible merge/split/repeat/
    reschedule/trigger/window interpretations with accepted/rejected
    partition, per-interpretation predicate results and rejection reason
    codes -- replayable, input-order independent."""

    ledger_id: str
    decision_scope: str
    interpretation_ids: Tuple[str, ...]
    accepted_interpretation_ids: Tuple[str, ...] = ()
    rejected_interpretation_ids: Tuple[str, ...] = ()
    predicate_results: Tuple[Tuple[str, str], ...] = ()
    rejection_reason_codes: Tuple[str, ...] = ()
    merge_split_repeat_reschedule_trigger_rule_ids: Tuple[str, ...] = ()
    algorithm_version: str = D05_UNIT_ALGO_VERSION
    source_locator_ids: Tuple[str, ...] = ()
    lineage_hash: str = ""

    def __post_init__(self) -> None:
        _require_member(self.decision_scope, INTERPRETATION_SCOPES,
                        "ScheduleInterpretationLedger.decision_scope")
        interps = _canonical_sorted(self.interpretation_ids)
        object.__setattr__(self, "interpretation_ids", interps)
        if not interps:
            raise ScheduleSliceError(
                "interpretation ledger requires at least one interpretation id")
        accepted = _canonical_sorted(self.accepted_interpretation_ids)
        rejected = _canonical_sorted(self.rejected_interpretation_ids)
        object.__setattr__(self, "accepted_interpretation_ids", accepted)
        object.__setattr__(self, "rejected_interpretation_ids", rejected)
        overlap = set(accepted) & set(rejected)
        if overlap:
            raise ScheduleSliceError(
                f"interpretation ids accepted and rejected overlap: "
                f"{sorted(overlap)}")
        union = set(accepted) | set(rejected)
        if union != set(interps):
            raise ScheduleSliceError(
                "accepted ∪ rejected must exactly equal interpretation_ids "
                "(every feasible interpretation is decided, §6)")
        for interp_id in set(accepted) | set(rejected):
            if interp_id not in interps:
                raise ScheduleSliceError(
                    f"interpretation {interp_id!r} not in interpretation_ids")
        predicates: List[Tuple[str, str]] = []
        seen_pred: Set[str] = set()
        for item in self.predicate_results:
            if not isinstance(item, tuple) or len(item) != 2:
                raise ScheduleSliceError(
                    "predicate_results entries must be (interpretation_id, "
                    "predicate) tuples")
            interp_id, predicate = item
            if not isinstance(interp_id, str) or not interp_id.strip():
                raise ScheduleSliceError(
                    "predicate_results interpretation ids must be non-empty")
            if interp_id not in interps:
                raise ScheduleSliceError(
                    f"predicate result for unknown interpretation "
                    f"{interp_id!r}")
            if interp_id in seen_pred:
                raise ScheduleSliceError(
                    f"duplicate predicate result for interpretation "
                    f"{interp_id!r}")
            seen_pred.add(interp_id)
            _require_member(predicate, INTERPRETATION_PREDICATES,
                            "ScheduleInterpretationLedger.predicate_results")
            predicates.append((interp_id, predicate))
        predicates.sort(key=lambda kv: kv[0])
        object.__setattr__(self, "predicate_results", tuple(predicates))
        if set(interp_id for interp_id, _ in predicates) != set(interps):
            raise ScheduleSliceError(
                "predicate_results must cover every interpretation id")
        reasons = _canonical_sorted(self.rejection_reason_codes)
        for code in reasons:
            _require_member(code, REASON_CODES,
                            "ScheduleInterpretationLedger.rejection_reason_codes")
        object.__setattr__(self, "rejection_reason_codes", reasons)
        if rejected and not reasons:
            raise ScheduleSliceError(
                "rejected interpretations require at least one rejection "
                "reason code (§6)")
        object.__setattr__(
            self, "merge_split_repeat_reschedule_trigger_rule_ids",
            _canonical_sorted(
                self.merge_split_repeat_reschedule_trigger_rule_ids))
        _validate_nonempty(self.algorithm_version,
                           "ScheduleInterpretationLedger.algorithm_version")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        payload = {
            "decision_scope": self.decision_scope,
            "interpretation_ids": list(interps),
            "accepted_interpretation_ids": list(accepted),
            "rejected_interpretation_ids": list(rejected),
            "predicate_results": [list(p) for p in predicates],
            "rejection_reason_codes": list(reasons),
            "merge_split_repeat_reschedule_trigger_rule_ids": list(
                self.merge_split_repeat_reschedule_trigger_rule_ids),
            "algorithm_version": self.algorithm_version,
            "source_locator_ids": list(self.source_locator_ids),
        }
        computed = "d05-interp-" + content_hash(payload)
        if self.ledger_id and self.ledger_id != computed:
            raise ScheduleSliceError(
                f"ScheduleInterpretationLedger.ledger_id {self.ledger_id!r} "
                f"does not match {computed!r}")
        object.__setattr__(self, "ledger_id", computed)
        if self.lineage_hash and self.lineage_hash != computed:
            raise ScheduleSliceError(
                f"ScheduleInterpretationLedger.lineage_hash "
                f"{self.lineage_hash!r} does not match {computed!r}")
        object.__setattr__(self, "lineage_hash", computed)


def schedule_evaluation_window_id(
    *,
    anchor_kind: str,
    anchor_source_role: str,
    calendar_semantics: str,
    study_day_zero_exists: Optional[bool],
    lower_offset: str,
    upper_offset: str,
    lower_endpoint_inclusive: Optional[bool],
    upper_endpoint_inclusive: Optional[bool],
    grace_period: str,
    date_precision: str,
    timezone: str,
    propagation_rule: str,
    anchor_episode_id: str = "",
) -> str:
    """Stable evaluation-window id (no run/snapshot/revision).

    Different re-screening/treatment/trigger episodes must use different
    ``evaluation_window_id`` so one window never closes another (§3.4);
    pass ``anchor_episode_id`` to discriminate episode-scoped windows
    (the stable core also carries ``anchor_episode_id``)."""
    return "d05-winid-" + content_hash({
        "anchor_kind": anchor_kind,
        "anchor_source_role": anchor_source_role,
        "calendar_semantics": calendar_semantics,
        "study_day_zero_exists": study_day_zero_exists,
        "lower_offset": lower_offset,
        "upper_offset": upper_offset,
        "lower_endpoint_inclusive": lower_endpoint_inclusive,
        "upper_endpoint_inclusive": upper_endpoint_inclusive,
        "grace_period": grace_period,
        "date_precision": date_precision,
        "timezone": timezone,
        "propagation_rule": propagation_rule,
        "anchor_episode_id": anchor_episode_id,
    })


def schedule_unit_stable_core(
    *,
    project_ref: str,
    subject_ref: str,
    site_ref: str,
    unit_kind: str,
    planned_visit_key: str = "",
    planned_activity_key: str = "",
    stable_actual_object_key: str = "",
    evaluation_window_id: str = "",
    rule_id: str = "",
    anchor_episode_id: str = "",
) -> str:
    """Frozen stable core (§3.4): project/subject/site/owner/unit-kind/
    obligation keys/window/rule/anchor episode -- never Run/snapshot/
    revision, display version, free text or evaluation results."""
    _require_member(unit_kind, UNIT_KINDS, "schedule_unit_stable_core.unit_kind")
    for name, value in (("project_ref", project_ref),
                        ("subject_ref", subject_ref),
                        ("site_ref", site_ref)):
        _validate_nonempty(value, f"schedule_unit_stable_core.{name}")
    return "d05-core-" + content_hash({
        "project_ref": project_ref,
        "subject_ref": subject_ref,
        "site_ref": site_ref,
        "owner_domain": D05_DOMAIN,
        "unit_kind": unit_kind,
        "planned_visit_key": planned_visit_key,
        "planned_activity_key": planned_activity_key,
        "stable_actual_object_key": stable_actual_object_key,
        "evaluation_window_id": evaluation_window_id,
        "rule_id": rule_id,
        "anchor_episode_id": anchor_episode_id,
    })


def schedule_unit_classifier(
    *,
    unit_kind: str,
    planned_visit_key: str = "",
    planned_activity_key: str = "",
    stable_actual_object_key: str = "",
    evaluation_window_id: str = "",
    rule_id: str = "",
) -> str:
    """Stable classifier: the same clinical obligation keeps the same
    classifier N->N+1; rule/algorithm changes produce superseded lineage,
    never a classifier change pretending data resolved itself (§3.4)."""
    _require_member(unit_kind, UNIT_KINDS,
                    "schedule_unit_classifier.unit_kind")
    return "d05-classifier-" + content_hash({
        "owner_domain": D05_DOMAIN,
        "unit_kind": unit_kind,
        "planned_visit_key": planned_visit_key,
        "planned_activity_key": planned_activity_key,
        "stable_actual_object_key": stable_actual_object_key,
        "evaluation_window_id": evaluation_window_id,
        "rule_id": rule_id,
    })


@dataclass(frozen=True)
class ScheduleEvaluationUnit:
    """One D05 evaluation unit (§3.3, §3.4).  ``unit_id`` is the stable
    content address of the frozen stable core (no Run/snapshot/revision);
    ``lineage_hash`` is the full content address including referenced
    decision/assignment ids and locators."""

    unit_id: str
    project_ref: str
    subject_ref: str
    site_ref: str
    unit_kind: str
    planned_visit_key: str = ""
    planned_activity_key: str = ""
    stable_actual_object_key: str = ""
    evaluation_window_id: str = ""
    anchor_episode_id: str = ""
    rule_id: str = ""
    rule_version: str = D05_RULE_LINEAGE_DEFAULT
    planned_visit_id: str = ""
    planned_activity_id: str = ""
    actual_bundle_id: str = ""
    actual_activity_id: str = ""
    applicability_decision_id: str = ""
    visit_assignment_id: str = ""
    activity_assignment_id: str = ""
    classifier: str = ""
    stable_core: str = ""
    source_locator_ids: Tuple[str, ...] = ()
    lineage_hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.project_ref, "ScheduleEvaluationUnit.project_ref")
        _validate_nonempty(self.subject_ref, "ScheduleEvaluationUnit.subject_ref")
        _validate_nonempty(self.site_ref, "ScheduleEvaluationUnit.site_ref")
        _require_member(self.unit_kind, UNIT_KINDS,
                        "ScheduleEvaluationUnit.unit_kind")
        _validate_optional_str(self.rule_version,
                               "ScheduleEvaluationUnit.rule_version")
        if self.unit_kind in (UNIT_VISIT_OCCURRENCE, UNIT_VISIT_TIMING,
                              UNIT_VISIT_ORDER):
            if not self.planned_visit_key.strip():
                raise ScheduleSliceError(
                    f"unit_kind {self.unit_kind!r} requires planned_visit_key")
        elif self.unit_kind in (UNIT_ACTIVITY_OCCURRENCE, UNIT_ACTIVITY_TIMING):
            if not self.planned_activity_key.strip():
                raise ScheduleSliceError(
                    f"unit_kind {self.unit_kind!r} requires "
                    f"planned_activity_key")
        elif self.unit_kind == UNIT_ACTUAL_ASSIGNMENT:
            if not self.stable_actual_object_key.strip():
                raise ScheduleSliceError(
                    "unit_kind actual_assignment requires "
                    "stable_actual_object_key")
        core = schedule_unit_stable_core(
            project_ref=self.project_ref, subject_ref=self.subject_ref,
            site_ref=self.site_ref, unit_kind=self.unit_kind,
            planned_visit_key=self.planned_visit_key,
            planned_activity_key=self.planned_activity_key,
            stable_actual_object_key=self.stable_actual_object_key,
            evaluation_window_id=self.evaluation_window_id,
            rule_id=self.rule_id, anchor_episode_id=self.anchor_episode_id)
        if self.stable_core and self.stable_core != core:
            raise ScheduleSliceError(
                f"ScheduleEvaluationUnit.stable_core {self.stable_core!r} "
                f"does not match {core!r}")
        object.__setattr__(self, "stable_core", core)
        unit_id = "d05-unit-" + content_hash({
            "stable_core": core,
        })
        if self.unit_id and self.unit_id != unit_id:
            raise ScheduleSliceError(
                f"ScheduleEvaluationUnit.unit_id {self.unit_id!r} does not "
                f"match {unit_id!r}")
        object.__setattr__(self, "unit_id", unit_id)
        classifier = schedule_unit_classifier(
            unit_kind=self.unit_kind,
            planned_visit_key=self.planned_visit_key,
            planned_activity_key=self.planned_activity_key,
            stable_actual_object_key=self.stable_actual_object_key,
            evaluation_window_id=self.evaluation_window_id,
            rule_id=self.rule_id)
        if self.classifier and self.classifier != classifier:
            raise ScheduleSliceError(
                f"ScheduleEvaluationUnit.classifier {self.classifier!r} "
                f"does not match {classifier!r}")
        object.__setattr__(self, "classifier", classifier)
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        lineage = "d05-unit-lineage-" + content_hash({
            "unit_id": unit_id,
            "rule_version": self.rule_version,
            "planned_visit_id": self.planned_visit_id,
            "planned_activity_id": self.planned_activity_id,
            "actual_bundle_id": self.actual_bundle_id,
            "actual_activity_id": self.actual_activity_id,
            "applicability_decision_id": self.applicability_decision_id,
            "visit_assignment_id": self.visit_assignment_id,
            "activity_assignment_id": self.activity_assignment_id,
            "source_locator_ids": list(self.source_locator_ids),
        })
        if self.lineage_hash and self.lineage_hash != lineage:
            raise ScheduleSliceError(
                f"ScheduleEvaluationUnit.lineage_hash {self.lineage_hash!r} "
                f"does not match {lineage!r}")
        object.__setattr__(self, "lineage_hash", lineage)


# ---------------------------------------------------------------------------
# Coverage-gap notice (§3.3, §8.5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VisitCoverageGapNotice:
    """资料不足提示 for a not_evaluable unit (§8.5): never a Query, never a
    risk.  ``notice_id`` is a deterministic content address (unit + reason
    + sorted roles/locators); ``audience_text`` is user-facing Chinese
    without engineering jargon."""

    notice_id: str
    unit_id: str
    reason_code: str
    missing_evidence_roles: Tuple[str, ...] = ()
    plan_locator_ids: Tuple[str, ...] = ()
    reachable_source_locator_ids: Tuple[str, ...] = ()
    audience_text: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.unit_id, "VisitCoverageGapNotice.unit_id")
        _require_member(self.reason_code, REASON_CODES,
                        "VisitCoverageGapNotice.reason_code")
        _validate_nonempty(self.audience_text,
                           "VisitCoverageGapNotice.audience_text")
        missing = _canonical_sorted(self.missing_evidence_roles)
        plan_loc = _canonical_sorted(self.plan_locator_ids)
        reachable = _canonical_sorted(self.reachable_source_locator_ids)
        object.__setattr__(self, "missing_evidence_roles", missing)
        object.__setattr__(self, "plan_locator_ids", plan_loc)
        object.__setattr__(self, "reachable_source_locator_ids", reachable)
        computed = "d05-gap-" + content_hash({
            "unit_id": self.unit_id,
            "reason_code": self.reason_code,
            "missing_evidence_roles": list(missing),
            "plan_locator_ids": list(plan_loc),
            "reachable_source_locator_ids": list(reachable),
        })
        if self.notice_id and self.notice_id != computed:
            raise ScheduleSliceError(
                f"VisitCoverageGapNotice.notice_id {self.notice_id!r} does "
                f"not match {computed!r}")
        object.__setattr__(self, "notice_id", computed)


# ---------------------------------------------------------------------------
# Journey value-object schemas (§3.3, §10) -- projection functions are
# worker_03's; this module owns the fixed renderer-neutral schemas only.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlannedVisitMarker:
    """Minimal planned-visit marker on the shared visit axis (§10)."""

    marker_id: str
    planned_visit_id: str
    audience_name: str
    phase: str
    nominal_anchor: str
    window_start: str
    window_end: str
    date_precision: str
    status_hint: str
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.planned_visit_id,
                           "PlannedVisitMarker.planned_visit_id")
        _validate_nonempty(self.audience_name,
                           "PlannedVisitMarker.audience_name")
        _validate_nonempty(self.phase, "PlannedVisitMarker.phase")
        _require_member(self.status_hint, MARKER_STATUS_HINTS,
                        "PlannedVisitMarker.status_hint")
        _require_member(self.date_precision, PRECISIONS,
                        "PlannedVisitMarker.date_precision")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        computed = "d05-pvm-" + content_hash({
            "planned_visit_id": self.planned_visit_id,
            "audience_name": self.audience_name,
            "phase": self.phase,
            "nominal_anchor": self.nominal_anchor,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "date_precision": self.date_precision,
            "status_hint": self.status_hint,
            "source_locator_ids": list(self.source_locator_ids),
        })
        if self.marker_id and self.marker_id != computed:
            raise ScheduleSliceError(
                f"PlannedVisitMarker.marker_id {self.marker_id!r} does not "
                f"match {computed!r}")
        object.__setattr__(self, "marker_id", computed)


@dataclass(frozen=True)
class ActualEncounterMarker:
    """Minimal actual-encounter marker (§10): planned markers and actual
    markers are distinct objects joined by stable assignment edges."""

    marker_id: str
    encounter_id: str
    encounter_kind: str
    anchor_state: str
    start: str
    end: str
    date_precision: str
    assignment_id: str
    audience_name: str = ""
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.encounter_id,
                           "ActualEncounterMarker.encounter_id")
        _require_member(self.encounter_kind, ENCOUNTER_KINDS,
                        "ActualEncounterMarker.encounter_kind")
        _require_member(self.anchor_state, ANCHOR_STATES,
                        "ActualEncounterMarker.anchor_state")
        _require_member(self.date_precision, PRECISIONS,
                        "ActualEncounterMarker.date_precision")
        _validate_optional_str(self.audience_name,
                               "ActualEncounterMarker.audience_name")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        computed = "d05-aem-" + content_hash({
            "encounter_id": self.encounter_id,
            "encounter_kind": self.encounter_kind,
            "anchor_state": self.anchor_state,
            "start": self.start,
            "end": self.end,
            "date_precision": self.date_precision,
            "assignment_id": self.assignment_id,
            "audience_name": self.audience_name,
            "source_locator_ids": list(self.source_locator_ids),
        })
        if self.marker_id and self.marker_id != computed:
            raise ScheduleSliceError(
                f"ActualEncounterMarker.marker_id {self.marker_id!r} does "
                f"not match {computed!r}")
        object.__setattr__(self, "marker_id", computed)


@dataclass(frozen=True)
class VisitRiskMarker:
    """Minimal risk marker (§10): anchors to an actual date/interval or a
    nominal planned window; missing/conflicting dates go to the pending
    area, never a fabricated timepoint."""

    marker_id: str
    audience_label: str
    monitoring_priority: str
    anchor_kind: str
    anchor_state: str
    unit_id: str
    candidate_or_risk_id: str
    anchor_start: str = ""
    anchor_end: str = ""
    date_precision: str = PRECISION_UNKNOWN
    supporting_locator_ids: Tuple[str, ...] = ()
    counterevidence_locator_ids: Tuple[str, ...] = ()
    query_ids: Tuple[str, ...] = ()
    coverage_gap: bool = False

    def __post_init__(self) -> None:
        _validate_nonempty(self.audience_label,
                           "VisitRiskMarker.audience_label")
        _require_member(self.monitoring_priority, VALID_MONITORING_PRIORITIES,
                        "VisitRiskMarker.monitoring_priority")
        _require_member(self.anchor_kind, RELATION_TYPES,
                        "VisitRiskMarker.anchor_kind")
        _require_member(self.anchor_state, ANCHOR_STATES,
                        "VisitRiskMarker.anchor_state")
        _validate_nonempty(self.unit_id, "VisitRiskMarker.unit_id")
        _validate_nonempty(self.candidate_or_risk_id,
                           "VisitRiskMarker.candidate_or_risk_id")
        _require_member(self.date_precision, PRECISIONS,
                        "VisitRiskMarker.date_precision")
        object.__setattr__(self, "supporting_locator_ids",
                           _canonical_sorted(self.supporting_locator_ids))
        object.__setattr__(self, "counterevidence_locator_ids",
                           _canonical_sorted(self.counterevidence_locator_ids))
        object.__setattr__(self, "query_ids",
                           _canonical_sorted(self.query_ids))
        computed = "d05-risk-marker-" + content_hash({
            "audience_label": self.audience_label,
            "monitoring_priority": self.monitoring_priority,
            "anchor_kind": self.anchor_kind,
            "anchor_state": self.anchor_state,
            "unit_id": self.unit_id,
            "candidate_or_risk_id": self.candidate_or_risk_id,
            "anchor_start": self.anchor_start,
            "anchor_end": self.anchor_end,
            "date_precision": self.date_precision,
            "supporting_locator_ids": list(self.supporting_locator_ids),
            "counterevidence_locator_ids":
                list(self.counterevidence_locator_ids),
            "query_ids": list(self.query_ids),
            "coverage_gap": self.coverage_gap,
        })
        if self.marker_id and self.marker_id != computed:
            raise ScheduleSliceError(
                f"VisitRiskMarker.marker_id {self.marker_id!r} does not "
                f"match {computed!r}")
        object.__setattr__(self, "marker_id", computed)


@dataclass(frozen=True)
class VisitJourneyProjection:
    """Renderer-neutral journey projection schema (§3.3, §10).
    Planned-visit markers and actual-encounter markers stay separate
    objects joined by assignment edges; out-of-cutoff markers live in
    their own area.  Projection *functions* live in worker_03's
    ``visit_schedule_projection`` module."""

    projection_id: str
    subject_ref: str
    site_ref: str
    planned_visit_markers: Tuple[PlannedVisitMarker, ...] = ()
    actual_encounter_markers: Tuple[ActualEncounterMarker, ...] = ()
    activity_markers: Tuple[Any, ...] = ()
    assignment_edges: Tuple[Tuple[str, str], ...] = ()
    risk_markers: Tuple[VisitRiskMarker, ...] = ()
    pending_time_markers: Tuple[Any, ...] = ()
    out_of_cutoff_markers: Tuple[Any, ...] = ()
    source_locator_ids: Tuple[str, ...] = ()
    payload_hash: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref,
                           "VisitJourneyProjection.subject_ref")
        _validate_nonempty(self.site_ref, "VisitJourneyProjection.site_ref")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        edges: List[Tuple[str, str]] = []
        for edge in self.assignment_edges:
            if not isinstance(edge, tuple) or len(edge) != 2:
                raise ScheduleSliceError(
                    "assignment_edges entries must be (planned_id, "
                    "actual_id) tuples")
            a, b = edge
            if not isinstance(a, str) or not a.strip() \
                    or not isinstance(b, str) or not b.strip():
                raise ScheduleSliceError(
                    "assignment_edges ids must be non-empty strings")
            edges.append((a, b))
        edges.sort()
        object.__setattr__(self, "assignment_edges", tuple(edges))
        payload = {
            "subject_ref": self.subject_ref,
            "site_ref": self.site_ref,
            "planned_visit_markers": [
                m.marker_id for m in self.planned_visit_markers],
            "actual_encounter_markers": [
                m.marker_id for m in self.actual_encounter_markers],
            "assignment_edges": [list(e) for e in edges],
            "risk_markers": [m.marker_id for m in self.risk_markers],
            "activity_markers": _marker_id_list(
                self.activity_markers,
                expected_type="VisitActivityMarker", id_prefix="d05-avm-"),
            "pending_time_markers": _marker_id_list(
                self.pending_time_markers,
                expected_type="PendingContextMarker",
                id_prefix="d05-pending-"),
            "out_of_cutoff_markers": _marker_id_list(
                self.out_of_cutoff_markers,
                expected_type="OutOfCutoffContextMarker",
                id_prefix="d05-ooc-"),
        }
        computed = "d05-proj-" + content_hash(payload)
        if self.projection_id and self.projection_id != computed:
            raise ScheduleSliceError(
                f"VisitJourneyProjection.projection_id {self.projection_id!r} "
                f"does not match {computed!r}")
        object.__setattr__(self, "projection_id", computed)
        payload["source_locator_ids"] = list(self.source_locator_ids)
        payload_hash = "d05-proj-payload-" + content_hash(payload)
        if self.payload_hash and self.payload_hash != payload_hash:
            raise ScheduleSliceError(
                f"VisitJourneyProjection.payload_hash {self.payload_hash!r} "
                f"does not match {payload_hash!r}")
        object.__setattr__(self, "payload_hash", payload_hash)
