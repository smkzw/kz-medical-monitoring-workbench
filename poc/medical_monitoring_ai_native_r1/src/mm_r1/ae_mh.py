"""Synthetic AE/MH under-reporting vertical slice.

The implementation deliberately keeps four things separate:

* rows in ``ae``/``mh`` become formal :class:`CanonicalFact` values;
* signals in symptoms, laboratory, examination, hospitalization, procedure,
  CM, dosing and serious-event tables become :class:`RiskCandidate` values;
* a reported AE/MH match is counterevidence and does not create a candidate;
* lifecycle/projection/query objects remain append-only domain outputs.

No model, service or project adapter is used here.  The functions consume the
worker_01 domain and Store contracts and are deterministic for the same input
listing and identity/rule lineage.
"""

from __future__ import annotations

import datetime as _dt
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union

from .domain import (
    ArtifactCompleteness,
    ArtifactEnvelope,
    CanonicalFact,
    CoverageManifest,
    CoverageUnit,
    CoverageUnitStatus,
    PAYLOAD_ROLE_CANDIDATE,
    RISK_TYPE_POTENTIAL_UNREPORTED_AE,
    RISK_TYPE_POTENTIAL_UNREPORTED_MH,
    RiskCandidate,
    RiskIdentity,
    RiskInstance,
    RiskLifecycleState,
    RiskTransition,
    QueryDraft,
    NodeType,
    SnapshotAcceptanceState,
    SnapshotBaselineProof,
    StoreError,
    SubjectTemporalSpine,
    TemporalEvent,
    SCOPE_RISK_DOMAIN,
    SCOPE_ROW,
    SCOPE_SITE,
    SCOPE_SUBJECT,
    SCOPE_TABLE,
    content_hash,
    new_id,
    now_iso,
    to_jsonable,
)


IDENTITY_ALGORITHM = "synthetic-ae-mh-identity-v1"
RULE_LINEAGE = "synthetic-ae-mh-under-reporting-rule-v1"
DISCOVERY_NODE_ID = "ae-mh-candidate-discovery"

_SEVERITY_RANK = {
    "low": 1,
    "mild": 1,
    "medium": 2,
    "moderate": 2,
    "high": 3,
    "severe": 4,
    "critical": 4,
}

_REPORT_TABLES = {"ae": "reported_ae", "mh": "reported_mh"}
_EVIDENCE_TABLES = {
    "symptoms",
    "labs",
    "laboratory",
    "examinations",
    "hospitalizations",
    "procedures",
    "concomitant_medications",
    "cm",
    "dosing",
    "serious_events",
}
DEFAULT_REQUIRED_TABLES = (
    "ae",
    "mh",
    "symptoms",
    "labs",
    "examinations",
    "hospitalizations",
    "procedures",
    "concomitant_medications",
    "dosing",
    "serious_events",
)

_ALIASES = {
    "rash": "skin rash",
    "skin rash evaluation": "skin rash",
    "alt": "alt elevation",
    "alanine aminotransferase elevation": "alt elevation",
    "unplanned hospitalization": "unplanned admission",
    "unplanned admission": "unplanned admission",
}


@dataclass(frozen=True)
class EvidenceLink:
    """A stable, user-facing link to a synthetic listing row."""

    source_ref: str
    table: str
    record_id: str
    subject_id: str
    site_id: Optional[str]
    actual_date: Optional[str]
    evidence_domain: str
    polarity: str = "supporting"
    note: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_ref": self.source_ref,
            "table": self.table,
            "record_id": self.record_id,
            "subject_id": self.subject_id,
            "site_id": self.site_id,
            "actual_date": self.actual_date,
            "evidence_domain": self.evidence_domain,
            "polarity": self.polarity,
            "note": self.note,
        }


@dataclass
class Counterevidence:
    """Evidence that explains why a signal is not a new AE/MH candidate."""

    counterevidence_id: str
    subject_id: str
    risk_type: str
    concept: str
    kind: str
    reason: str
    evidence_refs: List[str] = field(default_factory=list)
    matched_fact_ids: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "counterevidence_id": self.counterevidence_id,
            "subject_id": self.subject_id,
            "risk_type": self.risk_type,
            "concept": self.concept,
            "kind": self.kind,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
            "matched_fact_ids": list(self.matched_fact_ids),
        }


@dataclass
class LifecycleResult:
    """Current risk instances plus append-only transitions for one run."""

    instances: List[RiskInstance] = field(default_factory=list)
    transitions: List[RiskTransition] = field(default_factory=list)
    relation_by_identity: Dict[str, str] = field(default_factory=dict)

    @property
    def by_identity(self) -> Dict[str, RiskInstance]:
        return {i.identity_key: i for i in self.instances}


@dataclass
class AEMHResult:
    """Complete deterministic output of one AE/MH analysis node."""

    project_id: str
    run_id: str
    snapshot_version: str
    reported_facts: List[CanonicalFact] = field(default_factory=list)
    candidates: List[RiskCandidate] = field(default_factory=list)
    counterevidence: List[Counterevidence] = field(default_factory=list)
    evidence_links: Dict[str, List[EvidenceLink]] = field(default_factory=dict)
    candidate_details: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Identity-level metadata/evidence survives when a high-risk candidate is
    # absent from N+1 and is carried forward by the lifecycle gate.
    identity_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    historical_evidence_refs: Dict[str, List[str]] = field(default_factory=dict)
    temporal_spines: Dict[str, SubjectTemporalSpine] = field(default_factory=dict)
    queries: List[QueryDraft] = field(default_factory=list)
    lifecycle: LifecycleResult = field(default_factory=LifecycleResult)
    coverage: Optional[CoverageManifest] = None
    coverage_complete: bool = False
    snapshot_baseline_eligible: bool = False
    required_tables: List[str] = field(default_factory=list)

    @property
    def reported_ae_count(self) -> int:
        return sum(1 for f in self.reported_facts if f.fact_type == "reported_ae")

    @property
    def reported_mh_count(self) -> int:
        return sum(1 for f in self.reported_facts if f.fact_type == "reported_mh")

    @property
    def reported_ae_mh_count(self) -> int:
        return self.reported_ae_count + self.reported_mh_count

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    def candidate_fact_separation(self) -> Dict[str, Any]:
        return {
            "candidate_ids": [c.candidate_id for c in self.candidates],
            "candidate_count": len(self.candidates),
            "reported_fact_ids": [f.fact_id for f in self.reported_facts],
            "reported_fact_count": len(self.reported_facts),
            "candidates_counted_as_reported": False,
        }

    def as_dict(self) -> Dict[str, Any]:
        return {
            "fixture_marker": "SYNTHETIC",
            "project_id": self.project_id,
            "run_id": self.run_id,
            "snapshot_version": self.snapshot_version,
            "reported_facts": to_jsonable(self.reported_facts),
            "candidates": to_jsonable(self.candidates),
            "counterevidence": to_jsonable(self.counterevidence),
            "evidence_links": {
                k: [link.as_dict() for link in v] for k, v in self.evidence_links.items()
            },
            "candidate_details": to_jsonable(self.candidate_details),
            "identity_metadata": to_jsonable(self.identity_metadata),
            "historical_evidence_refs": to_jsonable(self.historical_evidence_refs),
            "temporal_spines": to_jsonable(self.temporal_spines),
            "queries": to_jsonable(self.queries),
            "lifecycle": to_jsonable(self.lifecycle),
            "coverage": to_jsonable(self.coverage) if self.coverage else None,
            "coverage_complete": self.coverage_complete,
            "snapshot_baseline_eligible": self.snapshot_baseline_eligible,
            "required_tables": list(self.required_tables),
            "candidate_fact_separation": self.candidate_fact_separation(),
        }


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _normalise(value: Any) -> str:
    value = re.sub(r"\s+", " ", _text(value).strip().lower())
    return _ALIASES.get(value, value)


