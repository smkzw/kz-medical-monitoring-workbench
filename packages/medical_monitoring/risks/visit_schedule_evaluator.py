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


# ---------------------------------------------------------------------------
# Evaluation identity
# ---------------------------------------------------------------------------

D05_EVAL_ALGO_VERSION = "d05_eval_v1"

#: Versioned evidence-predicate ids used by the assignment algorithms (§5.1).
PRED_EXPLICIT_MAPPING = "d05-pred-explicit-mapping-v1"
PRED_OFFICIAL_CODE = "d05-pred-official-code-v1"
PRED_PHASE_EPISODE_MODALITY = "d05-pred-phase-episode-modality-v1"
PRED_COMPOSITION_SCOPE = "d05-pred-composition-scope-v1"
PRED_WINDOW_EXCLUSION = "d05-pred-window-exclusion-v1"
PRED_ACTIVITY_CLAIM = "d05-pred-activity-claim-contradiction-v1"

#: Maturity-expression token meaning "the window's latest inclusive endpoint
#: (+ grace)"; anything else is a signed day count or ISO day/week duration.
MATURITY_WINDOW_LATEST = "window_latest_endpoint"


# ---------------------------------------------------------------------------
# Positive subtypes (§8.2) -- closed set with user-facing Chinese labels
# ---------------------------------------------------------------------------

POSITIVE_VISIT_OVERWINDOW = "visit_overwindow"
POSITIVE_VISIT_MISSING = "visit_missing"
POSITIVE_VISIT_ORDER_INCONSISTENT = "visit_order_inconsistent"
POSITIVE_VISIT_DUPLICATE = "visit_duplicate"
POSITIVE_VISIT_ASSIGNMENT_INCONSISTENT = "visit_assignment_inconsistent"
POSITIVE_ASSESSMENT_MISSING = "required_assessment_missing"
POSITIVE_ASSESSMENT_MISTIMED = "required_assessment_mistimed"
POSITIVE_SAMPLE_MISSING = "required_sample_missing"
POSITIVE_SAMPLE_MISTIMED = "required_sample_mistimed"
POSITIVE_SCHEDULE_RULE_INCONSISTENT = "schedule_rule_inconsistent"

POSITIVE_SUBTYPES: Tuple[str, ...] = (
    POSITIVE_VISIT_OVERWINDOW,
    POSITIVE_VISIT_MISSING,
    POSITIVE_VISIT_ORDER_INCONSISTENT,
    POSITIVE_VISIT_DUPLICATE,
    POSITIVE_VISIT_ASSIGNMENT_INCONSISTENT,
    POSITIVE_ASSESSMENT_MISSING,
    POSITIVE_ASSESSMENT_MISTIMED,
    POSITIVE_SAMPLE_MISSING,
    POSITIVE_SAMPLE_MISTIMED,
    POSITIVE_SCHEDULE_RULE_INCONSISTENT,
)

POSITIVE_SUBTYPE_LABELS: Mapping[str, str] = {
    POSITIVE_VISIT_OVERWINDOW: "访视时间待核实",
    POSITIVE_VISIT_MISSING: "访视完成情况待核实",
    POSITIVE_VISIT_ORDER_INCONSISTENT: "访视先后顺序待核实",
    POSITIVE_VISIT_DUPLICATE: "访视重复记录待核实",
    POSITIVE_VISIT_ASSIGNMENT_INCONSISTENT: "访视归属待核实",
    POSITIVE_ASSESSMENT_MISSING: "评估记录待核实",
    POSITIVE_ASSESSMENT_MISTIMED: "评估时间待核实",
    POSITIVE_SAMPLE_MISSING: "样本采集记录待核实",
    POSITIVE_SAMPLE_MISTIMED: "样本采集时间待核实",
    POSITIVE_SCHEDULE_RULE_INCONSISTENT: "方案时序要求待核实",
}

#: Engineering tokens that must never appear in audience-facing strings
#: (challenge 89).
AUDIENCE_FORBIDDEN_TOKENS: Tuple[str, ...] = (
    "positive", "candidate", "formal fact", "候选信号", "正式事实",
    "只读投影", "规则引擎命中", "后端", "模型置信度",
)

_PRIORITY_HIGH = "high"
_PRIORITY_MEDIUM = "medium"
_PRIORITY_LOW = "low"
_PRIORITY_UNKNOWN = "unknown"


def audience_tokens_clean(text: str) -> bool:
    """True when an audience-facing string carries no engineering jargon."""
    lowered = text.lower()
    return not any(token.lower() in lowered for token in AUDIENCE_FORBIDDEN_TOKENS)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class VisitScheduleEvaluatorError(Exception):
    """A D05 evaluation invariant was violated."""


# ---------------------------------------------------------------------------
# Small private helpers
# ---------------------------------------------------------------------------

_DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DAY_COUNT_RE = re.compile(r"^[+-]?\d+$")
_ISO_DURATION_RE = re.compile(r"^P(?:\d+[DW])+$")
_REPEAT_RE = re.compile(r"^repeat:(?:(\d+)|unlimited)$")


def _canonical_sorted(value: Sequence[str]) -> Tuple[str, ...]:
    return tuple(sorted({v for v in value if v.strip()}))


def _validate_nonempty(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise VisitScheduleEvaluatorError(
            f"{field_name} is required and must be a non-empty string")
    return value


def _validate_optional_str(value: Any, field_name: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise VisitScheduleEvaluatorError(
            f"{field_name} must be a string, got {type(value).__name__}")
    return value


def _day_date(raw: str) -> Optional[datetime.date]:
    raw = (raw or "").strip()
    if not raw or not _DAY_RE.match(raw):
        return None
    try:
        return datetime.date.fromisoformat(raw)
    except ValueError:
        return None


def _day_interval(raw: str) -> Tuple[Optional[datetime.date],
                                     Optional[datetime.date]]:
    """Earliest/latest day-dates implied by a partial date."""
    raw = (raw or "").strip()
    if not raw:
        return None, None
    if _DAY_RE.match(raw):
        day = _day_date(raw)
        return day, day
    parts = raw.split("-")
    if len(parts) == 2:
        try:
            year = int(parts[0])
            month = int(parts[1])
            lo = datetime.date(year, month, 1)
            hi = datetime.date(year + (month == 12), (month % 12) + 1, 1) \
                - datetime.timedelta(days=1)
            return lo, hi
        except ValueError:
            return None, None
    if len(parts) == 1 and raw.isdigit() and 1900 <= int(raw) <= 2200:
        return datetime.date(int(raw), 1, 1), datetime.date(int(raw), 12, 31)
    return None, None


def _day_instant_interval(
    lo: datetime.date, hi: datetime.date,
) -> Tuple[datetime.datetime, datetime.datetime]:
    start = datetime.datetime(lo.year, lo.month, lo.day,
                              tzinfo=datetime.timezone.utc)
    end = datetime.datetime(hi.year, hi.month, hi.day, 23, 59, 59, 999999,
                            tzinfo=datetime.timezone.utc)
    return start, end


def _offset_days(value: str) -> Optional[int]:
    """Signed day count or ISO PnD/PnW duration -> day count; None when
    unfrozen (month/year durations are not frozen in v1)."""
    value = (value or "").strip()
    if not value:
        return 0
    if _DAY_COUNT_RE.match(value):
        return int(value)
    if _ISO_DURATION_RE.match(value):
        days = 0
        for chunk in re.findall(r"(\d+)([DW])", value):
            n = int(chunk[0])
            days += n * 7 if chunk[1] == "W" else n
        return days
    return None


def _repeat_multiplicity(repeat_rule: str) -> int:
    repeat_rule = (repeat_rule or "").strip()
    if not repeat_rule:
        return 1
    m = _REPEAT_RE.match(repeat_rule)
    if not m:
        return 1
    if m.group(1) is not None:
        try:
            return max(1, int(m.group(1)))
        except ValueError:
            return 1
    return 2


def _order_key(order: str) -> Tuple[int, ...]:
    """Numeric-aware planned-order key (VISITNUM is never time authority)."""
    return tuple(int(part) for part in re.findall(r"\d+", order or "0")) \
        or (0,)


def _modality_for_encounter_kind(encounter_kind: str) -> str:
    return {
        ENCOUNTER_ONSITE: MODALITY_ONSITE,
        ENCOUNTER_REMOTE: MODALITY_REMOTE,
        ENCOUNTER_HOSPITAL: MODALITY_HOSPITAL,
        ENCOUNTER_HOME: MODALITY_HOME,
    }.get(encounter_kind, "")


def _bundle_interval_relation_to_day(
    bundle: ActualEncounterBundle,
) -> Tuple[Optional[datetime.date], Optional[datetime.date], bool]:
    """(lo_day, hi_day, complete) of a bundle interval at day granularity."""
    lo: Optional[datetime.date] = None
    hi: Optional[datetime.date] = None
    if bundle.date_precision not in (PRECISION_DAY, PRECISION_MONTH,
                                     PRECISION_YEAR):
        return None, None, False
    for raw in (bundle.derived_start, bundle.derived_end):
        if not (raw or "").strip():
            continue
        interval = _day_interval(raw)
        if interval is None or interval[0] is None:
            return None, None, False
        lo = interval[0] if lo is None else min(lo, interval[0])
        hi = interval[1] if hi is None else max(hi, interval[1])
    if lo is None or hi is None:
        return None, None, False
    complete = bundle.date_precision == PRECISION_DAY
    return lo, hi, complete


def _day_interval_of(
    record: Any,
) -> Tuple[Optional[datetime.date], Optional[datetime.date], bool]:
    lo: Optional[datetime.date] = None
    hi: Optional[datetime.date] = None
    for raw in (getattr(record, "start", ""), getattr(record, "end", "")):
        if not (raw or "").strip():
            continue
        interval = _day_interval(raw)
        if interval is None or interval[0] is None:
            return None, None, False
        lo = interval[0] if lo is None else min(lo, interval[0])
        hi = interval[1] if hi is None else max(hi, interval[1])
    if lo is None or hi is None:
        return None, None, False
    complete = getattr(record, "date_precision", PRECISION_DAY) \
        == PRECISION_DAY
    return lo, hi, complete


# ---------------------------------------------------------------------------
# Priority policy (§9.1) -- closed enums and first-match precedence
# ---------------------------------------------------------------------------

IMPACT_RIGHTS_SAFETY = "rights_safety"
IMPACT_CRITICAL_TREATMENT = "critical_treatment"
IMPACT_PRIMARY_ENDPOINT = "primary_endpoint"
IMPACT_KEY_SECONDARY_ENDPOINT = "key_secondary_endpoint"
IMPACT_MANDATORY_CRITICAL_SAMPLE = "mandatory_critical_sample"
IMPACT_OTHER_REQUIRED = "other_required"
IMPACT_ADMINISTRATIVE = "administrative"
IMPACT_CLASSES: Tuple[str, ...] = (
    IMPACT_RIGHTS_SAFETY, IMPACT_CRITICAL_TREATMENT, IMPACT_PRIMARY_ENDPOINT,
    IMPACT_KEY_SECONDARY_ENDPOINT, IMPACT_MANDATORY_CRITICAL_SAMPLE,
    IMPACT_OTHER_REQUIRED, IMPACT_ADMINISTRATIVE,
)

RECURRENCE_SINGLE = "single"
RECURRENCE_REPEATED_SUBJECT = "repeated_subject"
RECURRENCE_REPEATED_SITE = "repeated_site"
RECURRENCE_CLASSES: Tuple[str, ...] = (
    RECURRENCE_SINGLE, RECURRENCE_REPEATED_SUBJECT, RECURRENCE_REPEATED_SITE,
)

RECOVERABILITY_RECOVERABLE = "recoverable"
RECOVERABILITY_TIME_CRITICAL = "time_critical"
RECOVERABILITY_IRRECOVERABLE = "irrecoverable"
RECOVERABILITY_UNKNOWN = "unknown"
RECOVERABILITY_CLASSES: Tuple[str, ...] = (
    RECOVERABILITY_RECOVERABLE, RECOVERABILITY_TIME_CRITICAL,
    RECOVERABILITY_IRRECOVERABLE, RECOVERABILITY_UNKNOWN,
)

ACTIONABILITY_ACTIONABLE = "actionable"
ACTIONABILITY_CONTEXT_ONLY = "context_only"
ACTIONABILITY_UNKNOWN = "unknown"
ACTIONABILITY_CLASSES: Tuple[str, ...] = (
    ACTIONABILITY_ACTIONABLE, ACTIONABILITY_CONTEXT_ONLY, ACTIONABILITY_UNKNOWN,
)


@dataclass(frozen=True)
class D05PriorityPolicy:
    """Versioned, content-addressed priority policy input (§9.1).

    The four inputs are closed enums frozen by the plan decompiler /
    deterministic QC -- never model free-form scoring.
    """

    policy_id: str
    impact_class: str
    recurrence_class: str
    recoverability: str
    actionability: str
    rule_version: str = D05_RULE_LINEAGE_DEFAULT
    source_locator_ids: Tuple[str, ...] = ()
    hash: str = ""

    def __post_init__(self) -> None:
        for name, value, closed in (
            ("impact_class", self.impact_class, IMPACT_CLASSES),
            ("recurrence_class", self.recurrence_class, RECURRENCE_CLASSES),
            ("recoverability", self.recoverability, RECOVERABILITY_CLASSES),
            ("actionability", self.actionability, ACTIONABILITY_CLASSES),
        ):
            if value not in closed:
                raise VisitScheduleEvaluatorError(
                    f"D05PriorityPolicy.{name}={value!r} is not a frozen "
                    f"closed enum {closed}")
        _validate_nonempty(self.rule_version, "D05PriorityPolicy.rule_version")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        computed = "d05-policy-" + content_hash({
            "impact_class": self.impact_class,
            "recurrence_class": self.recurrence_class,
            "recoverability": self.recoverability,
            "actionability": self.actionability,
            "rule_version": self.rule_version,
            "source_locator_ids": list(self.source_locator_ids),
        })
        if self.policy_id and self.policy_id != computed:
            raise VisitScheduleEvaluatorError(
                f"D05PriorityPolicy.policy_id {self.policy_id!r} does not "
                f"match {computed!r}")
        object.__setattr__(self, "policy_id", computed)
        if self.hash and self.hash != computed:
            raise VisitScheduleEvaluatorError(
                f"D05PriorityPolicy.hash {self.hash!r} does not match "
                f"{computed!r}")
        object.__setattr__(self, "hash", computed)


@dataclass(frozen=True)
class D05PriorityVerdict:
    """Result of one frozen priority decision (§9.1)."""

    policy_id: str
    priority: str
    machine_close_forbidden: bool
    rights_or_safety_critical: bool
    precedence_step: int
    reason_codes: Tuple[str, ...]
    coverage_note: str = ""
    hash: str = ""

    def __post_init__(self) -> None:
        if self.priority not in VALID_MONITORING_PRIORITIES:
            raise VisitScheduleEvaluatorError(
                f"D05PriorityVerdict.priority={self.priority!r} invalid")
        _validate_nonempty(self.policy_id, "D05PriorityVerdict.policy_id")
        if not isinstance(self.precedence_step, int) \
                or not 1 <= self.precedence_step <= 5:
            raise VisitScheduleEvaluatorError(
                "D05PriorityVerdict.precedence_step must be an int in 1..5")
        object.__setattr__(self, "reason_codes",
                           _canonical_sorted(self.reason_codes))
        if self.machine_close_forbidden \
                and self.priority != _PRIORITY_HIGH:
            raise VisitScheduleEvaluatorError(
                "machine_close_forbidden priority verdict must be high "
                "(challenge 115)")
        computed = "d05-priority-" + content_hash({
            "policy_id": self.policy_id,
            "priority": self.priority,
            "machine_close_forbidden": self.machine_close_forbidden,
            "rights_or_safety_critical": self.rights_or_safety_critical,
            "precedence_step": self.precedence_step,
            "reason_codes": list(self.reason_codes),
            "coverage_note": self.coverage_note,
        })
        if self.hash and self.hash != computed:
            raise VisitScheduleEvaluatorError(
                f"D05PriorityVerdict.hash {self.hash!r} does not match "
                f"{computed!r}")
        object.__setattr__(self, "hash", computed)


def resolve_d05_priority(policy: D05PriorityPolicy) -> D05PriorityVerdict:
    """Frozen v1 precedence (§9.1): first matching step wins, escalate to
    high capped.  Unknown never defaults to low; rights/safety and
    critical-treatment are always high and machine-close-forbidden."""
    impact = policy.impact_class
    recurrence = policy.recurrence_class
    recoverability = policy.recoverability
    actionability = policy.actionability

    # Step 1 -- rights/safety or critical treatment.
    if impact in (IMPACT_RIGHTS_SAFETY, IMPACT_CRITICAL_TREATMENT):
        note = ""
        reasons = (REASON_OTHER,)
        if recoverability == RECOVERABILITY_UNKNOWN \
                or actionability in (ACTIONABILITY_CONTEXT_ONLY,
                                     ACTIONABILITY_UNKNOWN):
            note = ("安全/权益或关键治疗影响已确定；可行动性/可恢复性输入"
                    "未知，仅提示覆盖与上下文，不降低优先级")
            reasons = (REASON_COVERAGE_INCOMPLETE,)
        return D05PriorityVerdict(
            policy_id=policy.policy_id, priority=_PRIORITY_HIGH,
            machine_close_forbidden=True,
            rights_or_safety_critical=(impact == IMPACT_RIGHTS_SAFETY),
            precedence_step=1, reason_codes=reasons, coverage_note=note)

    # Step 2 -- any other impact class with unknown recoverability or
    # unknown/context-only actionability: unknown, never a default low.
    if recoverability == RECOVERABILITY_UNKNOWN \
            or actionability in (ACTIONABILITY_CONTEXT_ONLY,
                                 ACTIONABILITY_UNKNOWN):
        return D05PriorityVerdict(
            policy_id=policy.policy_id, priority=_PRIORITY_UNKNOWN,
            machine_close_forbidden=False, rights_or_safety_critical=False,
            precedence_step=2, reason_codes=(REASON_COVERAGE_INCOMPLETE,))

    # Step 3 -- primary endpoint / mandatory critical sample.
    if impact in (IMPACT_PRIMARY_ENDPOINT, IMPACT_MANDATORY_CRITICAL_SAMPLE):
        if recoverability in (RECOVERABILITY_TIME_CRITICAL,
                              RECOVERABILITY_IRRECOVERABLE):
            priority = _PRIORITY_HIGH
        else:
            priority = _PRIORITY_MEDIUM
        return D05PriorityVerdict(
            policy_id=policy.policy_id, priority=priority,
            machine_close_forbidden=False, rights_or_safety_critical=False,
            precedence_step=3, reason_codes=(REASON_OTHER,))

    # Step 4 -- key secondary endpoint / other required.
    if impact in (IMPACT_KEY_SECONDARY_ENDPOINT, IMPACT_OTHER_REQUIRED):
        if recurrence == RECURRENCE_REPEATED_SITE \
                or recoverability == RECOVERABILITY_IRRECOVERABLE:
            priority = _PRIORITY_HIGH
        else:
            priority = _PRIORITY_MEDIUM
        return D05PriorityVerdict(
            policy_id=policy.policy_id, priority=priority,
            machine_close_forbidden=False, rights_or_safety_critical=False,
            precedence_step=4, reason_codes=(REASON_OTHER,))

    # Step 5 -- administrative.
    if recurrence == RECURRENCE_SINGLE \
            and recoverability == RECOVERABILITY_RECOVERABLE \
            and actionability == ACTIONABILITY_ACTIONABLE:
        return D05PriorityVerdict(
            policy_id=policy.policy_id, priority=_PRIORITY_LOW,
            machine_close_forbidden=False, rights_or_safety_critical=False,
            precedence_step=5, reason_codes=(REASON_OTHER,))
    if recurrence == RECURRENCE_REPEATED_SUBJECT:
        return D05PriorityVerdict(
            policy_id=policy.policy_id, priority=_PRIORITY_MEDIUM,
            machine_close_forbidden=False, rights_or_safety_critical=False,
            precedence_step=5, reason_codes=(REASON_OTHER,))
    return D05PriorityVerdict(
        policy_id=policy.policy_id, priority=_PRIORITY_HIGH,
        machine_close_forbidden=False, rights_or_safety_critical=False,
        precedence_step=5, reason_codes=(REASON_OTHER,))


# ---------------------------------------------------------------------------
# Query context (§9.2) -- enrollment-aware three-part wording gate
# ---------------------------------------------------------------------------

QUERY_CONTEXT_NOT_OCCURRED = "enrollment_not_occurred"
QUERY_CONTEXT_ENROLLED = "enrolled_or_post_enrollment"
QUERY_CONTEXT_UNRESOLVED = "enrollment_state_unresolved"
QUERY_CONTEXTS: Tuple[str, ...] = (
    QUERY_CONTEXT_NOT_OCCURRED, QUERY_CONTEXT_ENROLLED,
    QUERY_CONTEXT_UNRESOLVED,
)


@dataclass(frozen=True)
class EnrollmentEvidence:
    """Locatable screening/randomization/enrollment/first-dose/disposition
    evidence used to freeze the Query context (§9.2) -- never guessed from
    the current page or the model."""

    subject_ref: str
    randomized_or_enrolled: Optional[bool] = None
    received_study_intervention: Optional[bool] = None
    disposition_recorded: Optional[bool] = None
    coverage_complete: bool = False
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref, "EnrollmentEvidence.subject_ref")
        for name in ("randomized_or_enrolled",
                     "received_study_intervention", "disposition_recorded"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, bool):
                raise VisitScheduleEvaluatorError(
                    f"EnrollmentEvidence.{name} must be bool or None")
        if not isinstance(self.coverage_complete, bool):
            raise VisitScheduleEvaluatorError(
                "EnrollmentEvidence.coverage_complete must be bool")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))


@dataclass(frozen=True)
class D05EnrollmentContext:
    """Frozen enrollment-aware Query context (§9.2)."""

    subject_ref: str
    query_context: str
    rationale: str
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref, "D05EnrollmentContext.subject_ref")
        if self.query_context not in QUERY_CONTEXTS:
            raise VisitScheduleEvaluatorError(
                f"D05EnrollmentContext.query_context={self.query_context!r} "
                f"invalid")
        _validate_nonempty(self.rationale, "D05EnrollmentContext.rationale")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))


def resolve_d05_enrollment_context(
    *, evidence: EnrollmentEvidence,
) -> D05EnrollmentContext:
    """Frozen §9.2 truth table (token values are shared contract literals,
    identical to the D04 slice's tokens).

    A generic disposition record does not prove enrollment (§9.2): the
    ``enrolled_or_post_enrollment`` context requires an explicit
    randomization/enrollment or study-intervention record with complete
    coverage.  ``disposition_recorded=True`` alone never implies enrolled;
    with both enrollment/intervention explicitly false and complete coverage
    it supports ``enrollment_not_occurred`` (e.g. a screen-failure-like
    disposition), otherwise the state is unresolved.
    """
    enrolled = (
        evidence.coverage_complete
        and (evidence.randomized_or_enrolled is True
             or evidence.received_study_intervention is True))
    if enrolled:
        return D05EnrollmentContext(
            subject_ref=evidence.subject_ref,
            query_context=QUERY_CONTEXT_ENROLLED,
            rationale="已记录随机/入组或接受研究干预",
            source_locator_ids=evidence.source_locator_ids)
    not_occurred = (
        evidence.coverage_complete
        and evidence.randomized_or_enrolled is False
        and evidence.received_study_intervention is False)
    if not_occurred:
        return D05EnrollmentContext(
            subject_ref=evidence.subject_ref,
            query_context=QUERY_CONTEXT_NOT_OCCURRED,
            rationale="确定尚未随机/入组且未接受研究干预",
            source_locator_ids=evidence.source_locator_ids)
    return D05EnrollmentContext(
        subject_ref=evidence.subject_ref,
        query_context=QUERY_CONTEXT_UNRESOLVED,
        rationale="随机/入组/首次给药状态或时序无法确定，资料不足",
        source_locator_ids=evidence.source_locator_ids)


