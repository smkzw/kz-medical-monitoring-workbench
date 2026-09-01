"""R5-S5 AE/MH match-history public-authority producer.

The current packet is reconstructed from the frozen current and previous
authority slices in one ``AuthorityBundleV02``.  History is append-only: the
previous reminder entries are retained byte-for-byte as typed records and new
decision entries link to the preceding entry hash.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal, Optional, Tuple

from mm_r5.public_authority_common import (
    AEMH_CONTRACT_ID,
    AEMH_DOMAINS,
    AEMH_EVENT_KINDS,
    AEMHFullGraphInputV02,
    AEMH_MATCH_STATES,
    AuthorityBundleV02,
    FALLBACK_POLICY,
    PublicAuthorityReceipt,
    PublicAuthorityValidationIssue,
    PublicAuthorityValidationResult,
    PublicScopeIdentity,
    PublicSourceLocator,
    SourceRevisionContentPair,
    authority_issues,
    canonical_sha256,
    fail,
    issue,
    make_receipt,
    make_scope_identity,
    make_source_locator,
    make_source_pairs,
    validation_result,
)


@dataclass(frozen=True)
class AEMHHistoryMembershipIndex:
    candidate_refs: Tuple[str, ...]
    later_fact_refs: Tuple[str, ...]
    membership_content_hash: str
    source_locator_refs: Tuple[str, ...]
    thread_refs: Tuple[str, ...]


@dataclass(frozen=True)
class AEMHIdentityEvidence:
    entity_content_identity: str
    entity_ref: str
    evidence_content_hash: str
    evidence_kind: Literal["candidate", "later_fact", "considered_fact"]
    evidence_ref: str
    source_locator_content_hash: str
    source_locator_ref: str
    source_raw_payload_hash: str


@dataclass(frozen=True)
class AEMHMatchHistoryEntry:
    entry_hash: str
    entry_id: str
    event_kind: Literal["reminder_created", "match_decided", "withdrawn", "reappeared"]
    identity_evidence: Tuple[AEMHIdentityEvidence, ...]
    identity_evidence_refs: Tuple[str, ...]
    later_fact_content_identities: Tuple[str, ...]
    later_fact_refs: Tuple[str, ...]
    match_state: Optional[Literal["exact", "ambiguous", "rejected"]]
    prior_entry_hash: Optional[str]
    reason_code: str
    retained_evidence_locator_refs: Tuple[str, ...]
    risk_lifecycle_effect: Literal["none"]
    seq: int
    snapshot_ref: str


@dataclass(frozen=True)
class AEMHThreadPrefixAnchor:
    accepted_prefix_head_hash: Optional[str]
    accepted_prefix_seq: int
    prefix_content_hash: str
    previous_thread_content_hash: Optional[str]
    thread_ref: str


@dataclass(frozen=True)
class AEMHMatchThread:
    candidate_content_identity: str
    domain: Literal["ae", "mh"]
    evidence_locator_refs: Tuple[str, ...]
    history_entries: Tuple[AEMHMatchHistoryEntry, ...]
    original_candidate_ref: str
    original_reminder_ref: str
    project_ref: str
    site_ref: str
    subject_ref: str
    thread_content_hash: str
    thread_ref: str


@dataclass(frozen=True)
class AEMHMatchHistoryPublicProjection:
    accepted_thread_prefixes: Tuple[AEMHThreadPrefixAnchor, ...]
    contract_id: str
    cutoff_endpoint: "PublicCutoffEndpoint"
    fallback_policy: Literal["fail_closed_no_nearest"]
    membership_index: AEMHHistoryMembershipIndex
    previous_projection_content_hash: Optional[str]
    previous_projection_ref: Optional[str]
    projection_content_hash: str
    projection_id: str
    receipt_ref: str
    schema_version: str
    scope_identity: PublicScopeIdentity
    source_locators: Tuple[PublicSourceLocator, ...]
    threads: Tuple[AEMHMatchThread, ...]


@dataclass(frozen=True)
class AEMHMatchHistoryAuthorityPacket:
    packet_content_hash: str
    projection: AEMHMatchHistoryPublicProjection
    receipt: PublicAuthorityReceipt


# Imported lazily in the annotation above to keep the shared-object ownership
# in public_authority_common explicit at runtime.
from mm_r5.public_authority_common import PublicCutoffEndpoint  # noqa: E402


def _scope(source_scope: object) -> PublicScopeIdentity:
    return make_scope_identity(
        project_ref=source_scope.project_ref,
        run_ref=source_scope.run_ref,
        site_ref=source_scope.site_ref,
        snapshot_ref=source_scope.snapshot_ref,
        spine_ref=source_scope.spine_ref,
        subject_ref=source_scope.subject_ref,
        cutoff_state="present" if source_scope.cutoff_ref is not None else "absent",
        cutoff_ref=source_scope.cutoff_ref,
    )


def _revision_identity(revision_ref: str) -> str:
    return canonical_sha256({"revision": revision_ref, "accepted": True})


def _fact_pair_key(row: Tuple[str, str]) -> str:
    return row[0]


def _evidence_ref_key(row: AEMHIdentityEvidence) -> str:
    return row.evidence_ref


def _thread_ref_key(row: AEMHMatchThread) -> str:
    return row.thread_ref


def _locator_ref_key(row: PublicSourceLocator) -> str:
    return row.locator_ref


def _prefix_ref_key(row: AEMHThreadPrefixAnchor) -> str:
    return row.thread_ref


def _entity_identity(kind: str, ref: str, locator: PublicSourceLocator) -> str:
    return canonical_sha256({
        "entity_kind": kind,
        "entity_ref": ref,
        "source_locator_ref": locator.locator_ref,
        "source_raw_payload_hash": locator.raw_payload_hash,
    })


def _evidence(
    evidence_ref: str,
    evidence_kind: Literal["candidate", "later_fact", "considered_fact"],
    entity_ref: str,
    locator: PublicSourceLocator,
) -> AEMHIdentityEvidence:
    entity_content_identity = _entity_identity(evidence_kind, entity_ref, locator)
    core = {
        "evidence_ref": evidence_ref,
        "evidence_kind": evidence_kind,
        "entity_ref": entity_ref,
        "entity_content_identity": entity_content_identity,
        "source_locator_ref": locator.locator_ref,
        "source_locator_content_hash": locator.locator_content_hash,
        "source_raw_payload_hash": locator.raw_payload_hash,
    }
    return AEMHIdentityEvidence(
        entity_content_identity=entity_content_identity,
        entity_ref=entity_ref,
        evidence_content_hash=canonical_sha256(core),
        evidence_kind=evidence_kind,
        evidence_ref=evidence_ref,
        source_locator_content_hash=locator.locator_content_hash,
        source_locator_ref=locator.locator_ref,
        source_raw_payload_hash=locator.raw_payload_hash,
    )


def _entry(
    thread_key: str,
    seq: int,
    event_kind: Literal["reminder_created", "match_decided", "withdrawn", "reappeared"],
    snapshot_ref: str,
    match_state: Optional[Literal["exact", "ambiguous", "rejected"]],
    fact_refs: Tuple[str, ...],
    fact_hashes: Tuple[str, ...],
    evidence: Tuple[AEMHIdentityEvidence, ...],
    retained: Tuple[str, ...],
    reason_code: str,
    prior_entry_hash: Optional[str],
) -> AEMHMatchHistoryEntry:
    if len(fact_refs) != len(fact_hashes):
        raise ValueError("AEMH_FACT_IDENTITY_CARDINALITY")
    pairs = tuple(sorted(zip(fact_refs, fact_hashes), key=_fact_pair_key))
    identity_evidence = tuple(sorted(evidence, key=_evidence_ref_key))
    core = {
        "entry_id": f"history-entry::{thread_key}::{seq}",
        "seq": seq,
        "event_kind": event_kind,
        "snapshot_ref": snapshot_ref,
        "match_state": match_state,
        "later_fact_refs": tuple(row[0] for row in pairs),
        "later_fact_content_identities": tuple(row[1] for row in pairs),
        "identity_evidence_refs": tuple(sorted(row.evidence_ref for row in identity_evidence)),
        "identity_evidence": identity_evidence,
        "retained_evidence_locator_refs": tuple(sorted(retained)),
        "reason_code": reason_code,
        "risk_lifecycle_effect": "none",
        "prior_entry_hash": prior_entry_hash,
    }
    return AEMHMatchHistoryEntry(
        entry_hash=canonical_sha256(core),
        entry_id=core["entry_id"],
        event_kind=event_kind,
        identity_evidence=identity_evidence,
        identity_evidence_refs=core["identity_evidence_refs"],
        later_fact_content_identities=core["later_fact_content_identities"],
        later_fact_refs=core["later_fact_refs"],
        match_state=match_state,
        prior_entry_hash=prior_entry_hash,
        reason_code=reason_code,
        retained_evidence_locator_refs=core["retained_evidence_locator_refs"],
        risk_lifecycle_effect="none",
        seq=seq,
        snapshot_ref=snapshot_ref,
    )


def _thread(
    *,
    thread_ref: str,
    project_ref: str,
    site_ref: str,
    domain: Literal["ae", "mh"],
    subject_ref: str,
    original_candidate_ref: str,
    candidate_content_identity: str,
    original_reminder_ref: str,
    history_entries: Tuple[AEMHMatchHistoryEntry, ...],
    evidence_locator_refs: Tuple[str, ...],
) -> AEMHMatchThread:
    core = {
        "thread_ref": thread_ref,
        "project_ref": project_ref,
        "site_ref": site_ref,
        "domain": domain,
        "subject_ref": subject_ref,
        "original_candidate_ref": original_candidate_ref,
        "candidate_content_identity": candidate_content_identity,
        "original_reminder_ref": original_reminder_ref,
        "history_entries": history_entries,
        "evidence_locator_refs": tuple(sorted(evidence_locator_refs)),
    }
    return AEMHMatchThread(
        candidate_content_identity=candidate_content_identity,
        domain=domain,
        evidence_locator_refs=core["evidence_locator_refs"],
        history_entries=history_entries,
        original_candidate_ref=original_candidate_ref,
        original_reminder_ref=original_reminder_ref,
        project_ref=project_ref,
        site_ref=site_ref,
        subject_ref=subject_ref,
        thread_content_hash=canonical_sha256(core),
        thread_ref=thread_ref,
    )


def _evaluation(
    projection: AEMHMatchHistoryPublicProjection,
    pairs: Tuple[SourceRevisionContentPair, ...],
) -> Tuple[str, ...]:
    values = [
        projection.projection_content_hash,
        projection.scope_identity.identity_content_hash,
        projection.membership_index.membership_content_hash,
        projection.cutoff_endpoint.cutoff_content_hash,
        *(pair.accepted_content_hash for pair in pairs),
    ]
    if projection.previous_projection_content_hash is not None:
        values.append(projection.previous_projection_content_hash)
    values.extend(prefix.prefix_content_hash for prefix in projection.accepted_thread_prefixes)
    for thread in projection.threads:
        values.extend((thread.candidate_content_identity, thread.thread_content_hash))
        for entry in thread.history_entries:
            values.append(entry.entry_hash)
            values.extend(entry.later_fact_content_identities)
            values.extend(evidence.evidence_content_hash for evidence in entry.identity_evidence)
    values.extend(locator.locator_content_hash for locator in projection.source_locators)
    return tuple(sorted(set(values)))


def _build_packet(
    identity: PublicScopeIdentity,
    threads: Tuple[AEMHMatchThread, ...],
    locators: Tuple[PublicSourceLocator, ...],
    pairs: Tuple[SourceRevisionContentPair, ...],
    previous: Optional[AEMHMatchHistoryAuthorityPacket],
) -> AEMHMatchHistoryAuthorityPacket:
    threads = tuple(sorted(threads, key=_thread_ref_key))
    locators = tuple(sorted(locators, key=_locator_ref_key))
    membership_core = {
        "thread_refs": tuple(thread.thread_ref for thread in threads),
        "candidate_refs": tuple(sorted(thread.original_candidate_ref for thread in threads)),
        "later_fact_refs": tuple(sorted({
            ref
            for thread in threads
            for entry in thread.history_entries
            for ref in entry.later_fact_refs
        })),
        "source_locator_refs": tuple(locator.locator_ref for locator in locators),
    }
    membership = AEMHHistoryMembershipIndex(
        candidate_refs=membership_core["candidate_refs"],
        later_fact_refs=membership_core["later_fact_refs"],
        membership_content_hash=canonical_sha256(membership_core),
        source_locator_refs=membership_core["source_locator_refs"],
        thread_refs=membership_core["thread_refs"],
    )
    previous_ref = None
    previous_hash = None
    prefixes = []
    if previous is not None:
        previous_ref = previous.projection.projection_id
        previous_hash = previous.projection.projection_content_hash
        old_by_ref = {thread.thread_ref: thread for thread in previous.projection.threads}
        for thread in threads:
            old = old_by_ref[thread.thread_ref]
            core = {
                "thread_ref": thread.thread_ref,
                "accepted_prefix_seq": len(old.history_entries),
                "accepted_prefix_head_hash": old.history_entries[-1].entry_hash,
                "previous_thread_content_hash": old.thread_content_hash,
            }
            prefixes.append(AEMHThreadPrefixAnchor(
                accepted_prefix_head_hash=core["accepted_prefix_head_hash"],
                accepted_prefix_seq=core["accepted_prefix_seq"],
                prefix_content_hash=canonical_sha256(core),
                previous_thread_content_hash=core["previous_thread_content_hash"],
                thread_ref=thread.thread_ref,
            ))
    prefixes = tuple(sorted(prefixes, key=_prefix_ref_key))
    cutoff_candidates = tuple(
        locator.locator_ref
        for locator in locators
        if locator.authority_entity_kind == "candidate"
        and locator.authority_entity_ref == "candidate::suspected-ae::1"
    )
    if len(cutoff_candidates) != 1:
        raise ValueError("AEMH_CUTOFF_LOCATOR_BINDING")
    cutoff_core = {
        "state": "present",
        "exact_date": identity.cutoff_ref,
        "source_locator_refs": (cutoff_candidates[0],),
    }
    cutoff = PublicCutoffEndpoint(
        cutoff_content_hash=canonical_sha256(cutoff_core),
        exact_date=identity.cutoff_ref,
        source_locator_refs=(cutoff_candidates[0],),
        state="present",
    )
    projection_id = canonical_sha256({
        "contract_id": AEMH_CONTRACT_ID,
        "schema_version": "2026-08-19.1",
        "scope_identity_hash": identity.identity_content_hash,
        "membership_index_hash": membership.membership_content_hash,
    })
    receipt_id = canonical_sha256({
        "receipt_variant": "aemh_match_history",
        "authority_contract_id": AEMH_CONTRACT_ID,
        "scope_identity_hash": identity.identity_content_hash,
        "public_projection_id": projection_id,
    })
    projection_core = {
        "contract_id": AEMH_CONTRACT_ID,
        "schema_version": "2026-08-19.1",
        "projection_id": projection_id,
        "receipt_ref": receipt_id,
        "scope_identity": identity,
        "cutoff_endpoint": cutoff,
        "fallback_policy": FALLBACK_POLICY,
        "previous_projection_ref": previous_ref,
        "previous_projection_content_hash": previous_hash,
        "accepted_thread_prefixes": prefixes,
        "threads": threads,
        "source_locators": locators,
        "membership_index": membership,
    }
    projection_hash = canonical_sha256(projection_core)
    projection = AEMHMatchHistoryPublicProjection(
        accepted_thread_prefixes=prefixes,
        contract_id=AEMH_CONTRACT_ID,
        cutoff_endpoint=cutoff,
        fallback_policy=FALLBACK_POLICY,
        membership_index=membership,
        previous_projection_content_hash=previous_hash,
        previous_projection_ref=previous_ref,
        projection_content_hash=projection_hash,
        projection_id=projection_id,
        receipt_ref=receipt_id,
        schema_version="2026-08-19.1",
        scope_identity=identity,
        source_locators=locators,
        threads=threads,
    )
    receipt = make_receipt(
        receipt_variant="aemh_match_history",
        authority_contract_id=AEMH_CONTRACT_ID,
        scope=identity,
        projection_id=projection_id,
        projection_content_hash=projection_hash,
        evaluation_content_identities=_evaluation(projection, pairs),
        source_revision_content_pairs=pairs,
    )
    return AEMHMatchHistoryAuthorityPacket(
        packet_content_hash=canonical_sha256({
            "receipt_content_hash": receipt.receipt_content_hash,
            "projection_content_hash": projection.projection_content_hash,
        }),
        projection=projection,
        receipt=receipt,
    )


def _revision_partition_issues(
    locator_specs: Tuple[object, ...],
    revision_specs: Tuple[object, ...],
    path_prefix: str,
) -> Tuple[PublicAuthorityValidationIssue, ...]:
    issues = []
    locator_by_ref = {row.locator_ref: row for row in locator_specs}
    owner_by_locator = {}
    revision_refs = tuple(row.revision_ref for row in revision_specs)
    revision_ref_set = set(revision_refs)
    locator_refs = tuple(row.locator_ref for row in locator_specs)
    if len(revision_refs) != len(set(revision_refs)):
        issues.append(issue("PUB_SOURCE_REVISION_DUPLICATE", path_prefix + "/revisions", priority=20))
    if len(locator_refs) != len(set(locator_refs)):
        issues.append(issue("PUB_SOURCE_LOCATOR_DUPLICATE", path_prefix + "/locators", priority=20))
    for revision in revision_specs:
        if not revision.locator_refs:
            issues.append(issue("PUB_SOURCE_REVISION_EMPTY", path_prefix + "/revisions", priority=20))
        if len(revision.locator_refs) != len(set(revision.locator_refs)):
            issues.append(issue("PUB_SOURCE_LOCATOR_DUPLICATE", path_prefix + "/revisions", priority=30))
        for locator_ref in revision.locator_refs:
            if locator_ref not in locator_by_ref:
                issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", path_prefix + "/revisions", priority=30))
            elif locator_ref in owner_by_locator:
                issues.append(issue("PUB_SOURCE_REVISION_OVERLAP", path_prefix + "/revisions", priority=30))
            else:
                owner_by_locator[locator_ref] = revision.revision_ref
    if set(owner_by_locator) != set(locator_by_ref):
        issues.append(issue("PUB_SOURCE_LOCATOR_UNUSED", path_prefix + "/locators", priority=29))
    for locator in locator_specs:
        if locator.locator_ref not in owner_by_locator:
            if locator.revision_ref not in revision_ref_set:
                issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", path_prefix + "/locators", priority=30))
        elif owner_by_locator[locator.locator_ref] != locator.revision_ref:
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", path_prefix + "/locators", priority=30))
    return tuple(issues)


def _decision_lifecycle_issues(
    source: AEMHFullGraphInputV02,
) -> Tuple[PublicAuthorityValidationIssue, ...]:
    issues = []
    thread_refs = {row.thread_ref for row in source.thread_specs}
    decisions_by_thread = {thread_ref: [] for thread_ref in thread_refs}
    seen_decision_refs = set()
    for decision in source.decision_records:
        if decision.decision_ref in seen_decision_refs:
            issues.append(issue("AEMH_MATCH_DECISION_DUPLICATE", "/source/decision_records", priority=17))
        seen_decision_refs.add(decision.decision_ref)
        if decision.thread_ref not in decisions_by_thread:
            continue
        decisions_by_thread[decision.thread_ref].append(decision)
        if len(decision.fact_refs) != len(set(decision.fact_refs)):
            issues.append(issue("AEMH_FACT_DUPLICATE", "/source/decision_records/fact_refs", priority=20))
        if len(decision.considered_fact_refs) != len(set(decision.considered_fact_refs)):
            issues.append(issue("AEMH_FACT_DUPLICATE", "/source/decision_records/considered_fact_refs", priority=20))
        if set(decision.fact_refs) & set(decision.considered_fact_refs):
            issues.append(issue("AEMH_FACT_ROLE_OVERLAP", "/source/decision_records", priority=20))
        if decision.event_kind == "reminder_created":
            issues.append(issue("AEMH_LIFECYCLE_TRANSITION_INVALID", "/source/decision_records/event_kind", priority=18))
            if decision.match_state is not None:
                issues.append(issue("AEMH_MATCH_STATE_INVALID", "/source/decision_records/match_state", priority=30))
        elif decision.event_kind == "match_decided":
            if decision.match_state not in AEMH_MATCH_STATES:
                issues.append(issue("AEMH_MATCH_STATE_INVALID", "/source/decision_records/match_state", priority=30))
            elif decision.match_state == "exact":
                if len(decision.fact_refs) != 1 or decision.considered_fact_refs:
                    issues.append(issue("AEMH_MATCH_EVIDENCE_MISSING", "/source/decision_records", priority=18))
            elif decision.match_state == "ambiguous":
                if len(decision.fact_refs) < 2 or decision.considered_fact_refs:
                    issues.append(issue("AEMH_MATCH_EVIDENCE_MISSING", "/source/decision_records", priority=18))
            elif decision.match_state == "rejected":
                if decision.fact_refs or not decision.considered_fact_refs:
                    issues.append(issue("AEMH_MATCH_EVIDENCE_MISSING", "/source/decision_records", priority=18))
        else:
            if decision.match_state is not None:
                issues.append(issue("AEMH_MATCH_STATE_INVALID", "/source/decision_records/match_state", priority=30))
            if not decision.fact_refs or decision.considered_fact_refs:
                issues.append(issue("AEMH_MATCH_EVIDENCE_MISSING", "/source/decision_records", priority=18))
    for thread_ref in thread_refs:
        decisions = decisions_by_thread[thread_ref]
        if not decisions:
            continue
        match_decisions = tuple(
            decision for decision in decisions if decision.event_kind == "match_decided"
        )
        if len(match_decisions) != 1:
            code = "AEMH_MATCH_DECISION_DUPLICATE" if len(match_decisions) > 1 else "AEMH_LIFECYCLE_TRANSITION_INVALID"
            issues.append(issue(code, "/source/decision_records", priority=17 if len(match_decisions) > 1 else 18))
        lifecycle = "reminder_created"
        matched_state = None
        matched_facts = ()
        for decision in decisions:
            if decision.event_kind == "match_decided":
                if lifecycle != "reminder_created":
                    issues.append(issue("AEMH_MATCH_DECISION_DUPLICATE", "/source/decision_records", priority=17))
                lifecycle = "matched"
                matched_state = decision.match_state
                matched_facts = tuple(sorted(decision.fact_refs))
            elif decision.event_kind == "withdrawn":
                if lifecycle != "matched" or matched_state not in ("exact", "ambiguous"):
                    issues.append(issue("AEMH_LIFECYCLE_TRANSITION_INVALID", "/source/decision_records", priority=18))
                if tuple(sorted(decision.fact_refs)) != matched_facts:
                    issues.append(issue("AEMH_LIFECYCLE_TRANSITION_INVALID", "/source/decision_records", priority=18))
                lifecycle = "withdrawn"
            elif decision.event_kind == "reappeared":
                if lifecycle != "withdrawn":
                    issues.append(issue("AEMH_LIFECYCLE_TRANSITION_INVALID", "/source/decision_records", priority=18))
                if tuple(sorted(decision.fact_refs)) != matched_facts:
                    issues.append(issue("AEMH_LIFECYCLE_TRANSITION_INVALID", "/source/decision_records", priority=18))
                lifecycle = "reappeared"
    return tuple(issues)


def _aemh_input_issues(authority: AuthorityBundleV02) -> Tuple[PublicAuthorityValidationIssue, ...]:
    issues = list(authority_issues(authority, AEMH_CONTRACT_ID))
    if issues or not isinstance(authority.source, AEMHFullGraphInputV02):
        return tuple(issues)
    source = authority.source
    if len(source.thread_specs) != 2 or tuple(sorted(row.domain for row in source.thread_specs)) != AEMH_DOMAINS:
        issues.append(issue("PUB_THREAD_COVERAGE_MISMATCH", "/source/thread_specs", priority=20))
    if source.current_scope.cutoff_ref is None or source.previous_scope.cutoff_ref is None:
        issues.append(issue("PUB_CUTOFF_BINDING_INVALID", "/source/current_scope", priority=20))
    scope_pairs = (
        (source.current_scope.project_ref, source.previous_scope.project_ref, "/source/project_ref"),
        (source.current_scope.run_ref, source.previous_scope.run_ref, "/source/run_ref"),
        (source.current_scope.site_ref, source.previous_scope.site_ref, "/source/site_ref"),
        (source.current_scope.subject_ref, source.previous_scope.subject_ref, "/source/subject_ref"),
    )
    for current_value, previous_value, path in scope_pairs:
        if current_value != previous_value:
            issues.append(issue("PUB_IDENTITY_SCOPE_MISMATCH", path, priority=30))
    for cutoff_ref in (source.current_scope.cutoff_ref, source.previous_scope.cutoff_ref):
        if cutoff_ref is not None:
            try:
                date.fromisoformat(cutoff_ref)
            except ValueError:
                issues.append(issue("PUB_DATE_INVALID", "/source/scope/cutoff_ref", priority=20))
    issues.extend(_decision_lifecycle_issues(source))
    current_refs = tuple(row.locator_ref for row in source.current_locator_specs)
    previous_refs = tuple(row.locator_ref for row in source.previous_locator_specs)
    if len(current_refs) != len(set(current_refs)) or len(previous_refs) != len(set(previous_refs)):
        issues.append(issue("PUB_SOURCE_LOCATOR_DUPLICATE", "/source", priority=20))
    current_by_ref = {row.locator_ref: row for row in source.current_locator_specs}
    previous_by_ref = {row.locator_ref: row for row in source.previous_locator_specs}
    current_revision_by_ref = {row.revision_ref: row for row in source.current_revision_specs}
    previous_revision_by_ref = {row.revision_ref: row for row in source.previous_revision_specs}
    issues.extend(_revision_partition_issues(
        source.current_locator_specs,
        source.current_revision_specs,
        "/source/current",
    ))
    issues.extend(_revision_partition_issues(
        source.previous_locator_specs,
        source.previous_revision_specs,
        "/source/previous",
    ))
    for locator in source.current_locator_specs:
        if locator.snapshot_ref != source.current_scope.snapshot_ref:
            issues.append(issue("PUB_IDENTITY_SNAPSHOT_MISMATCH", "/source/current_locator_specs", priority=30))
        revision = (
            current_revision_by_ref[locator.revision_ref]
            if locator.revision_ref in current_revision_by_ref
            else None
        )
        if revision is None or locator.locator_ref not in revision.locator_refs:
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/current_locator_specs", priority=30))
    for locator in source.previous_locator_specs:
        if locator.snapshot_ref != source.previous_scope.snapshot_ref:
            issues.append(issue("PUB_IDENTITY_SNAPSHOT_MISMATCH", "/source/previous_locator_specs", priority=30))
        revision = (
            previous_revision_by_ref[locator.revision_ref]
            if locator.revision_ref in previous_revision_by_ref
            else None
        )
        if revision is None or locator.locator_ref not in revision.locator_refs:
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/previous_locator_specs", priority=30))
    for locator in source.current_locator_specs + source.previous_locator_specs:
        if locator.revision_content_identity != _revision_identity(locator.revision_ref):
            issues.append(issue("PUB_SOURCE_REVISION_HASH_MISMATCH", "/source/locator_specs", priority=30))
    for revision in source.current_revision_specs + source.previous_revision_specs:
        if revision.revision_content_identity != _revision_identity(revision.revision_ref):
            issues.append(issue("PUB_SOURCE_REVISION_HASH_MISMATCH", "/source/revision_specs", priority=30))
    for revision in source.current_revision_specs:
        if any(locator_ref not in current_by_ref for locator_ref in revision.locator_refs):
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/current/revisions", priority=30))
    for revision in source.previous_revision_specs:
        if any(locator_ref not in previous_by_ref for locator_ref in revision.locator_refs):
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/previous/revisions", priority=30))
    thread_refs = {row.thread_ref for row in source.thread_specs}
    domain_by_thread = {row.thread_ref: row.domain for row in source.thread_specs}
    if any(record.thread_ref not in thread_refs for record in source.decision_records):
        issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/decision_records", priority=30))
    current_public_by_ref = {
        row.locator_ref: make_source_locator(row)
        for row in source.current_locator_specs
    }
    previous_public_by_ref = {
        row.locator_ref: make_source_locator(row)
        for row in source.previous_locator_specs
    }
    current_by_entity = {}
    previous_by_entity = {}
    for locator in source.current_locator_specs:
        key = (locator.authority_thread_ref, locator.authority_domain, locator.entity_kind, locator.entity_ref)
        if key in current_by_entity:
            issues.append(issue("PUB_SOURCE_LOCATOR_DUPLICATE", "/source/current_locator_specs", priority=30))
        current_by_entity[key] = current_public_by_ref[locator.locator_ref]
    for locator in source.previous_locator_specs:
        key = (locator.authority_thread_ref, locator.authority_domain, locator.entity_kind, locator.entity_ref)
        if key in previous_by_entity:
            issues.append(issue("PUB_SOURCE_LOCATOR_DUPLICATE", "/source/previous_locator_specs", priority=30))
        previous_by_entity[key] = previous_public_by_ref[locator.locator_ref]
    used_current_refs = set()
    used_previous_refs = set()
    current_cutoff_candidates = tuple(
        locator.locator_ref
        for locator in source.current_locator_specs
        if locator.entity_kind == "candidate"
        and locator.entity_ref == "candidate::suspected-ae::1"
    )
    if len(current_cutoff_candidates) != 1:
        issues.append(issue("AEMH_CUTOFF_LOCATOR_BINDING", "/source/current_locator_specs", priority=30))
    else:
        used_current_refs.add(current_cutoff_candidates[0])
    for spec in source.thread_specs:
        expected = (spec.thread_ref, spec.domain, "candidate", spec.candidate_ref)
        if spec.candidate_locator_ref not in previous_by_ref:
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/thread_specs/candidate_locator_ref", priority=30))
        elif (
            previous_by_ref[spec.candidate_locator_ref].authority_thread_ref,
            previous_by_ref[spec.candidate_locator_ref].authority_domain,
            previous_by_ref[spec.candidate_locator_ref].entity_kind,
            previous_by_ref[spec.candidate_locator_ref].entity_ref,
        ) != expected:
            issues.append(issue("AEMH_EVIDENCE_AUTHORITY_BINDING", "/source/thread_specs", priority=30))
        else:
            used_previous_refs.add(spec.candidate_locator_ref)
        current_candidate_key = expected
        if current_candidate_key not in current_by_entity:
            issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/current_locator_specs", priority=30))
        else:
            current_candidate = current_by_entity[current_candidate_key]
            used_current_refs.add(current_candidate.locator_ref)
            if spec.candidate_locator_ref not in current_public_by_ref:
                issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/current_locator_specs", priority=30))
            else:
                previous_candidate = previous_public_by_ref[spec.candidate_locator_ref]
                if _entity_identity("candidate", spec.candidate_ref, current_candidate) != _entity_identity(
                    "candidate", spec.candidate_ref, previous_candidate
                ):
                    issues.append(issue("AEMH_THREAD_STABLE_IDENTITY_MISMATCH", "/source/current_locator_specs", priority=18))
    for decision in source.decision_records:
        if decision.thread_ref not in domain_by_thread:
            continue
        for fact_ref in decision.fact_refs + decision.considered_fact_refs:
            entity_kind = "later_fact" if fact_ref in decision.fact_refs else "considered_fact"
            key = (
                decision.thread_ref,
                domain_by_thread[decision.thread_ref],
                entity_kind,
                fact_ref,
            )
            if key not in current_by_entity:
                issues.append(issue("PUB_SOURCE_JOIN_MISMATCH", "/source/decision_records", priority=30))
            else:
                used_current_refs.add(current_by_entity[key].locator_ref)
    if set(used_current_refs) != set(current_by_ref):
        issues.append(issue("PUB_SOURCE_LOCATOR_UNUSED", "/source/current_locator_specs", priority=29))
    if set(used_previous_refs) != set(previous_by_ref):
        issues.append(issue("PUB_SOURCE_LOCATOR_UNUSED", "/source/previous_locator_specs", priority=29))
    return tuple(issues)


def _build_aemh(authority: AuthorityBundleV02) -> AEMHMatchHistoryAuthorityPacket:
    source = authority.source
    if not isinstance(source, AEMHFullGraphInputV02):
        fail(validation_result((issue("PUB_TYPE_MISMATCH", "/source", origin="parent", priority=1),)))
    previous_identity = _scope(source.previous_scope)
    current_identity = _scope(source.current_scope)
    previous_locators = tuple(sorted((make_source_locator(row) for row in source.previous_locator_specs), key=_locator_ref_key))
    current_locators = tuple(sorted((make_source_locator(row) for row in source.current_locator_specs), key=_locator_ref_key))
    previous_by_ref = {row.locator_ref: row for row in previous_locators}
    previous_authority_by_ref = {row.locator_ref: row for row in source.previous_locator_specs}
    current_locator_by_ref = {row.locator_ref: row for row in current_locators}
    current_by_entity = {
        (row.authority_thread_ref, row.authority_domain, row.entity_kind, row.entity_ref): current_locator_by_ref[row.locator_ref]
        for row in source.current_locator_specs
    }
    previous_threads = []
    for spec in source.thread_specs:
        locator = previous_by_ref[spec.candidate_locator_ref]
        authority_locator = previous_authority_by_ref[spec.candidate_locator_ref]
        expected_key = (spec.thread_ref, spec.domain, "candidate", spec.candidate_ref)
        actual_key = (
            authority_locator.authority_thread_ref,
            authority_locator.authority_domain,
            authority_locator.entity_kind,
            authority_locator.entity_ref,
        )
        if actual_key != expected_key:
            raise ValueError("AEMH_EVIDENCE_AUTHORITY_BINDING")
        evidence = _evidence(
            f"identity-evidence::candidate::{spec.domain}1",
            "candidate",
            spec.candidate_ref,
            locator,
        )
        entry = _entry(
            f"{spec.domain}::1",
            1,
            "reminder_created",
            source.previous_scope.snapshot_ref,
            None,
            (),
            (),
            (evidence,),
            (locator.locator_ref,),
            spec.reminder_reason,
            None,
        )
        previous_threads.append(_thread(
            thread_ref=spec.thread_ref,
            project_ref=previous_identity.project_ref,
            site_ref=previous_identity.site_ref,
            domain=spec.domain,
            subject_ref=previous_identity.subject_ref,
            original_candidate_ref=spec.candidate_ref,
            candidate_content_identity=_entity_identity("candidate", spec.candidate_ref, locator),
            original_reminder_ref=entry.entry_id,
            history_entries=(entry,),
            evidence_locator_refs=(locator.locator_ref,),
        ))
    previous = _build_packet(
        previous_identity,
        tuple(previous_threads),
        previous_locators,
        make_source_pairs(source.previous_revision_specs),
        None,
    )
    old_by_ref = {thread.thread_ref: thread for thread in previous.projection.threads}
    decisions_by_thread = {thread.thread_ref: [] for thread in previous.projection.threads}
    for decision in source.decision_records:
        decisions_by_thread[decision.thread_ref].append(decision)
    current_threads = []
    for spec in source.thread_specs:
        old = old_by_ref[spec.thread_ref]
        entries = list(old.history_entries)
        retained = {spec.candidate_locator_ref}
        for decision in decisions_by_thread[spec.thread_ref]:
            evidence = []
            fact_hashes = []
            if decision.event_kind == "match_decided":
                candidate_key = (spec.thread_ref, spec.domain, "candidate", spec.candidate_ref)
                evidence.append(_evidence(
                    f"identity-evidence::candidate::{spec.domain}1",
                    "candidate",
                    spec.candidate_ref,
                    current_by_entity[candidate_key],
                ))
            for fact_ref in decision.fact_refs:
                locator = current_by_entity[(spec.thread_ref, spec.domain, "later_fact", fact_ref)]
                evidence.append(_evidence(
                    f"identity-evidence::later_fact::{canonical_sha256(fact_ref)[:12]}",
                    "later_fact",
                    fact_ref,
                    locator,
                ))
                fact_hashes.append(_entity_identity("later_fact", fact_ref, locator))
                retained.add(locator.locator_ref)
            for fact_ref in decision.considered_fact_refs:
                locator = current_by_entity[(spec.thread_ref, spec.domain, "considered_fact", fact_ref)]
                evidence.append(_evidence(
                    f"identity-evidence::considered_fact::{canonical_sha256(fact_ref)[:12]}",
                    "considered_fact",
                    fact_ref,
                    locator,
                ))
                retained.add(locator.locator_ref)
            entries.append(_entry(
                f"{spec.domain}::1",
                len(entries) + 1,
                decision.event_kind,
                source.current_scope.snapshot_ref,
                decision.match_state,
                decision.fact_refs,
                tuple(fact_hashes),
                tuple(evidence),
                tuple(sorted(retained)),
                decision.reason_code,
                entries[-1].entry_hash,
            ))
        current_threads.append(_thread(
            thread_ref=spec.thread_ref,
            project_ref=current_identity.project_ref,
            site_ref=current_identity.site_ref,
            domain=spec.domain,
            subject_ref=current_identity.subject_ref,
            original_candidate_ref=spec.candidate_ref,
            candidate_content_identity=old.candidate_content_identity,
            original_reminder_ref=old.original_reminder_ref,
            history_entries=tuple(entries),
            evidence_locator_refs=tuple(sorted(retained)),
        ))
    return _build_packet(
        current_identity,
        tuple(current_threads),
        current_locators,
        make_source_pairs(source.current_revision_specs),
        previous,
    )


def build_aemh_match_history_authority(
    source: AuthorityBundleV02,
) -> AEMHMatchHistoryAuthorityPacket:
    """Build the current AE/MH history packet from AuthorityBundleV02 only."""
    issues = _aemh_input_issues(source)
    if issues:
        fail(validation_result(issues))
    try:
        return _build_aemh(source)
    except (KeyError, StopIteration, ValueError, TypeError):
        fail(validation_result((issue("PUB_CONSTRUCTION_FAILED", "/authority", priority=50),)))


def validate_aemh_match_history_authority(
    candidate: AEMHMatchHistoryAuthorityPacket,
    source: AuthorityBundleV02,
) -> PublicAuthorityValidationResult:
    """Rebuild current history and compare it without trusting candidate data."""
    issues = list(_aemh_input_issues(source))
    if not isinstance(candidate, AEMHMatchHistoryAuthorityPacket):
        issues.append(issue("PUB_TYPE_MISMATCH", "/candidate", origin="parent", priority=1))
        return validation_result(issues)
    if issues:
        return validation_result(issues)
    try:
        expected = _build_aemh(source)
    except (AssertionError, KeyError, StopIteration, ValueError, TypeError):
        return validation_result((issue("PUB_HASH_MISMATCH", "/candidate", priority=50),))
    if candidate != expected:
        expected_threads = {thread.thread_ref: thread for thread in expected.projection.threads}
        candidate_threads = {thread.thread_ref: thread for thread in candidate.projection.threads}
        history_changed = False
        for thread_ref in expected_threads:
            expected_thread = expected_threads[thread_ref]
            if (
                thread_ref not in candidate_threads
                or candidate_threads[thread_ref].history_entries != expected_thread.history_entries
            ):
                history_changed = True
                break
        code = "AEMH_HISTORY_NOT_APPEND_ONLY" if history_changed else "PUB_HASH_MISMATCH"
        return validation_result((issue(code, "/candidate", priority=50),))
    return validation_result(())
