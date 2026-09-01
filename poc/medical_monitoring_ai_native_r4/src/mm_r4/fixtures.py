"""Synthetic challenge-matrix fixtures for the R4 D01 AE/MH slice (worker_03).

Every fixture in this module is **deterministic, synthetic and offline**.
No real-project data, table names, thresholds or 30-day rules are encoded.
The fixtures build:

* real R2 :class:`AcceptanceService` baseline-eligible snapshots (so the
  R4 :class:`R4LifecycleAdapter` can establish and close risks through
  the frozen R2 public API);
* R4 :class:`SemanticRecord` / :class:`SemanticRecordSet` inputs covering
  every challenge category required by the frozen matrix §6 test matrix:
  five L1 dispositions, hidden cross-role cases, false-positive NCS /
  alternative diagnosis, false-negative partial date / seriousness,
  missing-role coverage, count/join attacks, and the Query-export-not-
  send / center-pattern-not-risk anti-invariants.

The factories are intentionally thin: they construct the same frozen
public value objects the production code uses, so tests exercise the real
join invariants and the real lifecycle rather than mocks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from mm_r2.acceptance import (
    ACCEPTED_BY_SYSTEM_POLICY,
    AcceptanceService,
    SnapshotAcceptanceState,
    SnapshotBinding,
)
from mm_r2.domain import (
    IdentityAlgorithm,
    ListingSnapshot,
    MappingDefinition,
    MappingResult,
    SourceRevision,
)
from mm_r2.identity import IdentityResolution, make_record_identity
from mm_r2.risk import RiskLifecycle

from .aemh import (
    AEMHUnitResult,
    ConceptEquivalence,
    EventMatchStrategy,
    ProtocolAEMHBoundary,
    REQUIRED_AEMH_ROLES,
    SemanticRecord,
    SemanticRecordSet,
    TemporalTolerance,
    evaluate_aemh_unit,
)
from .contracts import EvaluationUnit, L1Disposition, SourceLocator
from .coverage import CoverageLedger, ExpectedSet

__all__ = [
    "PROJECT_ID",
    "DOMAIN_ID",
    "RUN_ID",
    "RULE_LINEAGE",
    "UNIT_ALGO_VERSION",
    "STRATEGY_VERSION",
    "BOUNDARY_VERSION",
    "ChallengeCase",
    "ChallengeMatrix",
    "build_challenge_matrix",
    "make_locator",
    "make_record",
    "make_anchor_records",
    "make_record_set",
    "make_unit",
    "make_boundary",
    "make_strategy",
    "make_acceptance_service",
    "make_baseline_snapshot",
    "make_subsequent_snapshot",
    "make_lifecycle",
    "evaluate",
    "make_closed_ledger",
    "make_unit_evaluation",
    "attach_risk_ref",
]


# ---------------------------------------------------------------------------
# Stable synthetic constants (no project specifics, no fixed table names)
# ---------------------------------------------------------------------------

PROJECT_ID = "proj-synthetic-001"
DOMAIN_ID = "D01_aemh"
RUN_ID = "run-synthetic-001"
RULE_LINEAGE = "d01-aemh-rule-v1"
UNIT_ALGO_VERSION = "d01-unit-algo-v1"
STRATEGY_VERSION = "ems-v1"
BOUNDARY_VERSION = "pb-v1"

_DEFAULT_CONCEPT = "MedDRA:10019242"  # headache PT (synthetic placeholder)
_ALT_CONCEPT = "MedDRA:10035581"      # a distinct concept for mismatch


# ---------------------------------------------------------------------------
# Primitive builders
# ---------------------------------------------------------------------------

def make_locator(
    record_id: str,
    table_semantic: str = "reported_ae",
    *,
    snapshot_id: str = "snap-accepted-001",
    source_revision_id: str = "sr-listing-001",
) -> SourceLocator:
    return SourceLocator(
        snapshot_id=snapshot_id,
        source_revision_id=source_revision_id,
        table_semantic=table_semantic,
        record_id=record_id,
        column_or_anchor="row",
    )


def make_record(
    role: str,
    concept: str,
    record_id: str,
    *,
    event_date_raw: str = "",
    subject_ref: str = "S001",
    site_ref: str = "SITE01",
    intensity: str = "",
    seriousness_criteria: Sequence[str] = (),
    intensity_scale: str = "",
    visit_label: str = "",
    phase: str = "",
    ai_assertion: bool = False,
    note: str = "",
    clinical_significance: str = "",
    alternative_diagnosis: str = "",
    alternative_diagnosis_confirmed: bool = False,
    anchor_descriptor: str = "",
    action_taken: str = "",
    outcome: str = "",
    snapshot_id: str = "snap-accepted-001",
    source_revision_id: str = "sr-listing-001",
) -> SemanticRecord:
    return SemanticRecord(
        role=role,
        concept=concept,
        locator=make_locator(
            record_id, table_semantic=role,
            snapshot_id=snapshot_id,
            source_revision_id=source_revision_id),
        event_date_raw=event_date_raw,
        subject_ref=subject_ref,
        site_ref=site_ref,
        intensity=intensity,
        seriousness_criteria=tuple(seriousness_criteria),
        intensity_scale=intensity_scale,
        visit_label=visit_label,
        phase=phase,
        ai_assertion=ai_assertion,
        note=note,
        clinical_significance=clinical_significance,
        alternative_diagnosis=alternative_diagnosis,
        alternative_diagnosis_confirmed=alternative_diagnosis_confirmed,
        anchor_descriptor=anchor_descriptor,
        action_taken=action_taken,
        outcome=outcome,
    )


def make_anchor_records(
    subject_ref: str = "S001",
    site_ref: str = "SITE01",
    start_date: str = "2026-01-01",
    end_date: str = "2026-06-30",
    start_desc: str = "icf_date",
    end_desc: str = "end_of_treatment_plus_30d",
    *,
    snapshot_id: str = "snap-accepted-001",
    source_revision_id: str = "sr-listing-001",
) -> List[SemanticRecord]:
    return [
        make_record("subject_identity", "subject", "subj-anchor",
                    subject_ref=subject_ref, site_ref=site_ref,
                    snapshot_id=snapshot_id,
                    source_revision_id=source_revision_id),
        make_record("site_identity", "site", "site-anchor",
                    subject_ref=subject_ref, site_ref=site_ref,
                    snapshot_id=snapshot_id,
                    source_revision_id=source_revision_id),
        make_record("temporal_anchor", "anchor", "anchor-start",
                    subject_ref=subject_ref, site_ref=site_ref,
                    event_date_raw=start_date,
                    anchor_descriptor=start_desc,
                    snapshot_id=snapshot_id,
                    source_revision_id=source_revision_id),
        make_record("temporal_anchor", "anchor", "anchor-end",
                    subject_ref=subject_ref, site_ref=site_ref,
                    event_date_raw=end_date,
                    anchor_descriptor=end_desc,
                    snapshot_id=snapshot_id,
                    source_revision_id=source_revision_id),
    ]


def make_record_set(
    records: Sequence[SemanticRecord],
    *,
    subject_ref: str = "S001",
    site_ref: str = "SITE01",
    empty_covered_roles: Sequence[str] = (),
    available_roles_override: Optional[Sequence[str]] = None,
) -> SemanticRecordSet:
    anchors = make_anchor_records(subject_ref=subject_ref, site_ref=site_ref)
    all_records = list(anchors) + list(records)
    if available_roles_override is not None:
        available = tuple(sorted(set(available_roles_override)))
    else:
        available = tuple(sorted(set(r.role for r in all_records)))
    avail_set = set(available)
    ec = list(empty_covered_roles)
    for role in REQUIRED_AEMH_ROLES:
        if role not in avail_set and role not in ec:
            ec.append(role)
    return SemanticRecordSet(
        records=tuple(all_records),
        subject_ref=subject_ref,
        site_ref=site_ref,
        scope_key=subject_ref,
        available_roles=available,
        empty_covered_roles=tuple(sorted(set(ec))),
    )


def make_unit(
    scope_key: str = "S001",
    concept: str = _DEFAULT_CONCEPT,
    temporal_window: str = "study-period-v1",
    *,
    project_id: str = PROJECT_ID,
    domain_id: str = DOMAIN_ID,
) -> EvaluationUnit:
    return EvaluationUnit(
        project_id=project_id,
        domain_id=domain_id,
        scope_type="subject",
        scope_key=scope_key,
        normalized_concept_or_rule_item=concept,
        temporal_window=temporal_window,
        rule_or_knowledge_lineage=RULE_LINEAGE,
        unit_algorithm_version=UNIT_ALGO_VERSION,
    )


def make_boundary(
    *,
    boundary_id: str = "pb-d01-v1",
    version: str = BOUNDARY_VERSION,
    exclusions: Sequence[str] = (),
    applicable: bool = True,
    non_applicable_reason: str = "",
    start_anchor: str = "icf_date",
    end_anchor: str = "end_of_treatment_plus_30d",
) -> ProtocolAEMHBoundary:
    return ProtocolAEMHBoundary(
        boundary_id=boundary_id,
        version=version,
        reporting_start_anchor=start_anchor,
        reporting_end_anchor=end_anchor,
        protocol_exclusions=tuple(exclusions),
        applicable=applicable,
        non_applicable_reason=non_applicable_reason,
    )


def make_strategy(
    *,
    concept_groups: Sequence[Sequence[str]] = (),
    tolerance_days: Optional[int] = None,
    strategy_id: str = "ems-d01-v1",
    version: str = STRATEGY_VERSION,
) -> EventMatchStrategy:
    return EventMatchStrategy(
        strategy_id=strategy_id,
        version=version,
        concept_equivalence=ConceptEquivalence(
            groups=tuple(frozenset(g) for g in concept_groups),
            version=version,
        ),
        temporal_tolerance=TemporalTolerance(
            tolerance_days=tolerance_days,
            version=version,
        ),
    )


def evaluate(
    records: Sequence[SemanticRecord],
    *,
    unit: Optional[EvaluationUnit] = None,
    record_set: Optional[SemanticRecordSet] = None,
    protocol_boundary: Optional[ProtocolAEMHBoundary] = None,
    match_strategy: Optional[EventMatchStrategy] = None,
    project_id: str = PROJECT_ID,
    rule_lineage: str = RULE_LINEAGE,
    snapshot_id: str = "snap-accepted-001",
    **kwargs: Any,
) -> AEMHUnitResult:
    """Evaluate a synthetic record collection through the D01 engine."""
    _unit = unit or make_unit()
    _rs = record_set or make_record_set(records)
    _pb = protocol_boundary or make_boundary()
    _ms = match_strategy or make_strategy()
    return evaluate_aemh_unit(
        unit=_unit,
        record_set=_rs,
        protocol_boundary=_pb,
        match_strategy=_ms,
        project_id=project_id,
        rule_lineage=rule_lineage,
        snapshot_id=snapshot_id,
        **kwargs,
    )


def make_unit_evaluation(
    unit_result: AEMHUnitResult,
    *,
    snapshot_id: str = "snap-accepted-001",
    rule_lineage: str = RULE_LINEAGE,
    l0_status: str = "covered",
) -> Any:
    """Build a worker_01 :class:`UnitEvaluation` from a D01 unit result
    with caller-supplied L0/provenance."""
    return unit_result.to_unit_evaluation(
        l0_status=l0_status,
        provenance_snapshot_id=snapshot_id,
        provenance_rule_lineage=rule_lineage,
    )


def make_closed_ledger(
    unit_results: Sequence[AEMHUnitResult],
    *,
    snapshot_id: str = "snap-accepted-001",
    rule_lineage: str = RULE_LINEAGE,
    domain_id: str = DOMAIN_ID,
    run_id: str = RUN_ID,
) -> CoverageLedger:
    """Build a *closed* R4 :class:`CoverageLedger` whose expected unit
    ids exactly equal the supplied unit results' unit ids.

    Each unit result is converted to a :class:`UnitEvaluation` with the
    given provenance snapshot/rule lineage.  The ledger is closed so
    ``is_domain_complete`` is meaningful.
    """
    from .coverage import expected_set_hash
    unit_ids = [ur.unit_id for ur in unit_results]
    eset = ExpectedSet(
        expected_set_hash_value=expected_set_hash(unit_ids),
        unit_ids=tuple(unit_ids),
        domain_id=domain_id,
        run_id=run_id,
        expected_count=len(unit_ids),
    )
    ledger = CoverageLedger(expected_set=eset)
    for ur in unit_results:
        ue = make_unit_evaluation(
            ur, snapshot_id=snapshot_id, rule_lineage=rule_lineage)
        ledger.assign(ue)
    ledger.close()
    return ledger


def attach_risk_ref(
    unit_result: AEMHUnitResult,
    *,
    risk_instance_id: str,
    risk_identity_id: str,
    risk_state: str = "established",
) -> AEMHUnitResult:
    """Return a copy of ``unit_result`` with a historical risk-instance
    ref attached, so a ``NEGATIVE`` N+1 unit explicitly links the prior
    risk (Codex round-3 finding 4).
    """
    from .contracts import RiskInstanceRef
    from dataclasses import replace as _replace
    ref = RiskInstanceRef(
        risk_instance_id=risk_instance_id,
        risk_identity_id=risk_identity_id,
        risk_state=risk_state,
    )
    return _replace(
        unit_result,
        risk_instance_refs=unit_result.risk_instance_refs + (ref,))


# ---------------------------------------------------------------------------
# Acceptance-service + lifecycle factories
# ---------------------------------------------------------------------------

def make_acceptance_service(local_user: str = "test") -> AcceptanceService:
    """A fresh real :class:`AcceptanceService` for synthetic snapshots."""
    return AcceptanceService(local_user=local_user)


def _make_accepted_snapshot(
    service: AcceptanceService,
    *,
    pid: str,
    rid: str,
    sid: str,
    rows: Optional[List[Dict[str, Any]]] = None,
    eligible: bool = True,
) -> Any:
    """Build a synthetic accepted snapshot directly from public R2 APIs.

    No ``sys.path`` mutation, no import from any R2 tests/helper module
    (Codex round-3 finding 2).  Uses only public constructors:
    ``SourceRevision.from_bytes``, ``ListingSnapshot.from_content``,
    ``IdentityAlgorithm``, ``MappingDefinition``, ``MappingResult.from_verified``,
    ``make_record_identity``, ``IdentityResolution``, ``SnapshotBinding``,
    and ``AcceptanceService.register / evidence / advance``.
    """
    _rows = rows if rows is not None else [{"subject": "S001", "ae": "Nausea"}]
    source = SourceRevision.from_bytes(
        revision_id=rid, project_id=pid, source_type="listing",
        version="v1", source_bytes=b"synthetic",
    )
    snap = ListingSnapshot.from_content(
        snapshot_id=sid, project_id=pid, revision_id=rid,
        snapshot_version=f"cutoff-{sid}", rows=_rows,
    )
    algo = IdentityAlgorithm(
        algorithm_id="alg-1", name="record-id", version="1")
    mapping = MappingDefinition(
        mapping_id="m1", project_id=pid, source_revision_id=rid,
        identity_algorithm_id="alg-1", source_field="AETERM",
        canonical_field="ae_term", version="1", confidence=1.0,
        is_critical=True,
    )
    result = MappingResult.from_verified(
        result_id="mr1", project_id=pid, snapshot=snap,
        mapping=mapping, identity_algorithm=algo, record_count=len(_rows),
    )
    subjects = [r.get("subject", "S001") for r in _rows]
    rec_ids = [make_record_identity(pid, algo, {"subject": s}) for s in subjects]
    resolution = IdentityResolution(algorithm=algo, resolved=tuple(rec_ids))
    binding = SnapshotBinding(
        project_id=pid, snapshot=snap, source=source,
        identity_algorithm=algo, mapping_definitions=(mapping,),
        mapping_results=(result,), identity_resolution=resolution,
    )
    actor = ACCEPTED_BY_SYSTEM_POLICY
    service.register(binding, actor)
    service.advance(sid, SnapshotAcceptanceState.STRUCTURALLY_VALID, actor,
                    evidence=service.evidence(sid, actor, structural_validation_complete=True))
    service.advance(sid, SnapshotAcceptanceState.MAPPING_REVIEWED, actor,
                    evidence=service.evidence(sid, actor))
    service.advance(sid, SnapshotAcceptanceState.SNAPSHOT_ACCEPTED, actor,
                    evidence=service.evidence(sid, actor, approved_scope=True))
    if eligible:
        service.advance(sid, SnapshotAcceptanceState.BASELINE_ELIGIBLE, actor,
                        evidence=service.evidence(sid, actor, source_coverage_complete=True,
                                                  approved_scope=True))
    return snap


def make_baseline_snapshot(
    service: AcceptanceService,
    *,
    snapshot_id: str = "snap-accepted-001",
    revision_id: str = "sr-listing-001",
    project_id: str = PROJECT_ID,
    rows: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Register a baseline-eligible full snapshot and return its id."""
    if rows is None:
        rows = [{"subject": "S001", "ae": "Nausea"}]
    _make_accepted_snapshot(
        service, pid=project_id, rid=revision_id, sid=snapshot_id, rows=rows)
    return snapshot_id


