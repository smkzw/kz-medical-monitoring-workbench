"""Synthetic, offline AuthorityBundleV02 fixtures for the R5-S5 producers.

The fixture graph is encoded as immutable typed records rather than loaded from
the accepted artifact files.  It is intentionally small but exercises the
accepted subject cutoff/partial-date path and the AEMH exact/rejected,
withdrawn, and reappeared history path.
"""

from __future__ import annotations

from typing import Optional, Tuple

from mm_r5.public_authority_common import (
    AEMHDecisionInputV02,
    AEMHFullGraphInputV02,
    AEMHThreadInputV02,
    AuthorityBundleV02,
    AxisInputV02,
    CutoffEndpointBindingV02,
    DomainInputV02,
    EndpointInputV02,
    IdentityScopeInputV02,
    LocatorInputV02,
    PhaseInputV02,
    RevisionInputV02,
    RiskInputV02,
    ScopeInputV02,
    SubjectEventInputV02,
    SubjectFullGraphInputV02,
    TEMPORAL_V01_MANIFEST_SHA256,
    TEMPORAL_V02_CONTRACT_ID,
    TEMPORAL_V02_SCHEMA_VERSION,
    VisitInputV02,
    canonical_sha256,
    without_field,
)


def _revision_identity(revision_ref: str) -> str:
    return canonical_sha256({"revision": revision_ref, "accepted": True})


def _endpoint(
    state: str,
    exact_date: Optional[str],
    locator_refs: Tuple[str, ...],
    *,
    range_start: Optional[str] = None,
    range_end: Optional[str] = None,
    candidates: Tuple[str, ...] = (),
    projectable: bool = True,
    study_day: Optional[int] = None,
) -> EndpointInputV02:
    return EndpointInputV02(
        candidates=candidates,
        exact_date=exact_date,
        locator_refs=locator_refs,
        projectable=projectable,
        range_authorized=projectable,
        range_end=range_end,
        range_start=range_start,
        state=state,
        study_day=study_day,
    )


def _locator(
    locator_ref: str,
    record_ref: str,
    anchor: str,
    snapshot_ref: str,
    revision_ref: str,
    *,
    entity_kind: Optional[str] = None,
    entity_ref: Optional[str] = None,
    authority_domain: Optional[str] = None,
    authority_thread_ref: Optional[str] = None,
) -> LocatorInputV02:
    return LocatorInputV02(
        anchor=anchor,
        authority_domain=authority_domain,
        authority_thread_ref=authority_thread_ref,
        entity_kind=entity_kind,
        entity_ref=entity_ref,
        locator_ref=locator_ref,
        record_ref=record_ref,
        revision_content_identity=_revision_identity(revision_ref),
        revision_ref=revision_ref,
        snapshot_ref=snapshot_ref,
    )


def _seal_bundle(
    target_contract: str,
    source: object,
) -> AuthorityBundleV02:
    bundle = AuthorityBundleV02(
        authority_scope="synthetic_test_only",
        bundle_content_identity="0" * 64,
        contract_id=TEMPORAL_V02_CONTRACT_ID,
        execution_profile="full_parent_graph",
        schema_version=TEMPORAL_V02_SCHEMA_VERSION,
        source=source,
        target_contract=target_contract,
        temporal_v01_manifest_sha256=TEMPORAL_V01_MANIFEST_SHA256,
    )
    return AuthorityBundleV02(
        authority_scope=bundle.authority_scope,
        bundle_content_identity=canonical_sha256(without_field(bundle, "bundle_content_identity")),
        contract_id=bundle.contract_id,
        execution_profile=bundle.execution_profile,
        schema_version=bundle.schema_version,
        source=bundle.source,
        target_contract=bundle.target_contract,
        temporal_v01_manifest_sha256=bundle.temporal_v01_manifest_sha256,
    )


