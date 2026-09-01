"""Focused synthetic AE/MH vertical-slice acceptance tests.

Run only with:
    .venv/bin/python -m pytest -q poc/medical_monitoring_ai_native_r1/tests/test_ae_mh_vertical_slice.py
"""

from __future__ import annotations

from typing import List

from mm_r1.ae_mh import (
    IDENTITY_ALGORITHM,
    AEMHResult,
    build_ae_mh_artifact,
    mark_identity_ambiguous,
    merge_risk_identities,
    reconcile_risk_lifecycle,
    run_ae_mh_vertical_slice,
    split_risk_identity,
    query_text,
    persist_ae_mh_result,
)
from mm_r1.domain import (
    ExecutionManifest,
    NodeStatus,
    NodeType,
    RiskCandidate,
    RiskIdentity,
    RiskLifecycleState,
    ManifestNode,
    content_hash,
)
from mm_r1.fixtures import (
    SYNTHETIC_MARKER,
    SYNTHETIC_PROJECT_ID,
    SYNTHETIC_SNAPSHOT_N,
    SYNTHETIC_SNAPSHOT_N1,
    SYNTHETIC_SUBJECT_001,
    create_synthetic_run,
    seed_synthetic_snapshots,
)
from mm_r1.projections import build_projections, persist_projections


def _manual_candidate(event_identity: str, concept: str, run_id: str, severity: str) -> RiskCandidate:
    identity = RiskIdentity(
        project_id=SYNTHETIC_PROJECT_ID,
        scope="subject",
        subject_id=SYNTHETIC_SUBJECT_001,
        site_id="SYNTHETIC-SITE-A",
        risk_domain="potential_unreported_ae",
        event_identity=event_identity,
        normalized_concept=concept,
        temporal_window="SYNTHETIC-2026-01-01..SYNTHETIC-2026-01-02",
        lineage="SYNTHETIC-RULE",
        algorithm_version=IDENTITY_ALGORITHM,
    )
    return RiskCandidate(
        candidate_id=f"SYNTHETIC-CANDIDATE-{event_identity}-{run_id}",
        run_id=run_id,
        node_id="SYNTHETIC-NODE",
        risk_type="potential_unreported_ae",
        risk_domain="potential_unreported_ae",
        subject_id=SYNTHETIC_SUBJECT_001,
        site_id="SYNTHETIC-SITE-A",
        identity=identity,
        severity=severity,
        evidence_refs=[f"SYNTHETIC|row={event_identity}"],
        created_at="2026-01-01T00:00:00+00:00",
    )


def test_synthetic_n_n1_snapshots_are_full_and_accepted(r1_store):
    bundle = seed_synthetic_snapshots(r1_store)

    assert bundle.marker == SYNTHETIC_MARKER
    assert SYNTHETIC_MARKER in bundle.project.name
    assert bundle.snapshot_n.snapshot_id == SYNTHETIC_SNAPSHOT_N
    assert bundle.snapshot_n1.snapshot_id == SYNTHETIC_SNAPSHOT_N1
    assert bundle.snapshot_n.content_hash != bundle.snapshot_n1.content_hash
    assert bundle.snapshot_n.row_count == sum(map(len, bundle.listing_n.values()))
    assert bundle.snapshot_n1.row_count == sum(map(len, bundle.listing_n1.values()))
    assert set(bundle.listing_n) == set(bundle.listing_n1)
    assert all(
        row["fixture_marker"] == SYNTHETIC_MARKER
        for listing in (bundle.listing_n, bundle.listing_n1)
        for rows in listing.values()
        for row in rows
    )
    assert r1_store.get_acceptance(bundle.snapshot_n.snapshot_id).state.value == "baseline_eligible"
    assert r1_store.get_acceptance(bundle.snapshot_n1.snapshot_id).state.value == "baseline_eligible"
    assert r1_store.load_listing_content(bundle.snapshot_n1.snapshot_id) == bundle.listing_n1