def _date(row: Mapping[str, Any]) -> Optional[str]:
    for key in ("actual_date", "onset", "start_date", "date", "event_date"):
        if row.get(key):
            return _text(row[key])[:10]
    return None


def _date_distance(left: Optional[str], right: Optional[str]) -> Optional[int]:
    if not left or not right:
        return None
    try:
        return abs((_dt.date.fromisoformat(left) - _dt.date.fromisoformat(right)).days)
    except ValueError:
        return None


def _row_id(table: str, row: Mapping[str, Any], index: int) -> str:
    return _text(row.get("record_id") or row.get("id") or f"{table}-{index + 1}")


def evidence_ref(snapshot_version: str, table: str, row: Mapping[str, Any], index: int = 0) -> str:
    """Build a synthetic, queryable row locator with no filesystem path."""
    return (
        f"SYNTHETIC|snapshot={snapshot_version}|table={table}|row="
        f"{_row_id(table, row, index)}"
    )


def _concept(row: Mapping[str, Any]) -> str:
    for key in ("concept", "indication", "symptom", "term", "event_type"):
        if row.get(key):
            return _normalise(row[key])
    return "unspecified signal"


def _risk_type(table: str, row: Mapping[str, Any]) -> str:
    explicit = _text(row.get("risk_type"))
    if explicit in (RISK_TYPE_POTENTIAL_UNREPORTED_AE, RISK_TYPE_POTENTIAL_UNREPORTED_MH):
        return explicit
    if table in ("concomitant_medications", "cm"):
        return RISK_TYPE_POTENTIAL_UNREPORTED_MH
    return RISK_TYPE_POTENTIAL_UNREPORTED_AE


def _reported_table(risk_type: str) -> str:
    return "mh" if risk_type == RISK_TYPE_POTENTIAL_UNREPORTED_MH else "ae"


def _severity(row: Mapping[str, Any]) -> str:
    raw = _normalise(row.get("severity") or "medium")
    return raw if raw in _SEVERITY_RANK else "medium"


def severity_rank(value: Optional[str]) -> int:
    """Public sorting helper; unknown severities remain below ``low``."""
    return _SEVERITY_RANK.get(_normalise(value), 0)


def _event_identity(row: Mapping[str, Any], concept: str, actual_date: Optional[str]) -> str:
    explicit = _text(row.get("event_identity"))
    if explicit:
        return _normalise(explicit)
    return f"{concept}|{actual_date or 'date-unknown'}"


def _temporal_window(row: Mapping[str, Any], actual_date: Optional[str]) -> str:
    explicit_window = _text(row.get("temporal_window") or row.get("event_window"))
    if explicit_window:
        return _normalise(explicit_window)
    # An explicit event identity is the stable cross-domain anchor.  Using the
    # row's observation date here would split one event into separate risks
    # when a procedure, dose action or follow-up examination occurs a few days
    # later; the event identity itself still carries the synthetic date anchor.
    explicit_event = _text(row.get("event_identity"))
    if explicit_event:
        return f"event:{_normalise(explicit_event)}"
    start = _text(row.get("start_date") or actual_date or "date-unknown")[:10]
    end = _text(row.get("end_date") or actual_date or start)[:10]
    return f"{start}..{end}"


def _is_candidate_signal(row: Mapping[str, Any]) -> bool:
    return bool(
        row.get("candidate_signal")
        or row.get("potential_unreported")
        or row.get("possible_ae")
        or row.get("possible_mh")
    )


def _make_identity(
    project_id: str,
    table: str,
    row: Mapping[str, Any],
    risk_type: str,
    rule_lineage: str,
    algorithm_version: str,
) -> RiskIdentity:
    concept = _concept(row)
    actual_date = _date(row)
    return RiskIdentity(
        project_id=project_id,
        scope="subject",
        subject_id=_text(row.get("subject_id")) or None,
        site_id=_text(row.get("site_id")) or None,
        risk_domain=risk_type,
        event_identity=_event_identity(row, concept, actual_date),
        normalized_concept=concept,
        temporal_window=_temporal_window(row, actual_date),
        lineage=rule_lineage,
        algorithm_version=algorithm_version,
    )


def _reported_match(
    row: Mapping[str, Any],
    risk_type: str,
    reported_by_subject: Mapping[str, Sequence[Tuple[str, int, Mapping[str, Any]]]],
) -> Optional[Tuple[str, int, Mapping[str, Any]]]:
    subject_id = _text(row.get("subject_id"))
    if not subject_id:
        return None
    concept = _concept(row)
    event_identity = _normalise(row.get("event_identity"))
    actual_date = _date(row)
    reported_table = _reported_table(risk_type)
    for table, index, candidate in reported_by_subject.get(subject_id, ()):  # type: ignore
        if table != reported_table:
            continue
        if event_identity and _normalise(candidate.get("event_identity")) == event_identity:
            return table, index, candidate
        if _concept(candidate) != concept:
            continue
        distance = _date_distance(actual_date, _date(candidate))
        if distance is None or distance <= 30:
            return table, index, candidate
    return None


