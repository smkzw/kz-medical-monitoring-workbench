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