def test_ae_mh_discovery_separates_reported_facts_candidates_and_counterevidence(r1_store):
    bundle = seed_synthetic_snapshots(r1_store)
    result = run_ae_mh_vertical_slice(
        bundle.listing_n,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-N",
        snapshot_version="SYNTHETIC-N",
        store=r1_store,
        snapshot_id=bundle.snapshot_n.snapshot_id,
    )

    assert result.coverage_complete is True
    assert result.reported_ae_count == 2
    assert result.reported_mh_count == 1
    assert result.candidate_count > 0
    assert all(fact.fact_type in {"reported_ae", "reported_mh"} for fact in result.reported_facts)
    assert all(candidate.candidate_id not in {fact.fact_id for fact in result.reported_facts}
               for candidate in result.candidates)
    assert result.candidate_fact_separation()["candidates_counted_as_reported"] is False
    artifact = build_ae_mh_artifact(result)
    assert artifact.payload_role == "candidate"
    assert artifact.node_type == NodeType.AI_CANDIDATE
    assert artifact.is_publishable()[0] is True
    assert any(item.kind == "reported_match" for item in result.counterevidence)
    assert any(item.kind == "reported_match" and item.matched_fact_ids
               for item in result.counterevidence)
    # Rash and admission have more than one evidence domain; one identity is
    # retained while a merge transition explains the evidence consolidation.
    assert any(transition.kind == "merge" for transition in result.lifecycle.transitions)
    assert result.queries
    assert all(query.basis and query.finding and query.action for query in result.queries)


def test_n_plus_1_lifecycle_preserves_high_risk_and_resolves_complete_data_gap(r1_store):
    bundle = seed_synthetic_snapshots(r1_store)
    result_n = run_ae_mh_vertical_slice(
        bundle.listing_n,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-N",
        snapshot_version="SYNTHETIC-N",
        store=r1_store,
        snapshot_id=bundle.snapshot_n.snapshot_id,
    )
    result_n1 = run_ae_mh_vertical_slice(
        bundle.listing_n1,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-N1",
        snapshot_version="SYNTHETIC-N1",
        previous_result=result_n,
        store=r1_store,
        snapshot_id=bundle.snapshot_n1.snapshot_id,
    )

    by_concept = {
        metadata.get("concept"): key
        for key, metadata in result_n1.identity_metadata.items()
    }
    rash_key = by_concept["skin rash"]
    admission_key = by_concept["unplanned admission"]
    dizziness_key = by_concept["dizziness"]
    alt_key = by_concept["alt elevation"]

    assert result_n1.lifecycle.by_identity[rash_key].lifecycle_state != RiskLifecycleState.RESOLVED_BY_DATA
    assert result_n1.lifecycle.by_identity[rash_key].lifecycle_state != RiskLifecycleState.CLOSED
    assert result_n1.lifecycle.by_identity[admission_key].lifecycle_state != RiskLifecycleState.RESOLVED_BY_DATA
    assert result_n1.lifecycle.by_identity[admission_key].lifecycle_state != RiskLifecycleState.CLOSED
    assert result_n1.lifecycle.by_identity[dizziness_key].lifecycle_state == RiskLifecycleState.RESOLVED_BY_DATA
    assert result_n1.lifecycle.by_identity[alt_key].lifecycle_state == RiskLifecycleState.RESOLVED_BY_DATA
    fatigue_key = next(
        key for key, metadata in result_n.identity_metadata.items()
        if metadata.get("concept") == "fatigue"
    )
    assert fatigue_key in result_n1.identity_metadata
    assert result_n.lifecycle.by_identity[fatigue_key].instance_id == \
        result_n1.lifecycle.by_identity[fatigue_key].instance_id
    assert any(t.kind == "carry_forward" and t.instance_id ==
               result_n1.lifecycle.by_identity[fatigue_key].instance_id
               for t in result_n1.lifecycle.transitions)
    assert any(t.kind == "carry_forward_high_risk" and t.instance_id ==
               result_n1.lifecycle.by_identity[admission_key].instance_id
               for t in result_n1.lifecycle.transitions)
    assert any(t.kind == "resolve" and t.instance_id ==
               result_n1.lifecycle.by_identity[dizziness_key].instance_id
               for t in result_n1.lifecycle.transitions)