def _counterevidence(
    subject_id: str,
    risk_type: str,
    concept: str,
    kind: str,
    reason: str,
    refs: Iterable[str],
    matched_fact_ids: Iterable[str] = (),
) -> Counterevidence:
    ref_list = list(dict.fromkeys(refs))
    identity = content_hash({
        "subject_id": subject_id,
        "risk_type": risk_type,
        "concept": concept,
        "kind": kind,
        "refs": ref_list,
    })[:24]
    return Counterevidence(
        counterevidence_id=f"counter_{identity}",
        subject_id=subject_id,
        risk_type=risk_type,
        concept=concept,
        kind=kind,
        reason=reason,
        evidence_refs=ref_list,
        matched_fact_ids=list(matched_fact_ids),
    )


def build_subject_temporal_spines(
    listing: Mapping[str, Sequence[Mapping[str, Any]]],
    run_id: str,
    snapshot_version: str,
) -> Dict[str, SubjectTemporalSpine]:
    """Create one shared actual-date spine per synthetic subject."""
    rows_by_subject: Dict[str, List[Tuple[str, int, Mapping[str, Any], str]]] = defaultdict(list)
    for table in sorted(listing):
        for index, row in enumerate(listing.get(table, ())):
            subject_id = _text(row.get("subject_id"))
            if not subject_id:
                continue
            rows_by_subject[subject_id].append(
                (table, index, row, evidence_ref(snapshot_version, table, row, index))
            )
    spines: Dict[str, SubjectTemporalSpine] = {}
    for subject_id, rows in sorted(rows_by_subject.items()):
        dates = sorted(d for _, _, row, _ in rows if (d := _date(row)))
        first_date = dates[0] if dates else None
        events: List[TemporalEvent] = []
        seen: Set[str] = set()
        for table, index, row, source_ref in rows:
            if source_ref in seen:
                continue
            seen.add(source_ref)
            actual_date = _date(row)
            study_day: Optional[int] = None
            if actual_date and first_date:
                distance = _date_distance(actual_date, first_date)
                if distance is not None:
                    study_day = distance + 1
            events.append(TemporalEvent(
                event_id=source_ref,
                subject_id=subject_id,
                event_type=_text(row.get("event_type") or row.get("signal_type") or table),
                actual_date=actual_date,
                study_day=study_day,
                visit_label=_text(row.get("visit_label")) or None,
                phase=_text(row.get("phase")) or None,
                source_refs=[source_ref],
            ))
        spines[subject_id] = SubjectTemporalSpine(
            subject_id=subject_id,
            run_id=run_id,
            events=sorted(events, key=lambda event: (
                event.actual_date is None,
                event.actual_date or "",
                event.event_id,
            )),
        )
    return spines


def build_subject_temporal_spine(
    listing: Mapping[str, Sequence[Mapping[str, Any]]],
    subject_id: str,
    run_id: str,
    snapshot_version: str,
) -> SubjectTemporalSpine:
    """Singular convenience API backed by the same spine builder."""
    return build_subject_temporal_spines(listing, run_id, snapshot_version).get(
        subject_id,
        SubjectTemporalSpine(subject_id=subject_id, run_id=run_id),
    )


