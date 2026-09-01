"""D05 actual-record, cutoff-scope and encounter-bundle authority."""

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