def test_incomplete_listing_cannot_be_overridden_to_close_prior_risk(r1_store):
    bundle = seed_synthetic_snapshots(r1_store)
    result_n = run_ae_mh_vertical_slice(
        bundle.listing_n,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-N",
        snapshot_version="SYNTHETIC-N",
        store=r1_store,
        snapshot_id=bundle.snapshot_n.snapshot_id,
    )
    incomplete_listing = {
        table: list(rows) for table, rows in bundle.listing_n1.items()
    }
    incomplete_listing.pop("serious_events")
    result_n1 = run_ae_mh_vertical_slice(
        incomplete_listing,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-N1-INCOMPLETE",
        snapshot_version="SYNTHETIC-N1-INCOMPLETE",
        previous_result=result_n,
        current_coverage_complete=True,
        # Bare True remains non-authoritative; coverage incompleteness also fails closed.
        current_snapshot_baseline_eligible=True,
    )

    dizziness_key = next(
        key for key, metadata in result_n.identity_metadata.items()
        if metadata.get("concept") == "dizziness"
    )
    assert result_n1.coverage_complete is False
    assert result_n1.lifecycle.by_identity[dizziness_key].lifecycle_state == \
        RiskLifecycleState.NOT_EVALUABLE
    assert not any(
        transition.kind == "resolve"
        and transition.instance_id == result_n1.lifecycle.by_identity[dizziness_key].instance_id
        for transition in result_n1.lifecycle.transitions
    )


def test_complete_nonaccepted_listing_cannot_resolve_prior_risks(r1_store):
    bundle = seed_synthetic_snapshots(r1_store)
    result_n = run_ae_mh_vertical_slice(
        bundle.listing_n,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-N",
        snapshot_version="SYNTHETIC-N",
        store=r1_store,
        snapshot_id=bundle.snapshot_n.snapshot_id,
    )
    result_n1 = run_ae_mh_vertical_slice(
        bundle.listing_n1,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-N1-NONACCEPTED",
        snapshot_version="SYNTHETIC-N1-NONACCEPTED",
        previous_result=result_n,
        current_coverage_complete=True,
        current_snapshot_baseline_eligible=False,
    )

    by_concept = {
        metadata.get("concept"): key
        for key, metadata in result_n1.identity_metadata.items()
    }
    assert result_n1.coverage_complete is True
    assert result_n1.snapshot_baseline_eligible is False
    assert result_n1.lifecycle.by_identity[by_concept["dizziness"]].lifecycle_state == \
        RiskLifecycleState.NOT_EVALUABLE
    assert result_n1.lifecycle.by_identity[by_concept["unplanned admission"]].lifecycle_state == \
        RiskLifecycleState.NOT_EVALUABLE
    assert not any(transition.kind == "resolve" for transition in result_n1.lifecycle.transitions)