def discover_ae_mh(
    listing: Mapping[str, Sequence[Mapping[str, Any]]],
    project_id: str,
    run_id: str,
    snapshot_version: str,
    *,
    node_id: str = DISCOVERY_NODE_ID,
    required_tables: Optional[Sequence[str]] = None,
    rule_lineage: str = RULE_LINEAGE,
    algorithm_version: str = IDENTITY_ALGORITHM,
) -> AEMHResult:
    """Discover synthetic AE/MH candidates and formal reported facts.

    The returned coverage manifest includes table, row, subject, site and risk
    domain units. Missing required tables are explicitly marked
    ``not_evaluable`` and ``coverage_complete`` is false; the function never
    silently turns absent input into a clean analysis.
    """
    required = list(dict.fromkeys(required_tables or DEFAULT_REQUIRED_TABLES))
    expected: List[CoverageUnit] = []
    produced: List[CoverageUnit] = []
    coverage_complete = True
    for table in required:
        if table not in listing:
            expected.append(CoverageUnit(
                scope=SCOPE_TABLE,
                key=table,
                status=CoverageUnitStatus.NOT_EVALUABLE,
                reason=f"{table} is absent from the {snapshot_version} full listing",
            ))
            coverage_complete = False
            continue
        expected.append(CoverageUnit(scope=SCOPE_TABLE, key=table))
        produced.append(CoverageUnit(
            scope=SCOPE_TABLE, key=table, status=CoverageUnitStatus.COVERED,
        ))

    reported_facts: List[CanonicalFact] = []
    reported_rows: Dict[str, List[Tuple[str, int, Mapping[str, Any]]]] = defaultdict(list)
    subjects: Set[str] = set()
    sites: Set[str] = set()
    risk_domains: Set[str] = set()
    for table in ("ae", "mh"):
        for index, row in enumerate(listing.get(table, ())):
            subject_id = _text(row.get("subject_id"))
            site_id = _text(row.get("site_id")) or None
            if subject_id:
                subjects.add(subject_id)
            if site_id:
                sites.add(site_id)
            if not subject_id:
                coverage_complete = False
                continue
            ref = evidence_ref(snapshot_version, table, row, index)
            body = dict(row)
            body.setdefault("fixture_marker", "SYNTHETIC")
            fact = CanonicalFact(
                fact_type=_REPORT_TABLES[table],
                body=body,
                subject_id=subject_id,
                site_id=site_id,
                source_refs=[ref],
                fact_id=f"fact_{content_hash({'run_id': run_id, 'ref': ref})[:24]}",
            )
            fact.fact_hash = fact.canonical_hash()
            reported_facts.append(fact)
            reported_rows[subject_id].append((table, index, row))

            expected.append(CoverageUnit(scope=SCOPE_ROW, key=ref))
            produced.append(CoverageUnit(
                scope=SCOPE_ROW, key=ref, status=CoverageUnitStatus.COVERED,
            ))

    candidates: List[RiskCandidate] = []
    counterevidence: List[Counterevidence] = []
    links: Dict[str, List[EvidenceLink]] = defaultdict(list)
    details: Dict[str, Dict[str, Any]] = {}
    identity_metadata: Dict[str, Dict[str, Any]] = {}
    for table in sorted(listing):
        if table in _REPORT_TABLES:
            continue
        rows = listing.get(table, ())
        if not isinstance(rows, (list, tuple)):
            raise ValueError(f"listing table '{table}' must be a list")
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise ValueError(f"listing row {table}[{index}] must be a mapping")
            subject_id = _text(row.get("subject_id"))
            site_id = _text(row.get("site_id")) or None
            ref = evidence_ref(snapshot_version, table, row, index)
            expected.append(CoverageUnit(scope=SCOPE_ROW, key=ref))
            produced.append(CoverageUnit(
                scope=SCOPE_ROW, key=ref, status=CoverageUnitStatus.COVERED,
            ))
            if subject_id:
                subjects.add(subject_id)
            else:
                coverage_complete = False
                continue
            if site_id:
                sites.add(site_id)
            risk_type = _risk_type(table, row)
            concept = _concept(row)
            risk_domains.add(risk_type)
            actual_date = _date(row)
            link = EvidenceLink(
                source_ref=ref,
                table=table,
                record_id=_row_id(table, row, index),
                subject_id=subject_id,
                site_id=site_id,
                actual_date=actual_date,
                evidence_domain=_text(row.get("signal_type") or table),
                polarity="supporting" if _is_candidate_signal(row) else "context",
                note=_text(row.get("note")),
            )

            if row.get("counterevidence_for"):
                counterevidence.append(_counterevidence(
                    subject_id,
                    risk_type,
                    concept,
                    "data_correction",
                    f"{table} row explicitly counters event {row.get('counterevidence_for')}",
                    [ref],
                ))
            if not _is_candidate_signal(row):
                continue
            matched = _reported_match(row, risk_type, reported_rows)
            if matched is not None:
                matched_table, matched_index, matched_row = matched
                matched_ref = evidence_ref(snapshot_version, matched_table, matched_row, matched_index)
                matched_fact = next(
                    (
                        fact for fact in reported_facts
                        if fact.source_refs == [matched_ref]
                    ),
                    None,
                )
                counterevidence.append(_counterevidence(
                    subject_id,
                    risk_type,
                    concept,
                    "reported_match",
                    f"signal matches an existing reported {matched_table.upper()} record",
                    [ref, matched_ref],
                    [matched_fact.fact_id] if matched_fact else (),
                ))
                continue

            identity = _make_identity(
                project_id, table, row, risk_type, rule_lineage, algorithm_version,
            )
            candidate_id = (
                f"candidate_{identity.stable_key()[:24]}_"
                f"{content_hash({'run_id': run_id, 'ref': ref})[:12]}"
            )
            candidate = RiskCandidate(
                candidate_id=candidate_id,
                run_id=run_id,
                node_id=node_id,
                risk_type=risk_type,
                risk_domain=risk_type,
                subject_id=subject_id,
                site_id=site_id,
                identity=identity,
                severity=_severity(row),
                evidence_refs=[ref],
                created_at=now_iso(),
            )
            candidates.append(candidate)
            links[candidate_id].append(link)
            identity_key = identity.stable_key()
            identity_metadata.setdefault(identity_key, {
                "fixture_marker": "SYNTHETIC",
                "subject_id": subject_id,
                "site_id": site_id,
                "risk_type": risk_type,
                "risk_domain": risk_type,
                "concept": concept,
                "event_identity": identity.event_identity,
                "temporal_window": identity.temporal_window,
            })
            details[candidate_id] = {
                "fixture_marker": "SYNTHETIC",
                "table": table,
                "record_id": _row_id(table, row, index),
                "concept": concept,
                "actual_date": actual_date,
                "event_identity": identity.event_identity,
                "identity_key": identity.stable_key(),
                "identity_ambiguous": bool(row.get("identity_ambiguous")),
                "candidate_not_fact": True,
            }

    for subject_id in subjects:
        expected.append(CoverageUnit(scope=SCOPE_SUBJECT, key=subject_id))
        produced.append(CoverageUnit(
            scope=SCOPE_SUBJECT, key=subject_id, status=CoverageUnitStatus.COVERED,
        ))
    for site_id in sites:
        expected.append(CoverageUnit(scope=SCOPE_SITE, key=site_id))
        produced.append(CoverageUnit(
            scope=SCOPE_SITE, key=site_id, status=CoverageUnitStatus.COVERED,
        ))
    for risk_domain in sorted(risk_domains):
        expected.append(CoverageUnit(scope=SCOPE_RISK_DOMAIN, key=risk_domain))
        produced.append(CoverageUnit(
            scope=SCOPE_RISK_DOMAIN, key=risk_domain, status=CoverageUnitStatus.COVERED,
        ))
    coverage = CoverageManifest(expected=expected, produced=produced).reconcile()
    coverage_ok, _ = coverage.is_fully_covered()
    coverage_complete = coverage_complete and coverage_ok
    return AEMHResult(
        project_id=project_id,
        run_id=run_id,
        snapshot_version=snapshot_version,
        reported_facts=reported_facts,
        candidates=candidates,
        counterevidence=counterevidence,
        evidence_links=dict(links),
        candidate_details=details,
        identity_metadata=identity_metadata,
        temporal_spines=build_subject_temporal_spines(listing, run_id, snapshot_version),
        coverage=coverage,
        coverage_complete=coverage_complete,
        required_tables=required,
    )


# Descriptive aliases for callers that prefer the full name.
discover_candidates = discover_ae_mh
discover_ae_mh_candidates = discover_ae_mh


def build_ae_mh_artifact(result: AEMHResult) -> ArtifactEnvelope:
    """Wrap candidate analysis in the shared candidate-only artifact contract."""
    evidence_refs = list(dict.fromkeys(
        ref
        for candidate in result.candidates
        for ref in candidate.evidence_refs
    ))
    completeness = (
        ArtifactCompleteness.COMPLETE
        if result.coverage_complete
        else ArtifactCompleteness.NOT_EVALUABLE
    )
    payload = {
        "fixture_marker": "SYNTHETIC",
        "candidate_fact_separation": result.candidate_fact_separation(),
        "candidates": to_jsonable(result.candidates),
        "counterevidence": to_jsonable(result.counterevidence),
        "reported_fact_ids_for_matching_only": [fact.fact_id for fact in result.reported_facts],
        "queries": to_jsonable(result.queries),
        "lifecycle": to_jsonable(result.lifecycle),
    }
    return ArtifactEnvelope(
        artifact_type="synthetic_ae_mh_under_reporting",
        version="r1",
        run_id=result.run_id,
        node_id=DISCOVERY_NODE_ID,
        node_type=NodeType.AI_CANDIDATE,
        payload=payload,
        payload_role=PAYLOAD_ROLE_CANDIDATE,
        input_hashes=[content_hash({
            "project_id": result.project_id,
            "snapshot_version": result.snapshot_version,
            "coverage": to_jsonable(result.coverage),
        })],
        evidence_refs=evidence_refs,
        coverage=result.coverage,
        completeness=completeness,
        qc_status="deterministic_coverage_checked",
    )


