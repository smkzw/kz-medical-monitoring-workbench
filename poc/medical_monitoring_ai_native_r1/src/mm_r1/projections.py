"""Dashboard-first projections for the synthetic AE/MH vertical slice.

The projections are read-only JSON-shaped views.  Profile and Timeline receive
the same serialized ``SubjectTemporalSpine`` payload and the same
``temporal_spine_id``.  Formal AE/MH counts are computed only from
``CanonicalFact`` values; candidate counts are exposed separately and can
never inflate the reported AE/MH denominator.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .ae_mh import AEMHResult, EvidenceLink, severity_rank, query_text
from .domain import (
    CanonicalFact,
    ProjectionVersion,
    RiskCandidate,
    RiskInstance,
    RiskLifecycleState,
    content_hash,
    to_jsonable,
)


@dataclass
class ProjectionBundle:
    """All audience-facing projections for one synthetic run."""

    project_dashboard: Dict[str, Any]
    site_dashboards: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    subject_profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    subject_timelines: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    versions: List[ProjectionVersion] = field(default_factory=list)

    def __getitem__(self, key: str) -> Any:
        aliases = {
            "dashboard": self.project_dashboard,
            "project": self.project_dashboard,
            "sites": self.site_dashboards,
            "subjects": self.subject_profiles,
            "profiles": self.subject_profiles,
            "timelines": self.subject_timelines,
        }
        if key in aliases:
            return aliases[key]
        return getattr(self, key)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "project_dashboard": self.project_dashboard,
            "site_dashboards": self.site_dashboards,
            "subject_profiles": self.subject_profiles,
            "subject_timelines": self.subject_timelines,
            "versions": to_jsonable(self.versions),
        }


def _risk_sort_key(card: Mapping[str, Any]) -> Tuple[int, int, str]:
    # Highest severity first; lifecycle state is a secondary deterministic
    # signal, and identity keeps equal cards stable.  This is dashboard order,
    # not a task queue priority.
    state_priority = {
        "established": 4,
        "escalated": 5,
        "reopened": 5,
        "not_evaluable": 6,
        "superseded": 1,
        "resolved_by_data": 0,
    }
    return (
        -severity_rank(card.get("severity")),
        -state_priority.get(card.get("lifecycle_state", ""), 2),
        str(card.get("identity_key", "")),
    )


def _fact_card(fact: CanonicalFact) -> Dict[str, Any]:
    return {
        "fact_id": fact.fact_id,
        "fact_type": fact.fact_type,
        "subject_id": fact.subject_id,
        "site_id": fact.site_id,
        "body": dict(fact.body),
        "evidence_links": list(fact.source_refs),
        "is_formal_ae_mh_fact": True,
    }


def _candidate_by_identity(result: AEMHResult) -> Dict[str, List[RiskCandidate]]:
    grouped: Dict[str, List[RiskCandidate]] = defaultdict(list)
    for candidate in result.candidates:
        grouped[candidate.identity.stable_key()].append(candidate)
    return grouped


def _link_dict(ref: str, *, historical: bool = False) -> Dict[str, Any]:
    return {"source_ref": ref, "fixture_marker": "SYNTHETIC", "historical": historical}


def _risk_card(
    instance: RiskInstance,
    result: AEMHResult,
    candidates_by_identity: Mapping[str, Sequence[RiskCandidate]],
) -> Dict[str, Any]:
    key = instance.identity_key
    candidates = list(candidates_by_identity.get(key, ()))
    metadata = dict(result.identity_metadata.get(key, {}))
    representative = sorted(
        candidates,
        key=lambda c: (-severity_rank(c.severity), c.candidate_id),
    )[0] if candidates else None
    subject_id = representative.subject_id if representative else metadata.get("subject_id")
    site_id = representative.site_id if representative else metadata.get("site_id")
    refs: List[str] = []
    for candidate in candidates:
        refs.extend(candidate.evidence_refs)
    current_refs = list(dict.fromkeys(refs))
    historical_refs = list(result.historical_evidence_refs.get(key, ()))
    links = [_link_dict(ref, historical=ref not in current_refs) for ref in dict.fromkeys(
        current_refs + historical_refs
    )]
    if not links:
        links = [_link_dict(ref) for transition in result.lifecycle.transitions
                 if transition.instance_id == instance.instance_id
                 for ref in transition.evidence_refs]
    return {
        "fixture_marker": "SYNTHETIC",
        "instance_id": instance.instance_id,
        "identity_key": key,
        "risk_type": representative.risk_type if representative else metadata.get("risk_type"),
        "risk_domain": representative.risk_domain if representative else metadata.get("risk_domain"),
        "subject_id": subject_id,
        "site_id": site_id,
        "concept": (
            result.candidate_details.get(representative.candidate_id, {}).get("concept")
            if representative else metadata.get("concept")
        ),
        "severity": instance.current_severity,
        "lifecycle_state": instance.lifecycle_state.value,
        "identity_ambiguous": instance.identity_ambiguous,
        "candidate_count": len(candidates),
        "is_candidate": bool(candidates),
        "candidate_not_counted_as_reported": True,
        "is_formal_ae_mh_fact": False,
        "evidence_links": links,
        "transition_kinds": [
            transition.kind for transition in result.lifecycle.transitions
            if transition.instance_id == instance.instance_id
        ],
    }


def _query_card(query: Any) -> Dict[str, Any]:
    return {
        "query_id": query.query_id,
        "status": query.status,
        "subject_id": query.subject_id,
        "site_id": query.site_id,
        "basis": query.basis,
        "finding": query.finding,
        "action": query.action,
        "three_part_text": query_text(query),
        "evidence_links": list(query.evidence_refs),
    }


def _counts(result: AEMHResult, facts: Sequence[CanonicalFact]) -> Dict[str, Any]:
    reported_ae = sum(1 for fact in facts if fact.fact_type == "reported_ae")
    reported_mh = sum(1 for fact in facts if fact.fact_type == "reported_mh")
    return {
        "candidate_count": len(result.candidates),
        "reported_ae_count": reported_ae,
        "reported_mh_count": reported_mh,
        "reported_ae_mh_count": reported_ae + reported_mh,
        "candidates_counted_as_reported": 0,
        "counterevidence_count": len(result.counterevidence),
    }


def build_projections(result: AEMHResult) -> ProjectionBundle:
    """Build project/site/subject dashboard, Profile and Timeline views."""
    candidates_by_identity = _candidate_by_identity(result)
    risk_cards = [
        _risk_card(instance, result, candidates_by_identity)
        for instance in result.lifecycle.instances
    ]
    risk_cards.sort(key=_risk_sort_key)
    fact_cards = [_fact_card(fact) for fact in result.reported_facts]
    queries = [_query_card(query) for query in result.queries]

    subject_ids = set(result.temporal_spines)
    subject_ids.update(f.subject_id for f in result.reported_facts if f.subject_id)
    subject_ids.update(c.subject_id for c in result.candidates if c.subject_id)
    subject_ids.update(
        metadata.get("subject_id")
        for metadata in result.identity_metadata.values()
        if metadata.get("subject_id")
    )
    site_ids = set(card.get("site_id") for card in risk_cards if card.get("site_id"))
    site_ids.update(f.site_id for f in result.reported_facts if f.site_id)

    profiles: Dict[str, Dict[str, Any]] = {}
    timelines: Dict[str, Dict[str, Any]] = {}
    for subject_id in sorted(subject_ids):
        spine = result.temporal_spines.get(subject_id)
        if spine is None:
            # A carried-forward identity may have no row in the current listing;
            # preserve an explicit empty shared spine rather than inventing time.
            from .domain import SubjectTemporalSpine
            spine = SubjectTemporalSpine(subject_id=subject_id, run_id=result.run_id)
        spine_payload = to_jsonable(spine)
        subject_risks = [card for card in risk_cards if card.get("subject_id") == subject_id]
        subject_candidates = [
            candidate for candidate in result.candidates if candidate.subject_id == subject_id
        ]
        subject_facts = [
            card for card in fact_cards if card.get("subject_id") == subject_id
        ]
        subject_counterevidence = [
            item.as_dict() for item in result.counterevidence if item.subject_id == subject_id
        ]
        subject_queries = [
            card for card in queries if card.get("subject_id") == subject_id
        ]
        spine_id = f"spine:{result.run_id}:{subject_id}"
        common = {
            "fixture_marker": "SYNTHETIC",
            "run_id": result.run_id,
            "project_id": result.project_id,
            "subject_id": subject_id,
            "temporal_spine_id": spine_id,
            "temporal_spine": spine_payload,
            "risk_cards": subject_risks,
            "evidence_links": [
                link for card in subject_risks for link in card.get("evidence_links", ())
            ],
            "under_reporting_candidates": [
                {
                    "candidate_id": candidate.candidate_id,
                    "identity_key": candidate.identity.stable_key(),
                    "risk_type": candidate.risk_type,
                    "severity": candidate.severity,
                    "evidence_links": list(candidate.evidence_refs),
                    "is_formal_ae_mh_fact": False,
                }
                for candidate in subject_candidates
            ],
            "reported_ae_mh": subject_facts,
            "counterevidence": subject_counterevidence,
            "queries": subject_queries,
            "counts": {
                "candidate_count": len(subject_candidates),
                "reported_ae_mh_count": len(subject_facts),
                "candidates_counted_as_reported": 0,
            },
        }
        # Both views deliberately share the same spine id and exact payload.
        profiles[subject_id] = {
            **common,
            "kind": "subject_profile",
            "view": "dashboard",
            "dashboard_first": True,
            "medical_summary": "SYNTHETIC AE/MH evidence and risk summary",
        }
        timelines[subject_id] = {
            **common,
            "kind": "subject_timeline",
            "view": "dashboard",
            "dashboard_first": True,
            "candidate_overlays": [
                {
                    "identity_key": card.get("identity_key"),
                    "actual_date": next((event.get("actual_date") for event in spine_payload.get("events", [])
                                         if event.get("source_refs") and any(
                                             ref in {
                                                 link.get("source_ref") if isinstance(link, Mapping) else link
                                                 for link in card.get("evidence_links", ())
                                             }
                                             for ref in event.get("source_refs", ())
                                         )), None),
                    "line_style": "dashed",
                    "shape": "candidate",
                    "evidence_links": card.get("evidence_links", []),
                }
                for card in subject_risks if card.get("is_candidate")
            ],
            "reported_event_overlays": [
                {
                    "fact_id": fact.get("fact_id"),
                    "shape": "fact",
                    "line_style": "solid",
                    "evidence_links": fact.get("evidence_links", []),
                }
                for fact in subject_facts
            ],
        }

    site_dashboards: Dict[str, Dict[str, Any]] = {}
    for site_id in sorted(site_ids):
        site_risks = [card for card in risk_cards if card.get("site_id") == site_id]
        site_risks.sort(key=_risk_sort_key)
        site_facts = [fact for fact in fact_cards if fact.get("site_id") == site_id]
        site_candidates = [candidate for candidate in result.candidates if candidate.site_id == site_id]
        subjects = sorted({card.get("subject_id") for card in site_risks if card.get("subject_id")} |
                          {fact.get("subject_id") for fact in site_facts if fact.get("subject_id")})
        site_dashboards[site_id] = {
            "fixture_marker": "SYNTHETIC",
            "kind": "site_dashboard",
            "view": "dashboard",
            "dashboard_first": True,
            "project_id": result.project_id,
            "run_id": result.run_id,
            "site_id": site_id,
            "subjects": subjects,
            "risk_cards": site_risks,
            "evidence_links": [link for card in site_risks for link in card.get("evidence_links", ())],
            "counts": {
                "candidate_count": len(site_candidates),
                "reported_ae_mh_count": len(site_facts),
                "candidates_counted_as_reported": 0,
                "affected_subject_count": len(subjects),
            },
        }

    project_dashboard = {
        "fixture_marker": "SYNTHETIC",
        "kind": "project_dashboard",
        "view": "dashboard",
        "dashboard_first": True,
        "project_id": result.project_id,
        "run_id": result.run_id,
        "snapshot_version": result.snapshot_version,
        "risk_cards": risk_cards,
        "site_ids": sorted(site_ids),
        "subject_ids": sorted(subject_ids),
        "evidence_links": [link for card in risk_cards for link in card.get("evidence_links", ())],
        "queries": queries,
        "counterevidence": [item.as_dict() for item in result.counterevidence],
        "counts": _counts(result, result.reported_facts),
        "coverage_complete": result.coverage_complete,
        "coverage": to_jsonable(result.coverage) if result.coverage else None,
        "candidate_fact_separation": result.candidate_fact_separation(),
        "risk_order": [card.get("identity_key") for card in risk_cards],
    }

    versions: List[ProjectionVersion] = []
    projection_payloads = [
        ("project_dashboard", None, None, project_dashboard),
        *[("site_dashboard", None, site_id, payload) for site_id, payload in site_dashboards.items()],
        *[("subject_profile", subject_id, None, payload) for subject_id, payload in profiles.items()],
        *[("subject_timeline", subject_id, None, payload) for subject_id, payload in timelines.items()],
    ]
    for kind, subject_id, site_id, payload in projection_payloads:
        projection_id = ":".join(filter(None, [result.run_id, kind, subject_id, site_id]))
        versions.append(ProjectionVersion(
            projection_id=projection_id,
            run_id=result.run_id,
            project_id=result.project_id,
            kind=kind,
            version=1,
            subject_id=subject_id,
            site_id=site_id,
            source_hash=content_hash(payload),
        ))
    return ProjectionBundle(
        project_dashboard=project_dashboard,
        site_dashboards=site_dashboards,
        subject_profiles=profiles,
        subject_timelines=timelines,
        versions=versions,
    )


def build_dashboard_projections(result: AEMHResult) -> ProjectionBundle:
    """Explicit alias for dashboard-first callers."""
    return build_projections(result)


def persist_projections(store: Any, bundle: ProjectionBundle) -> int:
    """Persist projection payloads as append-only domain objects."""
    payloads: List[Tuple[ProjectionVersion, Dict[str, Any]]] = []
    payloads.append((bundle.versions[0], bundle.project_dashboard))
    version_by_id = {version.projection_id: version for version in bundle.versions}
    for site_id, payload in bundle.site_dashboards.items():
        version = version_by_id[":".join(filter(None, [
            bundle.project_dashboard["run_id"], "site_dashboard", None, site_id,
        ]))]
        payloads.append((version, payload))
    for subject_id, payload in bundle.subject_profiles.items():
        payloads.append((version_by_id[":".join(filter(None, [
            bundle.project_dashboard["run_id"], "subject_profile", subject_id, None,
        ]))], payload))
    for subject_id, payload in bundle.subject_timelines.items():
        payloads.append((version_by_id[":".join(filter(None, [
            bundle.project_dashboard["run_id"], "subject_timeline", subject_id, None,
        ]))], payload))
    for version, payload in payloads:
        store.put_domain_object(
            "projection",
            version.projection_id,
            payload,
            run_id=version.run_id,
            idempotency_key=f"projection:{version.projection_id}",
        )
    return len(payloads)


# Named projection aliases for straightforward imports.
project_dashboard_projection = build_projections
subject_profile_projection = build_projections
subject_timeline_projection = build_projections