# ---------------------------------------------------------------------------
# Input value objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StableVisitMapping:
    """Verified explicit stable mapping (§5.1 predicate 1): a bundle (by
    stable actual object key or an exact member encounter id) maps to one
    planned visit key.  Exactly one of the two keys is required."""

    planned_visit_key: str
    predicate_id: str = PRED_EXPLICIT_MAPPING
    rule_version: str = D05_UNIT_ALGO_VERSION
    stable_actual_object_key: str = ""
    encounter_id: str = ""
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.planned_visit_key,
                           "StableVisitMapping.planned_visit_key")
        _validate_nonempty(self.predicate_id, "StableVisitMapping.predicate_id")
        _validate_nonempty(self.rule_version, "StableVisitMapping.rule_version")
        _validate_optional_str(self.stable_actual_object_key,
                               "StableVisitMapping.stable_actual_object_key")
        _validate_optional_str(self.encounter_id,
                               "StableVisitMapping.encounter_id")
        if bool(self.stable_actual_object_key) == bool(self.encounter_id):
            raise VisitScheduleEvaluatorError(
                "StableVisitMapping requires exactly one of "
                "stable_actual_object_key / encounter_id")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))


@dataclass(frozen=True)
class OfficialCodeMapping:
    """Verified official visit-code / alias mapping within one protocol
    version (§5.1 predicate 2)."""

    recorded_visit_code: str
    official_visit_code: str
    protocol_version: str
    predicate_id: str = PRED_OFFICIAL_CODE
    rule_version: str = D05_UNIT_ALGO_VERSION
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.recorded_visit_code,
                           "OfficialCodeMapping.recorded_visit_code")
        _validate_nonempty(self.official_visit_code,
                           "OfficialCodeMapping.official_visit_code")
        _validate_nonempty(self.protocol_version,
                           "OfficialCodeMapping.protocol_version")
        _validate_nonempty(self.predicate_id, "OfficialCodeMapping.predicate_id")
        _validate_nonempty(self.rule_version, "OfficialCodeMapping.rule_version")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))


@dataclass(frozen=True)
class OfficialActivityCodeAlias:
    """Verified recorded-activity-code alias within one clinical domain
    (§7.1 predicate 2)."""

    recorded_activity_code: str
    official_activity_code: str
    clinical_domain: str
    predicate_id: str = "d05-pred-activity-code-v1"
    rule_version: str = D05_UNIT_ALGO_VERSION
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.recorded_activity_code,
                           "OfficialActivityCodeAlias.recorded_activity_code")
        _validate_nonempty(self.official_activity_code,
                           "OfficialActivityCodeAlias.official_activity_code")
        _validate_nonempty(self.clinical_domain,
                           "OfficialActivityCodeAlias.clinical_domain")
        _validate_nonempty(self.predicate_id,
                           "OfficialActivityCodeAlias.predicate_id")
        _validate_nonempty(self.rule_version,
                           "OfficialActivityCodeAlias.rule_version")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))


@dataclass(frozen=True)
class ObligationApplicability:
    """Per-obligation applicability outcome (§4.1/§4.2).

    ``applicable`` is tri-state: True / False (unique authoritative
    not-applicable, e.g. locatable phase end, death, withdrawal) / None
    (unknown).  Unknown never infers not-applicable from "no further data"
    (challenge 14).
    """

    obligation_key: str
    applicable: Optional[bool]
    reason_code: str = ""
    authority_locator_ids: Tuple[str, ...] = ()
    effective_time: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.obligation_key,
                           "ObligationApplicability.obligation_key")
        if self.applicable is not None and not isinstance(self.applicable,
                                                          bool):
            raise VisitScheduleEvaluatorError(
                "ObligationApplicability.applicable must be bool or None")
        _validate_optional_str(self.reason_code,
                               "ObligationApplicability.reason_code")
        _validate_optional_str(self.effective_time,
                               "ObligationApplicability.effective_time")
        if self.applicable is False:
            if not self.reason_code.strip():
                raise VisitScheduleEvaluatorError(
                    "not-applicable obligation requires a reason code "
                    "(locatable authority)")
        object.__setattr__(self, "authority_locator_ids",
                           _canonical_sorted(self.authority_locator_ids))


@dataclass(frozen=True)
class ScheduleConsistencyIssue:
    """A declared plan self-inconsistency (§3.3 unit kind
    ``schedule_consistency``, challenge 78)."""

    issue_id: str
    rule_ids: Tuple[str, ...]
    reason_code: str = REASON_OTHER
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.issue_id, "ScheduleConsistencyIssue.issue_id")
        rules = _canonical_sorted(self.rule_ids)
        if not rules:
            raise VisitScheduleEvaluatorError(
                "ScheduleConsistencyIssue requires at least one rule id")
        object.__setattr__(self, "rule_ids", rules)
        _validate_optional_str(self.reason_code,
                               "ScheduleConsistencyIssue.reason_code")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))


@dataclass(frozen=True)
class AnchorBindingRequest:
    """Explicit anchor-binding expectations for one planned visit (§5.3).

    For producer relations every expected dimension must be declared
    explicitly -- omission never behaves as a wildcard; the binding is
    resolved through worker_01's :func:`bind_typed_schedule_anchor`.  For
    internal fixed references ``anchor_day`` carries the Day-1 date; for
    chained prior-actual-visit relations the anchor is resolved internally
    from the prior visit's unique dated assignment (never a nearest-date
    shortcut).
    """

    planned_visit_key: str
    relation_type: str
    producer_ref: Optional[CrossDomainEvidenceRef] = None
    producer_domain: str = ""
    producer_unit_id: str = ""
    stable_source_event_key: str = ""
    content_hash: str = ""
    phase: str = ""
    episode_id: str = ""
    anchor_start: str = ""
    anchor_end: str = ""
    date_precision: str = PRECISION_DAY
    timezone: str = ""
    anchor_day: str = ""
    affected_planned_activity_keys: Tuple[str, ...] = ()
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.planned_visit_key,
                           "AnchorBindingRequest.planned_visit_key")
        if self.relation_type not in RELATION_TYPES:
            raise VisitScheduleEvaluatorError(
                f"AnchorBindingRequest.relation_type={self.relation_type!r} "
                f"invalid")
        if self.relation_type in PRODUCER_RELATION_TYPES:
            if self.producer_ref is None:
                raise VisitScheduleEvaluatorError(
                    f"producer anchor relation {self.relation_type!r} "
                    f"requires a producer_ref")
            if not self.anchor_start.strip() or not self.anchor_end.strip():
                raise VisitScheduleEvaluatorError(
                    "producer anchor binding requires explicit expected "
                    "anchor_start/anchor_end (no omission)")
            if self.anchor_day.strip():
                raise VisitScheduleEvaluatorError(
                    "producer anchor binding must not carry anchor_day")
        elif self.relation_type == RELATION_FIXED_REFERENCE:
            if not self.anchor_day.strip():
                raise VisitScheduleEvaluatorError(
                    "fixed-reference anchor binding requires anchor_day")
            if self.producer_ref is not None:
                raise VisitScheduleEvaluatorError(
                    "fixed-reference anchor binding must not carry a "
                    "producer ref")
        elif self.relation_type == RELATION_PRIOR_ACTUAL_VISIT:
            if self.producer_ref is not None or self.anchor_day.strip():
                raise VisitScheduleEvaluatorError(
                    "chained-prior-visit anchor binding is resolved "
                    "internally; must not carry producer ref or anchor_day")
        else:
            raise VisitScheduleEvaluatorError(
                f"anchor relation {self.relation_type!r} is not supported "
                f"by the evaluator v1")
        if self.relation_type not in PRODUCER_RELATION_TYPES:
            for name in ("producer_domain", "producer_unit_id",
                         "stable_source_event_key", "content_hash"):
                if getattr(self, name):
                    raise VisitScheduleEvaluatorError(
                        f"internal anchor binding must not carry {name}")
        object.__setattr__(self, "affected_planned_activity_keys",
                           _canonical_sorted(self.affected_planned_activity_keys))
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))


# ---------------------------------------------------------------------------
# Window arithmetic (§6) -- frozen v1; never defaults, never silent padding
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WindowBounds:
    """Determinate day bounds of one window, or the failure status."""

    lo_day: str = ""
    hi_day: str = ""
    determinable: bool = True
    reason_code: str = ""
    precision: str = PRECISION_DAY


def window_bounds(
    *, window_rule: Optional[VisitWindowRule], anchor_day: str,
) -> WindowBounds:
    """Frozen day-level window bounds from a window rule and an anchor day.

    * ``lower_offset``/``upper_offset`` are signed day counts or ISO PnD/PnW;
      ISO month/year durations are unfrozen in v1 (not_evaluable);
    * study-day semantics honor ``study_day_zero_exists``: with Day 0 the
      anchor is day 0; without Day 0 the anchor is day 1 and study day N
      maps to anchor + (N - 1) (the frozen v1 conversion, challenge 28);
    * endpoint inclusivity is tri-state; an unfrozen (None) endpoint makes
      the window non-determinable (challenge 20 -- never defaulted);
    * grace extends the upper endpoint.
    """
    if window_rule is None:
        return WindowBounds(determinable=False,
                            reason_code=REASON_PRECISION_INSUFFICIENT)
    if not anchor_day.strip():
        return WindowBounds(determinable=False, reason_code=REASON_ANCHOR_MISSING)
    anchor = _day_date(anchor_day)
    if anchor is None:
        return WindowBounds(determinable=False,
                            reason_code=REASON_TIME_ROLE_MISSING)
    if window_rule.lower_endpoint_inclusive is None \
            or window_rule.upper_endpoint_inclusive is None:
        return WindowBounds(determinable=False,
                            reason_code=REASON_PRECISION_INSUFFICIENT)
    lower = _offset_days(window_rule.lower_offset)
    upper = _offset_days(window_rule.upper_offset)
    grace = _offset_days(window_rule.grace_period)
    if lower is None or upper is None or grace is None:
        return WindowBounds(determinable=False,
                            reason_code=REASON_PRECISION_INSUFFICIENT)

    def _apply(offset: int) -> datetime.date:
        if window_rule.calendar_semantics == "study_day":
            if window_rule.study_day_zero_exists is False:
                offset = offset - 1
        return anchor + datetime.timedelta(days=offset)

    lo = _apply(lower)
    hi = _apply(upper)
    hi = hi + datetime.timedelta(days=grace)
    if not window_rule.lower_endpoint_inclusive:
        lo = lo + datetime.timedelta(days=1)
    if not window_rule.upper_endpoint_inclusive:
        hi = hi - datetime.timedelta(days=1)
    return WindowBounds(lo_day=lo.isoformat(), hi_day=hi.isoformat(),
                        determinable=True,
                        precision=window_rule.date_precision)


# ---------------------------------------------------------------------------
# Maturity (§4.2, challenge 113) -- never default the window-latest endpoint
# ---------------------------------------------------------------------------

def maturity_day_for(
    *, maturity_rule: EvaluationMaturityRule, anchor_day: str,
    window_rule: Optional[VisitWindowRule] = None,
) -> Optional[str]:
    """The maturity day of one unit kind under a frozen maturity rule.

    ``maturity_expression`` is either the token ``window_latest_endpoint``
    (the window's inclusive latest endpoint incl. grace) or a signed day
    count / ISO day-week duration from the anchor.  None means the maturity
    timepoint cannot be computed (missing anchor / unfrozen expression) and
    the obligation is evaluated ``not_evaluable`` (challenge 113).
    """
    if not anchor_day.strip():
        return None
    anchor = _day_date(anchor_day)
    if anchor is None:
        return None
    expression = (maturity_rule.maturity_expression or "").strip()
    if expression == MATURITY_WINDOW_LATEST:
        if window_rule is None:
            return None
        bounds = window_bounds(window_rule=window_rule, anchor_day=anchor_day)
        if not bounds.determinable or not bounds.hi_day:
            return None
        return bounds.hi_day
    offset = _offset_days(expression)
    if offset is None:
        return None
    return (anchor + datetime.timedelta(days=offset)).isoformat()


# ---------------------------------------------------------------------------
# Assignment contexts
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VisitAssignmentContext:
    """Frozen inputs of the visit-assignment algorithm for one Run."""

    project_ref: str
    subject_ref: str
    site_ref: str
    applicable_visit_keys: Tuple[str, ...]
    planned_visits: Tuple[PlannedVisitDefinition, ...]
    explicit_mappings: Tuple[StableVisitMapping, ...]
    code_mappings: Tuple[OfficialCodeMapping, ...]
    anchor_day_by_visit_key: Tuple[Tuple[str, str], ...]
    encounter_by_id: Mapping[str, ActualEncounterRecord]
    protocol_version: str = ""
    allow_unscheduled_visits: bool = False
    mapping_coverage_complete: bool = True
    code_coverage_complete: bool = True

    def visit_by_key(self, key: str) -> Optional[PlannedVisitDefinition]:
        for visit in self.planned_visits:
            if visit.planned_visit_key == key:
                return visit
        return None

    def anchor_day(self, key: str) -> str:
        for item in self.anchor_day_by_visit_key:
            if item[0] == key:
                return item[1]
        return ""

    def bundle_encounter_kind(self, bundle: ActualEncounterBundle) -> str:
        kinds = [self.encounter_by_id[m].encounter_kind
                 for m in bundle.member_encounter_ids
                 if m in self.encounter_by_id]
        if not kinds:
            return ENCOUNTER_UNKNOWN
        if all(k == kinds[0] for k in kinds):
            return kinds[0]
        return ENCOUNTER_UNKNOWN


@dataclass(frozen=True)
class ActivityAssignmentContext:
    """Frozen inputs of the activity-assignment algorithm for one Run."""

    subject_ref: str
    site_ref: str
    planned_activities: Tuple[PlannedActivityDefinition, ...]
    code_aliases: Tuple[OfficialActivityCodeAlias, ...]
    planned_activity_visit_key: Mapping[str, str]
    actual_activities: Tuple[ActualActivityRecord, ...] = ()
    allow_unscheduled_activities: bool = False
    activity_evidence_complete: bool = True


# ---------------------------------------------------------------------------
# Visit assignment (§5.1) -- closed evidence-predicate order, never
# nearest-date / VISITNUM / row-order
# ---------------------------------------------------------------------------

def _is_claim_code(code: str) -> bool:
    """True when a recorded visit code claims a planned visit; unscheduled
    tokens are explicit non-claims (§5.1 unplanned_supported path)."""
    code = (code or "").strip().upper()
    return bool(code) and code not in ("UNSCHEDULED", "UNPLANNED", "N/A")


def _visit_candidate_keys(
    *, bundle: ActualEncounterBundle, ctx: VisitAssignmentContext,
) -> Tuple[List[str], Dict[str, str], Set[str], bool]:
    """Candidate planned-visit keys for one bundle, per-candidate rejected
    reasons, applied predicate ids and a claim-complete flag.

    Never selects a winner by nearest date / VISITNUM / row order; the time
    window only excludes candidates that are determinately impossible
    (bundle entirely before the candidate's window start).
    """
    candidates: List[str] = []
    rejected: Dict[str, str] = {}
    applied: Set[str] = set()
    claim_complete = True

    # Predicate 1 -- verified explicit stable mapping / source parent key.
    explicit_keys: Set[str] = set()
    for mapping in ctx.explicit_mappings:
        if mapping.stable_actual_object_key == bundle.stable_actual_object_key \
                or (mapping.encounter_id
                    and mapping.encounter_id in bundle.member_encounter_ids):
            explicit_keys.add(mapping.planned_visit_key)
    if explicit_keys:
        applied.add(PRED_EXPLICIT_MAPPING)
        if len(explicit_keys) > 1:
            # Conflicting verified mappings: never choose by order/date.
            return [], {}, applied, True
        mapped_key = next(iter(explicit_keys))
        if mapped_key not in ctx.applicable_visit_keys:
            # The record claims a planned visit outside the unique
            # applicable plan: unassigned_inconsistent, never absorbed.
            return [], {mapped_key: REASON_SCHEDULE_MISSING}, applied, True
        return [mapped_key], {}, applied, True

    # Predicate 2 -- official visit code + verified alias mapping.
    codes: Set[str] = set()
    for member_id in bundle.member_encounter_ids:
        encounter = ctx.encounter_by_id.get(member_id)
        code = encounter.recorded_visit_code if encounter else ""
        if _is_claim_code(code):
            codes.add(code)
    official_keys: Set[str] = set()
    code_incomplete = False
    for code in sorted(codes):
        mapped_official: Set[str] = set()
        for mapping in ctx.code_mappings:
            if mapping.recorded_visit_code == code \
                    and mapping.protocol_version == ctx.protocol_version:
                mapped_official.add(mapping.official_visit_code)
        if not mapped_official:
            code_incomplete = True
            continue
        for official in mapped_official:
            for visit in ctx.planned_visits:
                if visit.official_visit_code == official \
                        and visit.planned_visit_key in ctx.applicable_visit_keys:
                    official_keys.add(visit.planned_visit_key)
    if codes and not code_incomplete:
        applied.add(PRED_OFFICIAL_CODE)
        if len(official_keys) > 1:
            # Two planned visits share the official code with equal other
            # evidence -> multi-feasible boundary, never nearest date.
            return sorted(official_keys), {}, applied, True
        if len(official_keys) == 1:
            return [next(iter(official_keys))], {}, applied, True
        # Codes mapped but no applicable visit carries the official code.
        return [], {c: REASON_SCHEDULE_MISSING for c in codes}, applied, \
            ctx.code_coverage_complete
    if codes and code_incomplete:
        applied.add(PRED_OFFICIAL_CODE)
        claim_complete = False
        candidates = sorted(official_keys)

    # No claim (no recorded claim code): every applicable visit is
    # possible under the remaining predicates; the caller decides
    # unplanned/not_evaluable.
    if not codes:
        candidates = sorted(ctx.applicable_visit_keys)

    # Predicate 3 -- phase/episode/modality compatibility.
    applied.add(PRED_PHASE_EPISODE_MODALITY)
    modality = _modality_for_encounter_kind(ctx.bundle_encounter_kind(bundle))
    surviving: List[str] = []
    for key in candidates:
        visit = ctx.visit_by_key(key)
        if visit is None:
            rejected[key] = REASON_SCHEDULE_MISSING
            continue
        reason = ""
        if modality and visit.allowed_modalities \
                and modality not in visit.allowed_modalities:
            reason = REASON_OTHER
        if not reason and bundle.assignment_scope == ASSIGNMENT_SCOPE_MULTI \
                and not visit.merge_or_split_rule.strip():
            reason = REASON_OTHER
        if reason:
            rejected[key] = reason
            continue
        surviving.append(key)
    candidates = surviving

    # Predicate 4 -- composition/scope rules (bundle membership authority
    # already validated by worker_01; nothing further to exclude here).

    # Predicate 5 -- window exclusion (only determinately impossible
    # candidates; never a nearest-date winner).
    if candidates:
        applied.add(PRED_WINDOW_EXCLUSION)
        lo_day, hi_day, complete = _bundle_interval_relation_to_day(bundle)
        if complete and lo_day is not None and hi_day is not None:
            surviving = []
            for key in candidates:
                visit = ctx.visit_by_key(key)
                anchor_day = ctx.anchor_day(key)
                if visit is None or not anchor_day:
                    surviving.append(key)
                    continue
                bounds = window_bounds(window_rule=visit.window_rule,
                                       anchor_day=anchor_day)
                if bounds.determinable and bounds.lo_day:
                    lo_bound = _day_date(bounds.lo_day)
                    if lo_bound is not None and hi_day < lo_bound:
                        # The whole encounter interval precedes the visit's
                        # earliest possible date: impossible candidate.
                        rejected[key] = REASON_TIME_ROLE_MISSING
                        continue
                surviving.append(key)
            candidates = surviving
    return candidates, rejected, applied, claim_complete


def resolve_visit_assignment(
    *, bundle: ActualEncounterBundle, ctx: VisitAssignmentContext,
) -> VisitAssignmentDecision:
    """One bundle -> planned visit assignment decision (§5.1)."""
    claims_visit = any(
        (ctx.encounter_by_id.get(mid) is not None
         and _is_claim_code(ctx.encounter_by_id[mid].recorded_visit_code))
        for mid in bundle.member_encounter_ids)
    # An explicitly unscheduled contact allowed by the plan is decided
    # before candidate resolution (§5.1 unplanned_supported): it never
    # competes with planned visits.
    explicitly_unscheduled = (
        ctx.allow_unscheduled_visits and not claims_visit and any(
            ctx.encounter_by_id.get(mid) is not None
            and (ctx.encounter_by_id[mid].encounter_kind
                 == ENCOUNTER_UNSCHEDULED
                 or not _is_claim_code(
                     ctx.encounter_by_id[mid].recorded_visit_code))
            for mid in bundle.member_encounter_ids))
    candidates, rejected, applied, claim_complete = _visit_candidate_keys(
        bundle=bundle, ctx=ctx)
    evidence_predicates = _canonical_sorted(applied)
    rejected_reasons = _canonical_sorted(rejected.values())

    if explicitly_unscheduled:
        return VisitAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_bundle_id=bundle.bundle_id,
            candidate_planned_visit_ids=(),
            decision_status=VISIT_ASSIGNMENT_UNPLANNED_SUPPORTED,
            evidence_predicate_ids=evidence_predicates,
            rejected_candidate_reasons=rejected_reasons,
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=bundle.source_locator_ids)

    if len(candidates) == 1:
        return VisitAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_bundle_id=bundle.bundle_id,
            candidate_planned_visit_ids=tuple(candidates),
            decision_status=VISIT_ASSIGNMENT_UNIQUE,
            selected_planned_visit_id=candidates[0],
            evidence_predicate_ids=evidence_predicates,
            rejected_candidate_reasons=rejected_reasons,
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=bundle.source_locator_ids)
    if len(candidates) >= 2:
        return VisitAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_bundle_id=bundle.bundle_id,
            candidate_planned_visit_ids=tuple(candidates),
            decision_status=VISIT_ASSIGNMENT_MULTI_FEASIBLE,
            evidence_predicate_ids=evidence_predicates,
            rejected_candidate_reasons=rejected_reasons,
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=bundle.source_locator_ids)

    # Zero feasible candidates.
    evidence_complete = (
        ctx.mapping_coverage_complete and ctx.code_coverage_complete
        and claim_complete)
    if claims_visit and evidence_complete:
        return VisitAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_bundle_id=bundle.bundle_id,
            candidate_planned_visit_ids=(),
            decision_status=VISIT_ASSIGNMENT_UNASSIGNED_INCONSISTENT,
            evidence_predicate_ids=evidence_predicates,
            rejected_candidate_reasons=rejected_reasons,
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=bundle.source_locator_ids)
    return VisitAssignmentDecision(
        assignment_id="", subject_ref=ctx.subject_ref,
        actual_bundle_id=bundle.bundle_id,
        candidate_planned_visit_ids=(),
        decision_status=VISIT_ASSIGNMENT_NOT_EVALUABLE,
        evidence_predicate_ids=evidence_predicates,
        rejected_candidate_reasons=rejected_reasons,
        algorithm_version=D05_UNIT_ALGO_VERSION,
        source_locator_ids=bundle.source_locator_ids)


