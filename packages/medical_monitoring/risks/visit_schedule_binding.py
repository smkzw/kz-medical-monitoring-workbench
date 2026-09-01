"""D05 assignment decisions and typed schedule-anchor binding."""

from __future__ import annotations

from .visit_schedule_types import *
from .visit_schedule_types import (
    _SHA256_RE,
    _ISO_DURATION_RE,
    _DAY_COUNT_RE,
    _PRECISION_RANK,
    _validate_nonempty,
    _validate_optional_str,
    _freeze_tuple,
    _canonical_sorted,
    _require_member,
    _date_precision,
    _day_date,
    _day_interval,
    _coarsest_precision,
    _tzinfo,
    _parse_instant,
    _day_instant_interval,
    _interval_compare,
    _payload_ids,
    _marker_id_list,
)
from .visit_schedule_records import *
from .visit_schedule_records import (
    _validate_record_dates,
    _record_content_hash,
    _member_effective_interval,
    _derived_bundle_interval,
)

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
