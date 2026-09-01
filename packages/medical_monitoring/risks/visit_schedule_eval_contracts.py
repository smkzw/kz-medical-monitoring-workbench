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