def resolve_visit_assignments(
    *, bundles: Sequence[ActualEncounterBundle],
    ctx: VisitAssignmentContext,
) -> Tuple[VisitAssignmentDecision, ...]:
    """All bundle -> visit assignment decisions (canonical order)."""
    return tuple(
        resolve_visit_assignment(bundle=bundle, ctx=ctx)
        for bundle in sorted(bundles, key=lambda b: b.bundle_id))


# ---------------------------------------------------------------------------
# Activity assignment (§7) + consumption ledger
# ---------------------------------------------------------------------------

def _activity_candidate_keys(
    *, activity: ActualActivityRecord, visit_key: str,
    planned_activities: Sequence[PlannedActivityDefinition],
    code_aliases: Sequence[OfficialActivityCodeAlias],
) -> Tuple[List[PlannedActivityDefinition], Dict[str, str]]:
    """Candidate planned activities already scoped to the assigned visit."""
    candidates: List[PlannedActivityDefinition] = []
    rejected: Dict[str, str] = {}
    for planned in planned_activities:
        if planned.owner_domain != OWNER_D05:
            continue
        if planned.activity_kind != activity.activity_kind:
            rejected[planned.planned_activity_key] = REASON_OTHER
            continue
        if planned.clinical_domain and activity.clinical_domain \
                and planned.clinical_domain != activity.clinical_domain:
            rejected[planned.planned_activity_key] = REASON_OTHER
            continue
        code_ok = (activity.recorded_activity_code
                   == planned.official_activity_code)
        if not code_ok:
            for alias in code_aliases:
                if alias.recorded_activity_code \
                        == activity.recorded_activity_code \
                        and alias.official_activity_code \
                        == planned.official_activity_code \
                        and alias.clinical_domain == planned.clinical_domain:
                    code_ok = True
                    break
        if not code_ok:
            rejected[planned.planned_activity_key] = REASON_OTHER
            continue
        candidates.append(planned)
    return candidates, rejected


def resolve_activity_assignment(
    *, activity: ActualActivityRecord, visit_key: str,
    ctx: ActivityAssignmentContext,
) -> Tuple[ActivityAssignmentDecision, ...]:
    """One actual activity -> planned activity assignment (§7.1/§7.2).

    Returns one decision for a single obligation and one decision per
    obligation for allowed repeat/resample multi-consumption (the closed
    ``unique`` status carries exactly one selected id; the consumption
    ledger aggregates the shared row, §7.2)."""
    if not visit_key:
        # No determinately assigned visit context for this activity.
        return (ActivityAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_activity_id=activity.actual_activity_id,
            candidate_planned_activity_ids=(),
            decision_status=ACTIVITY_ASSIGNMENT_NOT_EVALUABLE,
            evidence_predicate_ids=(),
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=activity.source_locator_ids),)
    planned_of_visit = [
        a for a in ctx.planned_activities
        if ctx.planned_activity_visit_key.get(a.planned_activity_id, "")
        == visit_key]
    candidates, _ = _activity_candidate_keys(
        activity=activity, visit_key=visit_key,
        planned_activities=planned_of_visit,
        code_aliases=ctx.code_aliases)
    if len(candidates) == 1:
        planned = candidates[0]
        repeat_ok = bool(planned.repeat_rule.strip())
        return (ActivityAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_activity_id=activity.actual_activity_id,
            candidate_planned_activity_ids=(planned.planned_activity_key,),
            decision_status=ACTIVITY_ASSIGNMENT_UNIQUE,
            selected_planned_activity_ids=(planned.planned_activity_key,),
            repeat_or_resample_parent_id=(
                planned.planned_activity_key if repeat_ok else ""),
            repeat_rule_id=(planned.repeat_rule if repeat_ok else ""),
            evidence_predicate_ids=(PRED_ACTIVITY_CLAIM,),
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=activity.source_locator_ids),)
    if len(candidates) >= 2:
        all_repeat = all(bool(c.repeat_rule.strip()) for c in candidates)
        if all_repeat:
            # Allowed repeat/resample multi-consumption: one unique
            # decision per obligation; the ledger row aggregates them with
            # an explicit repeat rule (§7.2, challenges 61/110).
            decisions = []
            for planned in sorted(candidates,
                                  key=lambda c: c.planned_activity_key):
                decisions.append(ActivityAssignmentDecision(
                    assignment_id="", subject_ref=ctx.subject_ref,
                    actual_activity_id=activity.actual_activity_id,
                    candidate_planned_activity_ids=(
                        planned.planned_activity_key,),
                    decision_status=ACTIVITY_ASSIGNMENT_UNIQUE,
                    selected_planned_activity_ids=(
                        planned.planned_activity_key,),
                    repeat_or_resample_parent_id=planned.planned_activity_key,
                    repeat_rule_id=planned.repeat_rule,
                    evidence_predicate_ids=(PRED_ACTIVITY_CLAIM,),
                    algorithm_version=D05_UNIT_ALGO_VERSION,
                    source_locator_ids=activity.source_locator_ids))
            return tuple(decisions)
        return (ActivityAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_activity_id=activity.actual_activity_id,
            candidate_planned_activity_ids=tuple(
                sorted(c.planned_activity_key for c in candidates)),
            decision_status=ACTIVITY_ASSIGNMENT_DUPLICATE_CONSUMPTION,
            selected_planned_activity_ids=tuple(
                sorted(c.planned_activity_key for c in candidates)),
            evidence_predicate_ids=(PRED_ACTIVITY_CLAIM,),
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=activity.source_locator_ids),)
    # Zero candidates.
    unscheduled = ctx.allow_unscheduled_activities and (
        not activity.recorded_activity_code.strip()
        or "UNSCHED" in activity.recorded_activity_code.upper())
    if unscheduled:
        return (ActivityAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_activity_id=activity.actual_activity_id,
            candidate_planned_activity_ids=(),
            decision_status=ACTIVITY_ASSIGNMENT_UNPLANNED_SUPPORTED,
            evidence_predicate_ids=(),
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=activity.source_locator_ids),)
    if ctx.activity_evidence_complete \
            and activity.recorded_activity_code.strip():
        # Complete-evidence mislabel: the record claims a planned activity
        # that no applicable obligation matches.  Status is not_evaluable
        # (the closed activity-status set has no unassigned token) but the
        # reverse-coverage ledger stays open and the actual_assignment unit
        # evaluates positive (the issue predicate is true under every
        # feasible interpretation, §5.1).
        return (ActivityAssignmentDecision(
            assignment_id="", subject_ref=ctx.subject_ref,
            actual_activity_id=activity.actual_activity_id,
            candidate_planned_activity_ids=(),
            decision_status=ACTIVITY_ASSIGNMENT_NOT_EVALUABLE,
            evidence_predicate_ids=(PRED_ACTIVITY_CLAIM,),
            algorithm_version=D05_UNIT_ALGO_VERSION,
            source_locator_ids=activity.source_locator_ids),)
    return (ActivityAssignmentDecision(
        assignment_id="", subject_ref=ctx.subject_ref,
        actual_activity_id=activity.actual_activity_id,
        candidate_planned_activity_ids=(),
        decision_status=ACTIVITY_ASSIGNMENT_NOT_EVALUABLE,
        evidence_predicate_ids=(),
        algorithm_version=D05_UNIT_ALGO_VERSION,
        source_locator_ids=activity.source_locator_ids),)


def resolve_activity_assignments(
    *, activities: Sequence[ActualActivityRecord],
    visit_key_by_activity: Mapping[str, str],
    ctx: ActivityAssignmentContext,
) -> Tuple[ActivityAssignmentDecision, ...]:
    """All actual-activity assignments (canonical order)."""
    decisions: List[ActivityAssignmentDecision] = []
    for activity in sorted(activities, key=lambda a: a.actual_activity_id):
        visit_key = visit_key_by_activity.get(activity.actual_activity_id, "")
        decisions.extend(resolve_activity_assignment(
            activity=activity, visit_key=visit_key, ctx=ctx))
    return tuple(decisions)


def build_consumption_ledgers(
    *,
    assignments: Sequence[ActivityAssignmentDecision],
    planned_activities: Sequence[PlannedActivityDefinition],
    site_ref: str,
) -> Tuple[ActualActivityConsumptionLedger, ...]:
    """Consumption ledgers (actual -> planned index) with reverse coverage
    status; the planned -> actual index is derived by the caller from these
    rows (§7.2)."""
    by_activity: Dict[str, List[ActivityAssignmentDecision]] = {}
    for decision in assignments:
        by_activity.setdefault(decision.actual_activity_id, []).append(decision)
    ledgers: List[ActualActivityConsumptionLedger] = []
    for actual_activity_id in sorted(by_activity):
        decisions = sorted(by_activity[actual_activity_id],
                           key=lambda d: d.assignment_id)
        consuming: Set[str] = set()
        repeat_rules: Set[str] = set()
        for decision in decisions:
            consuming.update(decision.selected_planned_activity_ids)
            if decision.repeat_rule_id:
                repeat_rules.update(decision.repeat_rule_id.split("|"))
        consuming_ids = _canonical_sorted(consuming)
        if not consuming_ids:
            continue  # unplanned/not_evaluable with no consumer
        multiplicity = max(
            1, max((_repeat_multiplicity(r) for r in repeat_rules),
                   default=1))
        if len(consuming_ids) > multiplicity:
            multiplicity = len(consuming_ids)
        repeat_rule_id = "|".join(sorted(repeat_rules))
        closed = len(consuming_ids) <= multiplicity and (
            len(consuming_ids) == 1 or bool(repeat_rule_id))
        ledgers.append(ActualActivityConsumptionLedger(
            ledger_id="", subject_ref=decisions[0].subject_ref,
            site_ref=site_ref, actual_activity_id=actual_activity_id,
            consuming_planned_activity_ids=consuming_ids,
            allowed_multiplicity=multiplicity,
            repeat_rule_id=repeat_rule_id,
            assignment_ids=tuple(sorted(
                d.assignment_id for d in decisions)),
            reverse_coverage_status=(
                REVERSE_COVERAGE_CLOSED if closed else REVERSE_COVERAGE_OPEN),
            source_locator_ids=_canonical_sorted(
                loc for d in decisions for loc in d.source_locator_ids)))
    return tuple(ledgers)


# ---------------------------------------------------------------------------
# Expected-set expansion (§4) and gates
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExpectedSetExpansion:
    """Result of the gate + expected-set phase (§4.3 order)."""

    gates: Tuple[ScheduleGate, ...]
    gate_accounting: Any
    expected_units: Tuple[ScheduleEvaluationUnit, ...]
    expected_set: ExpectedSet
    anchor_refs: Tuple[TypedScheduleAnchorRef, ...]
    anchor_day_by_visit_key: Tuple[Tuple[str, str], ...]
    out_of_cutoff_object_ids: Tuple[str, ...]
    future_obligation_keys: Tuple[str, ...]
    excluded_obligation_keys: Tuple[str, ...]
    visit_assignment_prepass: Tuple[Tuple[str, str], ...]
    # (visit key, bundle id) unique pre-pass candidates used to decide
    # timing/order unit existence; deterministic.
    activity_assignment_prepass: Tuple[Tuple[str, str], ...]
    # (activity id, planned activity key) unique pre-pass candidates.
    scope_decisions: Tuple[ActualRecordScopeDecision, ...]
    cutoff: ClinicalEventCutoff


def _applicability_gate(
    *, decision: VisitScheduleApplicabilityDecision,
) -> ScheduleGate:
    status = decision.decision_status
    decision_status = (
        GATE_DECISION_BOUNDARY
        if status == APPLICABILITY_MULTI_FEASIBLE_BOUNDARY
        else GATE_DECISION_NOT_EVALUABLE)
    return ScheduleGate(
        gate_id="", gate_kind=GATE_APPLICABILITY,
        subject_ref=decision.subject_ref, site_ref=decision.site_ref,
        gate_state=GATE_OPEN, decision_status=decision_status,
        feasible_schedule_ids=decision.feasible_schedule_ids,
        reason_codes=decision.reason_codes or (REASON_VERSION_MISSING,),
        source_locator_ids=decision.source_locator_ids)


def _cutoff_scope_gates(
    *, scope_decisions: Sequence[ActualRecordScopeDecision],
    subject_ref: str, site_ref: str,
) -> Tuple[ScheduleGate, ...]:
    gates: List[ScheduleGate] = []
    seen: Set[str] = set()
    for decision in scope_decisions:
        if decision.scope_status not in (SCOPE_BOUNDARY, SCOPE_NOT_EVALUABLE):
            continue
        if decision.scope_decision_id in seen:
            continue  # one gate per stable decision per Run
        seen.add(decision.scope_decision_id)
        decision_status = (
            GATE_DECISION_BOUNDARY
            if decision.scope_status == SCOPE_BOUNDARY
            else GATE_DECISION_NOT_EVALUABLE)
        gates.append(ScheduleGate(
            gate_id="", gate_kind=GATE_CUTOFF_SCOPE,
            subject_ref=subject_ref, site_ref=site_ref,
            gate_state=GATE_OPEN, decision_status=decision_status,
            reason_codes=decision.reason_codes,
            source_locator_ids=decision.source_locator_ids))
    return tuple(gates)


def _visit_actual_day(bundle: ActualEncounterBundle) -> str:
    """The bundle's derived start day (chained-anchor propagation source);
    empty when the bundle is not day-dated."""
    lo, _, complete = _bundle_interval_relation_to_day(bundle)
    if not complete or lo is None:
        return ""
    return lo.isoformat()