def build_subject_authority_bundle() -> AuthorityBundleV02:
    visit_locator = "locator::visit::v1"
    ae_locator = "locator::event::ae1"
    mh_locator = "locator::event::mh1"
    cutoff_locator = "locator::cutoff::v1"
    revision = "source-revision::listing::N+1"
    exact_start = _endpoint("exact", "2026-08-01", (visit_locator,), study_day=1)
    exact_end = _endpoint("exact", "2026-08-02", (ae_locator,), study_day=2)
    partial = _endpoint(
        "partial",
        None,
        (mh_locator,),
        range_start="2026-08-01",
        range_end="2026-08-31",
        candidates=("2026-08",),
    )
    missing = _endpoint("missing", None, (mh_locator,), projectable=False)
    source = SubjectFullGraphInputV02(
        axis=AxisInputV02(
            anchor_event_ref="event::ae::1",
            axis_ref="axis::subject::001-0001::N+1",
            day_zero_convention="anchor_day_one",
            mode="calendar",
            study_day_enabled=True,
            timezone="Asia/Shanghai",
        ),
        cutoff_binding=CutoffEndpointBindingV02(
            exact_date="2026-08-19",
            source_locator_refs=(cutoff_locator,),
            state="present",
        ),
        domain_applicability=tuple(
            DomainInputV02(
                domain=domain,
                event_refs=(f"event::{domain}::1",) if domain in ("ae", "mh") else (),
                risk_refs=("risk-anchor::ae::1",) if domain == "ae" else (),
                state="applicable" if domain in ("ae", "mh") else "not_provided",
            )
            for domain in (
                "ae",
                "mh",
                "cm",
                "ip",
                "lab_exam",
                "hospital_procedure",
                "symptom_efficacy",
                "protocol_compliance",
            )
        ),
        events=(
            SubjectEventInputV02(
                content_identity=canonical_sha256({"event": "ae::1", "content": "accepted"}),
                domain="ae",
                end=exact_end,
                event_ref="event::ae::1",
                geometry="closed_interval",
                locator_refs=(ae_locator,),
                risk_refs=("risk-anchor::ae::1",),
                start=exact_start,
                subtype="ae",
                visit_ref="visit::actual::v1",
            ),
            SubjectEventInputV02(
                content_identity=canonical_sha256({"event": "mh::1", "content": "accepted"}),
                domain="mh",
                end=missing,
                event_ref="event::mh::1",
                geometry="open_end",
                locator_refs=(mh_locator,),
                risk_refs=(),
                start=partial,
                subtype="mh",
                visit_ref=None,
            ),
        ),
        locator_specs=(
            _locator(cutoff_locator, "run-row::1", "data_cutoff", "snapshot::N+1", revision),
            _locator(ae_locator, "ae-row::1", "start_end_date", "snapshot::N+1", revision),
            _locator(mh_locator, "mh-row::1", "start_end_date", "snapshot::N+1", revision),
            _locator(visit_locator, "visit-row::v1", "visit_date", "snapshot::N+1", revision),
        ),
        phase=PhaseInputV02(
            end=missing,
            geometry="open_end",
            label_zh="治疗期",
            locator_refs=(visit_locator,),
            phase_ref="phase::treatment",
            start=exact_start,
        ),
        revision_specs=(RevisionInputV02(
            locator_refs=tuple(sorted((cutoff_locator, ae_locator, mh_locator, visit_locator))),
            revision_content_identity=_revision_identity(revision),
            revision_ref=revision,
        ),),
        risk=RiskInputV02(
            content_identity=canonical_sha256({"risk": "ae::1", "severity": "high"}),
            domain="ae",
            end=exact_start,
            event_ref="event::ae::1",
            geometry="point",
            locator_refs=(ae_locator,),
            risk_anchor_ref="risk-anchor::ae::1",
            risk_ref="risk::ae::1",
            risk_type_zh="严重性核查",
            severity="high",
            start=exact_start,
            visit_ref="visit::actual::v1",
        ),
        scope=IdentityScopeInputV02(
            project_ref="project::synthetic-contract-example",
            run_ref="run::synthetic-contract-example",
            site_ref="site::001",
            snapshot_ref="snapshot::N+1",
            spine_ref="spine::001-0001::N+1",
            subject_ref="subject::001-0001",
        ),
        visit=VisitInputV02(
            actual=exact_start,
            actual_encounter_ref="encounter::v1",
            assignment_ref="assignment::v1",
            locator_refs=(visit_locator,),
            nominal=exact_start,
            phase_ref="phase::treatment",
            planned_visit_ref="visit::planned::v1",
            visit_ref="visit::actual::v1",
        ),
    )
    return _seal_bundle("subject-temporal-public-v1", source)


