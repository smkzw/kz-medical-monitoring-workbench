"""D05 gates, evaluation-unit identity and Journey value objects."""

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
from .visit_schedule_binding import *
from .visit_schedule_binding import (
    _anchor_gate,
    _ref_ctx,
    _producer_stable_event_key,
    _anchor_binding_verdict,
)

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