def test_identity_ambiguity_merge_split_supersede_and_not_evaluable_semantics():
    previous = _manual_candidate("SYNTHETIC-EVENT-OLD", "synthetic finding", "SYNTHETIC-RUN-N", "high")
    current_left = _manual_candidate("SYNTHETIC-EVENT-LEFT", "synthetic left", "SYNTHETIC-RUN-N1", "medium")
    current_right = _manual_candidate("SYNTHETIC-EVENT-RIGHT", "synthetic right", "SYNTHETIC-RUN-N1", "medium")

    # Pure deterministic core retains the verified bool; public merge/split wrappers
    # require a Store lookup bound to the candidates' project.
    split = reconcile_risk_lifecycle(
        [current_left, current_right],
        previous_candidates=[previous],
        current_run_id="SYNTHETIC-RUN-N1",
        current_coverage_complete=True,
        current_snapshot_baseline_eligible=True,
        split_groups={
            previous.identity.stable_key(): [
                current_left.identity.stable_key(),
                current_right.identity.stable_key(),
            ]
        },
    )
    assert split.by_identity[previous.identity.stable_key()].lifecycle_state == RiskLifecycleState.SUPERSEDED
    assert all(
        split.by_identity[candidate.identity.stable_key()].lifecycle_state == RiskLifecycleState.ESTABLISHED
        for candidate in (current_left, current_right)
    )
    assert any(transition.kind == "split" for transition in split.transitions)

    ambiguous = mark_identity_ambiguous(current_left, current_run_id="SYNTHETIC-RUN-N1")
    ambiguous_instance = ambiguous.by_identity[current_left.identity.stable_key()]
    assert ambiguous_instance.identity_ambiguous is True
    assert ambiguous_instance.lifecycle_state == RiskLifecycleState.NOT_EVALUABLE
    assert any(transition.kind == "identity_ambiguous" for transition in ambiguous.transitions)

    superseded = reconcile_risk_lifecycle(
        [],
        previous_candidates=[previous],
        current_run_id="SYNTHETIC-RUN-N1",
        rules_changed=True,
    )
    assert superseded.by_identity[previous.identity.stable_key()].lifecycle_state == RiskLifecycleState.SUPERSEDED
    assert any(transition.kind == "supersede" for transition in superseded.transitions)

    not_evaluable = reconcile_risk_lifecycle(
        [],
        previous_candidates=[previous],
        current_run_id="SYNTHETIC-RUN-N1",
        current_coverage_complete=False,
    )
    assert not_evaluable.by_identity[previous.identity.stable_key()].lifecycle_state == RiskLifecycleState.NOT_EVALUABLE
    assert any(transition.kind == "not_evaluable" for transition in not_evaluable.transitions)


def test_merge_split_gate_failure_keeps_current_and_prior_identities_not_evaluable():
    prior_merge_left = _manual_candidate(
        "SYNTHETIC-MERGE-OLD-LEFT", "synthetic merge left", "SYNTHETIC-RUN-N", "medium"
    )
    prior_merge_right = _manual_candidate(
        "SYNTHETIC-MERGE-OLD-RIGHT", "synthetic merge right", "SYNTHETIC-RUN-N", "medium"
    )
    current_merge = _manual_candidate(
        "SYNTHETIC-MERGE-CURRENT", "synthetic merge", "SYNTHETIC-RUN-N1", "medium"
    )
    merge_result = reconcile_risk_lifecycle(
        [current_merge],
        previous_candidates=[prior_merge_left, prior_merge_right],
        current_run_id="SYNTHETIC-RUN-N1",
        current_coverage_complete=False,
        current_snapshot_baseline_eligible=True,
        merge_groups={
            current_merge.identity.stable_key(): [
                prior_merge_left.identity.stable_key(),
                prior_merge_right.identity.stable_key(),
            ]
        },
    )
    assert all(
        instance.lifecycle_state == RiskLifecycleState.NOT_EVALUABLE
        for instance in merge_result.instances
    )
    assert not any(transition.kind == "merge" for transition in merge_result.transitions)

    prior_split = _manual_candidate(
        "SYNTHETIC-SPLIT-OLD", "synthetic split", "SYNTHETIC-RUN-N", "high"
    )
    current_split_left = _manual_candidate(
        "SYNTHETIC-SPLIT-LEFT", "synthetic split left", "SYNTHETIC-RUN-N1", "medium"
    )
    current_split_right = _manual_candidate(
        "SYNTHETIC-SPLIT-RIGHT", "synthetic split right", "SYNTHETIC-RUN-N1", "medium"
    )
    split_result = reconcile_risk_lifecycle(
        [current_split_left, current_split_right],
        previous_candidates=[prior_split],
        current_run_id="SYNTHETIC-RUN-N1",
        current_coverage_complete=True,
        current_snapshot_baseline_eligible=False,
        split_groups={
            prior_split.identity.stable_key(): [
                current_split_left.identity.stable_key(),
                current_split_right.identity.stable_key(),
            ]
        },
    )
    assert all(
        instance.lifecycle_state == RiskLifecycleState.NOT_EVALUABLE
        for instance in split_result.instances
    )
    assert not any(transition.kind == "split" for transition in split_result.transitions)