def build_aemh_authority_bundle() -> AuthorityBundleV02:
    previous_snapshot = "snapshot::N"
    current_snapshot = "snapshot::N+1"
    previous_revision = "source-revision::listing::N"
    current_revision = "source-revision::listing::N+1"
    previous_locators = (
        _locator(
            "locator::reminder::ae1",
            "clue-row::1",
            "concept",
            previous_snapshot,
            previous_revision,
            entity_kind="candidate",
            entity_ref="candidate::suspected-ae::1",
            authority_domain="ae",
            authority_thread_ref="aemh-thread::ae::1",
        ),
        _locator(
            "locator::reminder::mh1",
            "clue-row::2",
            "concept",
            previous_snapshot,
            previous_revision,
            entity_kind="candidate",
            entity_ref="candidate::suspected-mh::1",
            authority_domain="mh",
            authority_thread_ref="aemh-thread::mh::1",
        ),
    )
    current_locators = (
        _locator(
            "locator::considered-fact::mh1",
            "mh-row::considered-1",
            "term",
            current_snapshot,
            current_revision,
            entity_kind="considered_fact",
            entity_ref="considered-fact::reported-mh::1",
            authority_domain="mh",
            authority_thread_ref="aemh-thread::mh::1",
        ),
        _locator(
            "locator::fact::ae1",
            "ae-row::later-1",
            "term",
            current_snapshot,
            current_revision,
            entity_kind="later_fact",
            entity_ref="fact::reported-ae::later-1",
            authority_domain="ae",
            authority_thread_ref="aemh-thread::ae::1",
        ),
        _locator(
            "locator::reminder::ae1",
            "clue-row::1",
            "concept",
            current_snapshot,
            previous_revision,
            entity_kind="candidate",
            entity_ref="candidate::suspected-ae::1",
            authority_domain="ae",
            authority_thread_ref="aemh-thread::ae::1",
        ),
        _locator(
            "locator::reminder::mh1",
            "clue-row::2",
            "concept",
            current_snapshot,
            previous_revision,
            entity_kind="candidate",
            entity_ref="candidate::suspected-mh::1",
            authority_domain="mh",
            authority_thread_ref="aemh-thread::mh::1",
        ),
    )
    source = AEMHFullGraphInputV02(
        current_locator_specs=current_locators,
        current_revision_specs=(
            RevisionInputV02(
                locator_refs=("locator::reminder::ae1", "locator::reminder::mh1"),
                revision_content_identity=_revision_identity(previous_revision),
                revision_ref=previous_revision,
            ),
            RevisionInputV02(
                locator_refs=("locator::considered-fact::mh1", "locator::fact::ae1"),
                revision_content_identity=_revision_identity(current_revision),
                revision_ref=current_revision,
            ),
        ),
        current_scope=ScopeInputV02(
            cutoff_ref="2026-08-19",
            project_ref="project::synthetic-contract-example",
            run_ref="run::synthetic-contract-example",
            site_ref="site::001",
            snapshot_ref=current_snapshot,
            spine_ref="spine::001-0001::N+1",
            subject_ref="subject::001-0001",
        ),
        decision_records=(
            AEMHDecisionInputV02(
                considered_fact_refs=(),
                decision_ref="decision::ae::exact",
                event_kind="match_decided",
                fact_refs=("fact::reported-ae::later-1",),
                match_state="exact",
                reason_code="exact_identity_and_temporal_match",
                thread_ref="aemh-thread::ae::1",
            ),
            AEMHDecisionInputV02(
                considered_fact_refs=(),
                decision_ref="decision::ae::withdrawn",
                event_kind="withdrawn",
                fact_refs=("fact::reported-ae::later-1",),
                match_state=None,
                reason_code="later_fact_withdrawn",
                thread_ref="aemh-thread::ae::1",
            ),
            AEMHDecisionInputV02(
                considered_fact_refs=(),
                decision_ref="decision::ae::reappeared",
                event_kind="reappeared",
                fact_refs=("fact::reported-ae::later-1",),
                match_state=None,
                reason_code="same_later_fact_reappeared",
                thread_ref="aemh-thread::ae::1",
            ),
            AEMHDecisionInputV02(
                considered_fact_refs=("considered-fact::reported-mh::1",),
                decision_ref="decision::mh::rejected",
                event_kind="match_decided",
                fact_refs=(),
                match_state="rejected",
                reason_code="rejected_after_identity_evidence_review",
                thread_ref="aemh-thread::mh::1",
            ),
        ),
        previous_locator_specs=previous_locators,
        previous_revision_specs=(RevisionInputV02(
            locator_refs=("locator::reminder::ae1", "locator::reminder::mh1"),
            revision_content_identity=_revision_identity(previous_revision),
            revision_ref=previous_revision,
        ),),
        previous_scope=ScopeInputV02(
            cutoff_ref="2026-08-10",
            project_ref="project::synthetic-contract-example",
            run_ref="run::synthetic-contract-example",
            site_ref="site::001",
            snapshot_ref=previous_snapshot,
            spine_ref="spine::001-0001::N",
            subject_ref="subject::001-0001",
        ),
        thread_specs=(
            AEMHThreadInputV02(
                candidate_locator_ref="locator::reminder::ae1",
                candidate_ref="candidate::suspected-ae::1",
                domain="ae",
                reminder_reason="suspected_unreported_ae_reminder",
                thread_ref="aemh-thread::ae::1",
            ),
            AEMHThreadInputV02(
                candidate_locator_ref="locator::reminder::mh1",
                candidate_ref="candidate::suspected-mh::1",
                domain="mh",
                reminder_reason="suspected_unreported_mh_reminder",
                thread_ref="aemh-thread::mh::1",
            ),
        ),
    )
    return _seal_bundle("aemh-match-history-public-v1", source)


def build_authority_bundle(target_contract: str) -> AuthorityBundleV02:
    if target_contract == "subject-temporal-public-v1":
        return build_subject_authority_bundle()
    if target_contract == "aemh-match-history-public-v1":
        return build_aemh_authority_bundle()
    raise ValueError("unknown target contract")


# Explicit aliases make the fixture easy to consume from focused tests while
# preserving one construction path per accepted authority target.
build_subject_temporal_authority_bundle = build_subject_authority_bundle
build_aemh_match_history_authority_bundle = build_aemh_authority_bundle
build_valid_subject_authority = build_subject_authority_bundle
build_valid_aemh_authority = build_aemh_authority_bundle