def expand_expected_set(
    *,
    run_id: str,
    project_ref: str,
    subject_ref: str,
    site_ref: str,
    snapshot_as_of: SnapshotAsOf,
    clinical_event_cutoff: ClinicalEventCutoff,
    applicability_decision: VisitScheduleApplicabilityDecision,
    planned_visits: Sequence[PlannedVisitDefinition],
    planned_activities: Sequence[PlannedActivityDefinition],
    maturity_rules: Mapping[str, EvaluationMaturityRule],
    anchor_bindings: Sequence[AnchorBindingRequest],
    scope_decisions: Sequence[ActualRecordScopeDecision],
    obligation_applicability: Mapping[str, ObligationApplicability],
    schedule_consistency_issues: Sequence[ScheduleConsistencyIssue],
    activity_window_rules: Mapping[str, VisitWindowRule],
    visit_assignment_ctx: VisitAssignmentContext,
    activity_assignment_ctx: ActivityAssignmentContext,
    bundles: Sequence[ActualEncounterBundle],
    prior_resolved_gates: Sequence[ScheduleGate] = (),
    chained_anchor_prior_day_by_key: Optional[
        Mapping[str, str]] = None,
) -> ExpectedSetExpansion:
    """Gate + expected-set expansion in the frozen §4.3 order.

    ``chained_anchor_prior_day_by_key`` maps a planned_visit_key to its
    complete actual-visit day considering **all** bundles (in-scope and
    out-of-cutoff): an out-of-cutoff actual record still proves a prior
    visit occurred as a chained-anchor interpretation (§5.3), even though
    it never enters the L1 assignment (the two are orthogonal).  When two
    or more distinct prior visits at the immediately-preceding order level
    each carry a complete interpretation, the chained anchor is ambiguous
    and resolves to a single boundary ``GATE_ANCHOR`` (challenge 102),
    not a nearest-date winner.
    """
    gates: List[ScheduleGate] = list(prior_resolved_gates)
    cutoff_day = _day_date(clinical_event_cutoff.cutoff)

    # 1. Applicability gate (subject level).
    if applicability_decision.decision_status != APPLICABILITY_UNIQUE_ACTIVE:
        gates.append(_applicability_gate(decision=applicability_decision))
        expected_set = ExpectedSet.from_units([], domain_id=D05_DOMAIN,
                                              run_id=run_id)
        accounting = validate_gate_run_accounting(gates=gates, run_id=run_id)
        return ExpectedSetExpansion(
            gates=tuple(gates), gate_accounting=accounting,
            expected_units=(), expected_set=expected_set, anchor_refs=(),
            anchor_day_by_visit_key=(), out_of_cutoff_object_ids=(),
            future_obligation_keys=(), excluded_obligation_keys=(),
            visit_assignment_prepass=(), activity_assignment_prepass=(),
            scope_decisions=tuple(scope_decisions),
            cutoff=clinical_event_cutoff)

    applicable_visit_keys = visit_assignment_ctx.applicable_visit_keys

    # 2. Owner routing: unresolved owner -> one routing gate; producer-owned
    # activities are excluded from the D05 expected-set (§2.3).
    routing_activity_keys: Set[str] = set()
    producer_owned_keys: Set[str] = set()
    for activity in planned_activities:
        if activity.owner_domain == OWNER_UNRESOLVED:
            routing_activity_keys.add(activity.planned_activity_key)
        elif activity.owner_domain != OWNER_D05:
            producer_owned_keys.add(activity.planned_activity_key)
    if routing_activity_keys:
        gates.append(ScheduleGate(
            gate_id="", gate_kind=GATE_ROUTING,
            subject_ref=subject_ref, site_ref=site_ref,
            gate_state=GATE_OPEN, decision_status=GATE_DECISION_NOT_EVALUABLE,
            feasible_owner_domains=(OWNER_UNRESOLVED,),
            affected_planned_activity_keys=_canonical_sorted(
                routing_activity_keys),
            reason_codes=(REASON_ROUTING_COMPETITION,),
            source_locator_ids=()))
    excluded_keys = set(routing_activity_keys) | set(producer_owned_keys)

    # 3. Cutoff-scope gates from the scope decisions.
    gates.extend(_cutoff_scope_gates(scope_decisions=scope_decisions,
                                     subject_ref=subject_ref,
                                     site_ref=site_ref))

    # 4. Anchor resolution (fixed / producer / chained) -- §4.3 order.
    # Chained anchors need the prior visit's unique *actual* date, so a
    # minimal bundle->visit pre-pass runs first (same assignment algorithm;
    # only fixed anchors are available at this stage, which is exactly the
    # §4.3 "unique resolve" requirement -- never a nearest-date shortcut).
    actual_day_by_visit_key: Dict[str, str] = {}
    for bundle in sorted(bundles, key=lambda b: b.bundle_id):
        decision = resolve_visit_assignment(bundle=bundle, ctx=visit_assignment_ctx)
        if decision.decision_status == VISIT_ASSIGNMENT_UNIQUE:
            day = _visit_actual_day(bundle)
            if day:
                actual_day_by_visit_key.setdefault(
                    decision.selected_planned_visit_id, day)

    binding_by_key = {b.planned_visit_key: b for b in anchor_bindings}
    anchor_by_key: Dict[str, TypedScheduleAnchorRef] = {}
    anchor_day_by_key: Dict[str, str] = {}
    anchor_gate_keys: Set[str] = set()
    anchor_gates: List[ScheduleGate] = []
    ordered_keys = sorted(
        applicable_visit_keys,
        key=lambda k: _order_key(visit_assignment_ctx.visit_by_key(k).planned_order)
        if visit_assignment_ctx.visit_by_key(k) else (0,))
    resolved_anchor_refs: List[TypedScheduleAnchorRef] = []
    for visit_key in ordered_keys:
        visit = visit_assignment_ctx.visit_by_key(visit_key)
        if visit is None:
            continue
        binding = binding_by_key.get(visit_key)
        if binding is None:
            anchor_gate_keys.add(visit_key)
            continue
        relation = binding.relation_type
        if relation == RELATION_PRIOR_ACTUAL_VISIT:
            prior_level_keys = [
                k for k in ordered_keys
                if _order_key(
                    visit_assignment_ctx.visit_by_key(k).planned_order)
                < _order_key(visit.planned_order)]
            if prior_level_keys:
                max_prior_order = max(
                    _order_key(
                        visit_assignment_ctx.visit_by_key(k).planned_order)
                    for k in prior_level_keys)
                prior_level_keys = [
                    k for k in prior_level_keys
                    if _order_key(
                        visit_assignment_ctx.visit_by_key(k).planned_order)
                    == max_prior_order]
            # Complete feasible prior interpretations: each distinct prior
            # visit at the immediately-preceding order level with a
            # locatable actual-visit day (in-scope or out-of-cutoff).
            feasible_priors: List[str] = []
            for prior_key in prior_level_keys:
                day = actual_day_by_visit_key.get(prior_key, "")
                if not day:
                    day = (chained_anchor_prior_day_by_key or {}).get(
                        prior_key, "")
                if day:
                    feasible_priors.append(prior_key)
            if len(feasible_priors) >= 2:
                # Two+ complete feasible prior interpretations -> the
                # chained anchor is ambiguous: one boundary anchor gate
                # with the feasible anchor refs (challenge 102); never a
                # nearest-date / last-in-order winner.
                feasible_refs: List[TypedScheduleAnchorRef] = []
                for prior_key in sorted(feasible_priors):
                    prior_day = (actual_day_by_visit_key.get(prior_key, "")
                                 or (chained_anchor_prior_day_by_key or {}).get(
                                     prior_key, ""))
                    prior_binding = binding_by_key.get(prior_key)
                    # Each chained-anchor interpretation is one distinct
                    # prior visit occurrence; the episode discriminator
                    # keeps the two interpretations' stable anchor ids
                    # distinct (the anchor date is lineage-only, never a
                    # stable-id dimension, so the prior visit identity is
                    # carried here).
                    feasible_refs.append(TypedScheduleAnchorRef(
                        anchor_ref_id="", producer_domain="",
                        producer_unit_id="", stable_source_event_key="",
                        content_hash="", subject_ref=subject_ref,
                        site_ref=site_ref,
                        phase=prior_binding.phase if prior_binding else "",
                        episode_id=("prior:" + prior_key + ":" + prior_day),
                        anchor_start=prior_day, anchor_end=prior_day,
                        date_precision=PRECISION_DAY, timezone="",
                        relation_type=RELATION_PRIOR_ACTUAL_VISIT,
                        source_locator_ids=(
                            prior_binding.source_locator_ids
                            if prior_binding else ())))
                anchor_gate_keys.add(visit_key)
                anchor_gates.append(ScheduleGate(
                    gate_id="", gate_kind=GATE_ANCHOR,
                    subject_ref=subject_ref, site_ref=site_ref,
                    gate_state=GATE_OPEN,
                    decision_status=GATE_DECISION_BOUNDARY,
                    feasible_anchor_ref_ids=tuple(sorted(
                        r.anchor_ref_id for r in feasible_refs)),
                    affected_planned_visit_keys=(visit_key,),
                    affected_planned_activity_keys=_canonical_sorted(
                        binding.affected_planned_activity_keys),
                    missing_evidence_roles=(ANCHOR_ROLE_VISIT_SCHEDULE,),
                    reason_codes=(REASON_MULTIPLE_FEASIBLE,),
                    source_locator_ids=binding.source_locator_ids))
                resolved_anchor_refs.extend(feasible_refs)
                continue
            prior_day = ""
            if len(feasible_priors) == 1:
                prior_key = feasible_priors[0]
                prior_day = (actual_day_by_visit_key.get(prior_key, "")
                             or (chained_anchor_prior_day_by_key or {}).get(
                                 prior_key, ""))
            if not prior_day:
                anchor_gate_keys.add(visit_key)
                anchor_gates.append(_chained_anchor_gate(
                    visit_key=visit_key, subject_ref=subject_ref,
                    site_ref=site_ref,
                    affected_activity_keys=binding.affected_planned_activity_keys))
                continue
            ref = TypedScheduleAnchorRef(
                anchor_ref_id="", producer_domain="", producer_unit_id="",
                stable_source_event_key="", content_hash="",
                subject_ref=subject_ref, site_ref=site_ref,
                phase=binding.phase, episode_id=binding.episode_id,
                anchor_start=prior_day, anchor_end=prior_day,
                date_precision=PRECISION_DAY, timezone="",
                relation_type=RELATION_PRIOR_ACTUAL_VISIT,
                source_locator_ids=binding.source_locator_ids)
            anchor_by_key[visit_key] = ref
            anchor_day_by_key[visit_key] = prior_day
            resolved_anchor_refs.append(ref)
            continue
        if relation == RELATION_FIXED_REFERENCE:
            outcome = bind_typed_schedule_anchor(
                relation_type=relation, subject_ref=subject_ref,
                site_ref=site_ref, anchor_start=binding.anchor_day,
                anchor_end=binding.anchor_day,
                date_precision=PRECISION_DAY, timezone="",
                phase=binding.phase, episode_id=binding.episode_id,
                affected_planned_visit_keys=(visit_key,),
                affected_planned_activity_keys=binding.affected_planned_activity_keys,
                source_locators=())
        else:
            outcome = bind_typed_schedule_anchor(
                relation_type=relation, subject_ref=subject_ref,
                site_ref=site_ref, producer_ref=binding.producer_ref,
                producer_domain=binding.producer_domain,
                producer_unit_id=binding.producer_unit_id,
                stable_source_event_key=binding.stable_source_event_key,
                content_hash=binding.content_hash, phase=binding.phase,
                episode_id=binding.episode_id,
                anchor_start=binding.anchor_start,
                anchor_end=binding.anchor_end,
                date_precision=binding.date_precision,
                timezone=binding.timezone,
                affected_planned_visit_keys=(visit_key,),
                affected_planned_activity_keys=binding.affected_planned_activity_keys,
                source_locators=())
        if outcome.is_bound:
            ref = outcome.anchor_ref
            assert ref is not None
            anchor_by_key[visit_key] = ref
            anchor_day_by_key[visit_key] = ref.anchor_start
            resolved_anchor_refs.append(ref)
        else:
            gate = outcome.gate
            assert gate is not None
            anchor_gate_keys.add(visit_key)
            anchor_gates.append(gate)
    gates.extend(anchor_gates)
    for key in anchor_gate_keys:
        binding = binding_by_key.get(key)
        if binding is not None:
            excluded_keys.update(binding.affected_planned_activity_keys)

    # 5. Expected-unit expansion over applicable, anchored, matured
    # obligations.  Out-of-cutoff records never enter the medical
    # denominator (§4.2); they are projected as Journey future context only.
    out_of_cutoff_ids = tuple(sorted(
        d.actual_object_id for d in scope_decisions
        if d.scope_status == SCOPE_OUT_OF_CUTOFF))

    units: List[ScheduleEvaluationUnit] = []
    future_keys: Set[str] = set()
    visit_prepass: List[Tuple[str, str]] = []

    # Pre-pass visit candidates: unique dated bundle -> visit key (also
    # decides timing/order unit existence; deterministic).
    for bundle in sorted(bundles, key=lambda b: b.bundle_id):
        decision = resolve_visit_assignment(bundle=bundle, ctx=visit_assignment_ctx)
        if decision.decision_status == VISIT_ASSIGNMENT_UNIQUE:
            visit_prepass.append(
                (decision.selected_planned_visit_id, bundle.bundle_id))

    for visit in sorted(planned_visits, key=lambda v: v.planned_visit_key):
        key = visit.planned_visit_key
        if key not in applicable_visit_keys:
            continue
        if key in excluded_keys or key in anchor_gate_keys:
            continue
        anchor_day = anchor_day_by_key.get(key, "")
        occurrence_rule = maturity_rules.get(UNIT_VISIT_OCCURRENCE)
        occurrence_unit = _build_visit_unit(
            unit_kind=UNIT_VISIT_OCCURRENCE, visit=visit,
            project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, rule=occurrence_rule,
            anchor_day=anchor_day, window_rule=visit.window_rule,
            anchor_episode_id=anchor_by_key.get(key, "").episode_id
            if key in anchor_by_key else "",
            cutoff_day=cutoff_day)
        if occurrence_unit is not None:
            units.append(occurrence_unit)
        else:
            future_keys.add(key)
        assigned_bundle = next(
            (bundle_id for vk, bundle_id in visit_prepass if vk == key), "")
        if assigned_bundle:
            timing_rule = maturity_rules.get(UNIT_VISIT_TIMING)
            timing_unit = _build_visit_unit(
                unit_kind=UNIT_VISIT_TIMING, visit=visit,
                project_ref=project_ref, subject_ref=subject_ref,
                site_ref=site_ref, rule=timing_rule,
                anchor_day=anchor_day, window_rule=visit.window_rule,
                anchor_episode_id=anchor_by_key.get(key, "").episode_id
                if key in anchor_by_key else "",
                cutoff_day=cutoff_day)
            if timing_unit is not None:
                units.append(timing_unit)
        if visit.visit_kind == VISIT_SCHEDULED:
            predecessor = _predecessor_visit(visit, planned_visits)
            if predecessor is not None and any(
                    vk == predecessor.planned_visit_key
                    for vk, _ in visit_prepass):
                order_rule = maturity_rules.get(UNIT_VISIT_ORDER)
                order_unit = _build_visit_unit(
                    unit_kind=UNIT_VISIT_ORDER, visit=visit,
                    project_ref=project_ref, subject_ref=subject_ref,
                    site_ref=site_ref, rule=order_rule,
                    anchor_day=anchor_day, window_rule=visit.window_rule,
                    anchor_episode_id=anchor_by_key.get(key, "").episode_id
                    if key in anchor_by_key else "",
                    cutoff_day=cutoff_day)
                if order_unit is not None:
                    units.append(order_unit)

    # Activity units under anchored, applicable visits.
    visit_keys_set = set(applicable_visit_keys) - excluded_keys - anchor_gate_keys
    activity_prepass: List[Tuple[str, str]] = []
    for activity in planned_activities:
        if activity.owner_domain != OWNER_D05:
            continue
        if activity.planned_activity_key in excluded_keys:
            continue
        visit_key = _visit_key_of_activity(activity, planned_visits)
        if visit_key is None or visit_key not in visit_keys_set:
            continue
        anchor_day = anchor_day_by_key.get(visit_key, "")
        window_rule = activity_window_rules.get(activity.planned_activity_key)
        occurrence_rule = maturity_rules.get(UNIT_ACTIVITY_OCCURRENCE)
        occurrence_unit = _build_activity_unit(
            unit_kind=UNIT_ACTIVITY_OCCURRENCE, activity=activity,
            project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, rule=occurrence_rule,
            anchor_day=anchor_day, window_rule=window_rule,
            anchor_episode_id=anchor_by_key.get(visit_key, "").episode_id
            if visit_key in anchor_by_key else "",
            cutoff_day=cutoff_day)
        if occurrence_unit is not None:
            units.append(occurrence_unit)
        else:
            future_keys.add(activity.planned_activity_key)
        timing_rule = maturity_rules.get(UNIT_ACTIVITY_TIMING)
        if timing_rule is not None and window_rule is not None \
                and _activity_prepass_unique(
                    activity=activity, visit_key=visit_key,
                    activity_assignment_ctx=activity_assignment_ctx):
            timing_unit = _build_activity_unit(
                unit_kind=UNIT_ACTIVITY_TIMING, activity=activity,
                project_ref=project_ref, subject_ref=subject_ref,
                site_ref=site_ref, rule=timing_rule,
                anchor_day=anchor_day, window_rule=window_rule,
                anchor_episode_id=anchor_by_key.get(visit_key, "").episode_id
                if visit_key in anchor_by_key else "",
                cutoff_day=cutoff_day)
            if timing_unit is not None:
                units.append(timing_unit)
                for actual in activity_assignment_ctx.actual_activities:
                    planned_of_visit = [
                        a for a in activity_assignment_ctx.planned_activities
                        if activity_assignment_ctx.planned_activity_visit_key.get(
                            a.planned_activity_id, "") == visit_key]
                    cands, _ = _activity_candidate_keys(
                        activity=actual, visit_key=visit_key,
                        planned_activities=planned_of_visit,
                        code_aliases=activity_assignment_ctx.code_aliases)
                    if len(cands) == 1 \
                            and cands[0].planned_activity_key \
                            == activity.planned_activity_key:
                        activity_prepass.append(
                            (actual.actual_activity_id,
                             activity.planned_activity_key))
                        break

    # Actual-assignment units for problematic in-scope actual objects.
    for bundle in sorted(bundles, key=lambda b: b.bundle_id):
        decision = resolve_visit_assignment(bundle=bundle, ctx=visit_assignment_ctx)
        if decision.decision_status not in (
                VISIT_ASSIGNMENT_MULTI_FEASIBLE,
                VISIT_ASSIGNMENT_UNASSIGNED_INCONSISTENT,
                VISIT_ASSIGNMENT_NOT_EVALUABLE):
            continue
        unit = _build_assignment_unit(
            unit_kind=UNIT_ACTUAL_ASSIGNMENT,
            stable_actual_object_key=bundle.stable_actual_object_key,
            project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, rule_id="d05-assignment-v1",
            anchor_episode_id="")
        if unit is not None:
            units.append(unit)

    # Activity-level reverse check units (duplicate consumption /
    # complete-evidence mislabel; §7.2) -- decided by the same assignment
    # algorithm over the pre-pass visit context.
    bundle_by_encounter = {
        member_id: b.bundle_id
        for b in bundles for member_id in b.member_encounter_ids}
    visit_by_bundle = {
        d.actual_bundle_id: d.selected_planned_visit_id
        for d in (resolve_visit_assignment(bundle=b, ctx=visit_assignment_ctx)
                  for b in bundles)
        if d.decision_status == VISIT_ASSIGNMENT_UNIQUE}
    for actual in sorted(activity_assignment_ctx.actual_activities,
                         key=lambda a: a.actual_activity_id):
        visit_key = ""
        for encounter_id in actual.encounter_refs:
            bundle_id = bundle_by_encounter.get(encounter_id, "")
            if bundle_id and bundle_id in visit_by_bundle:
                visit_key = visit_by_bundle[bundle_id]
                break
        if not visit_key:
            continue
        planned_of_visit = [
            a for a in planned_activities
            if activity_assignment_ctx.planned_activity_visit_key.get(
                a.planned_activity_id, "") == visit_key]
        candidates, _ = _activity_candidate_keys(
            activity=actual, visit_key=visit_key,
            planned_activities=planned_of_visit,
            code_aliases=activity_assignment_ctx.code_aliases)
        problematic = (
            (len(candidates) >= 2
             and not all(bool(c.repeat_rule.strip()) for c in candidates))
            or (len(candidates) == 0
                and actual.recorded_activity_code.strip()
                and "UNSCHED" not in actual.recorded_activity_code.upper()
                and activity_assignment_ctx.activity_evidence_complete))
        if not problematic:
            continue
        unit = _build_assignment_unit(
            unit_kind=UNIT_ACTUAL_ASSIGNMENT,
            stable_actual_object_key=actual.stable_actual_object_key,
            project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, rule_id="d05-assignment-v1",
            anchor_episode_id="")
        if unit is not None:
            units.append(unit)

    # Schedule-consistency units for declared plan self-inconsistencies.
    for issue in schedule_consistency_issues:
        unit = _build_assignment_unit(
            unit_kind=UNIT_SCHEDULE_CONSISTENCY,
            stable_actual_object_key="",
            project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, rule_id="|".join(issue.rule_ids),
            anchor_episode_id="")
        if unit is not None:
            units.append(unit)

    units = _dedupe_units(units)
    expected_set = ExpectedSet.from_units(units, domain_id=D05_DOMAIN,
                                          run_id=run_id)
    accounting = validate_gate_run_accounting(gates=gates, run_id=run_id)
    return ExpectedSetExpansion(
        gates=tuple(gates), gate_accounting=accounting,
        expected_units=tuple(units), expected_set=expected_set,
        anchor_refs=tuple(resolved_anchor_refs),
        anchor_day_by_visit_key=tuple(sorted(anchor_day_by_key.items())),
        out_of_cutoff_object_ids=out_of_cutoff_ids,
        future_obligation_keys=tuple(sorted(future_keys)),
        excluded_obligation_keys=tuple(sorted(excluded_keys)),
        visit_assignment_prepass=tuple(sorted(visit_prepass)),
        activity_assignment_prepass=tuple(sorted(activity_prepass)),
        scope_decisions=tuple(scope_decisions),
        cutoff=clinical_event_cutoff)


def _chained_anchor_gate(
    *, visit_key: str, subject_ref: str, site_ref: str,
    affected_activity_keys: Sequence[str],
) -> ScheduleGate:
    return ScheduleGate(
        gate_id="", gate_kind=GATE_ANCHOR, subject_ref=subject_ref,
        site_ref=site_ref, gate_state=GATE_OPEN,
        decision_status=GATE_DECISION_NOT_EVALUABLE,
        affected_planned_visit_keys=(visit_key,),
        affected_planned_activity_keys=_canonical_sorted(
            affected_activity_keys),
        missing_evidence_roles=(ANCHOR_ROLE_VISIT_SCHEDULE,),
        reason_codes=(REASON_ANCHOR_MISSING,),
        source_locator_ids=())


def _predecessor_visit(
    visit: PlannedVisitDefinition,
    planned_visits: Sequence[PlannedVisitDefinition],
) -> Optional[PlannedVisitDefinition]:
    """The immediately previous scheduled visit by explicit planned_order
    (VISITNUM is never order authority)."""
    order = _order_key(visit.planned_order)
    candidates = [
        v for v in planned_visits
        if v.visit_kind == VISIT_SCHEDULED
        and v.planned_visit_key != visit.planned_visit_key
        and _order_key(v.planned_order) < order]
    if not candidates:
        return None
    return max(candidates, key=lambda v: _order_key(v.planned_order))


def _visit_key_of_activity(
    activity: PlannedActivityDefinition,
    planned_visits: Sequence[PlannedVisitDefinition],
) -> Optional[str]:
    for visit in planned_visits:
        if visit.planned_visit_id == activity.planned_visit_id:
            return visit.planned_visit_key
    return None


def _activity_prepass_unique(
    *, activity: PlannedActivityDefinition, visit_key: str,
    activity_assignment_ctx: ActivityAssignmentContext,
) -> bool:
    """True when any in-scope actual activity uniquely maps to this planned
    activity under the assignment algorithm (timing-unit existence)."""
    planned_of_visit = [
        a for a in activity_assignment_ctx.planned_activities
        if activity_assignment_ctx.planned_activity_visit_key.get(
            a.planned_activity_id, "") == visit_key]
    for actual in activity_assignment_ctx.actual_activities:
        if actual.activity_kind != activity.activity_kind:
            continue
        candidates, _ = _activity_candidate_keys(
            activity=actual, visit_key=visit_key,
            planned_activities=planned_of_visit,
            code_aliases=activity_assignment_ctx.code_aliases)
        if len(candidates) == 1 \
                and candidates[0].planned_activity_key \
                == activity.planned_activity_key:
            return True
    return False


def _build_visit_unit(
    *, unit_kind: str, visit: PlannedVisitDefinition,
    project_ref: str, subject_ref: str, site_ref: str,
    rule: Optional[EvaluationMaturityRule],
    anchor_day: str, window_rule: VisitWindowRule,
    anchor_episode_id: str, cutoff_day: Optional[datetime.date],
) -> Optional[ScheduleEvaluationUnit]:
    """One visit unit; None when the obligation is not matured at cutoff
    (future plan-axis only, §4.2)."""
    if rule is None:
        # Missing maturity rule: not_evaluable unit, never a default
        # window-latest endpoint (challenge 113).
        return _unit_for_kind(
            unit_kind=unit_kind, project_ref=project_ref,
            subject_ref=subject_ref, site_ref=site_ref,
            planned_visit=visit, planned_activity=None,
            rule_id=visit.window_rule.window_rule_id,
            rule_version=visit.window_rule.rule_version,
            evaluation_window_id=_window_id(visit.window_rule,
                                            anchor_episode_id),
            anchor_episode_id=anchor_episode_id)
    if not anchor_day:
        return None  # anchor gate already accounts for the obligation
    window_id = _window_id(window_rule, anchor_episode_id)
    unit = _unit_for_kind(
        unit_kind=unit_kind, project_ref=project_ref,
        subject_ref=subject_ref, site_ref=site_ref,
        planned_visit=visit, planned_activity=None,
        rule_id=window_rule.window_rule_id,
        rule_version=window_rule.rule_version,
        evaluation_window_id=window_id,
        anchor_episode_id=anchor_episode_id)
    if unit is None:
        return None
    maturity_day = maturity_day_for(
        maturity_rule=rule, anchor_day=anchor_day,
        window_rule=window_rule)
    if maturity_day is None:
        return unit  # not_evaluable (maturity cannot be computed)
    maturity = _day_date(maturity_day)
    if maturity is None:
        return unit
    if cutoff_day is not None and maturity > cutoff_day:
        return None  # future obligation: plan axis only
    return unit


def _build_activity_unit(
    *, unit_kind: str, activity: PlannedActivityDefinition,
    project_ref: str, subject_ref: str, site_ref: str,
    rule: Optional[EvaluationMaturityRule],
    anchor_day: str, window_rule: Optional[VisitWindowRule],
    anchor_episode_id: str, cutoff_day: Optional[datetime.date],
) -> Optional[ScheduleEvaluationUnit]:
    rule_id = activity.timing_rule or activity.definition_hash
    if rule is None:
        return _unit_for_kind(
            unit_kind=unit_kind, project_ref=project_ref,
            subject_ref=subject_ref, site_ref=site_ref,
            planned_visit=None, planned_activity=activity,
            rule_id=rule_id, rule_version=D05_RULE_LINEAGE_DEFAULT,
            evaluation_window_id="", anchor_episode_id=anchor_episode_id)
    if not anchor_day or window_rule is None:
        # Anchor/activity window missing: keep a not_evaluable occurrence
        # unit (gap) instead of silently defaulting a window.
        return _unit_for_kind(
            unit_kind=unit_kind, project_ref=project_ref,
            subject_ref=subject_ref, site_ref=site_ref,
            planned_visit=None, planned_activity=activity,
            rule_id=rule_id, rule_version=D05_RULE_LINEAGE_DEFAULT,
            evaluation_window_id="", anchor_episode_id=anchor_episode_id)
    window_id = _window_id(window_rule, anchor_episode_id)
    unit = _unit_for_kind(
        unit_kind=unit_kind, project_ref=project_ref,
        subject_ref=subject_ref, site_ref=site_ref,
        planned_visit=None, planned_activity=activity,
        rule_id=window_rule.window_rule_id,
        rule_version=window_rule.rule_version,
        evaluation_window_id=window_id,
        anchor_episode_id=anchor_episode_id)
    if unit is None:
        return None
    maturity_day = maturity_day_for(
        maturity_rule=rule, anchor_day=anchor_day, window_rule=window_rule)
    if maturity_day is None:
        return unit
    maturity = _day_date(maturity_day)
    if maturity is None:
        return unit
    if cutoff_day is not None and maturity > cutoff_day:
        return None
    return unit


def _unit_for_kind(
    *, unit_kind: str, project_ref: str, subject_ref: str, site_ref: str,
    planned_visit: Optional[PlannedVisitDefinition],
    planned_activity: Optional[PlannedActivityDefinition],
    rule_id: str, rule_version: str, evaluation_window_id: str,
    anchor_episode_id: str,
) -> Optional[ScheduleEvaluationUnit]:
    try:
        return ScheduleEvaluationUnit(
            unit_id="", project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, unit_kind=unit_kind,
            planned_visit_key=planned_visit.planned_visit_key
            if planned_visit else "",
            planned_activity_key=planned_activity.planned_activity_key
            if planned_activity else "",
            evaluation_window_id=evaluation_window_id,
            anchor_episode_id=anchor_episode_id,
            rule_id=rule_id, rule_version=rule_version,
            planned_visit_id=planned_visit.planned_visit_id
            if planned_visit else "",
            planned_activity_id=planned_activity.planned_activity_id
            if planned_activity else "")
    except ScheduleSliceError:
        return None


def _build_assignment_unit(
    *, unit_kind: str, stable_actual_object_key: str,
    project_ref: str, subject_ref: str, site_ref: str,
    rule_id: str, anchor_episode_id: str,
) -> Optional[ScheduleEvaluationUnit]:
    try:
        return ScheduleEvaluationUnit(
            unit_id="", project_ref=project_ref, subject_ref=subject_ref,
            site_ref=site_ref, unit_kind=unit_kind,
            stable_actual_object_key=stable_actual_object_key,
            evaluation_window_id="", anchor_episode_id=anchor_episode_id,
            rule_id=rule_id, rule_version=D05_UNIT_ALGO_VERSION)
    except ScheduleSliceError:
        return None


def _window_id(window_rule: VisitWindowRule, anchor_episode_id: str) -> str:
    return schedule_evaluation_window_id(
        anchor_kind=window_rule.anchor_kind,
        anchor_source_role=window_rule.anchor_source_role,
        calendar_semantics=window_rule.calendar_semantics,
        study_day_zero_exists=window_rule.study_day_zero_exists,
        lower_offset=window_rule.lower_offset,
        upper_offset=window_rule.upper_offset,
        lower_endpoint_inclusive=window_rule.lower_endpoint_inclusive,
        upper_endpoint_inclusive=window_rule.upper_endpoint_inclusive,
        grace_period=window_rule.grace_period,
        date_precision=window_rule.date_precision,
        timezone=window_rule.timezone,
        propagation_rule=window_rule.propagation_rule,
        anchor_episode_id=anchor_episode_id)


def _dedupe_units(
    units: Sequence[ScheduleEvaluationUnit],
) -> List[ScheduleEvaluationUnit]:
    seen: Set[str] = set()
    result: List[ScheduleEvaluationUnit] = []
    for unit in units:
        if unit.unit_id in seen:
            continue
        seen.add(unit.unit_id)
        result.append(unit)
    return result