def query_text(query: QueryDraft) -> str:
    """Render the exact three-part Chinese Query draft shape."""
    return f"依据：{query.basis}\n发现：{query.finding}\n行动项：{query.action}"


def make_query_drafts(result: AEMHResult) -> List[QueryDraft]:
    """Create one draft per risk identity, with evidence links preserved."""
    grouped: Dict[str, List[RiskCandidate]] = defaultdict(list)
    for candidate in result.candidates:
        grouped[candidate.identity.stable_key()].append(candidate)
    queries: List[QueryDraft] = []
    for identity_key, group in sorted(grouped.items()):
        representative = sorted(
            group,
            key=lambda c: (-severity_rank(c.severity), c.candidate_id),
        )[0]
        detail = result.candidate_details.get(representative.candidate_id, {})
        refs: List[str] = []
        for candidate in group:
            refs.extend(candidate.evidence_refs)
        refs = list(dict.fromkeys(refs))
        subject = representative.subject_id or "未识别受试者"
        date = detail.get("actual_date") or representative.identity.temporal_window
        concept = detail.get("concept") or representative.identity.normalized_concept
        basis = (
            "本次 SYNTHETIC 全量 listing 的 AE/MH 漏报核查规则要求对症状、"
            "检查/实验室、操作/住院、CM 适应证和给药处置等跨域信号与已报告 AE/MH 逐一匹配"
        )
        finding = (
            f"受试者 {subject} 在 {date} 出现“{concept}”信号，"
            "当前 AE/MH listing 未发现可与该线索对应的记录；"
            f"证据定位：{', '.join(refs)}"
        )
        action = (
            "请核实该信号是否构成 AE/MH；如构成，请补充相应 AE/MH 记录并说明起始日期、"
            "严重程度、因果性及处置；如不构成，请说明医学判断和依据"
        )
        query_id = f"query_{content_hash({'run_id': result.run_id, 'identity': identity_key})[:24]}"
        queries.append(QueryDraft(
            query_id=query_id,
            run_id=result.run_id,
            basis=basis,
            finding=finding,
            action=action,
            subject_id=representative.subject_id,
            site_id=representative.site_id,
            evidence_refs=refs,
            status="draft",
            created_at=now_iso(),
        ))
    result.queries = queries
    return queries


def _instance_id(identity_key: str) -> str:
    return f"risk_{identity_key[:32]}"


def _transition(
    instance_id: str,
    from_state: Optional[RiskLifecycleState],
    to_state: RiskLifecycleState,
    kind: str,
    reason: str,
    evidence_refs: Iterable[str] = (),
) -> RiskTransition:
    refs = list(dict.fromkeys(evidence_refs))
    transition_content = {
        'instance_id': instance_id,
        'from': from_state.value if from_state else None,
        'to': to_state.value,
        'kind': kind,
        'reason': reason,
        'evidence_refs': refs,
    }
    transition_id = f"transition_{content_hash(transition_content)[:24]}"
    return RiskTransition(
        transition_id=transition_id,
        instance_id=instance_id,
        from_state=from_state,
        to_state=to_state,
        kind=kind,
        reason=reason,
        evidence_refs=refs,
        created_at=now_iso(),
    )


def _previous_instances(
    previous_candidates: Sequence[RiskCandidate],
    previous_instances: Sequence[RiskInstance],
) -> Dict[str, RiskInstance]:
    by_key = {i.identity_key: i for i in previous_instances}
    for candidate in previous_candidates:
        key = candidate.identity.stable_key()
        by_key.setdefault(key, RiskInstance(
            instance_id=_instance_id(key),
            run_id=candidate.run_id,
            identity_key=key,
            lifecycle_state=RiskLifecycleState.ESTABLISHED,
            current_severity=candidate.severity,
            opened_at=candidate.created_at or now_iso(),
            updated_at=candidate.created_at or now_iso(),
        ))
    return by_key


def _highest_previous_severity(
    key: str,
    previous_candidates_by_key: Mapping[str, Sequence[RiskCandidate]],
    instance: RiskInstance,
) -> str:
    values = [c.severity for c in previous_candidates_by_key.get(key, ())]
    values.append(instance.current_severity)
    return max(values, key=severity_rank) or "medium"


def resolve_baseline_eligibility(
    claim: Union[bool, SnapshotBaselineProof] = False,
    *,
    store: Any = None,
    snapshot_id: Optional[str] = None,
    expected_project_id: Optional[str] = None,
    expected_snapshot_version: Optional[str] = None,
) -> bool:
    """Public authority boundary for snapshot baseline eligibility.

    Authorization requires a live Store lookup with ``store``, ``snapshot_id``
    and the expected project identity.  The stored snapshot must belong to that
    project; when a snapshot version is supplied it must match as well.  A bare
    bool, a manufactured :class:`SnapshotBaselineProof`, or
    ``SnapshotBaselineProof.from_acceptance`` is evidence projection only and
    never grants resolution/merge/split authority.  This prevents both caller
    self-attestation and an eligible snapshot from another project authorizing
    the current analysis.
    """
    del claim  # projection-only; never authoritative
    if store is None or not snapshot_id or not expected_project_id:
        return False
    try:
        snapshot = store.get_listing_snapshot(snapshot_id)
        acceptance = store.get_acceptance(snapshot_id)
    except StoreError:
        return False
    if snapshot.project_id != expected_project_id:
        return False
    if expected_snapshot_version is not None and snapshot.snapshot_version != expected_snapshot_version:
        return False
    return (
        acceptance.state == SnapshotAcceptanceState.BASELINE_ELIGIBLE
        and not bool(getattr(acceptance, "blocked", False))
    )


def _single_candidate_project_id(
    current_candidates: Sequence[RiskCandidate],
    previous_candidates: Sequence[RiskCandidate],
) -> Optional[str]:
    """Return the one project shared by a lifecycle rewrite, else fail closed."""
    project_ids = {
        candidate.identity.project_id
        for candidate in tuple(current_candidates) + tuple(previous_candidates)
        if candidate.identity.project_id
    }
    return next(iter(project_ids)) if len(project_ids) == 1 else None