def test_accepted_complete_merge_and_split_preserve_explicit_lineage(r1_store):
    bundle = seed_synthetic_snapshots(r1_store)
    prior_merge_left = _manual_candidate(
        "SYNTHETIC-MERGE-ACCEPTED-LEFT", "synthetic merge left", "SYNTHETIC-RUN-N", "medium"
    )
    prior_merge_right = _manual_candidate(
        "SYNTHETIC-MERGE-ACCEPTED-RIGHT", "synthetic merge right", "SYNTHETIC-RUN-N", "medium"
    )
    current_merge = _manual_candidate(
        "SYNTHETIC-MERGE-ACCEPTED", "synthetic merge", "SYNTHETIC-RUN-N1", "medium"
    )
    merge_result = merge_risk_identities(
        [current_merge],
        [prior_merge_left, prior_merge_right],
        current_merge.identity.stable_key(),
        [prior_merge_left.identity.stable_key(), prior_merge_right.identity.stable_key()],
        current_run_id="SYNTHETIC-RUN-N1",
        current_coverage_complete=True,
        store=r1_store,
        snapshot_id=bundle.snapshot_n1.snapshot_id,
    )
    assert merge_result.by_identity[current_merge.identity.stable_key()].lifecycle_state == \
        RiskLifecycleState.ESTABLISHED
    assert all(
        merge_result.by_identity[candidate.identity.stable_key()].lifecycle_state ==
        RiskLifecycleState.SUPERSEDED
        for candidate in (prior_merge_left, prior_merge_right)
    )
    assert any(transition.kind == "merge" for transition in merge_result.transitions)

    prior_split = _manual_candidate(
        "SYNTHETIC-SPLIT-ACCEPTED-OLD", "synthetic split", "SYNTHETIC-RUN-N", "high"
    )
    current_split_left = _manual_candidate(
        "SYNTHETIC-SPLIT-ACCEPTED-LEFT", "synthetic split left", "SYNTHETIC-RUN-N1", "medium"
    )
    current_split_right = _manual_candidate(
        "SYNTHETIC-SPLIT-ACCEPTED-RIGHT", "synthetic split right", "SYNTHETIC-RUN-N1", "medium"
    )
    split_result = split_risk_identity(
        [current_split_left, current_split_right],
        [prior_split],
        prior_split.identity.stable_key(),
        [current_split_left.identity.stable_key(), current_split_right.identity.stable_key()],
        current_run_id="SYNTHETIC-RUN-N1",
        current_coverage_complete=True,
        store=r1_store,
        snapshot_id=bundle.snapshot_n1.snapshot_id,
    )
    assert split_result.by_identity[prior_split.identity.stable_key()].lifecycle_state == \
        RiskLifecycleState.SUPERSEDED
    assert all(
        split_result.by_identity[candidate.identity.stable_key()].lifecycle_state ==
        RiskLifecycleState.ESTABLISHED
        for candidate in (current_split_left, current_split_right)
    )
    assert any(transition.kind == "split" for transition in split_result.transitions)


