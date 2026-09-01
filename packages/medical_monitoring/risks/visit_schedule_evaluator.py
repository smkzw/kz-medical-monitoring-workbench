"""R4-D05 visit/assessment/sample timing slice -- evaluator (worker_02).

Frozen source of truth: ``FROZEN_R4_D05_CONTRACT_V1_2`` (§§1-15).  This
module owns the D05 **evaluation pipeline** assigned to worker_02, consuming
worker_01's immutable domain surface (:mod:`mm_r4.visit_schedule`) and the
shared R4 contract surface (:mod:`mm_r4.contracts`, :mod:`mm_r4.coverage`,
:mod:`mm_r4.lifecycle`):

1. **Gate phase** (contract §4.3 order): applicability decision gate,
   owner-routing gate, exact typed-anchor gates (fixed / chained prior
   actual visit / producer D03-D04 refs) and cutoff-scope gates.  An open
   gate never enters the medical expected-set and blocks domain
   completeness (challenges 6/7/74/77/101/102/105/106/112/116).
2. **Applicable expected-set** (§4): only ``unique_active`` applicability
   with closed gates and matured obligations enters the expected-set;
   future/out-of-cutoff obligations stay on the plan axis (challenges
   3/4/5/13/14/15/16/17/95/103/104/113); ``not_applicable`` produces an
   audit unit only under a locatable unique authority (§4.2).
3. **Bidirectional assignment** (§5, §7): encounter-bundle -> planned
   visit and actual-activity -> planned-activity assignment with the
   closed evidence-predicate order (explicit mapping, official code,
   phase/episode/modality, composition/scope, window exclusion only) --
   never nearest date, VISITNUM or row order (challenges 37-48, 60-62,
   107/108/109/110); consumption ledgers with reverse coverage in both
   directions (§7.2).
4. **Maturity evaluation** (§4.2, §6): frozen ``EvaluationMaturityRule``
   per unit kind; no default window-latest endpoint when the rule is
   missing (challenge 113).
5. **Five L1 dispositions** (§8) with the closed positive-subtype
   vocabulary and Chinese audience labels (§8.2).
6. **First-match priority policy** (§9.1): ``D05PriorityPolicy`` with the
   frozen precedence steps; rights/safety and critical-treatment impact is
   always high and machine-close-forbidden (challenge 115); unknown never
   defaults to low.
7. **Enrollment-aware three-part Chinese Query drafts** (§9.2,
   challenge 111) -- only ``enrolled_or_post_enrollment`` may append PD
   wording; ``not_evaluable`` never produces a Query (challenge 88).
8. **Lifecycle adapter integration**: unit results satisfy the neutral
   ``RiskDomainUnitResult`` protocol so the shared
   :class:`mm_r4.lifecycle.R4LifecycleAdapter` registers/establishes
   candidates, forces severity=high for rights/safety and refuses machine
   close for high/flagged risks (challenges 82/83/84/85).

Determinism: every id/hash is a content address; candidate sets, rejected
reasons, ledgers and interpretation ledgers are canonicalized; input order
never changes hashes (challenges 35/36/85/107/114).

All data is synthetic/offline.  No real project, provider, fixed visit
number, fixed window, fixed table name, medication rule or service.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, replace
from typing import (Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple)

from ..domain.identity import make_risk_identity
from ..domain.risk import RiskCandidate

from .contracts import (
    CrossDomainEvidenceRef,
    EvidenceItem,
    L0CoverageStatus,
    L1Disposition,
    L1bEvidencePolarity,
    QueryDraftRef,
    RiskCandidateRef,
    RiskInstanceRef,
    SourceLocator,
    SourceRecordRef,
    UnitEvaluation,
    VALID_MONITORING_PRIORITIES,
    content_hash,
)
from .coverage import (
    CoverageLedger,
    CoverageSummary,
    ExpectedSet,
    is_domain_complete,
)
from .visit_schedule import (
    ACTIVITY_ASSESSMENT,
    ACTIVITY_CONTACT,
    ACTIVITY_PROCEDURE,
    ACTIVITY_SAMPLE,
    ACTIVITY_ASSIGNMENT_DUPLICATE_CONSUMPTION,
    ACTIVITY_ASSIGNMENT_MULTI_FEASIBLE,
    ACTIVITY_ASSIGNMENT_NOT_EVALUABLE,
    ACTIVITY_ASSIGNMENT_UNIQUE,
    ACTIVITY_ASSIGNMENT_UNPLANNED_SUPPORTED,
    ANCHOR_ROLE_OTHER,
    ANCHOR_ROLE_VISIT_SCHEDULE,
    APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
    APPLICABILITY_UNIQUE_ACTIVE,
    ASSIGNMENT_SCOPE_MULTI,
    ActualActivityConsumptionLedger,
    ActualActivityRecord,
    ActualEncounterBundle,
    ActualEncounterRecord,
    ActualRecordScopeDecision,
    ClinicalEventCutoff,
    D05_DOMAIN,
    D05_RULE_LINEAGE_DEFAULT,
    D05_UNIT_ALGO_VERSION,
    ENCOUNTER_HOSPITAL,
    ENCOUNTER_HOME,
    ENCOUNTER_ONSITE,
    ENCOUNTER_REMOTE,
    ENCOUNTER_UNKNOWN,
    ENCOUNTER_UNSCHEDULED,
    EvaluationMaturityRule,
    GATE_ANCHOR,
    GATE_APPLICABILITY,
    GATE_CUTOFF_SCOPE,
    GATE_DECISION_BOUNDARY,
    GATE_DECISION_NOT_EVALUABLE,
    GATE_OPEN,
    GATE_ROUTING,
    INTERPRET_SCOPE_REPEAT,
    INTERPRET_SCOPE_WINDOW,
    MODALITY_HOME,
    MODALITY_HOSPITAL,
    MODALITY_ONSITE,
    MODALITY_REMOTE,
    OWNER_D05,
    OWNER_UNRESOLVED,
    PlannedActivityDefinition,
    PlannedVisitDefinition,
    PRECISION_DAY,
    PRECISION_MONTH,
    PRECISION_YEAR,
    PREDICATE_FALSE,
    PREDICATE_TRUE,
    PRODUCER_RELATION_TYPES,
    REASON_ANCHOR_MISSING,
    REASON_COVERAGE_INCOMPLETE,
    REASON_INTERVAL_STRADDLES,
    REASON_MAPPING_MISSING,
    REASON_MATURITY_RULE_MISSING,
    REASON_MULTIPLE_FEASIBLE,
    REASON_OTHER,
    REASON_PRECISION_INSUFFICIENT,
    REASON_ROUTING_COMPETITION,
    REASON_SCHEDULE_MISSING,
    REASON_TIME_ROLE_CONFLICT,
    REASON_TIME_ROLE_MISSING,
    REASON_TIMEZONE_MISSING,
    REASON_VERSION_MISSING,
    REASON_CODES,
    RELATION_FIXED_REFERENCE,
    RELATION_PRIOR_ACTUAL_VISIT,
    RELATION_TYPES,
    REVERSE_COVERAGE_CLOSED,
    REVERSE_COVERAGE_OPEN,
    SCOPE_BOUNDARY,
    SCOPE_IN_SCOPE,
    SCOPE_NOT_EVALUABLE,
    SCOPE_OUT_OF_CUTOFF,
    ScheduleEvaluationUnit,
    ScheduleGate,
    ScheduleInterpretationLedger,
    ScheduleSliceError,
    SnapshotAsOf,
    SUB_DAY_PRECISIONS,
    TypedScheduleAnchorRef,
    UNIT_ACTIVITY_OCCURRENCE,
    UNIT_ACTIVITY_TIMING,
    UNIT_ACTUAL_ASSIGNMENT,
    UNIT_SCHEDULE_CONSISTENCY,
    UNIT_VISIT_OCCURRENCE,
    UNIT_VISIT_ORDER,
    UNIT_VISIT_TIMING,
    VISIT_ASSIGNMENT_MULTI_FEASIBLE,
    VISIT_ASSIGNMENT_NOT_EVALUABLE,
    VISIT_ASSIGNMENT_UNASSIGNED_INCONSISTENT,
    VISIT_ASSIGNMENT_UNIQUE,
    VISIT_ASSIGNMENT_UNPLANNED_SUPPORTED,
    VISIT_SCHEDULED,
    ActivityAssignmentDecision,
    VisitAssignmentDecision,
    VisitCoverageGapNotice,
    VisitScheduleApplicabilityDecision,
    VisitWindowRule,
    bind_typed_schedule_anchor,
    resolve_actual_record_scope,
    schedule_evaluation_window_id,
    validate_gate_run_accounting,
)

from .visit_schedule_eval_contracts import *
from .visit_schedule_assignments import *
from .visit_schedule_expected import *
from .visit_schedule_results import *
from .visit_schedule_output_helpers import *
from .visit_schedule_results import _action_suffix
from .visit_schedule_unit_evaluation import *
from .visit_schedule_orchestration import *

__all__ = [
    "D05_EVAL_ALGO_VERSION",
    "POSITIVE_SUBTYPES",
    "POSITIVE_SUBTYPE_LABELS",
    "POSITIVE_VISIT_OVERWINDOW",
    "POSITIVE_VISIT_MISSING",
    "POSITIVE_VISIT_ORDER_INCONSISTENT",
    "POSITIVE_VISIT_DUPLICATE",
    "POSITIVE_VISIT_ASSIGNMENT_INCONSISTENT",
    "POSITIVE_ASSESSMENT_MISSING",
    "POSITIVE_ASSESSMENT_MISTIMED",
    "POSITIVE_SAMPLE_MISSING",
    "POSITIVE_SAMPLE_MISTIMED",
    "POSITIVE_SCHEDULE_RULE_INCONSISTENT",
    "IMPACT_CLASSES",
    "RECURRENCE_CLASSES",
    "RECOVERABILITY_CLASSES",
    "ACTIONABILITY_CLASSES",
    "D05PriorityPolicy",
    "D05PriorityVerdict",
    "resolve_d05_priority",
    "QUERY_CONTEXTS",
    "QUERY_CONTEXT_NOT_OCCURRED",
    "QUERY_CONTEXT_ENROLLED",
    "QUERY_CONTEXT_UNRESOLVED",
    "EnrollmentEvidence",
    "D05EnrollmentContext",
    "resolve_d05_enrollment_context",
    "StableVisitMapping",
    "OfficialCodeMapping",
    "OfficialActivityCodeAlias",
    "ObligationApplicability",
    "ScheduleConsistencyIssue",
    "AnchorBindingRequest",
    "D05UnitResult",
    "D05EvaluationOutcome",
    "build_d05_candidate",
    "build_d05_query_draft",
    "audience_tokens_clean",
    "evaluate_visit_schedule_run",
    "expand_expected_set",
    "resolve_visit_assignments",
    "resolve_activity_assignments",
    "build_consumption_ledgers",
    "resolve_visit_assignment",
    "resolve_activity_assignment",
    "window_bounds",
    "maturity_day_for",
]