def make_subsequent_snapshot(
    service: AcceptanceService,
    *,
    snapshot_id: str,
    revision_id: str,
    project_id: str = PROJECT_ID,
    rows: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Register a *subsequent* baseline-eligible full snapshot for close."""
    if rows is None:
        rows = [{"subject": "S001", "ae": "Nausea"}]
    _make_accepted_snapshot(
        service, pid=project_id, rid=revision_id, sid=snapshot_id, rows=rows)
    return snapshot_id


def make_lifecycle(local_user: str = "test") -> RiskLifecycle:
    return RiskLifecycle(local_user=local_user)


# ---------------------------------------------------------------------------
# Challenge matrix
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ChallengeCase:
    """One named synthetic challenge case.

    * ``name``: stable identifier.
    * ``category``: matrix §6 category (positive/negative/boundary/not_
      evaluable/fp/fn/coverage/incremental/anti-invariant/hidden).
    * ``records``: synthetic records (anchors are added automatically).
    * ``expected_l1``: the exact expected L1 disposition.
    * ``expected_candidate_count``: lower bound on candidates (>=).
    * ``expected_query_count``: lower bound on query refs (>=).
    * ``description``: one-line description for the test docstring.
    * ``kwargs``: extra evaluate kwargs (boundary/strategy overrides).
    """

    name: str
    category: str
    records: Tuple[SemanticRecord, ...]
    expected_l1: str
    expected_candidate_count: int = 0
    expected_query_count: int = 0
    description: str = ""
    kwargs: Tuple[Tuple[str, Any], ...] = ()
    subject: str = "S001"

    def evaluate_case(self, **extra: Any) -> AEMHUnitResult:
        kw = dict(self.kwargs)
        kw.update(extra)
        # ``subject_ref`` is baked into the records via make_record; it is
        # not a parameter of evaluate_aemh_unit, so do not forward it.
        return evaluate(list(self.records), **kw)


@dataclass(frozen=True)
class ChallengeMatrix:
    """The full synthetic challenge matrix for D01."""

    cases: Tuple[ChallengeCase, ...]

    def by_name(self, name: str) -> ChallengeCase:
        for c in self.cases:
            if c.name == name:
                return c
        raise KeyError(name)

    def names(self) -> Tuple[str, ...]:
        return tuple(c.name for c in self.cases)


def build_challenge_matrix() -> ChallengeMatrix:
    """Build the frozen-matrix §6 challenge set.

    Every category required by the frozen contract is represented:

    1. five exclusive L1 dispositions;
    2. hidden cross-role case (surface-normal, exposes under-reporting);
    3. false-positive: NCS-only, confirmed alternative diagnosis,
       protocol-excluded concept;
    4. false-negative: partial-date ambiguity, seriousness clue only;
    5. coverage: missing required role;
    6. anti-invariant: query-export-not-send (no send flag on Query),
       center-pattern-not-risk (no subject risk duplication);
    7. count/join: candidate ≠ source-record ≠ risk ≠ query.
    """
    cases: List[ChallengeCase] = []

    # -- 1. Five L1 dispositions ----------------------------------------

    cases.append(ChallengeCase(
        name="positive_suspected_under_report",
        category="positive",
        records=(
            make_record("reported_ae", _DEFAULT_CONCEPT, "ae-pos-1",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", _ALT_CONCEPT, "sym-pos-1",
                        event_date_raw="2026-03-15", intensity="moderate"),
        ),
        expected_l1=L1Disposition.POSITIVE,
        expected_candidate_count=1,
        expected_query_count=1,
        description="symptom with no matching reported AE -> positive clue",
    ))

    cases.append(ChallengeCase(
        name="negative_reported_match",
        category="negative",
        records=(
            make_record("reported_ae", _DEFAULT_CONCEPT, "ae-neg-1",
                        event_date_raw="2026-03-15"),
            make_record("symptom_event", _DEFAULT_CONCEPT, "sym-neg-1",
                        event_date_raw="2026-03-15", intensity="mild"),
        ),
        expected_l1=L1Disposition.NEGATIVE,
        description="symptom matches a reported AE on concept+date -> negative",
    ))

    cases.append(ChallengeCase(
        name="boundary_partial_date",
        category="boundary",
        records=(
            make_record("reported_ae", _DEFAULT_CONCEPT, "ae-bnd-1",
                        event_date_raw="2026-03-10"),
            make_record("symptom_event", _DEFAULT_CONCEPT, "sym-bnd-1",
                        event_date_raw="2026-03", intensity="moderate"),
        ),
        expected_l1=L1Disposition.BOUNDARY,
        description="month-precision date cannot resolve match -> boundary",
    ))

    cases.append(ChallengeCase(
        name="not_applicable_protocol",
        category="not_applicable",
        records=(
            make_record("reported_ae", _DEFAULT_CONCEPT, "ae-na-1",
                        event_date_raw="2026-03-01"),
        ),
        expected_l1=L1Disposition.NOT_APPLICABLE,
        kwargs=(("protocol_boundary", make_boundary(
            applicable=False,
            non_applicable_reason="该受试者在当前方案版本下不收集 AE/MH")),),
        description="protocol declares AE/MH not collected -> not_applicable",
    ))

    # -- 2. Hidden cross-role case --------------------------------------

    cases.append(ChallengeCase(
        name="hidden_cross_role_cm_indication",
        category="hidden",
        records=(
            make_record("reported_ae", _DEFAULT_CONCEPT, "ae-hidden-1",
                        event_date_raw="2026-03-01"),
            make_record("cm_indication", _ALT_CONCEPT, "cm-hidden-1",
                        event_date_raw="2026-03-20",
                        note="新增合并用药，适应证为疑似不良事件"),
        ),
        expected_l1=L1Disposition.POSITIVE,
        expected_candidate_count=1,
        expected_query_count=1,
        description="CM indication for an event with no matching AE -> hidden clue",
    ))

    # -- 3. False-positive challenges -----------------------------------

    cases.append(ChallengeCase(
        name="fp_ncs_only_no_action",
        category="false_positive",
        records=(
            make_record("reported_ae", _DEFAULT_CONCEPT, "ae-fp-ncs-1",
                        event_date_raw="2026-03-01"),
            make_record("lab_finding", _ALT_CONCEPT, "lab-fp-ncs-1",
                        event_date_raw="2026-03-15",
                        clinical_significance="NCS",
                        note="not clinically significant, no action"),
        ),
        expected_l1=L1Disposition.NEGATIVE,
        description="isolated NCS lab with no action -> negative (combination CE only)",
    ))

    cases.append(ChallengeCase(
        name="fp_confirmed_alternative_diagnosis",
        category="false_positive",
        records=(
            make_record("reported_ae", _DEFAULT_CONCEPT, "ae-fp-alt-1",
                        event_date_raw="2026-03-01"),
            make_record("exam_finding", _ALT_CONCEPT, "ex-fp-alt-1",
                        event_date_raw="2026-03-15",
                        alternative_diagnosis="确诊为非 AE 的替代诊断",
                        alternative_diagnosis_confirmed=True),
        ),
        expected_l1=L1Disposition.NEGATIVE,
        description="confirmed alternative diagnosis -> negative counterevidence",
    ))

    cases.append(ChallengeCase(
        name="fp_protocol_excluded_concept",
        category="false_positive",
        records=(
            make_record("reported_ae", _DEFAULT_CONCEPT, "ae-fp-exc-1",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", "MedDRA:PROTOCOL_EXCLUDED", "sym-fp-exc-1",
                        event_date_raw="2026-03-15", intensity="mild"),
        ),
        expected_l1=L1Disposition.NEGATIVE,
        kwargs=(("protocol_boundary", make_boundary(
            exclusions=("MedDRA:PROTOCOL_EXCLUDED",))),),
        description="protocol-excluded concept -> context evidence, not a clue",
    ))

    # -- 4. False-negative challenges -----------------------------------

    cases.append(ChallengeCase(
        name="fn_partial_date_seriousness",
        category="false_negative",
        records=(
            make_record("reported_ae", _DEFAULT_CONCEPT, "ae-fn-pd-1",
                        event_date_raw="2026-03-01"),
            make_record("healthcare_encounter", _ALT_CONCEPT, "hosp-fn-pd-1",
                        event_date_raw="2026-03",
                        seriousness_criteria=("hospitalization",)),
        ),
        expected_l1=L1Disposition.POSITIVE,
        expected_candidate_count=1,
        expected_query_count=1,
        description="hospitalization seriousness clue with partial date -> positive clue (false negative avoided)",
    ))

    # -- 5. Coverage challenge ------------------------------------------

    cases.append(ChallengeCase(
        name="coverage_missing_temporal_anchor",
        category="coverage",
        records=(
            make_record("subject_identity", "subject", "s-cov-1",
                        subject_ref="S001"),
            make_record("site_identity", "site", "st-cov-1",
                        subject_ref="S001"),
            make_record("reported_ae", _DEFAULT_CONCEPT, "ae-cov-1",
                        event_date_raw="2026-03-01"),
        ),
        expected_l1=L1Disposition.NOT_EVALUABLE,
        kwargs=(("record_set", SemanticRecordSet(
            records=(
                make_record("subject_identity", "subject", "s-cov-1"),
                make_record("site_identity", "site", "st-cov-1"),
                make_record("reported_ae", _DEFAULT_CONCEPT, "ae-cov-1",
                            event_date_raw="2026-03-01"),
            ),
            subject_ref="S001", site_ref="SITE01", scope_key="S001",
            available_roles=("subject_identity", "site_identity", "reported_ae"),
            empty_covered_roles=("reported_mh",),
        )),),
        description="missing temporal anchor -> not_evaluable (fail-closed)",
    ))

    # -- 6. Anti-invariant: query export != send ------------------------

    cases.append(ChallengeCase(
        name="anti_query_not_send",
        category="anti_invariant",
        records=(
            make_record("reported_ae", _DEFAULT_CONCEPT, "ae-aq-1",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", _ALT_CONCEPT, "sym-aq-1",
                        event_date_raw="2026-03-15", intensity="moderate"),
        ),
        expected_l1=L1Disposition.POSITIVE,
        expected_candidate_count=1,
        expected_query_count=1,
        description="Query draft is basis+finding+action; never carries a 'sent' flag",
    ))

    # -- 7. Count/join separation ---------------------------------------

    cases.append(ChallengeCase(
        name="count_join_separation",
        category="count_join",
        records=(
            make_record("reported_ae", _DEFAULT_CONCEPT, "ae-cj-1",
                        event_date_raw="2026-03-01"),
            make_record("reported_ae", _ALT_CONCEPT, "ae-cj-2",
                        event_date_raw="2026-03-02"),
            make_record("symptom_event", "MedDRA:9999999", "sym-cj-1",
                        event_date_raw="2026-03-15", intensity="severe"),
        ),
        expected_l1=L1Disposition.POSITIVE,
        expected_candidate_count=1,
        expected_query_count=1,
        description="1 candidate + 2 source records + 1 query; counts never contaminate",
    ))

    return ChallengeMatrix(cases=tuple(cases))