def reconcile_risk_lifecycle(
    current_candidates: Sequence[RiskCandidate],
    *,
    previous_candidates: Sequence[RiskCandidate] = (),
    previous_instances: Sequence[RiskInstance] = (),
    current_run_id: str = "",
    current_coverage_complete: bool = True,
    current_snapshot_baseline_eligible: bool = False,
    identity_ambiguous_keys: Iterable[str] = (),
    rules_changed: bool = False,
    mapping_changed: bool = False,
    identity_algorithm_changed: bool = False,
    merge_groups: Optional[Mapping[str, Sequence[str]]] = None,
    split_groups: Optional[Mapping[str, Sequence[str]]] = None,
) -> LifecycleResult:
    """Reconcile risk identities without destructive or misleading closure.

    ``merge_groups`` maps the target identity key to source keys.  ``split_groups``
    maps one source key to target keys.  Identity/rule/mapping changes supersede
    old identities; they are never represented as clinical resolution.  Missing
    high/severe risks are carried forward, while a missing low/medium risk is
    ``resolved_by_data`` only when the current full listing is complete and
    ``current_snapshot_baseline_eligible`` is True.

    This pure deterministic core accepts an already-verified bool for internal
    and focused unit tests only.  Public authority entry points must resolve that
    bool exclusively through :func:`resolve_baseline_eligibility` (live Store
    lookup); they must not pass a caller self-attested True.
    Explicit merge/split lineage changes use that same gate; otherwise both
    current and prior identities fall through to ``not_evaluable``.
    """
    coverage_complete = current_coverage_complete is True
    snapshot_baseline_eligible = current_snapshot_baseline_eligible is True
    identity_lineage_gate = coverage_complete and snapshot_baseline_eligible
    current_by_key: Dict[str, List[RiskCandidate]] = defaultdict(list)
    for candidate in current_candidates:
        current_by_key[candidate.identity.stable_key()].append(candidate)
    previous_by_key: Dict[str, List[RiskCandidate]] = defaultdict(list)
    for candidate in previous_candidates:
        previous_by_key[candidate.identity.stable_key()].append(candidate)
    previous = _previous_instances(previous_candidates, previous_instances)
    ambiguous = set(identity_ambiguous_keys)
    result = LifecycleResult()
    handled_current: Set[str] = set()
    handled_previous: Set[str] = set()

    def add_instance(
        key: str,
        state: RiskLifecycleState,
        candidate: Optional[RiskCandidate],
        prior: Optional[RiskInstance],
        ambiguous_flag: bool = False,
    ) -> RiskInstance:
        severity = candidate.severity if candidate is not None else (prior.current_severity if prior else None)
        instance = RiskInstance(
            instance_id=prior.instance_id if prior else _instance_id(key),
            run_id=current_run_id or (candidate.run_id if candidate else (prior.run_id if prior else "")),
            identity_key=key,
            lifecycle_state=state,
            identity_ambiguous=ambiguous_flag or (prior.identity_ambiguous if prior else False),
            current_severity=severity,
            opened_at=prior.opened_at if prior else (candidate.created_at if candidate else now_iso()),
            updated_at=now_iso(),
        )
        result.instances.append(instance)
        return instance

    def refs_for(key: str) -> List[str]:
        return list(dict.fromkeys(
            ref for candidate in current_by_key.get(key, ()) for ref in candidate.evidence_refs
        ))

    if identity_lineage_gate:
        # Explicit merge semantics: source identities are superseded by one target.
        for target_key, source_keys in sorted((merge_groups or {}).items()):
            source_keys = list(source_keys)
            if target_key not in current_by_key:
                continue
            target_candidate = sorted(current_by_key[target_key], key=lambda c: c.candidate_id)[0]
            target_prior = previous.get(target_key)
            target_instance = add_instance(
                target_key,
                RiskLifecycleState.ESTABLISHED,
                target_candidate,
                target_prior,
            )
            result.relation_by_identity[target_key] = "merge_target"
            result.transitions.append(_transition(
                target_instance.instance_id,
                target_prior.lifecycle_state if target_prior else None,
                target_instance.lifecycle_state,
                "merge",
                "multiple evidence identities were deterministically merged into one risk identity",
                refs_for(target_key),
            ))
            handled_current.add(target_key)
            for source_key in source_keys:
                prior = previous.get(source_key)
                if prior is None:
                    continue
                handled_previous.add(source_key)
                source_instance = add_instance(
                    source_key,
                    RiskLifecycleState.SUPERSEDED,
                    None,
                    prior,
                )
                result.relation_by_identity[source_key] = "merge_source"
                result.transitions.append(_transition(
                    source_instance.instance_id,
                    prior.lifecycle_state,
                    RiskLifecycleState.SUPERSEDED,
                    "merge",
                    f"source identity merged into {target_key}; not a clinical resolution",
                    refs_for(target_key),
                ))

        # Explicit split semantics: one old identity is superseded by several new ones.
        for source_key, target_keys in sorted((split_groups or {}).items()):
            prior = previous.get(source_key)
            if prior is not None:
                handled_previous.add(source_key)
                old_instance = add_instance(source_key, RiskLifecycleState.SUPERSEDED, None, prior)
                result.relation_by_identity[source_key] = "split_source"
                result.transitions.append(_transition(
                    old_instance.instance_id,
                    prior.lifecycle_state,
                    RiskLifecycleState.SUPERSEDED,
                    "split",
                    "one prior identity split into distinct current identities; not a clinical resolution",
                ))
            for target_key in target_keys:
                if target_key not in current_by_key:
                    continue
                candidate = sorted(current_by_key[target_key], key=lambda c: c.candidate_id)[0]
                instance = add_instance(target_key, RiskLifecycleState.ESTABLISHED, candidate, previous.get(target_key))
                result.relation_by_identity[target_key] = "split_target"
                result.transitions.append(_transition(
                    instance.instance_id,
                    previous.get(target_key).lifecycle_state if previous.get(target_key) else None,
                    instance.lifecycle_state,
                    "split",
                    f"new identity split from {source_key}",
                    refs_for(target_key),
                ))
                handled_current.add(target_key)

    # Current identities: establish, reopen or severity transition.
    for key in sorted(current_by_key):
        if key in handled_current:
            continue
        candidates = current_by_key[key]
        candidate = sorted(candidates, key=lambda c: (-severity_rank(c.severity), c.candidate_id))[0]
        prior = previous.get(key)
        if key in ambiguous:
            instance = add_instance(key, RiskLifecycleState.NOT_EVALUABLE, candidate, prior, True)
            result.relation_by_identity[key] = "identity_ambiguous"
            result.transitions.append(_transition(
                instance.instance_id,
                prior.lifecycle_state if prior else None,
                RiskLifecycleState.NOT_EVALUABLE,
                "identity_ambiguous",
                "same-event identity cannot be determined; automatic merge and closure are blocked",
                refs_for(key),
            ))
            handled_current.add(key)
            if prior:
                handled_previous.add(key)
            continue
        if not coverage_complete or not snapshot_baseline_eligible:
            state = RiskLifecycleState.NOT_EVALUABLE
            kind = "not_evaluable"
            reason = (
                "current full-listing coverage is incomplete; candidate remains visible "
                "without formal closure"
                if not coverage_complete
                else "current full listing is not baseline-eligible; candidate remains "
                "visible without formal closure"
            )
            from_state = prior.lifecycle_state if prior else None
        elif prior is None:
            state = RiskLifecycleState.ESTABLISHED
            kind = "establish"
            reason = "new evidence-supported AE/MH under-reporting candidate"
            from_state = None
        elif prior.lifecycle_state in (
            RiskLifecycleState.RESOLVED_BY_DATA,
            RiskLifecycleState.CLOSED,
            RiskLifecycleState.SUPERSEDED,
        ):
            state = RiskLifecycleState.REOPENED
            kind = "reopen"
            reason = "same stable risk identity reappeared in an accepted full listing"
            from_state = prior.lifecycle_state
        else:
            old_rank = severity_rank(prior.current_severity)
            new_rank = severity_rank(candidate.severity)
            if new_rank > old_rank:
                state, kind, reason = RiskLifecycleState.ESCALATED, "escalate", "candidate severity increased"
            elif new_rank < old_rank:
                state, kind, reason = RiskLifecycleState.DE_ESCALATED, "de_escalate", "candidate severity decreased"
            else:
                state, kind, reason = prior.lifecycle_state, "carry_forward", "same stable risk identity remains present"
            from_state = prior.lifecycle_state
        if (
            len(candidates) > 1
            and key not in ambiguous
            and coverage_complete
            and snapshot_baseline_eligible
        ):
            # Several independent evidence domains support one stable identity.
            # Keep one RiskInstance, but retain an explicit merge transition so
            # the longitudinal record explains the many-to-one reconciliation.
            kind = "merge"
            reason = "multiple evidence-domain candidates merged under one stable risk identity"
        instance = add_instance(key, state, candidate, prior)
        result.relation_by_identity[key] = "current"
        result.transitions.append(_transition(
            instance.instance_id,
            from_state,
            state,
            kind,
            reason,
            refs_for(key),
        ))
        handled_current.add(key)
        if prior:
            handled_previous.add(key)

    # Missing prior identities: never use disappearance as a universal close.
    for key in sorted(previous):
        if key in handled_previous or key in current_by_key:
            continue
        prior = previous[key]
        prior_severity = _highest_previous_severity(key, previous_by_key, prior)
        if rules_changed or mapping_changed or identity_algorithm_changed:
            state = RiskLifecycleState.SUPERSEDED
            kind = "supersede"
            reason = "identity/rule/mapping lineage changed; absence is not clinical resolution"
        elif not coverage_complete or not snapshot_baseline_eligible:
            state = RiskLifecycleState.NOT_EVALUABLE
            kind = "not_evaluable"
            reason = (
                "current full-listing coverage is incomplete; absence cannot support closure"
                if not coverage_complete
                else "current full listing is not baseline-eligible; absence cannot support closure"
            )
        elif severity_rank(prior_severity) >= severity_rank("high"):
            # This is the safety gate requested by the design: high/severe risks
            # remain visible even if the row disappears from N+1.
            state = prior.lifecycle_state
            kind = "carry_forward_high_risk"
            reason = "high/severe risk disappeared from N+1; no automatic closure is permitted"
        else:
            state = RiskLifecycleState.RESOLVED_BY_DATA
            kind = "resolve"
            reason = "accepted complete N+1 full listing shows the prior low/medium signal is absent or corrected"
        instance = add_instance(key, state, None, prior)
        result.relation_by_identity[key] = kind
        result.transitions.append(_transition(
            instance.instance_id,
            prior.lifecycle_state,
            state,
            kind,
            reason,
        ))

    # Stable output order: medium/high risks first, then identity.
    result.instances.sort(key=lambda i: (-severity_rank(i.current_severity), i.identity_key))
    return result