# ---------------------------------------------------------------------------
# Unit evaluation (§8) -- five exclusive L1 dispositions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class D05UnitResult:
    """The evaluation outcome of one D05 unit.

    Satisfies the neutral ``RiskDomainUnitResult`` protocol (contracts.py)
    and materializes a full :class:`UnitEvaluation` for the shared
    ``CoverageLedger``.
    """

    unit_id: str
    subject_ref: str
    site_ref: str
    unit_kind: str
    planned_visit_key: str = ""
    planned_activity_key: str = ""
    stable_actual_object_key: str = ""
    l1_disposition: str = L1Disposition.NOT_EVALUABLE
    monitoring_priority: str = _PRIORITY_UNKNOWN
    l0_status: str = L0CoverageStatus.COVERED
    positive_subtype: str = ""
    audience_label: str = ""
    query_context: str = ""
    not_evaluable_reason: str = ""
    boundary_reason: str = ""
    evaluation_window_id: str = ""
    rule_id: str = ""
    rule_version: str = D05_RULE_LINEAGE_DEFAULT
    anchor_kind: str = ""
    anchor_start: str = ""
    anchor_end: str = ""
    window_start: str = ""
    window_end: str = ""
    precision: str = PRECISION_DAY
    actual_start: str = ""
    actual_end: str = ""
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    risk_candidate_refs: Tuple[RiskCandidateRef, ...] = ()
    risk_instance_refs: Tuple[RiskInstanceRef, ...] = ()
    evidence: Tuple[EvidenceItem, ...] = ()
    source_record_refs: Tuple[SourceRecordRef, ...] = ()
    query_refs: Tuple[QueryDraftRef, ...] = ()
    coverage_gap_notices: Tuple[VisitCoverageGapNotice, ...] = ()
    classifier: str = ""
    stable_core: str = ""
    rights_or_safety_critical: bool = False
    machine_close_forbidden: bool = False
    priority_reason_codes: Tuple[str, ...] = ()
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.l1_disposition not in L1Disposition.ALL:
            raise VisitScheduleEvaluatorError(
                f"D05UnitResult.l1_disposition={self.l1_disposition!r} "
                f"invalid")
        if self.monitoring_priority not in VALID_MONITORING_PRIORITIES:
            raise VisitScheduleEvaluatorError(
                f"D05UnitResult.monitoring_priority="
                f"{self.monitoring_priority!r} invalid")
        if self.l0_status not in L0CoverageStatus.ALL_STATUSES:
            raise VisitScheduleEvaluatorError(
                f"D05UnitResult.l0_status={self.l0_status!r} invalid")
        if self.positive_subtype and \
                self.positive_subtype not in POSITIVE_SUBTYPES:
            raise VisitScheduleEvaluatorError(
                f"D05UnitResult.positive_subtype="
                f"{self.positive_subtype!r} invalid")
        if self.query_context and self.query_context not in QUERY_CONTEXTS:
            raise VisitScheduleEvaluatorError(
                f"D05UnitResult.query_context={self.query_context!r} invalid")
        if self.l1_disposition == L1Disposition.POSITIVE:
            if not self.positive_subtype:
                raise VisitScheduleEvaluatorError(
                    "positive unit requires a positive subtype")
            if not self.audience_label:
                raise VisitScheduleEvaluatorError(
                    "positive unit requires an audience label")
        if self.l1_disposition == L1Disposition.NOT_EVALUABLE:
            if not self.not_evaluable_reason:
                raise VisitScheduleEvaluatorError(
                    "not_evaluable unit requires not_evaluable_reason")
        for name in ("r2_candidates", "risk_candidate_refs",
                     "risk_instance_refs", "evidence", "source_record_refs",
                     "query_refs", "coverage_gap_notices"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        object.__setattr__(self, "priority_reason_codes",
                           _canonical_sorted(self.priority_reason_codes))
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))

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
        self, *, provenance_snapshot_id: str = "",
        provenance_rule_lineage: str = "",
    ) -> UnitEvaluation:
        polarities: List[str] = []
        for ev in self.evidence:
            if ev.polarity not in polarities:
                polarities.append(ev.polarity)
        return UnitEvaluation(
            unit_id=self.unit_id, l0_status=self.l0_status,
            l1_disposition=self.l1_disposition,
            l1b_polarities=tuple(sorted(polarities)),
            evidence=self.evidence,
            source_record_refs=self.source_record_refs,
            risk_candidate_refs=self.risk_candidate_refs,
            risk_instance_refs=self.risk_instance_refs,
            query_refs=self.query_refs,
            provenance_snapshot_id=provenance_snapshot_id,
            provenance_rule_lineage=provenance_rule_lineage,
            not_evaluable_reason=self.not_evaluable_reason)


# ---------------------------------------------------------------------------
# Candidates, Query drafts, gap notices (§9, §12)
# ---------------------------------------------------------------------------

def _risk_scope(
    *, site_ref: str, protocol_version: str, arm: str, cohort: str,
    phase: str, rule_content_hash: str, evaluation_window_id: str,
) -> Tuple[str, ...]:
    parts: Set[str] = {
        f"site:{site_ref}" if site_ref else "site:",
        f"protocol:{protocol_version}" if protocol_version else "protocol:",
        f"arm:{arm}" if arm else "arm:",
        f"cohort:{cohort}" if cohort else "cohort:",
        f"phase:{phase}" if phase else "phase:",
        f"rule:{rule_content_hash}",
        f"window:{evaluation_window_id}" if evaluation_window_id else "window:",
        f"ua:{D05_EVAL_ALGO_VERSION}",
    }
    return tuple(sorted(parts))


def build_d05_candidate(
    *, project_id: str, subject_ref: str, site_ref: str,
    unit: ScheduleEvaluationUnit, positive_subtype: str,
    audience_label: str, monitoring_priority: str,
    snapshot_id: str, rule_lineage: str,
    anchor_kind: str = "", anchor_start: str = "", anchor_end: str = "",
    window_start: str = "", window_end: str = "", precision: str = "",
    protocol_version: str = "", arm: str = "", cohort: str = "",
    phase: str = "", rights_or_safety_critical: bool = False,
    machine_close_forbidden: bool = False,
    source_locator_ids: Sequence[str] = (),
    full_locator_id: str = "",
    match_reason: str = "",
) -> RiskCandidate:
    """Build the R2 candidate for one positive/boundary D05 unit (public
    ``make_risk_identity`` only; identity detail mirrors D04 conventions)."""
    scope = _risk_scope(
        site_ref=site_ref, protocol_version=protocol_version, arm=arm,
        cohort=cohort, phase=phase,
        rule_content_hash=unit.rule_id or D05_RULE_LINEAGE_DEFAULT,
        evaluation_window_id=unit.evaluation_window_id)
    classifier = unit.classifier or unit.stable_core
    identity = make_risk_identity(
        project_id=project_id, subject_ref=subject_ref,
        domain=D05_DOMAIN, scope=list(scope),
        classifier=classifier)
    if unit.planned_activity_key:
        stable_event_key = (
            f"activity:{unit.planned_activity_key}:"
            f"{unit.evaluation_window_id}")
    else:
        stable_event_key = (
            f"visit:{unit.planned_visit_key}:{unit.evaluation_window_id}")
    sorted_locators = tuple(sorted(source_locator_ids))
    first_locator = sorted_locators[0] if sorted_locators else ""
    detail: Dict[str, Any] = {
        "risk_identity_id": identity.risk_identity_id,
        # The shared lifecycle adapter requires stable_core to exactly equal
        # the identity classifier (D04 convention).
        "stable_core": classifier,
        "lineage_fingerprint": "|".join(identity.scope),
        "scope": list(identity.scope),
        "classifier": identity.classifier,
        "domain": identity.domain,
        "stable_source_event_key": stable_event_key,
        "risk_family": unit.unit_kind,
        "positive_subtype": positive_subtype,
        "audience_label": audience_label,
        "evaluation_window_id": unit.evaluation_window_id,
        "monitoring_priority": monitoring_priority,
        "rights_or_safety_critical": rights_or_safety_critical,
        "machine_close_forbidden": machine_close_forbidden,
        "match_reason": match_reason or positive_subtype,
        "protocol_version": protocol_version,
        "locator_id": first_locator,
        "full_locator_id": full_locator_id or first_locator,
    }
    return RiskCandidate.from_signal(
        project_id=project_id, subject_ref=subject_ref,
        domain=D05_DOMAIN, signal_type=positive_subtype,
        source_snapshot_id=snapshot_id,
        rule_activation_id=rule_lineage or D05_RULE_LINEAGE_DEFAULT,
        severity_hint=monitoring_priority, confidence_hint=0.0,
        detail=detail)


_ANCHOR_LABELS: Mapping[str, str] = {
    RELATION_FIXED_REFERENCE: "固定基准日",
    RELATION_PRIOR_ACTUAL_VISIT: "前次实际访视",
    "first_ip_dose": "首次给药",
    "randomization": "随机化",
    "consent": "知情同意",
    "other_verified_protocol_anchor": "其他已验证方案锚点",
}


def _action_suffix(query_context: str) -> str:
    if query_context == QUERY_CONTEXT_NOT_OCCURRED:
        return ("请核实访视、评估或样本完成情况、筛选结论或数据记录，"
                "并补充或更正相应记录。")
    if query_context == QUERY_CONTEXT_ENROLLED:
        return ("请核实、说明、补充或更正相应记录；如确认不符合方案，"
                "请评估是否构成方案偏离并按相应流程处理。")
    return ("请先核实是否已随机/入组/接受研究干预及事件时序；"
            "当前资料不足，暂无法确认是否符合方案。")


def build_d05_query_draft(
    *, unit_id: str, subject_ref: str, protocol_version: str,
    plan_target: str, anchor_label: str, window_start: str, window_end: str,
    finding: str, query_context: str, candidate_id: str,
    source_locator_ids: Sequence[str],
) -> QueryDraftRef:
    """Three-part Chinese Query draft (§9.2) -- fixed format, enrollment-
    aware action; only ``enrolled_or_post_enrollment`` appends PD wording."""
    window_txt = ""
    if window_start and window_end:
        window_txt = f"；允许窗口 {window_start} 至 {window_end}"
    anchor_txt = _ANCHOR_LABELS.get(anchor_label, anchor_label or "计划锚点")
    basis = (
        f"依据：方案 {protocol_version} 规定{plan_target}；"
        f"计划锚点 {anchor_txt}{window_txt}。")
    finding_txt = (
        f"发现：参与者 {subject_ref} {finding}。"
        f"支持依据定位 {', '.join(sorted(set(source_locator_ids)))}。")
    action = f"行动项：{_action_suffix(query_context)}"
    return QueryDraftRef(
        query_id="d05-query-" + content_hash({
            "unit_id": unit_id,
            "basis": basis, "finding": finding_txt, "action": action,
            "source_locator_ids": sorted(set(source_locator_ids)),
        }),
        unit_id=unit_id, basis=basis, finding=finding_txt, action=action,
        source_locator_ids=tuple(sorted(set(source_locator_ids))),
        linked_candidate_id=candidate_id)


# ---------------------------------------------------------------------------
# Run orchestration (§4.3 order)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class D05EvaluationOutcome:
    """One subject's D05 Run evaluation result."""

    run_id: str
    project_ref: str
    subject_ref: str
    site_ref: str
    snapshot_as_of: SnapshotAsOf
    clinical_event_cutoff: ClinicalEventCutoff
    applicability_decision: VisitScheduleApplicabilityDecision
    gates: Tuple[ScheduleGate, ...]
    gate_accounting: Any
    expected_units: Tuple[ScheduleEvaluationUnit, ...]
    expected_set: ExpectedSet
    visit_assignments: Tuple[VisitAssignmentDecision, ...]
    activity_assignments: Tuple[ActivityAssignmentDecision, ...]
    consumption_ledgers: Tuple[ActualActivityConsumptionLedger, ...]
    reverse_consumption_index: Tuple[Tuple[str, str], ...]
    unit_results: Tuple[D05UnitResult, ...]
    coverage_ledger: CoverageLedger
    coverage_summary: CoverageSummary
    domain_complete: Tuple[bool, List[str]]
    candidates: Tuple[RiskCandidate, ...]
    query_drafts: Tuple[QueryDraftRef, ...]
    coverage_gap_notices: Tuple[VisitCoverageGapNotice, ...]
    interpretation_ledgers: Tuple[ScheduleInterpretationLedger, ...]
    anchor_refs: Tuple[TypedScheduleAnchorRef, ...]
    anchor_day_by_visit_key: Tuple[Tuple[str, str], ...]
    out_of_cutoff_object_ids: Tuple[str, ...]
    future_obligation_keys: Tuple[str, ...]
    excluded_obligation_keys: Tuple[str, ...]
    enrollment_context: D05EnrollmentContext

    def l1_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {d: 0 for d in L1Disposition.ALL}
        for result in self.unit_results:
            counts[result.l1_disposition] += 1
        return counts

    def gates_block_domain(self) -> bool:
        return self.gate_accounting.blocks_domain_complete


def combine_domain_complete(
    *,
    coverage_complete: Tuple[bool, List[str]],
    gate_accounting: Any,
    gates: Sequence[Any] = (),
) -> Tuple[bool, List[str]]:
    """The authoritative D05 medical-completeness verdict.

    Domain completeness is the AND of the closed coverage-ledger verdict
    (:func:`is_domain_complete`) and the D05 control-plane gate accounting
    (§3.3, §12): any open applicability / routing / anchor / cutoff-scope
    gate blocks the medical domain, independently of whether the L1 units
    happened to evaluate closed.  Returns ``(True, [])`` only when both hold;
    otherwise ``(False, deterministic reasons)`` with the gate block listed
    first.
    """
    reasons: List[str] = []
    open_kinds = tuple(
        sorted({var.gate_kind for var in gates
                if getattr(var, "gate_state", "") == GATE_OPEN}))
    blocks = bool(gate_accounting.blocks_domain_complete) or bool(open_kinds)
    if blocks:
        kind_txt = (", ".join(open_kinds) if open_kinds else "unclassified")
        reasons.append(
            f"open ScheduleGate(s) block domain completeness: {kind_txt}")
    coverage_ok, coverage_reasons = coverage_complete
    reasons.extend(coverage_reasons)
    return (True, []) if (coverage_ok and not blocks) else (False, reasons)


def _resolve_scope_decisions(
    *, records: Sequence[Any], snapshot_as_of: SnapshotAsOf,
    clinical_event_cutoff: ClinicalEventCutoff,
    record_locators: Mapping[str, SourceLocator],
    provided: Sequence[ActualRecordScopeDecision],
) -> Tuple[ActualRecordScopeDecision, ...]:
    if provided:
        return tuple(provided)
    decisions: List[ActualRecordScopeDecision] = []
    for record in records:
        object_id = getattr(record, "encounter_id", "") or getattr(
            record, "actual_activity_id", "")
        locator = record_locators.get(object_id)
        if locator is None:
            raise VisitScheduleEvaluatorError(
                f"record {object_id!r} has no source locator; cannot "
                f"resolve its scope (fail closed)")
        decisions.append(resolve_actual_record_scope(
            record=record, snapshot_as_of=snapshot_as_of,
            clinical_event_cutoff=clinical_event_cutoff,
            source_locators=(locator,)))
    return tuple(decisions)


def evaluate_visit_schedule_run(
    *,
    run_id: str,
    project_ref: str,
    subject_ref: str,
    site_ref: str,
    snapshot_as_of: SnapshotAsOf,
    clinical_event_cutoff: ClinicalEventCutoff,
    applicability_decision: VisitScheduleApplicabilityDecision,
    planned_visits: Sequence[PlannedVisitDefinition],
    planned_activities: Sequence[PlannedActivityDefinition] = (),
    maturity_rules: Optional[Mapping[str, EvaluationMaturityRule]] = None,
    anchor_bindings: Sequence[AnchorBindingRequest] = (),
    encounters: Sequence[ActualEncounterRecord] = (),
    activities: Sequence[ActualActivityRecord] = (),
    bundles: Sequence[ActualEncounterBundle] = (),
    scope_decisions: Sequence[ActualRecordScopeDecision] = (),
    record_locators: Optional[Mapping[str, SourceLocator]] = None,
    plan_locators: Sequence[SourceLocator] = (),
    explicit_visit_mappings: Sequence[StableVisitMapping] = (),
    official_code_mappings: Sequence[OfficialCodeMapping] = (),
    activity_code_aliases: Sequence[OfficialActivityCodeAlias] = (),
    activity_window_rules: Optional[Mapping[str, VisitWindowRule]] = None,
    obligation_applicability: Optional[Mapping[str, ObligationApplicability]] = None,
    priority_policies: Optional[Mapping[str, D05PriorityPolicy]] = None,
    assignment_priority_policy: Optional[D05PriorityPolicy] = None,
    source_coverage: Optional[Mapping[str, bool]] = None,
    enrollment: Optional[EnrollmentEvidence] = None,
    schedule_consistency_issues: Sequence[ScheduleConsistencyIssue] = (),
    allow_unscheduled_visits: bool = False,
    allow_unscheduled_activities: bool = False,
    mapping_coverage_complete: bool = True,
    code_coverage_complete: bool = True,
    prior_resolved_gates: Sequence[ScheduleGate] = (),
    interpretation_rule_ids: Sequence[str] = (),
) -> D05EvaluationOutcome:
    """Run the frozen §4.3 pipeline for one subject: gates -> expected-set
    -> bidirectional assignment + ledger -> per-unit evaluation -> L2/L3
    (candidates, Query drafts, coverage-gap notices) -> closed coverage
    ledger."""
    _validate_nonempty(run_id, "run_id")
    _validate_nonempty(project_ref, "project_ref")
    _validate_nonempty(subject_ref, "subject_ref")
    _validate_nonempty(site_ref, "site_ref")
    if not isinstance(snapshot_as_of, SnapshotAsOf):
        raise VisitScheduleEvaluatorError("snapshot_as_of must be SnapshotAsOf")
    if not isinstance(clinical_event_cutoff, ClinicalEventCutoff):
        raise VisitScheduleEvaluatorError(
            "clinical_event_cutoff must be ClinicalEventCutoff")
    maturity_rules = maturity_rules or {}
    activity_window_rules = activity_window_rules or {}
    obligation_applicability = obligation_applicability or {}
    priority_policies = priority_policies or {}
    source_coverage = source_coverage or {}
    record_locators = record_locators or {}

    # --- scope decisions (dual cutoff; worker_01 authority) ---------------
    scope_decisions = _resolve_scope_decisions(
        records=list(encounters) + list(activities),
        snapshot_as_of=snapshot_as_of,
        clinical_event_cutoff=clinical_event_cutoff,
        record_locators=record_locators,
        provided=scope_decisions)
    encounter_ids = {e.encounter_id for e in encounters}
    in_scope_encounter_ids = {
        d.actual_object_id for d in scope_decisions
        if d.scope_status == SCOPE_IN_SCOPE and d.actual_object_id
        in encounter_ids}
    in_scope_bundles = tuple(
        b for b in bundles
        if all(member in in_scope_encounter_ids
               for member in b.member_encounter_ids))
    in_scope_activity_ids = {
        d.actual_object_id for d in scope_decisions
        if d.scope_status == SCOPE_IN_SCOPE
        and d.actual_object_id in {a.actual_activity_id for a in activities}}
    in_scope_activities = tuple(
        a for a in activities if a.actual_activity_id in in_scope_activity_ids)

    # --- enrollment context (§9.2) ----------------------------------------
    enrollment_evidence = enrollment or EnrollmentEvidence(
        subject_ref=subject_ref)
    enrollment_context = resolve_d05_enrollment_context(
        evidence=enrollment_evidence)

    # --- assignment contexts ----------------------------------------------
    applicable_visit_keys = tuple(
        sorted((v.planned_visit_key for v in planned_visits),
               key=lambda k: _order_key(
                   next(v.planned_order for v in planned_visits
                        if v.planned_visit_key == k))))
    anchor_day_by_key: Dict[str, str] = {}
    for binding in anchor_bindings:
        if binding.relation_type == RELATION_FIXED_REFERENCE:
            anchor_day_by_key[binding.planned_visit_key] = binding.anchor_day
    encounter_by_id = {e.encounter_id: e for e in encounters}
    visit_ctx = VisitAssignmentContext(
        project_ref=project_ref, subject_ref=subject_ref, site_ref=site_ref,
        applicable_visit_keys=applicable_visit_keys,
        planned_visits=tuple(planned_visits),
        explicit_mappings=tuple(explicit_visit_mappings),
        code_mappings=tuple(official_code_mappings),
        anchor_day_by_visit_key=tuple(sorted(anchor_day_by_key.items())),
        encounter_by_id=encounter_by_id,
        protocol_version=applicability_decision.protocol_version,
        allow_unscheduled_visits=allow_unscheduled_visits,
        mapping_coverage_complete=mapping_coverage_complete,
        code_coverage_complete=code_coverage_complete)

    # Chained-anchor feasibility considers ALL bundles (in-scope and
    # out-of-cutoff): an out-of-cutoff actual visit still proves the visit
    # occurred as a chained-anchor interpretation (§5.3), orthogonally to
    # its L1 evaluability.  Only the unique assignment is authoritative;
    # never a nearest-date / row-order shortcut.
    chained_anchor_prior_day_by_key: Dict[str, str] = {}
    for bundle in sorted(bundles, key=lambda b: b.bundle_id):
        decision = resolve_visit_assignment(
            bundle=bundle, ctx=visit_ctx)
        if decision.decision_status == VISIT_ASSIGNMENT_UNIQUE:
            day = _visit_actual_day(bundle)
            if day:
                chained_anchor_prior_day_by_key.setdefault(
                    decision.selected_planned_visit_id, day)

    activity_visit_key_by_id: Dict[str, str] = {}
    for activity in planned_activities:
        visit_key = _visit_key_of_activity(activity, planned_visits)
        if visit_key:
            activity_visit_key_by_id[activity.planned_activity_id] = visit_key
    activity_ctx = ActivityAssignmentContext(
        subject_ref=subject_ref, site_ref=site_ref,
        planned_activities=tuple(planned_activities),
        code_aliases=tuple(activity_code_aliases),
        planned_activity_visit_key=activity_visit_key_by_id,
        actual_activities=in_scope_activities,
        allow_unscheduled_activities=allow_unscheduled_activities,
        activity_evidence_complete=mapping_coverage_complete
        and code_coverage_complete)

    # --- gate + expected-set expansion ------------------------------------
    expansion = expand_expected_set(
        run_id=run_id, project_ref=project_ref, subject_ref=subject_ref,
        site_ref=site_ref, snapshot_as_of=snapshot_as_of,
        clinical_event_cutoff=clinical_event_cutoff,
        applicability_decision=applicability_decision,
        planned_visits=planned_visits,
        planned_activities=planned_activities,
        maturity_rules=maturity_rules,
        anchor_bindings=anchor_bindings,
        scope_decisions=scope_decisions,
        obligation_applicability=obligation_applicability,
        schedule_consistency_issues=schedule_consistency_issues,
        activity_window_rules=activity_window_rules,
        visit_assignment_ctx=visit_ctx,
        activity_assignment_ctx=activity_ctx,
        bundles=in_scope_bundles,
        prior_resolved_gates=prior_resolved_gates,
        chained_anchor_prior_day_by_key=chained_anchor_prior_day_by_key)

    # --- real assignment passes -------------------------------------------
    visit_assignments = resolve_visit_assignments(
        bundles=in_scope_bundles, ctx=visit_ctx)
    visit_by_bundle = {
        d.actual_bundle_id: d.selected_planned_visit_id
        for d in visit_assignments
        if d.decision_status == VISIT_ASSIGNMENT_UNIQUE}
    bundle_by_encounter = {
        member_id: b.bundle_id
        for b in in_scope_bundles for member_id in b.member_encounter_ids}
    visit_key_by_activity: Dict[str, str] = {}
    for activity in in_scope_activities:
        visit_key = ""
        for encounter_id in activity.encounter_refs:
            bundle_id = bundle_by_encounter.get(encounter_id, "")
            if bundle_id and bundle_id in visit_by_bundle:
                visit_key = visit_by_bundle[bundle_id]
                break
        visit_key_by_activity[activity.actual_activity_id] = visit_key
    activity_assignments = resolve_activity_assignments(
        activities=in_scope_activities,
        visit_key_by_activity=visit_key_by_activity,
        ctx=activity_ctx)
    ledgers = build_consumption_ledgers(
        assignments=activity_assignments,
        planned_activities=planned_activities,
        site_ref=site_ref)
    reverse_index = tuple(sorted(
        (pid, d.actual_activity_id)
        for d in activity_assignments for pid in d.selected_planned_activity_ids))

    # --- final units with assignment links --------------------------------
    final_units: List[ScheduleEvaluationUnit] = []
    for unit in expansion.expected_units:
        final_units.append(_link_unit(unit, visit_assignments,
                                      activity_assignments, ledgers))

    # --- per-unit evaluation ----------------------------------------------
    cutoff_day = _day_date(clinical_event_cutoff.cutoff)
    results: List[D05UnitResult] = []
    candidate_inputs: List[Optional[Dict[str, Any]]] = []
    for unit in final_units:
        result, candidate_input = _evaluate_unit(
            unit=unit, expansion=expansion,
            visit_assignments=visit_assignments,
            activity_assignments=activity_assignments,
            ledgers=ledgers, reverse_index=reverse_index,
            planned_visits=planned_visits,
            planned_activities=planned_activities,
            encounters=encounters, activities=activities,
            bundles=in_scope_bundles,
            scope_decisions=scope_decisions,
            applicability_decision=applicability_decision,
            maturity_rules=maturity_rules,
            activity_window_rules=activity_window_rules,
            obligation_applicability=obligation_applicability,
            source_coverage=source_coverage,
            cutoff_day=cutoff_day,
            priority_policies=priority_policies,
            assignment_priority_policy=assignment_priority_policy,
            enrollment_context=enrollment_context,
            record_locators=record_locators,
            plan_locators=plan_locators)
        results.append(result)
        candidate_inputs.append(candidate_input)

    # --- L2/L3: candidates, queries, gap notices --------------------------
    candidates: List[RiskCandidate] = []
    queries: List[QueryDraftRef] = []
    gap_notices: List[VisitCoverageGapNotice] = []
    for index, (unit, candidate_input) in enumerate(
            zip(final_units, candidate_inputs)):
        result = results[index]
        if candidate_input is not None:
            first_loc = _first_locator(result)
            candidate = build_d05_candidate(
                project_id=project_ref, subject_ref=subject_ref,
                site_ref=site_ref, unit=unit,
                positive_subtype=candidate_input["positive_subtype"],
                audience_label=candidate_input["audience_label"],
                monitoring_priority=candidate_input["monitoring_priority"],
                snapshot_id=snapshot_as_of.snapshot_id,
                rule_lineage=candidate_input["rule_lineage"],
                anchor_kind=candidate_input["anchor_kind"],
                anchor_start=candidate_input["anchor_start"],
                anchor_end=candidate_input["anchor_end"],
                window_start=candidate_input["window_start"],
                window_end=candidate_input["window_end"],
                precision=candidate_input["precision"],
                protocol_version=applicability_decision.protocol_version,
                arm=applicability_decision.arm,
                cohort=applicability_decision.cohort,
                phase=applicability_decision.phase,
                rights_or_safety_critical=candidate_input[
                    "rights_or_safety_critical"],
                machine_close_forbidden=candidate_input[
                    "machine_close_forbidden"],
                source_locator_ids=result.all_source_locator_ids(),
                full_locator_id=first_loc.locator_id() if first_loc else "",
                match_reason=candidate_input["match_reason"])
            candidates.append(candidate)
            cand_ref = RiskCandidateRef(
                candidate_id=candidate.candidate_id,
                risk_identity_id=str(candidate.detail.get(
                    "risk_identity_id", "")),
                locator=first_loc)
            result = replace(
                result, r2_candidates=(candidate,),
                risk_candidate_refs=(cand_ref,))
            if result.l1_disposition == L1Disposition.POSITIVE:
                query = _build_query_for_result(
                    result=result, unit=unit,
                    protocol_version=applicability_decision.protocol_version,
                    enrollment_context=enrollment_context,
                    candidate_id=cand_ref.candidate_id,
                    plan_target=_plan_target_for(unit, planned_visits,
                                                 planned_activities))
                if query is not None:
                    queries.append(query)
                    result = replace(result, query_refs=(query,))
        if result.l1_disposition == L1Disposition.NOT_EVALUABLE:
            notice = _build_gap_notice(result)
            if notice is not None:
                gap_notices.append(notice)
                result = replace(result, coverage_gap_notices=(notice,))
        results[final_units.index(unit)] = result

    # --- closed coverage ledger -------------------------------------------
    expected = ExpectedSet.from_units(
        final_units, domain_id=D05_DOMAIN, run_id=run_id)
    ledger = CoverageLedger(expected_set=expected)
    for unit, result in zip(final_units, results):
        maturity_rule = maturity_rules.get(unit.unit_kind)
        provenance_rule = (maturity_rule.rule_version if maturity_rule
                           else D05_RULE_LINEAGE_DEFAULT)
        ledger.assign(result.to_unit_evaluation(
            provenance_snapshot_id=snapshot_as_of.snapshot_id,
            provenance_rule_lineage=provenance_rule))
    ledger.close()
    summary = ledger.close_and_summarize()
    coverage_complete = is_domain_complete(summary)
    domain_complete = combine_domain_complete(
        coverage_complete=coverage_complete,
        gate_accounting=expansion.gate_accounting,
        gates=expansion.gates)

    interp_ledgers = _build_interpretation_ledgers(
        visit_assignments=visit_assignments,
        activity_assignments=activity_assignments,
        rule_ids=interpretation_rule_ids)

    return D05EvaluationOutcome(
        run_id=run_id, project_ref=project_ref, subject_ref=subject_ref,
        site_ref=site_ref, snapshot_as_of=snapshot_as_of,
        clinical_event_cutoff=clinical_event_cutoff,
        applicability_decision=applicability_decision,
        gates=expansion.gates, gate_accounting=expansion.gate_accounting,
        expected_units=tuple(final_units), expected_set=expected,
        visit_assignments=visit_assignments,
        activity_assignments=activity_assignments,
        consumption_ledgers=ledgers,
        reverse_consumption_index=reverse_index,
        unit_results=tuple(results), coverage_ledger=ledger,
        coverage_summary=summary, domain_complete=domain_complete,
        candidates=tuple(candidates), query_drafts=tuple(queries),
        coverage_gap_notices=tuple(gap_notices),
        interpretation_ledgers=interp_ledgers,
        anchor_refs=expansion.anchor_refs,
        anchor_day_by_visit_key=expansion.anchor_day_by_visit_key,
        out_of_cutoff_object_ids=expansion.out_of_cutoff_object_ids,
        future_obligation_keys=expansion.future_obligation_keys,
        excluded_obligation_keys=expansion.excluded_obligation_keys,
        enrollment_context=enrollment_context)