def test_profile_timeline_share_spine_and_projections_remain_dashboard_first(r1_store):
    bundle = seed_synthetic_snapshots(r1_store)
    result_n = run_ae_mh_vertical_slice(
        bundle.listing_n,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-N",
        snapshot_version="SYNTHETIC-N",
        store=r1_store,
        snapshot_id=bundle.snapshot_n.snapshot_id,
    )
    result = run_ae_mh_vertical_slice(
        bundle.listing_n1,
        project_id=bundle.project_id,
        run_id="SYNTHETIC-RUN-N1",
        snapshot_version="SYNTHETIC-N1",
        previous_result=result_n,
        store=r1_store,
        snapshot_id=bundle.snapshot_n1.snapshot_id,
    )
    projections = build_projections(result)

    assert projections.project_dashboard["view"] == "dashboard"
    assert projections.project_dashboard["dashboard_first"] is True
    assert "task_queue" not in projections.project_dashboard
    assert projections.project_dashboard["counts"]["candidate_count"] == result.candidate_count
    assert projections.project_dashboard["counts"]["reported_ae_mh_count"] == result.reported_ae_mh_count
    assert projections.project_dashboard["counts"]["candidates_counted_as_reported"] == 0
    ranks = [
        {"low": 1, "medium": 2, "high": 3, "severe": 4}.get(card["severity"], 0)
        for card in projections.project_dashboard["risk_cards"]
    ]
    assert ranks == sorted(ranks, reverse=True)

    profile = projections.subject_profiles[SYNTHETIC_SUBJECT_001]
    timeline = projections.subject_timelines[SYNTHETIC_SUBJECT_001]
    assert profile["temporal_spine_id"] == timeline["temporal_spine_id"]
    assert profile["temporal_spine"] == timeline["temporal_spine"]
    assert "task_queue" not in profile and "task_queue" not in timeline
    assert profile["counts"]["candidates_counted_as_reported"] == 0
    assert all("SYNTHETIC" in link["source_ref"] for link in profile["evidence_links"])
    assert projections.site_dashboards
    assert all(payload["view"] == "dashboard" for payload in projections.site_dashboards.values())
    assert any(card["lifecycle_state"] == "carry_forward_high_risk" or
               "carry_forward_high_risk" in card["transition_kinds"]
               for card in projections.project_dashboard["risk_cards"])
    assert all(card["candidate_not_counted_as_reported"] for card in projections.project_dashboard["risk_cards"])
    assert all(query["three_part_text"].splitlines()[0].startswith("依据：")
               and query["three_part_text"].splitlines()[1].startswith("发现：")
               and query["three_part_text"].splitlines()[2].startswith("行动项：")
               for query in projections.project_dashboard["queries"])


def test_persisted_facts_are_formal_only_and_projection_objects_are_append_only(r1_store):
    bundle = seed_synthetic_snapshots(r1_store)
    run = create_synthetic_run(r1_store, bundle)
    r1_store.set_manifest(ExecutionManifest(
        run_id=run.run_id,
        nodes=[ManifestNode(
            node_id="SYNTHETIC-FACT-NODE",
            node_type=NodeType.DETERMINISTIC_SERVICE,
            artifact_required=False,
        )],
        identity_algorithm=IDENTITY_ALGORITHM,
        graph_version="SYNTHETIC-GRAPH",
        schema_version="SYNTHETIC-SCHEMA",
    ))
    r1_store.begin_node_run(run.run_id, "SYNTHETIC-FACT-NODE", NodeType.DETERMINISTIC_SERVICE,
                            "SYNTHETIC-FACT-KEY")
    r1_store.complete_node_run(run.run_id, "SYNTHETIC-FACT-NODE", "SYNTHETIC-FACT-KEY",
                               NodeStatus.PASSED, output={"fixture_marker": SYNTHETIC_MARKER})
    result = run_ae_mh_vertical_slice(
        bundle.listing_n1,
        project_id=bundle.project_id,
        run_id=run.run_id,
        snapshot_version="SYNTHETIC-N1",
        store=r1_store,
        snapshot_id=bundle.snapshot_n1.snapshot_id,
    )
    counts = persist_ae_mh_result(r1_store, result, facts_node_id="SYNTHETIC-FACT-NODE")
    projections = build_projections(result)
    projection_count = persist_projections(r1_store, projections)

    assert counts["facts"] == result.reported_ae_mh_count
    assert len(r1_store.list_facts(run.run_id)) == result.reported_ae_mh_count
    assert counts["candidates"] == result.candidate_count
    assert r1_store.list_domain_objects("risk_candidate")
    assert projection_count == len(projections.versions)
    assert r1_store.list_domain_objects("projection")
    assert all(fact.fact_type in {"reported_ae", "reported_mh"} for fact in r1_store.list_facts(run.run_id))