def mark_identity_ambiguous(
    candidate: RiskCandidate,
    *,
    current_run_id: Optional[str] = None,
) -> LifecycleResult:
    """Small explicit API for a fail-closed identity ambiguity case."""
    key = candidate.identity.stable_key()
    return reconcile_risk_lifecycle(
        [candidate],
        current_run_id=current_run_id or candidate.run_id,
        identity_ambiguous_keys=[key],
    )


def merge_risk_identities(
    current_candidates: Sequence[RiskCandidate],
    previous_candidates: Sequence[RiskCandidate],
    target_key: str,
    source_keys: Sequence[str],
    *,
    current_run_id: str = "",
    current_coverage_complete: bool = True,
    current_snapshot_baseline_eligible: Union[bool, SnapshotBaselineProof] = False,
    store: Any = None,
    snapshot_id: Optional[str] = None,
) -> LifecycleResult:
    """Public merge entry: baseline gate is Store-bound via store+snapshot_id."""
    return reconcile_risk_lifecycle(
        current_candidates,
        previous_candidates=previous_candidates,
        current_run_id=current_run_id,
        current_coverage_complete=current_coverage_complete,
        current_snapshot_baseline_eligible=resolve_baseline_eligibility(
            current_snapshot_baseline_eligible,
            store=store,
            snapshot_id=snapshot_id,
            expected_project_id=_single_candidate_project_id(
                current_candidates, previous_candidates
            ),
        ),
        merge_groups={target_key: list(source_keys)},
    )


def split_risk_identity(
    current_candidates: Sequence[RiskCandidate],
    previous_candidates: Sequence[RiskCandidate],
    source_key: str,
    target_keys: Sequence[str],
    *,
    current_run_id: str = "",
    current_coverage_complete: bool = True,
    current_snapshot_baseline_eligible: Union[bool, SnapshotBaselineProof] = False,
    store: Any = None,
    snapshot_id: Optional[str] = None,
) -> LifecycleResult:
    """Public split entry: baseline gate is Store-bound via store+snapshot_id."""
    return reconcile_risk_lifecycle(
        current_candidates,
        previous_candidates=previous_candidates,
        current_run_id=current_run_id,
        current_coverage_complete=current_coverage_complete,
        current_snapshot_baseline_eligible=resolve_baseline_eligibility(
            current_snapshot_baseline_eligible,
            store=store,
            snapshot_id=snapshot_id,
            expected_project_id=_single_candidate_project_id(
                current_candidates, previous_candidates
            ),
        ),
        split_groups={source_key: list(target_keys)},
    )