def _link_unit(
    unit: ScheduleEvaluationUnit,
    visit_assignments: Sequence[VisitAssignmentDecision],
    activity_assignments: Sequence[ActivityAssignmentDecision],
    ledgers: Sequence[ActualActivityConsumptionLedger],
) -> ScheduleEvaluationUnit:
    """Attach the resolved assignment ids to a unit (unit_id unchanged)."""
    visit_assignment_id = ""
    activity_assignment_id = ""
    actual_bundle_id = ""
    actual_activity_id = ""
    for decision in visit_assignments:
        if decision.selected_planned_visit_id == unit.planned_visit_key \
                and unit.planned_visit_key \
                and decision.decision_status == VISIT_ASSIGNMENT_UNIQUE:
            visit_assignment_id = decision.assignment_id
            actual_bundle_id = decision.actual_bundle_id
            break
    for decision in activity_assignments:
        if unit.planned_activity_key in decision.selected_planned_activity_ids:
            activity_assignment_id = decision.assignment_id
            actual_activity_id = decision.actual_activity_id
            break
    return replace(
        unit,
        visit_assignment_id=visit_assignment_id,
        activity_assignment_id=activity_assignment_id,
        actual_bundle_id=actual_bundle_id,
        actual_activity_id=actual_activity_id,
        lineage_hash="")


def _evaluate_unit(
    *, unit: ScheduleEvaluationUnit, expansion: ExpectedSetExpansion,
    visit_assignments: Sequence[VisitAssignmentDecision],
    activity_assignments: Sequence[ActivityAssignmentDecision],
    ledgers: Sequence[ActualActivityConsumptionLedger],
    reverse_index: Sequence[Tuple[str, str]],
    planned_visits: Sequence[PlannedVisitDefinition],
    planned_activities: Sequence[PlannedActivityDefinition],
    encounters: Sequence[ActualEncounterRecord],
    activities: Sequence[ActualActivityRecord],
    bundles: Sequence[ActualEncounterBundle],
    scope_decisions: Sequence[ActualRecordScopeDecision],
    applicability_decision: VisitScheduleApplicabilityDecision,
    maturity_rules: Mapping[str, EvaluationMaturityRule],
    activity_window_rules: Mapping[str, VisitWindowRule],
    obligation_applicability: Mapping[str, ObligationApplicability],
    source_coverage: Mapping[str, bool],
    cutoff_day: Optional[datetime.date],
    priority_policies: Mapping[str, D05PriorityPolicy],
    assignment_priority_policy: Optional[D05PriorityPolicy],
    enrollment_context: D05EnrollmentContext,
    record_locators: Mapping[str, SourceLocator],
    plan_locators: Sequence[SourceLocator],
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    """Evaluate one unit to an L1 disposition and build the candidate
    input for positive/boundary units."""
    kind = unit.unit_kind
    if kind == UNIT_VISIT_OCCURRENCE:
        return _eval_visit_occurrence(
            unit=unit, expansion=expansion,
            visit_assignments=visit_assignments,
            planned_visits=planned_visits, bundles=bundles,
            applicability_decision=applicability_decision,
            maturity_rules=maturity_rules,
            obligation_applicability=obligation_applicability,
            source_coverage=source_coverage,
            priority_policies=priority_policies,
            enrollment_context=enrollment_context,
            record_locators=record_locators, plan_locators=plan_locators)
    if kind == UNIT_VISIT_TIMING:
        return _eval_visit_timing(
            unit=unit, expansion=expansion,
            visit_assignments=visit_assignments,
            planned_visits=planned_visits, bundles=bundles,
            source_coverage=source_coverage,
            priority_policies=priority_policies,
            enrollment_context=enrollment_context,
            record_locators=record_locators, plan_locators=plan_locators)
    if kind == UNIT_VISIT_ORDER:
        return _eval_visit_order(
            unit=unit, visit_assignments=visit_assignments,
            planned_visits=planned_visits, bundles=bundles,
            source_coverage=source_coverage,
            priority_policies=priority_policies,
            enrollment_context=enrollment_context,
            record_locators=record_locators, plan_locators=plan_locators)
    if kind in (UNIT_ACTIVITY_OCCURRENCE, UNIT_ACTIVITY_TIMING):
        return _eval_activity(
            unit=unit, kind=kind, expansion=expansion,
            activity_assignments=activity_assignments,
            planned_visits=planned_visits,
            planned_activities=planned_activities,
            activities=activities,
            applicability_decision=applicability_decision,
            maturity_rules=maturity_rules,
            activity_window_rules=activity_window_rules,
            obligation_applicability=obligation_applicability,
            source_coverage=source_coverage,
            priority_policies=priority_policies,
            enrollment_context=enrollment_context,
            record_locators=record_locators, plan_locators=plan_locators)
    if kind == UNIT_ACTUAL_ASSIGNMENT:
        return _eval_actual_assignment(
            unit=unit, visit_assignments=visit_assignments,
            activity_assignments=activity_assignments,
            bundles=bundles, activities=activities,
            source_coverage=source_coverage,
            assignment_priority_policy=assignment_priority_policy,
            enrollment_context=enrollment_context,
            record_locators=record_locators, plan_locators=plan_locators)
    if kind == UNIT_SCHEDULE_CONSISTENCY:
        return _eval_schedule_consistency(
            unit=unit, assignment_priority_policy=assignment_priority_policy,
            enrollment_context=enrollment_context,
            plan_locators=plan_locators)
    raise VisitScheduleEvaluatorError(f"unsupported unit kind {kind!r}")


def _find_visit(unit: ScheduleEvaluationUnit,
                planned_visits: Sequence[PlannedVisitDefinition],
                ) -> Optional[PlannedVisitDefinition]:
    for visit in planned_visits:
        if visit.planned_visit_key == unit.planned_visit_key:
            return visit
    return None


def _find_activity(unit: ScheduleEvaluationUnit,
                   planned_activities: Sequence[PlannedActivityDefinition],
                   ) -> Optional[PlannedActivityDefinition]:
    for activity in planned_activities:
        if activity.planned_activity_key == unit.planned_activity_key:
            return activity
    return None


def _unique_bundle_for_visit(
    visit_key: str, visit_assignments: Sequence[VisitAssignmentDecision],
    bundles: Sequence[ActualEncounterBundle],
) -> Optional[ActualEncounterBundle]:
    for decision in visit_assignments:
        if decision.selected_planned_visit_id == visit_key \
                and decision.decision_status == VISIT_ASSIGNMENT_UNIQUE:
            for bundle in bundles:
                if bundle.bundle_id == decision.actual_bundle_id:
                    return bundle
    return None


def _assignment_for_bundle(
    bundle_id: str, visit_assignments: Sequence[VisitAssignmentDecision],
) -> Optional[VisitAssignmentDecision]:
    for decision in visit_assignments:
        if decision.actual_bundle_id == bundle_id:
            return decision
    return None


def _evidence_items(
    *, record_locators: Mapping[str, SourceLocator],
    plan_locators: Sequence[SourceLocator],
    record_ids: Sequence[str], plan_locator_ids: Sequence[str],
    polarity: str,
) -> Tuple[EvidenceItem, ...]:
    items: List[EvidenceItem] = []
    seen: Set[str] = set()
    for record_id in record_ids:
        locator = record_locators.get(record_id)
        if locator is None:
            continue
        key = locator.locator_id()
        if key in seen:
            continue
        seen.add(key)
        items.append(EvidenceItem(
            evidence_id="d05-ev-" + content_hash({
                "locator": key, "polarity": polarity,
                "role": locator.table_semantic}),
            polarity=polarity, locator=locator,
            evidence_role=locator.table_semantic,
            rule_lineage=D05_RULE_LINEAGE_DEFAULT))
    for locator in plan_locators:
        key = locator.locator_id()
        if key in seen:
            continue
        if plan_locator_ids and key not in plan_locator_ids:
            continue
        seen.add(key)
        items.append(EvidenceItem(
            evidence_id="d05-ev-" + content_hash({
                "locator": key, "polarity": polarity, "role": "plan"}),
            polarity=polarity, locator=locator,
            evidence_role="plan", rule_lineage=D05_RULE_LINEAGE_DEFAULT))
    return tuple(items)


def _policy_verdict(
    key: str, priority_policies: Mapping[str, D05PriorityPolicy],
    kind: str,
) -> Optional[D05PriorityVerdict]:
    policy = priority_policies.get(key)
    if policy is None:
        if kind == L1Disposition.POSITIVE:
            raise VisitScheduleEvaluatorError(
                f"positive unit for obligation {key!r} requires a frozen "
                f"D05PriorityPolicy (priority inputs must be closed "
                f"enums, §9.1)")
        return None
    return resolve_d05_priority(policy)


def _first_locator(result: D05UnitResult) -> Optional[SourceLocator]:
    for item in result.evidence:
        return item.locator
    for ref in result.source_record_refs:
        return ref.locator
    return None


def _eval_visit_occurrence(
    *, unit, expansion, visit_assignments, planned_visits, bundles,
    applicability_decision, maturity_rules, obligation_applicability,
    source_coverage, priority_policies, enrollment_context, record_locators,
    plan_locators,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    visit = _find_visit(unit, planned_visits)
    assert visit is not None
    key = unit.planned_visit_key
    applicability = obligation_applicability.get(
        key, ObligationApplicability(obligation_key=key, applicable=True))
    if applicability.applicable is False:
        return _not_applicable_result(
            unit=unit, reason=applicability.reason_code,
            authority_locator_ids=applicability.authority_locator_ids,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if applicability.applicable is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_COVERAGE_INCOMPLETE,
            gap_roles=("applicability",),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if maturity_rules.get(UNIT_VISIT_OCCURRENCE) is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_MATURITY_RULE_MISSING,
            gap_roles=(ANCHOR_ROLE_VISIT_SCHEDULE,),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    maturity_rule = maturity_rules[UNIT_VISIT_OCCURRENCE]
    if maturity_day_for(maturity_rule=maturity_rule,
                        anchor_day=_anchor_day_of(unit, expansion),
                        window_rule=visit.window_rule) is None:
        # Maturity cannot be computed (missing anchor / unfrozen window):
        # the obligation stays not_evaluable, never a false missing-positive
        # (§4.2, challenge 113).
        return _not_evaluable_result(
            unit=unit, reason=REASON_MATURITY_RULE_MISSING,
            gap_roles=(ANCHOR_ROLE_VISIT_SCHEDULE,),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if not source_coverage.get("encounter", True):
        return _not_evaluable_result(
            unit=unit, reason=REASON_COVERAGE_INCOMPLETE,
            gap_roles=("encounter",), l0_status=L0CoverageStatus.MISSING,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    bundle = _unique_bundle_for_visit(
        visit.planned_visit_key, visit_assignments, bundles)
    evidence = _evidence_items(
        record_locators=record_locators, plan_locators=plan_locators,
        record_ids=([bundle.member_encounter_ids[0]] if bundle else []),
        plan_locator_ids=visit.source_locator_ids,
        polarity=L1bEvidencePolarity.SUPPORTING)
    source_refs = _source_refs_for_bundle(bundle, record_locators)
    if bundle is not None:
        return _result(
            unit=unit, disposition=L1Disposition.NEGATIVE,
            priority=_priority_or_unknown(_policy_verdict(
                key, priority_policies, "negative")),
            evidence=evidence, source_refs=source_refs,
            anchor_kind=visit.anchor_rule.anchor_kind,
            window=visit.window_rule,
            anchor_day=_anchor_day_of(unit, expansion),
            actual_start=_bundle_start(bundle),
            actual_end=_bundle_end(bundle),
            enrollment_context=enrollment_context), None
    # A scope-gated record (boundary/not_evaluable scope) means "complete
    # absence" is not established: never a false visit_missing positive
    # (§4.2, §8.3; the cutoff-scope gate already blocks completeness).
    scope_gated = any(
        d.scope_status in (SCOPE_BOUNDARY, SCOPE_NOT_EVALUABLE)
        for d in expansion.scope_decisions)
    if scope_gated:
        return _not_evaluable_result(
            unit=unit, reason=REASON_COVERAGE_INCOMPLETE,
            gap_roles=("encounter",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    verdict = _policy_verdict(key, priority_policies, L1Disposition.POSITIVE)
    assert verdict is not None
    return _result(
        unit=unit, disposition=L1Disposition.POSITIVE,
        subtype=POSITIVE_VISIT_MISSING,
        audience_label=POSITIVE_SUBTYPE_LABELS[POSITIVE_VISIT_MISSING],
        priority=verdict.priority,
        evidence=evidence, source_refs=source_refs,
        anchor_kind=visit.anchor_rule.anchor_kind,
        window=visit.window_rule,
        anchor_day=_anchor_day_of(unit, expansion),
        rights_or_safety_critical=verdict.rights_or_safety_critical,
        machine_close_forbidden=verdict.machine_close_forbidden,
        priority_reason_codes=verdict.reason_codes,
        enrollment_context=enrollment_context), _candidate_input(
            unit=unit, subtype=POSITIVE_VISIT_MISSING,
            audience_label=POSITIVE_SUBTYPE_LABELS[POSITIVE_VISIT_MISSING],
            priority=verdict.priority,
            anchor_kind=visit.anchor_rule.anchor_kind,
            window=visit.window_rule,
            anchor_day=_anchor_day_of(unit, expansion),
            rights_or_safety_critical=verdict.rights_or_safety_critical,
            machine_close_forbidden=verdict.machine_close_forbidden,
            match_reason="missing visit with complete coverage")


def _eval_visit_timing(
    *, unit, expansion, visit_assignments, planned_visits, bundles,
    source_coverage, priority_policies, enrollment_context, record_locators,
    plan_locators,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    visit = _find_visit(unit, planned_visits)
    assert visit is not None
    bundle = _unique_bundle_for_visit(
        visit.planned_visit_key, visit_assignments, bundles)
    if bundle is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=("encounter",),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    anchor_day = _anchor_day_of(unit, expansion)
    bounds = window_bounds(window_rule=visit.window_rule, anchor_day=anchor_day)
    lo_day, hi_day, complete = _bundle_interval_relation_to_day(bundle)
    evidence = _evidence_items(
        record_locators=record_locators, plan_locators=plan_locators,
        record_ids=([bundle.member_encounter_ids[0]] if bundle else []),
        plan_locator_ids=visit.source_locator_ids,
        polarity=L1bEvidencePolarity.SUPPORTING)
    source_refs = _source_refs_for_bundle(bundle, record_locators)
    # Sub-day window precision: instant-level compare (challenges 26/27/66).
    if visit.window_rule.date_precision in SUB_DAY_PRECISIONS:
        record_precision = bundle.date_precision
        if record_precision == PRECISION_DAY:
            # Hour-level window with complete day-only source -> boundary
            # (challenge 66: the source is complete but cannot discriminate).
            verdict = _policy_verdict(unit.planned_visit_key,
                                      priority_policies, L1Disposition.BOUNDARY)
            boundary_priority = _priority_or_unknown(verdict)
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="小时级窗口但来源仅按日采集且覆盖完整",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                anchor_kind=visit.anchor_rule.anchor_kind,
                window=visit.window_rule, anchor_day=anchor_day,
                actual_start=_bundle_start(bundle),
                actual_end=_bundle_end(bundle),
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="访视时间边界待核实",
                    priority=boundary_priority,
                    anchor_kind=visit.anchor_rule.anchor_kind,
                    window=visit.window_rule, anchor_day=anchor_day,
                    match_reason="sub-day window with day-only source")
        if record_precision not in SUB_DAY_PRECISIONS:
            return _not_evaluable_result(
                unit=unit, reason=REASON_PRECISION_INSUFFICIENT,
                gap_roles=("window",),
                evidence=evidence, source_refs=source_refs,
                record_locators=record_locators, plan_locators=plan_locators,
                enrollment_context=enrollment_context), None
        if not bundle.timezone.strip():
            return _not_evaluable_result(
                unit=unit, reason=REASON_TIMEZONE_MISSING,
                gap_roles=("window",),
                evidence=evidence, source_refs=source_refs,
                record_locators=record_locators, plan_locators=plan_locators,
                enrollment_context=enrollment_context), None
        verdict, reason = _timing_compare_instants(
            window_rule=visit.window_rule, anchor_day=anchor_day,
            start=bundle.derived_start, end=bundle.derived_end,
            timezone=bundle.timezone)
        if verdict == L1Disposition.NEGATIVE:
            return _result(
                unit=unit, disposition=L1Disposition.NEGATIVE,
                priority=_priority_or_unknown(_policy_verdict(
                    unit.planned_visit_key, priority_policies, "negative")),
                evidence=evidence, source_refs=source_refs,
                anchor_kind=visit.anchor_rule.anchor_kind,
                window=visit.window_rule, anchor_day=anchor_day,
                actual_start=_bundle_start(bundle),
                actual_end=_bundle_end(bundle),
                enrollment_context=enrollment_context), None
        if verdict == L1Disposition.POSITIVE:
            return _timing_positive(
                unit=unit, visit=visit, bundle=bundle, bounds=bounds,
                priority_policies=priority_policies, evidence=evidence,
                source_refs=source_refs, expansion=expansion,
                enrollment_context=enrollment_context)
        if verdict == L1Disposition.BOUNDARY:
            policy_verdict = _policy_verdict(unit.planned_visit_key,
                                             priority_policies,
                                             L1Disposition.BOUNDARY)
            boundary_priority = _priority_or_unknown(policy_verdict)
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="跨午夜区间边界无法在瞬时精度确定",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                anchor_kind=visit.anchor_rule.anchor_kind,
                window=visit.window_rule, anchor_day=anchor_day,
                actual_start=_bundle_start(bundle),
                actual_end=_bundle_end(bundle),
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="访视时间边界待核实",
                    priority=boundary_priority,
                    anchor_kind=visit.anchor_rule.anchor_kind,
                    window=visit.window_rule, anchor_day=anchor_day,
                    match_reason="sub-day interval straddles the window")
        return _not_evaluable_result(
            unit=unit, reason=reason or REASON_PRECISION_INSUFFICIENT,
            gap_roles=("window",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if not bounds.determinable:
        return _not_evaluable_result(
            unit=unit, reason=bounds.reason_code or REASON_PRECISION_INSUFFICIENT,
            gap_roles=("window",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if lo_day is None or hi_day is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=("encounter",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    lo_bound = _day_date(bounds.lo_day)
    hi_bound = _day_date(bounds.hi_day)
    if lo_bound is None or hi_bound is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_PRECISION_INSUFFICIENT,
            gap_roles=("window",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if not complete:
        if hi_day < lo_bound or lo_day > hi_bound:
            return _timing_positive(
                unit=unit, visit=visit, bundle=bundle, bounds=bounds,
                priority_policies=priority_policies, evidence=evidence,
                source_refs=source_refs, expansion=expansion,
                enrollment_context=enrollment_context)
        if lo_day >= lo_bound and hi_day <= hi_bound:
            return _result(
                unit=unit, disposition=L1Disposition.NEGATIVE,
                priority=_priority_or_unknown(_policy_verdict(
                    unit.planned_visit_key, priority_policies, "negative")),
                evidence=evidence, source_refs=source_refs,
                anchor_kind=visit.anchor_rule.anchor_kind,
                window=visit.window_rule,
                anchor_day=_anchor_day_of(unit, expansion),
                actual_start=_bundle_start(bundle),
                actual_end=_bundle_end(bundle),
                enrollment_context=enrollment_context), None
        verdict = _policy_verdict(unit.planned_visit_key, priority_policies,
                                  L1Disposition.BOUNDARY)
        boundary_priority = _priority_or_unknown(verdict)
        return _result(
            unit=unit, disposition=L1Disposition.BOUNDARY,
            boundary_reason="部分日期区间跨越窗口边界且来源完整",
            priority=boundary_priority,
            evidence=evidence, source_refs=source_refs,
            anchor_kind=visit.anchor_rule.anchor_kind,
            window=visit.window_rule,
            anchor_day=_anchor_day_of(unit, expansion),
            actual_start=_bundle_start(bundle),
            actual_end=_bundle_end(bundle),
            enrollment_context=enrollment_context), _boundary_candidate_input(
                unit=unit, audience_label="访视时间边界待核实",
                priority=boundary_priority,
                anchor_kind=visit.anchor_rule.anchor_kind,
                window=visit.window_rule,
                anchor_day=_anchor_day_of(unit, expansion),
                match_reason="partial date interval straddles the window")
    if lo_day >= lo_bound and hi_day <= hi_bound:
        return _result(
            unit=unit, disposition=L1Disposition.NEGATIVE,
            priority=_priority_or_unknown(_policy_verdict(
                unit.planned_visit_key, priority_policies, "negative")),
            evidence=evidence, source_refs=source_refs,
            anchor_kind=visit.anchor_rule.anchor_kind,
            window=visit.window_rule,
            anchor_day=_anchor_day_of(unit, expansion),
            actual_start=_bundle_start(bundle),
            actual_end=_bundle_end(bundle),
            enrollment_context=enrollment_context), None
    return _timing_positive(
        unit=unit, visit=visit, bundle=bundle, bounds=bounds,
        priority_policies=priority_policies, evidence=evidence,
        source_refs=source_refs, expansion=expansion,
        enrollment_context=enrollment_context)


def _timing_positive(
    *, unit, visit, bundle, bounds, priority_policies, evidence, source_refs,
    expansion, enrollment_context,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    verdict = _policy_verdict(unit.planned_visit_key, priority_policies,
                              L1Disposition.POSITIVE)
    assert verdict is not None
    return _result(
        unit=unit, disposition=L1Disposition.POSITIVE,
        subtype=POSITIVE_VISIT_OVERWINDOW,
        audience_label=POSITIVE_SUBTYPE_LABELS[POSITIVE_VISIT_OVERWINDOW],
        priority=verdict.priority,
        evidence=evidence, source_refs=source_refs,
        anchor_kind=visit.anchor_rule.anchor_kind,
        window=visit.window_rule,
        anchor_day=_anchor_day_of(unit, expansion),
        actual_start=_bundle_start(bundle),
        actual_end=_bundle_end(bundle),
        rights_or_safety_critical=verdict.rights_or_safety_critical,
        machine_close_forbidden=verdict.machine_close_forbidden,
        priority_reason_codes=verdict.reason_codes,
        enrollment_context=enrollment_context), _candidate_input(
            unit=unit, subtype=POSITIVE_VISIT_OVERWINDOW,
            audience_label=POSITIVE_SUBTYPE_LABELS[POSITIVE_VISIT_OVERWINDOW],
            priority=verdict.priority,
            anchor_kind=visit.anchor_rule.anchor_kind,
            window=visit.window_rule,
            anchor_day=_anchor_day_of(unit, expansion),
            rights_or_safety_critical=verdict.rights_or_safety_critical,
            machine_close_forbidden=verdict.machine_close_forbidden,
            match_reason="actual visit outside the allowed window")


def _eval_visit_order(
    *, unit, visit_assignments, planned_visits, bundles, source_coverage,
    priority_policies, enrollment_context, record_locators, plan_locators,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    visit = _find_visit(unit, planned_visits)
    assert visit is not None
    predecessor = _predecessor_visit(visit, planned_visits)
    if predecessor is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=("encounter",),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    current = _unique_bundle_for_visit(
        visit.planned_visit_key, visit_assignments, bundles)
    prior = _unique_bundle_for_visit(
        predecessor.planned_visit_key, visit_assignments, bundles)
    if current is None or prior is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=("encounter",),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    current_lo, _, current_complete = _bundle_interval_relation_to_day(current)
    prior_lo, _, prior_complete = _bundle_interval_relation_to_day(prior)
    if not current_complete or not prior_complete \
            or current_lo is None or prior_lo is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=("encounter",),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    evidence = _evidence_items(
        record_locators=record_locators, plan_locators=plan_locators,
        record_ids=[current.member_encounter_ids[0],
                    prior.member_encounter_ids[0]],
        plan_locator_ids=visit.source_locator_ids,
        polarity=L1bEvidencePolarity.SUPPORTING)
    source_refs = tuple(
        _source_refs_for_bundle(current, record_locators)
        + _source_refs_for_bundle(prior, record_locators))
    if current_lo < prior_lo:
        verdict = _policy_verdict(unit.planned_visit_key, priority_policies,
                                  L1Disposition.POSITIVE)
        assert verdict is not None
        return _result(
            unit=unit, disposition=L1Disposition.POSITIVE,
            subtype=POSITIVE_VISIT_ORDER_INCONSISTENT,
            audience_label=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_VISIT_ORDER_INCONSISTENT],
            priority=verdict.priority,
            evidence=evidence, source_refs=source_refs,
            anchor_kind=visit.anchor_rule.anchor_kind,
            window=visit.window_rule,
            anchor_day="",
            actual_start=_bundle_start(current),
            actual_end=_bundle_end(current),
            rights_or_safety_critical=verdict.rights_or_safety_critical,
            machine_close_forbidden=verdict.machine_close_forbidden,
            priority_reason_codes=verdict.reason_codes,
            enrollment_context=enrollment_context), _candidate_input(
                unit=unit, subtype=POSITIVE_VISIT_ORDER_INCONSISTENT,
                audience_label=POSITIVE_SUBTYPE_LABELS[
                    POSITIVE_VISIT_ORDER_INCONSISTENT],
                priority=verdict.priority,
                anchor_kind=visit.anchor_rule.anchor_kind,
                window=visit.window_rule,
                anchor_day="",
                rights_or_safety_critical=verdict.rights_or_safety_critical,
                machine_close_forbidden=verdict.machine_close_forbidden,
                match_reason="actual visit order contradicts planned_order")
    return _result(
        unit=unit, disposition=L1Disposition.NEGATIVE,
        priority=_priority_or_unknown(_policy_verdict(
            unit.planned_visit_key, priority_policies, "negative")),
        evidence=evidence, source_refs=source_refs,
        anchor_kind=visit.anchor_rule.anchor_kind,
        window=visit.window_rule,
        anchor_day="",
        actual_start=_bundle_start(current),
        actual_end=_bundle_end(current),
        enrollment_context=enrollment_context), None


def _eval_activity(
    *, unit, kind, expansion, activity_assignments,
    planned_visits, planned_activities, activities,
    applicability_decision, maturity_rules, activity_window_rules,
    obligation_applicability, source_coverage, priority_policies,
    enrollment_context, record_locators, plan_locators,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    activity_def = _find_activity(unit, planned_activities)
    assert activity_def is not None
    key = unit.planned_activity_key
    applicability = obligation_applicability.get(
        key, ObligationApplicability(obligation_key=key, applicable=True))
    if applicability.applicable is False:
        return _not_applicable_result(
            unit=unit, reason=applicability.reason_code,
            authority_locator_ids=applicability.authority_locator_ids,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if applicability.applicable is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_COVERAGE_INCOMPLETE,
            gap_roles=("applicability",),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    assigned: List[ActualActivityRecord] = []
    for decision in activity_assignments:
        if key in decision.selected_planned_activity_ids:
            for actual in activities:
                if actual.actual_activity_id == decision.actual_activity_id:
                    assigned.append(actual)
    role = _role_for_kind(activity_def.activity_kind)
    role_covered = source_coverage.get(role, True)
    visit_key = _visit_key_of_activity(activity_def, planned_visits) or ""
    anchor_day = ""
    for item in expansion.anchor_day_by_visit_key:
        if item[0] == visit_key:
            anchor_day = item[1]
            break
    window_rule = activity_window_rules.get(key)
    if kind == UNIT_ACTIVITY_OCCURRENCE:
        maturity_rule = maturity_rules.get(UNIT_ACTIVITY_OCCURRENCE)
        if maturity_rule is not None and maturity_day_for(
                maturity_rule=maturity_rule, anchor_day=anchor_day,
                window_rule=window_rule) is None:
            return _not_evaluable_result(
                unit=unit, reason=REASON_MATURITY_RULE_MISSING,
                gap_roles=("window",),
                record_locators=record_locators, plan_locators=plan_locators,
                enrollment_context=enrollment_context), None
        if not role_covered:
            return _not_evaluable_result(
                unit=unit, reason=REASON_COVERAGE_INCOMPLETE,
                gap_roles=(role,), l0_status=L0CoverageStatus.MISSING,
                record_locators=record_locators, plan_locators=plan_locators,
                enrollment_context=enrollment_context), None
        if assigned:
            actual = assigned[0]
            return _result(
                unit=unit, disposition=L1Disposition.NEGATIVE,
                priority=_priority_or_unknown(_policy_verdict(
                    key, priority_policies, "negative")),
                evidence=_evidence_items(
                    record_locators=record_locators,
                    plan_locators=plan_locators,
                    record_ids=[actual.actual_activity_id],
                    plan_locator_ids=activity_def.source_locator_ids,
                    polarity=L1bEvidencePolarity.SUPPORTING),
                source_refs=_source_refs_for_activity(actual, record_locators),
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                enrollment_context=enrollment_context), None
        subtype = _missing_subtype(activity_def.activity_kind)
        verdict = _policy_verdict(key, priority_policies, L1Disposition.POSITIVE)
        assert verdict is not None
        return _result(
            unit=unit, disposition=L1Disposition.POSITIVE,
            subtype=subtype,
            audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
            priority=verdict.priority,
            evidence=_evidence_items(
                record_locators=record_locators,
                plan_locators=plan_locators, record_ids=(),
                plan_locator_ids=activity_def.source_locator_ids,
                polarity=L1bEvidencePolarity.SUPPORTING),
            source_refs=(),
            anchor_kind=activity_def.applicability_expression or "",
            window=window_rule, anchor_day=anchor_day,
            rights_or_safety_critical=verdict.rights_or_safety_critical,
            machine_close_forbidden=verdict.machine_close_forbidden,
            priority_reason_codes=verdict.reason_codes,
            enrollment_context=enrollment_context), _candidate_input(
                unit=unit, subtype=subtype,
                audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
                priority=verdict.priority,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                rights_or_safety_critical=verdict.rights_or_safety_critical,
                machine_close_forbidden=verdict.machine_close_forbidden,
                match_reason="required activity missing with complete coverage")
    # Activity timing.
    if not assigned:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=(role,),
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    actual = assigned[0]
    bounds = window_bounds(window_rule=window_rule, anchor_day=anchor_day)
    evidence = _evidence_items(
        record_locators=record_locators, plan_locators=plan_locators,
        record_ids=[actual.actual_activity_id],
        plan_locator_ids=activity_def.source_locator_ids,
        polarity=L1bEvidencePolarity.SUPPORTING)
    source_refs = _source_refs_for_activity(actual, record_locators)
    if window_rule is not None \
            and window_rule.date_precision in SUB_DAY_PRECISIONS:
        if actual.date_precision == PRECISION_DAY:
            boundary_priority = _priority_or_unknown(_policy_verdict(
                key, priority_policies, L1Disposition.BOUNDARY))
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="小时级窗口但来源仅按日采集且覆盖完整",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="评估/样本时间边界待核实",
                    priority=boundary_priority,
                    anchor_kind=activity_def.applicability_expression or "",
                    window=window_rule, anchor_day=anchor_day,
                    match_reason="sub-day window with day-only source")
        if actual.date_precision not in SUB_DAY_PRECISIONS \
                or not actual.timezone.strip():
            return _not_evaluable_result(
                unit=unit, reason=REASON_TIMEZONE_MISSING,
                gap_roles=("window",),
                evidence=evidence, source_refs=source_refs,
                record_locators=record_locators, plan_locators=plan_locators,
                enrollment_context=enrollment_context), None
        verdict, reason = _timing_compare_instants(
            window_rule=window_rule, anchor_day=anchor_day,
            start=actual.start, end=actual.end, timezone=actual.timezone)
        if verdict == L1Disposition.NEGATIVE:
            return _result(
                unit=unit, disposition=L1Disposition.NEGATIVE,
                priority=_priority_or_unknown(_policy_verdict(
                    key, priority_policies, "negative")),
                evidence=evidence, source_refs=source_refs,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                enrollment_context=enrollment_context), None
        if verdict == L1Disposition.POSITIVE:
            verdict_policy = _policy_verdict(
                key, priority_policies, L1Disposition.POSITIVE)
            assert verdict_policy is not None
            subtype = _mistimed_subtype(activity_def.activity_kind)
            return _result(
                unit=unit, disposition=L1Disposition.POSITIVE,
                subtype=subtype,
                audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
                priority=verdict_policy.priority,
                evidence=evidence, source_refs=source_refs,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                rights_or_safety_critical=verdict_policy.rights_or_safety_critical,
                machine_close_forbidden=verdict_policy.machine_close_forbidden,
                priority_reason_codes=verdict_policy.reason_codes,
                enrollment_context=enrollment_context), _candidate_input(
                    unit=unit, subtype=subtype,
                    audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
                    priority=verdict_policy.priority,
                    anchor_kind=activity_def.applicability_expression or "",
                    window=window_rule, anchor_day=anchor_day,
                    rights_or_safety_critical=verdict_policy.rights_or_safety_critical,
                    machine_close_forbidden=verdict_policy.machine_close_forbidden,
                    match_reason="required activity outside its independent window")
        if verdict == L1Disposition.BOUNDARY:
            boundary_priority = _priority_or_unknown(_policy_verdict(
                key, priority_policies, L1Disposition.BOUNDARY))
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="跨午夜区间边界无法在瞬时精度确定",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="评估/样本时间边界待核实",
                    priority=boundary_priority,
                    anchor_kind=activity_def.applicability_expression or "",
                    window=window_rule, anchor_day=anchor_day,
                    match_reason="sub-day interval straddles the window")
        return _not_evaluable_result(
            unit=unit, reason=reason or REASON_PRECISION_INSUFFICIENT,
            gap_roles=("window",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if not bounds.determinable:
        return _not_evaluable_result(
            unit=unit, reason=bounds.reason_code or REASON_PRECISION_INSUFFICIENT,
            gap_roles=("window",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    lo_day, hi_day, complete = _day_interval_of(actual)
    if lo_day is None or hi_day is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_TIME_ROLE_MISSING,
            gap_roles=(role,),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    lo_bound = _day_date(bounds.lo_day)
    hi_bound = _day_date(bounds.hi_day)
    if lo_bound is None or hi_bound is None:
        return _not_evaluable_result(
            unit=unit, reason=REASON_PRECISION_INSUFFICIENT,
            gap_roles=("window",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    if not complete:
        # Partial-date interval: determinate only when fully in or out.
        if hi_day < lo_bound or lo_day > hi_bound:
            pass  # fall through to the mistimed positive below
        elif lo_day >= lo_bound and hi_day <= hi_bound:
            return _result(
                unit=unit, disposition=L1Disposition.NEGATIVE,
                priority=_priority_or_unknown(_policy_verdict(
                    key, priority_policies, "negative")),
                evidence=evidence, source_refs=source_refs,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                enrollment_context=enrollment_context), None
        else:
            boundary_priority = _priority_or_unknown(_policy_verdict(
                key, priority_policies, L1Disposition.BOUNDARY))
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="部分日期区间跨越窗口边界且来源完整",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                anchor_kind=activity_def.applicability_expression or "",
                window=window_rule, anchor_day=anchor_day,
                actual_start=actual.start, actual_end=actual.end,
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="评估/样本时间边界待核实",
                    priority=boundary_priority,
                    anchor_kind=activity_def.applicability_expression or "",
                    window=window_rule, anchor_day=anchor_day,
                    match_reason="partial date interval straddles the window")
    if lo_day >= lo_bound and hi_day <= hi_bound:
        return _result(
            unit=unit, disposition=L1Disposition.NEGATIVE,
            priority=_priority_or_unknown(_policy_verdict(
                key, priority_policies, "negative")),
            evidence=evidence, source_refs=source_refs,
            anchor_kind=activity_def.applicability_expression or "",
            window=window_rule, anchor_day=anchor_day,
            actual_start=actual.start, actual_end=actual.end,
            enrollment_context=enrollment_context), None
    verdict = _policy_verdict(key, priority_policies, L1Disposition.POSITIVE)
    assert verdict is not None
    subtype = _mistimed_subtype(activity_def.activity_kind)
    return _result(
        unit=unit, disposition=L1Disposition.POSITIVE,
        subtype=subtype,
        audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
        priority=verdict.priority,
        evidence=evidence, source_refs=source_refs,
        anchor_kind=activity_def.applicability_expression or "",
        window=window_rule, anchor_day=anchor_day,
        actual_start=actual.start, actual_end=actual.end,
        rights_or_safety_critical=verdict.rights_or_safety_critical,
        machine_close_forbidden=verdict.machine_close_forbidden,
        priority_reason_codes=verdict.reason_codes,
        enrollment_context=enrollment_context), _candidate_input(
            unit=unit, subtype=subtype,
            audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
            priority=verdict.priority,
            anchor_kind=activity_def.applicability_expression or "",
            window=window_rule, anchor_day=anchor_day,
            rights_or_safety_critical=verdict.rights_or_safety_critical,
            machine_close_forbidden=verdict.machine_close_forbidden,
            match_reason="required activity outside its independent window")


def _eval_actual_assignment(
    *, unit, visit_assignments, activity_assignments, bundles, activities,
    source_coverage, assignment_priority_policy, enrollment_context,
    record_locators, plan_locators,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    """Actual-assignment unit for a problematic actual object (§5.1, §7.2)."""
    # Visit-level reverse check first.
    for bundle in bundles:
        if bundle.stable_actual_object_key != unit.stable_actual_object_key:
            continue
        decision = _assignment_for_bundle(bundle.bundle_id, visit_assignments)
        if decision is None:
            continue
        evidence = _evidence_items(
            record_locators=record_locators, plan_locators=plan_locators,
            record_ids=([bundle.member_encounter_ids[0]]
                        if bundle.member_encounter_ids else []),
            plan_locator_ids=(), polarity=L1bEvidencePolarity.SUPPORTING)
        source_refs = _source_refs_for_bundle(bundle, record_locators)
        if decision.decision_status == VISIT_ASSIGNMENT_MULTI_FEASIBLE:
            boundary_priority = _priority_or_unknown(
                _resolve_assignment_verdict(assignment_priority_policy))
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="两个及以上计划访视均有完整可行依据",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="访视归属边界待核实",
                    priority=boundary_priority,
                    match_reason="multiple feasible planned visits")
        if decision.decision_status == VISIT_ASSIGNMENT_UNASSIGNED_INCONSISTENT:
            return _assignment_positive(
                unit=unit, subtype=POSITIVE_VISIT_ASSIGNMENT_INCONSISTENT,
                evidence=evidence, source_refs=source_refs,
                policy=assignment_priority_policy,
                enrollment_context=enrollment_context)
        return _not_evaluable_result(
            unit=unit, reason=REASON_MAPPING_MISSING, gap_roles=("assignment",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    # Activity-level reverse check (mislabel / duplicate consumption).
    for decision in activity_assignments:
        if _stable_key_of_activity(decision.actual_activity_id, activities) \
                != unit.stable_actual_object_key:
            continue
        evidence = _evidence_items(
            record_locators=record_locators, plan_locators=plan_locators,
            record_ids=[decision.actual_activity_id],
            plan_locator_ids=(), polarity=L1bEvidencePolarity.SUPPORTING)
        source_refs = _source_refs_for_activity_id(
            decision.actual_activity_id, activities, record_locators)
        if decision.decision_status == ACTIVITY_ASSIGNMENT_DUPLICATE_CONSUMPTION:
            return _assignment_positive(
                unit=unit, subtype=POSITIVE_VISIT_DUPLICATE,
                evidence=evidence, source_refs=source_refs,
                policy=assignment_priority_policy,
                enrollment_context=enrollment_context)
        if decision.decision_status == ACTIVITY_ASSIGNMENT_MULTI_FEASIBLE:
            boundary_priority = _priority_or_unknown(
                _resolve_assignment_verdict(assignment_priority_policy))
            return _result(
                unit=unit, disposition=L1Disposition.BOUNDARY,
                boundary_reason="活动归属存在多个可行解释",
                priority=boundary_priority,
                evidence=evidence, source_refs=source_refs,
                enrollment_context=enrollment_context), _boundary_candidate_input(
                    unit=unit, audience_label="活动归属边界待核实",
                    priority=boundary_priority,
                    match_reason="multiple feasible planned activities")
        if decision.decision_status == ACTIVITY_ASSIGNMENT_NOT_EVALUABLE \
                and PRED_ACTIVITY_CLAIM in decision.evidence_predicate_ids:
            # Complete-evidence mislabel: positive under every feasible
            # interpretation (§5.1).
            return _assignment_positive(
                unit=unit, subtype=POSITIVE_VISIT_ASSIGNMENT_INCONSISTENT,
                evidence=evidence, source_refs=source_refs,
                policy=assignment_priority_policy,
                enrollment_context=enrollment_context)
        return _not_evaluable_result(
            unit=unit, reason=REASON_COVERAGE_INCOMPLETE,
            gap_roles=("assignment",),
            evidence=evidence, source_refs=source_refs,
            record_locators=record_locators, plan_locators=plan_locators,
            enrollment_context=enrollment_context), None
    return _not_evaluable_result(
        unit=unit, reason=REASON_COVERAGE_INCOMPLETE, gap_roles=("assignment",),
        record_locators=record_locators, plan_locators=plan_locators,
        enrollment_context=enrollment_context), None


def _assignment_positive(
    *, unit, subtype, evidence, source_refs, policy, enrollment_context,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    verdict = policy and resolve_d05_priority(policy)
    priority = verdict.priority if verdict else _PRIORITY_UNKNOWN
    machine_close = verdict.machine_close_forbidden if verdict else False
    rights_safety = verdict.rights_or_safety_critical if verdict else False
    reason_codes = verdict.reason_codes if verdict else ()
    return _result(
        unit=unit, disposition=L1Disposition.POSITIVE, subtype=subtype,
        audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
        priority=priority, evidence=evidence, source_refs=source_refs,
        rights_or_safety_critical=rights_safety,
        machine_close_forbidden=machine_close,
        priority_reason_codes=reason_codes,
        enrollment_context=enrollment_context), _candidate_input(
            unit=unit, subtype=subtype,
            audience_label=POSITIVE_SUBTYPE_LABELS[subtype],
            priority=priority,
            rights_or_safety_critical=rights_safety,
            machine_close_forbidden=machine_close,
            match_reason="actual object mis-assigned or duplicate")


def _eval_schedule_consistency(
    *, unit, assignment_priority_policy, enrollment_context, plan_locators,
) -> Tuple[D05UnitResult, Optional[Dict[str, Any]]]:
    verdict = assignment_priority_policy and resolve_d05_priority(
        assignment_priority_policy)
    priority = verdict.priority if verdict else _PRIORITY_UNKNOWN
    evidence = _evidence_items(
        record_locators={}, plan_locators=plan_locators,
        record_ids=(), plan_locator_ids=unit.source_locator_ids,
        polarity=L1bEvidencePolarity.SUPPORTING)
    return _result(
        unit=unit, disposition=L1Disposition.POSITIVE,
        subtype=POSITIVE_SCHEDULE_RULE_INCONSISTENT,
        audience_label=POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SCHEDULE_RULE_INCONSISTENT],
        priority=priority,
        evidence=evidence, source_refs=(),
        rights_or_safety_critical=(verdict.rights_or_safety_critical
                                   if verdict else False),
        machine_close_forbidden=(verdict.machine_close_forbidden
                                 if verdict else False),
        priority_reason_codes=verdict.reason_codes if verdict else (),
        enrollment_context=enrollment_context), _candidate_input(
            unit=unit, subtype=POSITIVE_SCHEDULE_RULE_INCONSISTENT,
            audience_label=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SCHEDULE_RULE_INCONSISTENT],
            priority=priority,
            rights_or_safety_critical=(verdict.rights_or_safety_critical
                                       if verdict else False),
            machine_close_forbidden=(verdict.machine_close_forbidden
                                     if verdict else False),
            match_reason="plan rules cannot be simultaneously satisfied")


def _result(
    *, unit, disposition, priority, evidence, source_refs,
    enrollment_context, subtype="", audience_label="",
    boundary_reason="", not_evaluable_reason="", l0_status=None,
    anchor_kind="", window=None, anchor_day="",
    actual_start="", actual_end="",
    rights_or_safety_critical=False, machine_close_forbidden=False,
    priority_reason_codes=(),
) -> D05UnitResult:
    window_start = ""
    window_end = ""
    precision = PRECISION_DAY
    if window is not None:
        bounds = window_bounds(window_rule=window, anchor_day=anchor_day)
        if bounds.determinable:
            window_start = bounds.lo_day or ""
            window_end = bounds.hi_day or ""
        precision = window.date_precision
    return D05UnitResult(
        unit_id=unit.unit_id, subject_ref=unit.subject_ref,
        site_ref=unit.site_ref, unit_kind=unit.unit_kind,
        planned_visit_key=unit.planned_visit_key,
        planned_activity_key=unit.planned_activity_key,
        stable_actual_object_key=unit.stable_actual_object_key,
        l1_disposition=disposition, monitoring_priority=priority,
        l0_status=l0_status or L0CoverageStatus.COVERED,
        positive_subtype=subtype, audience_label=audience_label,
        query_context=enrollment_context.query_context,
        not_evaluable_reason=not_evaluable_reason,
        boundary_reason=boundary_reason,
        evaluation_window_id=unit.evaluation_window_id,
        rule_id=unit.rule_id, rule_version=unit.rule_version,
        anchor_kind=anchor_kind,
        window_start=window_start, window_end=window_end,
        precision=precision,
        actual_start=actual_start, actual_end=actual_end,
        evidence=evidence, source_record_refs=source_refs,
        classifier=unit.classifier, stable_core=unit.stable_core,
        rights_or_safety_critical=rights_or_safety_critical,
        machine_close_forbidden=machine_close_forbidden,
        priority_reason_codes=priority_reason_codes,
        source_locator_ids=tuple(sorted(
            {item.locator.locator_id() for item in evidence})))


def _not_evaluable_result(
    *, unit, reason, gap_roles, record_locators, plan_locators,
    enrollment_context, evidence=(), source_refs=(),
    l0_status=L0CoverageStatus.COVERED,
) -> D05UnitResult:
    return _result(
        unit=unit, disposition=L1Disposition.NOT_EVALUABLE,
        priority=_PRIORITY_UNKNOWN,
        evidence=evidence, source_refs=source_refs,
        enrollment_context=enrollment_context,
        not_evaluable_reason=reason, l0_status=l0_status)


def _not_applicable_result(
    *, unit, reason, authority_locator_ids, record_locators, plan_locators,
    enrollment_context,
) -> D05UnitResult:
    evidence = _evidence_items(
        record_locators=record_locators, plan_locators=plan_locators,
        record_ids=(), plan_locator_ids=authority_locator_ids,
        polarity=L1bEvidencePolarity.CONTEXT)
    return _result(
        unit=unit, disposition=L1Disposition.NOT_APPLICABLE,
        priority=_PRIORITY_UNKNOWN,
        evidence=evidence, source_refs=(),
        enrollment_context=enrollment_context)


def _candidate_input(
    *, unit, subtype, audience_label, priority,
    anchor_kind="", window=None, anchor_day="",
    rights_or_safety_critical=False, machine_close_forbidden=False,
    match_reason="",
) -> Dict[str, Any]:
    window_start = ""
    window_end = ""
    precision = PRECISION_DAY
    if window is not None:
        bounds = window_bounds(window_rule=window, anchor_day=anchor_day)
        if bounds.determinable:
            window_start = bounds.lo_day or ""
            window_end = bounds.hi_day or ""
        precision = window.date_precision
    return {
        "positive_subtype": subtype, "audience_label": audience_label,
        "monitoring_priority": priority,
        "rule_lineage": unit.rule_id or D05_RULE_LINEAGE_DEFAULT,
        "anchor_kind": anchor_kind, "anchor_start": "",
        "anchor_end": "", "window_start": window_start,
        "window_end": window_end, "precision": precision,
        "rights_or_safety_critical": rights_or_safety_critical,
        "machine_close_forbidden": machine_close_forbidden,
        "match_reason": match_reason,
    }


def _build_query_for_result(
    *, result: D05UnitResult, unit: ScheduleEvaluationUnit,
    protocol_version: str, enrollment_context: D05EnrollmentContext,
    candidate_id: str, plan_target: str = "",
) -> Optional[QueryDraftRef]:
    if result.l1_disposition != L1Disposition.POSITIVE:
        return None
    locator_ids = result.all_source_locator_ids()
    if not locator_ids:
        # No locatable supporting evidence (e.g. missing visit without
        # supplied plan locators): no Query can be bound; the positive unit
        # and its candidate still stand (§9.2 requires locatable evidence).
        return None
    if not plan_target:
        plan_target = "访视"
    if result.positive_subtype in (POSITIVE_VISIT_MISSING,
                                   POSITIVE_ASSESSMENT_MISSING,
                                   POSITIVE_SAMPLE_MISSING):
        finding = f"{result.audience_label}：截止数据截止日未见相应记录"
    elif result.positive_subtype in (POSITIVE_VISIT_OVERWINDOW,
                                     POSITIVE_ASSESSMENT_MISTIMED,
                                     POSITIVE_SAMPLE_MISTIMED):
        finding = (f"{result.audience_label}：实际记录时间 "
                   f"{result.actual_start or '未知'}，需与允许窗口核对")
    elif result.positive_subtype == POSITIVE_VISIT_ORDER_INCONSISTENT:
        finding = "访视先后顺序与方案计划次序不一致，需核实"
    elif result.positive_subtype == POSITIVE_VISIT_DUPLICATE:
        finding = "同一实际记录被重复计入多个计划单元，需核实归属"
    elif result.positive_subtype == POSITIVE_VISIT_ASSIGNMENT_INCONSISTENT:
        finding = "实际记录归属与唯一可适用计划不一致，需核实访视归属"
    else:
        finding = "方案时序要求存在不一致，需核实"
    return build_d05_query_draft(
        unit_id=result.unit_id, subject_ref=result.subject_ref,
        protocol_version=protocol_version, plan_target=plan_target,
        anchor_label=result.anchor_kind or "计划锚点",
        window_start=result.window_start, window_end=result.window_end,
        finding=finding, query_context=enrollment_context.query_context,
        candidate_id=candidate_id,
        source_locator_ids=result.all_source_locator_ids())


def _plan_target_for(
    unit: ScheduleEvaluationUnit,
    planned_visits: Sequence[PlannedVisitDefinition],
    planned_activities: Sequence[PlannedActivityDefinition],
) -> str:
    if unit.planned_activity_key:
        for activity in planned_activities:
            if activity.planned_activity_key == unit.planned_activity_key:
                return f"评估/样本 {activity.audience_name}"
    if unit.planned_visit_key:
        for visit in planned_visits:
            if visit.planned_visit_key == unit.planned_visit_key:
                return f"访视 {visit.audience_visit_name}"
    return "访视"


def _boundary_candidate_input(
    *, unit: ScheduleEvaluationUnit, audience_label: str,
    priority: str, anchor_kind: str = "", window: Optional[VisitWindowRule] = None,
    anchor_day: str = "", match_reason: str = "",
) -> Dict[str, Any]:
    """Candidate input for a boundary unit: one clue with preserved
    uncertainty (§8.4); signal type is the closed unit kind, never a
    fabricated positive subtype."""
    window_start = ""
    window_end = ""
    precision = PRECISION_DAY
    if window is not None:
        bounds = window_bounds(window_rule=window, anchor_day=anchor_day)
        if bounds.determinable:
            window_start = bounds.lo_day or ""
            window_end = bounds.hi_day or ""
        precision = window.date_precision
    return {
        "positive_subtype": unit.unit_kind,
        "audience_label": audience_label,
        "monitoring_priority": priority,
        "rule_lineage": unit.rule_id or D05_RULE_LINEAGE_DEFAULT,
        "anchor_kind": anchor_kind, "anchor_start": "",
        "anchor_end": "", "window_start": window_start,
        "window_end": window_end, "precision": precision,
        "rights_or_safety_critical": False,
        "machine_close_forbidden": False,
        "match_reason": match_reason,
    }


def _build_gap_notice(result: D05UnitResult) -> Optional[VisitCoverageGapNotice]:
    if result.l1_disposition != L1Disposition.NOT_EVALUABLE:
        return None
    labels = {
        REASON_MATURITY_RULE_MISSING: "评价成熟规则未冻结，暂无法判断是否到计划时间",
        REASON_TIME_ROLE_MISSING: "实际日期或时间角色缺失，暂无法核对时间",
        REASON_COVERAGE_INCOMPLETE: "所需来源资料不完整，暂无法完成评价",
        REASON_PRECISION_INSUFFICIENT: "日期精度或窗口端点规则不足，暂无法完成评价",
        REASON_TIME_ROLE_CONFLICT: "实际日期角色冲突，暂无法完成评价",
        REASON_ANCHOR_MISSING: "计划锚点缺失，暂无法完成评价",
        REASON_MAPPING_MISSING: "访视/活动映射不足，暂无法确定归属",
    }
    reason = result.not_evaluable_reason or REASON_COVERAGE_INCOMPLETE
    audience_text = labels.get(reason, "资料不足，暂无法完成评价")
    return VisitCoverageGapNotice(
        notice_id="", unit_id=result.unit_id, reason_code=reason,
        missing_evidence_roles=(ANCHOR_ROLE_OTHER,),
        plan_locator_ids=(),
        reachable_source_locator_ids=result.all_source_locator_ids(),
        audience_text=audience_text)


def _build_interpretation_ledgers(
    *, visit_assignments: Sequence[VisitAssignmentDecision],
    activity_assignments: Sequence[ActivityAssignmentDecision],
    rule_ids: Sequence[str],
) -> Tuple[ScheduleInterpretationLedger, ...]:
    ledgers: List[ScheduleInterpretationLedger] = []
    for decision in visit_assignments:
        if decision.decision_status == VISIT_ASSIGNMENT_UNIQUE \
                and not decision.rejected_candidate_reasons:
            continue
        interpretations = tuple(decision.candidate_planned_visit_ids)
        accepted = (decision.selected_planned_visit_id,) \
            if decision.selected_planned_visit_id else ()
        rejected = tuple(
            c for c in interpretations if c not in accepted)
        predicates = tuple(
            (i, PREDICATE_TRUE if i in accepted else PREDICATE_FALSE)
            for i in interpretations)
        if not interpretations:
            continue
        try:
            ledgers.append(ScheduleInterpretationLedger(
                ledger_id="", decision_scope=INTERPRET_SCOPE_WINDOW,
                interpretation_ids=interpretations,
                accepted_interpretation_ids=accepted,
                rejected_interpretation_ids=rejected,
                predicate_results=predicates,
                rejection_reason_codes=tuple(
                    r for r in decision.rejected_candidate_reasons
                    if r in REASON_CODES) or (REASON_MULTIPLE_FEASIBLE,),
                merge_split_repeat_reschedule_trigger_rule_ids=rule_ids,
                algorithm_version=D05_UNIT_ALGO_VERSION,
                source_locator_ids=decision.source_locator_ids))
        except ScheduleSliceError:
            continue
    for decision in activity_assignments:
        if decision.decision_status == ACTIVITY_ASSIGNMENT_UNIQUE:
            continue
        interpretations = tuple(decision.candidate_planned_activity_ids)
        accepted = tuple(decision.selected_planned_activity_ids)
        rejected = tuple(
            c for c in interpretations if c not in accepted)
        predicates = tuple(
            (i, PREDICATE_TRUE if i in accepted else PREDICATE_FALSE)
            for i in interpretations)
        if not interpretations:
            continue
        try:
            ledgers.append(ScheduleInterpretationLedger(
                ledger_id="", decision_scope=INTERPRET_SCOPE_REPEAT,
                interpretation_ids=interpretations,
                accepted_interpretation_ids=accepted,
                rejected_interpretation_ids=rejected,
                predicate_results=predicates,
                rejection_reason_codes=(REASON_MULTIPLE_FEASIBLE,),
                merge_split_repeat_reschedule_trigger_rule_ids=rule_ids,
                algorithm_version=D05_UNIT_ALGO_VERSION,
                source_locator_ids=decision.source_locator_ids))
        except ScheduleSliceError:
            continue
    return tuple(ledgers)


# ---------------------------------------------------------------------------
# Small helpers used across evaluation
# ---------------------------------------------------------------------------

def _timing_compare_instants(
    *, window_rule: VisitWindowRule, anchor_day: str,
    start: str, end: str, timezone: str,
) -> Tuple[str, str]:
    """Sub-day window verdict at instant level (challenges 26/27).

    Returns (disposition_token, reason) where disposition_token is one of
    NEGATIVE / POSITIVE / BOUNDARY / NOT_EVALUABLE.  Cross-midnight events
    require a frozen timezone (challenge 26); a missing timezone that can
    change the conclusion is not_evaluable (challenge 27).
    """
    lo_i = _parse_instant(start, timezone)
    hi_i = _parse_instant(end, timezone)
    if lo_i is None and hi_i is None:
        return L1Disposition.NOT_EVALUABLE, REASON_TIME_ROLE_MISSING
    if hi_i is None:
        hi_i = lo_i
    if lo_i is None:
        lo_i = hi_i
    if hi_i < lo_i:  # cross-midnight with complete timezone
        hi_i = hi_i + datetime.timedelta(days=1)
    anchor = _day_date(anchor_day)
    if anchor is None:
        return L1Disposition.NOT_EVALUABLE, REASON_TIME_ROLE_MISSING
    if window_rule.lower_endpoint_inclusive is None \
            or window_rule.upper_endpoint_inclusive is None:
        return L1Disposition.NOT_EVALUABLE, REASON_PRECISION_INSUFFICIENT
    lower = _offset_days(window_rule.lower_offset)
    upper = _offset_days(window_rule.upper_offset)
    grace = _offset_days(window_rule.grace_period)
    if lower is None or upper is None or grace is None:
        return L1Disposition.NOT_EVALUABLE, REASON_PRECISION_INSUFFICIENT

    def _apply(offset: int) -> datetime.date:
        if window_rule.calendar_semantics == "study_day":
            if window_rule.study_day_zero_exists is False:
                offset = offset - 1
        return anchor + datetime.timedelta(days=offset)

    lo_start, _ = _day_instant_interval(_apply(lower), _apply(lower))
    _, hi_end = _day_instant_interval(
        _apply(upper) + datetime.timedelta(days=grace),
        _apply(upper) + datetime.timedelta(days=grace))
    if not window_rule.lower_endpoint_inclusive:
        lo_start = lo_start + datetime.timedelta(days=1)
    if not window_rule.upper_endpoint_inclusive:
        hi_end = hi_end - datetime.timedelta(days=1)
    if hi_i < lo_start or lo_i > hi_end:
        return L1Disposition.POSITIVE, ""
    if lo_i >= lo_start and hi_i <= hi_end:
        return L1Disposition.NEGATIVE, ""
    return L1Disposition.BOUNDARY, REASON_INTERVAL_STRADDLES


def _parse_instant(raw: str, tz_token: str) -> Optional[datetime.datetime]:
    """Parse a sub-day datetime instant, normalized to UTC when a timezone
    is provided; None when unparseable."""
    raw = (raw or "").strip()
    if not raw:
        return None
    tz: Optional[datetime.tzinfo] = None
    token = (tz_token or "").strip()
    if token in ("UTC", "utc"):
        tz = datetime.timezone.utc
    else:
        m = re.match(r"^([+-])(\d{2}):(\d{2})$", token)
        if m:
            sign = 1 if m.group(1) == "+" else -1
            tz = datetime.timezone(
                sign * datetime.timedelta(hours=int(m.group(2)),
                                          minutes=int(m.group(3))))
    try:
        parsed = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None:
        if tz is None:
            return None
        parsed = parsed.replace(tzinfo=tz)
    return parsed.astimezone(datetime.timezone.utc)


def _anchor_day_of(
    unit: ScheduleEvaluationUnit,
    expansion: ExpectedSetExpansion,
) -> str:
    for item in expansion.anchor_day_by_visit_key:
        if item[0] == unit.planned_visit_key:
            return item[1]
    return ""


def _source_refs_for_bundle(
    bundle: Optional[ActualEncounterBundle],
    record_locators: Mapping[str, SourceLocator],
) -> Tuple[SourceRecordRef, ...]:
    if bundle is None:
        return ()
    refs: List[SourceRecordRef] = []
    seen: Set[str] = set()
    for member_id in bundle.member_encounter_ids:
        locator = record_locators.get(member_id)
        if locator is None or locator.locator_id() in seen:
            continue
        seen.add(locator.locator_id())
        refs.append(SourceRecordRef(record_id=locator.record_id,
                                    locator=locator))
    return tuple(refs)


def _source_refs_for_activity(
    activity: ActualActivityRecord,
    record_locators: Mapping[str, SourceLocator],
) -> Tuple[SourceRecordRef, ...]:
    locator = record_locators.get(activity.actual_activity_id)
    if locator is None:
        return ()
    return (SourceRecordRef(record_id=locator.record_id, locator=locator),)


def _source_refs_for_activity_id(
    activity_id: str, activities: Sequence[ActualActivityRecord],
    record_locators: Mapping[str, SourceLocator],
) -> Tuple[SourceRecordRef, ...]:
    for activity in activities:
        if activity.actual_activity_id == activity_id:
            return _source_refs_for_activity(activity, record_locators)
    return ()


def _stable_key_of_activity(
    activity_id: str, activities: Sequence[ActualActivityRecord],
) -> str:
    for activity in activities:
        if activity.actual_activity_id == activity_id:
            return activity.stable_actual_object_key
    return ""


def _bundle_start(bundle: Optional[ActualEncounterBundle]) -> str:
    return (bundle.derived_start if bundle else "") or ""


def _bundle_end(bundle: Optional[ActualEncounterBundle]) -> str:
    return (bundle.derived_end if bundle else "") or ""


def _role_for_kind(activity_kind: str) -> str:
    return {
        ACTIVITY_ASSESSMENT: "assessment",
        ACTIVITY_SAMPLE: "sample",
        ACTIVITY_PROCEDURE: "procedure",
        ACTIVITY_CONTACT: "contact",
    }.get(activity_kind, "assessment")


def _missing_subtype(activity_kind: str) -> str:
    if activity_kind == ACTIVITY_SAMPLE:
        return POSITIVE_SAMPLE_MISSING
    return POSITIVE_ASSESSMENT_MISSING


def _mistimed_subtype(activity_kind: str) -> str:
    if activity_kind == ACTIVITY_SAMPLE:
        return POSITIVE_SAMPLE_MISTIMED
    return POSITIVE_ASSESSMENT_MISTIMED


def _resolve_assignment_verdict(
    policy: Optional[D05PriorityPolicy],
) -> Optional[D05PriorityVerdict]:
    if policy is None:
        return None
    return resolve_d05_priority(policy)


def _priority_or_unknown(verdict: Optional[D05PriorityVerdict]) -> str:
    if verdict is None:
        return _PRIORITY_UNKNOWN
    return verdict.priority