def run_ae_mh_vertical_slice(
    listing: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    project_id: str,
    run_id: str,
    snapshot_version: str,
    previous_result: Optional[AEMHResult] = None,
    current_coverage_complete: Optional[bool] = None,
    current_snapshot_baseline_eligible: Union[bool, SnapshotBaselineProof] = False,
    store: Any = None,
    snapshot_id: Optional[str] = None,
    identity_ambiguous_keys: Iterable[str] = (),
    rules_changed: bool = False,
    mapping_changed: bool = False,
    identity_algorithm_changed: bool = False,
    merge_groups: Optional[Mapping[str, Sequence[str]]] = None,
    split_groups: Optional[Mapping[str, Sequence[str]]] = None,
) -> AEMHResult:
    """Run discovery, lifecycle reconciliation and Query generation.

    Baseline eligibility for resolution/merge/split is authorized only by a live
    Store acceptance lookup bound to ``store`` + ``snapshot_id`` + this
    ``project_id``/``snapshot_version``.  Bool and
    :class:`SnapshotBaselineProof` arguments are projection-only and cannot
    self-attest, cross project boundaries, or override a non-eligible Store row.
    """
    result = discover_ae_mh(
        listing,
        project_id=project_id,
        run_id=run_id,
        snapshot_version=snapshot_version,
    )
    discovered_coverage_complete = result.coverage_complete
    caller_coverage_restriction = (
        True if current_coverage_complete is None else current_coverage_complete is True
    )
    effective_coverage_complete = discovered_coverage_complete and caller_coverage_restriction
    result.coverage_complete = effective_coverage_complete
    result.snapshot_baseline_eligible = resolve_baseline_eligibility(
        current_snapshot_baseline_eligible,
        store=store,
        snapshot_id=snapshot_id,
        expected_project_id=project_id,
        expected_snapshot_version=snapshot_version,
    )

    previous_candidates = previous_result.candidates if previous_result else ()
    previous_instances = previous_result.lifecycle.instances if previous_result else ()
    discovered_ambiguous = {
        candidate.identity.stable_key()
        for candidate in result.candidates
        if result.candidate_details.get(candidate.candidate_id, {}).get("identity_ambiguous")
    }
    result.lifecycle = reconcile_risk_lifecycle(
        result.candidates,
        previous_candidates=previous_candidates,
        previous_instances=previous_instances,
        current_run_id=run_id,
        current_coverage_complete=effective_coverage_complete,
        current_snapshot_baseline_eligible=result.snapshot_baseline_eligible,
        identity_ambiguous_keys=set(identity_ambiguous_keys) | discovered_ambiguous,
        rules_changed=rules_changed,
        mapping_changed=mapping_changed,
        identity_algorithm_changed=identity_algorithm_changed,
        merge_groups=merge_groups,
        split_groups=split_groups,
    )
    if previous_result is not None:
        for key, metadata in previous_result.identity_metadata.items():
            result.identity_metadata.setdefault(key, dict(metadata))
        for key, refs in previous_result.historical_evidence_refs.items():
            result.historical_evidence_refs.setdefault(key, list(refs))
        for candidate in previous_result.candidates:
            key = candidate.identity.stable_key()
            result.historical_evidence_refs.setdefault(key, [])
            result.historical_evidence_refs[key] = list(dict.fromkeys(
                result.historical_evidence_refs[key] + list(candidate.evidence_refs)
            ))
    for candidate in result.candidates:
        key = candidate.identity.stable_key()
        result.historical_evidence_refs.setdefault(key, [])
        result.historical_evidence_refs[key] = list(dict.fromkeys(
            result.historical_evidence_refs[key] + list(candidate.evidence_refs)
        ))
    make_query_drafts(result)
    return result


def persist_ae_mh_result(
    store: Any,
    result: AEMHResult,
    *,
    facts_node_id: Optional[str] = None,
    candidate_node_id: str = DISCOVERY_NODE_ID,
) -> Dict[str, int]:
    """Persist append-only domain outputs through the shared Store.

    Formal facts are committed only when the caller supplies an opened
    deterministic/human node.  Candidate, counterevidence, lifecycle, Query
    and spine objects are stored as versioned domain objects and are never
    promoted by this function.
    """
    counts = {"facts": 0, "candidates": 0, "counterevidence": 0,
              "instances": 0, "transitions": 0, "queries": 0, "spines": 0}
    if facts_node_id:
        counts["facts"] = store.commit_facts(
            result.run_id,
            facts_node_id,
            f"facts:{result.run_id}:{result.snapshot_version}",
            result.reported_facts,
        )
    for candidate in result.candidates:
        store.put_domain_object(
            "risk_candidate",
            candidate.candidate_id,
            candidate,
            run_id=result.run_id,
            idempotency_key=f"candidate:{result.run_id}:{candidate.candidate_id}",
        )
        counts["candidates"] += 1
    for item in result.counterevidence:
        store.put_domain_object(
            "ae_mh_counterevidence",
            item.counterevidence_id,
            item,
            run_id=result.run_id,
            idempotency_key=f"counterevidence:{result.run_id}:{item.counterevidence_id}",
        )
        counts["counterevidence"] += 1
    for instance in result.lifecycle.instances:
        store.put_domain_object(
            "risk_instance",
            instance.instance_id,
            instance,
            run_id=result.run_id,
            idempotency_key=f"risk-instance:{result.run_id}:{instance.instance_id}",
        )
        counts["instances"] += 1
    for transition in result.lifecycle.transitions:
        store.put_domain_object(
            "risk_transition",
            transition.transition_id,
            transition,
            run_id=result.run_id,
            idempotency_key=f"risk-transition:{result.run_id}:{transition.transition_id}",
        )
        counts["transitions"] += 1
    for query in result.queries:
        store.put_domain_object(
            "query_draft",
            query.query_id,
            query,
            run_id=result.run_id,
            idempotency_key=f"query:{result.run_id}:{query.query_id}",
        )
        counts["queries"] += 1
    for subject_id, spine in result.temporal_spines.items():
        store.put_domain_object(
            "subject_temporal_spine",
            f"{result.run_id}:{subject_id}",
            spine,
            run_id=result.run_id,
            idempotency_key=f"spine:{result.run_id}:{subject_id}",
        )
        counts["spines"] += 1
    return counts


# More explicit alias for external callers.
run_synthetic_ae_mh = run_ae_mh_vertical_slice
