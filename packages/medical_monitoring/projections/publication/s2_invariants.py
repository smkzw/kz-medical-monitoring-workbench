"""Frozen cross-object invariants for the R5 S2 authority packet."""
from __future__ import annotations

from datetime import date
from typing import Any, Callable, Dict, Tuple

from .s2_contracts import *  # noqa: F401,F403
from .s2_contracts import _SEVERITY_RANK

# ---------------------------------------------------------------------------
# Cross-object invariants (frozen error codes from the schema)
# ---------------------------------------------------------------------------


def _fail(error_code: str, message: str) -> None:
    raise S2InvariantError(error_code, message)


def _check_authority_scope(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``synthetic_offline_test_only``: the packet carries the
    planner-frozen authority mode and cannot express clinical/real-project/
    model/product/production/security authority (it has no such fields; the
    mode enum is a single closed literal)."""
    if packet.authority_mode != AUTHORITY_MODE_S2:
        _fail("authority_scope_violation",
              f"authority_mode must be {AUTHORITY_MODE_S2!r}, got "
              f"{packet.authority_mode!r}")


def _check_packet_identity(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``packet_identity_nonrecursive``: the content hash is the
    SHA-256 of the canonical packet JSON excluding exactly the two identity
    keys, and the id is the literal prefix plus that hash."""
    expected_hash = compute_packet_content_hash(packet)
    if packet.packet_content_hash != expected_hash:
        _fail("packet_identity_hash_cycle_or_mismatch",
              "packet_content_hash does not match the canonical packet "
              f"hash: got {packet.packet_content_hash!r}, expected "
              f"{expected_hash!r}")
    if packet.packet_id != PACKET_ID_PREFIX + expected_hash:
        _fail("packet_identity_hash_cycle_or_mismatch",
              "packet_id is not the literal prefix plus the content hash: "
              f"got {packet.packet_id!r}")


def _check_receipt_identity(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``receipt_identity_exact``: project/run/snapshot/cutoff/
    visibility/source identities agree across the receipt, the bindings and
    the deep-link target; the S2 chain requires a non-null cutoff."""
    receipt = packet.authority_receipt
    risk = packet.project_risk_binding
    if receipt.cutoff_ref is None:
        _fail("receipt_identity_mismatch",
              "the S2 chain requires a non-null receipt cutoff_ref")
    for name, expected, actual in (
            ("project_ref", receipt.project_ref, risk.project_ref),
            ("run_ref", receipt.run_ref, risk.run_ref),
            ("snapshot_ref", receipt.snapshot_ref, risk.snapshot_ref),
            ("cutoff_ref", receipt.cutoff_ref, risk.cutoff_ref)):
        if expected != actual:
            _fail("receipt_identity_mismatch",
                  f"receipt.{name} {expected!r} != project_risk_binding."
                  f"{name} {actual!r}")
    if (receipt.public_projection_id != risk.public_projection_id
            or receipt.public_projection_content_hash
            != risk.public_projection_content_hash):
        _fail("receipt_identity_mismatch",
              "receipt public projection identity differs from "
              "project_risk_binding")
    if (receipt.visibility_decision_id
            != packet.deep_link_target.visibility_decision_ref
            or receipt.visibility_decision_hash
            != packet.deep_link_target.visibility_decision_hash):
        _fail("receipt_identity_mismatch",
              "receipt visibility decision differs from the deep-link "
              "target")
    for name, expected, actual in (
            ("project_ref", receipt.project_ref,
             packet.deep_link_target.project_ref),
            ("run_ref", receipt.run_ref, packet.deep_link_target.run_ref),
            ("snapshot_ref", receipt.snapshot_ref,
             packet.deep_link_target.snapshot_ref)):
        if expected != actual:
            _fail("receipt_identity_mismatch",
                  f"receipt.{name} {expected!r} != deep_link_target.{name} "
                  f"{actual!r}")


def _check_project_risk_binding(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``project_risk_exact``: the risk binding identities agree
    with the receipt and the inspector/temporal risk refs (the equality to
    the bound D10RiskMarker / D10ProjectProjection is the W2 builder's
    external verification against the real R4 pipeline; every packet-internal
    equality is verified here)."""
    receipt = packet.authority_receipt
    risk = packet.project_risk_binding
    for name, expected, actual in (
            ("public_projection_id", receipt.public_projection_id,
             risk.public_projection_id),
            ("public_projection_content_hash",
             receipt.public_projection_content_hash,
             risk.public_projection_content_hash)):
        if expected != actual:
            _fail("project_risk_binding_mismatch",
                  f"project_risk_binding.{name} {actual!r} != receipt "
                  f"{expected!r}")
    risk_refs = (packet.project_risk_binding.risk_ref,
                 packet.inspector_binding.risk_ref,
                 packet.temporal_binding.risk_ref)
    if len(set(risk_refs)) != 1:
        _fail("project_risk_binding_mismatch",
              "the project risk ref must be the single shared Inspector/"
              "temporal/project binding risk ref")


def _check_center_member_relation(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``center_pattern_member_relation``: the pattern member is
    ``member_kind=center_pattern``, the individual members are EXACTLY its
    descendant member refs with ``member_kind=individual_risk`` on the same
    site, and at least two individuals exist."""
    pattern = packet.center_pattern_member
    individuals = packet.individual_members
    center = packet.center_binding
    if pattern.member_kind != "center_pattern":
        _fail("center_member_relation_mismatch",
              "center_pattern_member.member_kind must be center_pattern, "
              f"got {pattern.member_kind!r}")
    if center.pattern_ref != pattern.member_ref:
        _fail("center_member_relation_mismatch",
              "center_binding.pattern_ref must equal the pattern member ref")
    descendants = tuple(sorted(set(pattern.descendant_member_refs)))
    if tuple(sorted(m.member_ref for m in individuals)) != descendants:
        _fail("center_member_relation_mismatch",
              "individual_members are not exactly the pattern "
              "descendant_member_refs")
    if center.pattern_descendant_member_refs != descendants:
        _fail("center_member_relation_mismatch",
              "center_binding.pattern_descendant_member_refs must equal the "
              "pattern descendant member refs")
    if center.individual_risk_refs != tuple(
            sorted(m.member_ref for m in individuals)):
        _fail("center_member_relation_mismatch",
              "center_binding.individual_risk_refs must equal the "
              "individual member refs")
    for member in individuals:
        if member.member_kind != "individual_risk":
            _fail("center_member_relation_mismatch",
                  f"individual member {member.member_ref!r} must have "
                  f"member_kind=individual_risk, got {member.member_kind!r}")
        if member.site_stable_id != pattern.site_stable_id:
            _fail("center_member_relation_mismatch",
                  f"individual member {member.member_ref!r} site "
                  f"{member.site_stable_id!r} differs from the pattern site "
                  f"{pattern.site_stable_id!r}")
    if center.site_ref != pattern.site_stable_id:
        _fail("center_member_relation_mismatch",
              "center_binding.site_ref must equal the pattern "
              "site_stable_id")


def _check_center_domain_authority(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``center_domain_from_typed_relation``: the R5 domain equals
    the recorded typed R4 risk/outcome domain (both closed) and every member
    producer relation is recorded exactly (no count/UI/filename/test-id
    inference).  Equality to the D10TypedInput.signal_definition is the W2
    builder's external verification."""
    center = packet.center_binding
    pattern = packet.center_pattern_member
    individuals = packet.individual_members
    if center.r5_domain != center.r4_risk_or_outcome_domain:
        _fail("center_domain_authority_mismatch",
              "center_binding.r5_domain must equal "
              "r4_risk_or_outcome_domain")
    expected_domains = tuple(sorted(set(
        [pattern.producer_domain] +
        [member.producer_domain for member in individuals])))
    if center.member_producer_domains != expected_domains:
        _fail("center_domain_authority_mismatch",
              "center_binding.member_producer_domains must record every "
              "pattern/individual producer relation exactly")


def _check_center_severity_authority(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``center_severity_from_typed_members``: severity is the
    maximum high>medium>low over the actual pattern and individual member
    monitoring priorities; unknown/critical values fail closed."""
    center = packet.center_binding
    pattern = packet.center_pattern_member
    individuals = packet.individual_members
    priorities = ([pattern.monitoring_priority] +
                  [member.monitoring_priority for member in individuals])
    for priority in priorities:
        if priority not in _SEVERITY_RANK:
            _fail("center_severity_authority_mismatch",
                  f"member monitoring_priority {priority!r} is not a closed "
                  "S2 severity (unknown/critical fail closed)")
    maximum = max(priorities, key=lambda value: _SEVERITY_RANK[value])
    if center.member_priorities != tuple(sorted(set(priorities))):
        _fail("center_severity_authority_mismatch",
              "center_binding.member_priorities must be the sorted-unique "
              "actual member priorities")
    if center.r5_severity != maximum:
        _fail("center_severity_authority_mismatch",
              f"center_binding.r5_severity {center.r5_severity!r} must be "
              f"the maximum member priority {maximum!r}")


def _check_temporal_cardinality(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``single_temporal_chain``: exactly one visit, one event and
    one risk anchor share subject/spine/domain/severity/source; event/visit
    refs are non-null throughout."""
    temporal = packet.temporal_binding
    center = packet.center_binding
    inspector = packet.inspector_binding
    if (temporal.domain != center.r5_domain
            or temporal.domain != inspector.domain):
        _fail("temporal_cardinality_mismatch",
              "temporal domain must equal the center and inspector domain")
    if (temporal.severity != center.r5_severity
            or temporal.severity != inspector.severity):
        _fail("temporal_cardinality_mismatch",
              "temporal severity must equal the center and inspector "
              "severity")
    if temporal.source_locator_ref != packet.source_binding.locator_id:
        _fail("temporal_cardinality_mismatch",
              "temporal source_locator_ref must equal the source binding "
              "locator id")
    for name in ("visit_ref", "event_ref", "risk_anchor_ref"):
        if getattr(temporal, name) is None or not getattr(temporal, name):
            _fail("temporal_cardinality_mismatch",
                  f"temporal {name} must be non-null throughout the single "
                  "chain")


def _check_temporal_authority(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``temporal_same_authority``: temporal project/run/snapshot/
    site/subject/cutoff/risk/member identities equal the receipt, the center
    member and the deep-link target."""
    temporal = packet.temporal_binding
    receipt = packet.authority_receipt
    center = packet.center_binding
    link = packet.deep_link_target
    for name, expected, actual in (
            ("cutoff_ref", receipt.cutoff_ref, temporal.cutoff_ref),
            ("risk_ref", packet.project_risk_binding.risk_ref,
             temporal.risk_ref)):
        if expected != actual:
            _fail("temporal_authority_mismatch",
                  f"temporal.{name} {actual!r} differs from the authority "
                  f"{expected!r}")
    if link.subject_ref is None or temporal.subject_ref != link.subject_ref:
        _fail("temporal_authority_mismatch",
              "temporal subject_ref must equal the deep-link target "
              "subject_ref")
    if link.site_ref is None or center.site_ref != link.site_ref:
        _fail("temporal_authority_mismatch",
              "center site_ref must equal the deep-link target site_ref")
    if link.member_object_ref != center.pattern_ref:
        _fail("temporal_authority_mismatch",
              "deep-link member_object_ref must equal the center pattern "
              "member ref")


def _check_date_geometry(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``no_date_fabrication``: date_state=exact requires the
    actual date and event start; event end never precedes start; the nominal
    date never replaces the actual date and no nearest visit matching is
    allowed."""
    temporal = packet.temporal_binding
    if temporal.date_state != "exact":
        _fail("date_geometry_mismatch",
              "date_state must be exact for the single temporal chain")
    if temporal.actual_date is None or temporal.event_start is None:
        _fail("date_geometry_mismatch",
              "date_state=exact requires actual_date and event_start")
    if (temporal.event_end is not None
            and temporal.event_end < temporal.event_start):
        _fail("date_geometry_mismatch",
              "event_end must not precede event_start")
    if temporal.nominal_date is not None and temporal.actual_date is None:
        _fail("date_geometry_mismatch",
              "nominal_date must never replace the actual date")
    item = packet.reference_baseline_items[0]
    separator = ".." if ".." in item.temporal_window else "/"
    bounds = item.temporal_window.split(separator)
    if len(bounds) != 2:
        _fail("date_geometry_mismatch",
              "baseline temporal_window must be one exact ISO date range")
    try:
        window_start, window_end = (
            date.fromisoformat(bounds[0]), date.fromisoformat(bounds[1]))
    except (TypeError, ValueError):
        _fail("date_geometry_mismatch",
              "baseline temporal_window must use exact ISO-8601 dates")
    if window_end < window_start:
        _fail("date_geometry_mismatch",
              "baseline temporal_window end must not precede start")
    event_end = temporal.event_end or temporal.event_start
    if not (window_start <= temporal.actual_date <= window_end
            and window_start <= temporal.event_start <= window_end
            and window_start <= event_end <= window_end):
        _fail("date_geometry_mismatch",
              "visit/event dates must lie inside the packet-bound temporal "
              "window")


def _check_source_binding(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``source_one_hop_exact``: one locatable deep-link target
    whose source locator equals the EvidenceRef locator id, bound to the same
    member/source/revision pair with fallback_policy=none."""
    source = packet.source_binding
    evidence = packet.source_evidence
    link = packet.deep_link_target
    if link.locator_resolution_state != "locatable":
        _fail("source_binding_mismatch",
              "deep-link target must be locatable")
    if link.source_locator is None or link.source_locator != source.locator_id:
        _fail("source_binding_mismatch",
              "deep-link source_locator must equal the source binding "
              "locator id")
    if evidence.locator_id != source.locator_id:
        _fail("source_binding_mismatch",
              "source_evidence.locator_id must equal the source binding "
              "locator id")
    for name in ("locator_kind", "source_file", "row_or_cell_ref",
                 "lineage_ref"):
        if getattr(source, name) != getattr(evidence, name):
            _fail("source_binding_mismatch",
                  f"source_binding.{name} must exactly equal "
                  f"source_evidence.{name}")
    if source.fallback_policy != "none":
        _fail("source_binding_mismatch",
              "fallback_policy must be none (no nearest fallback)")
    if link.member_object_ref != packet.center_pattern_member.member_ref:
        _fail("source_binding_mismatch",
              "deep-link member_object_ref must equal the center pattern "
              "member")
    item = packet.reference_baseline_items[0]
    if item.source_revision_id != source.revision_id:
        _fail("source_binding_mismatch",
              "baseline item source_revision_id must equal the source "
              "binding revision_id")
    pairs = {(pair.revision_id, pair.content_hash)
             for pair in packet.authority_receipt.source_revision_content_pairs}
    if (source.revision_id, source.revision_content_hash) not in pairs:
        _fail("source_binding_mismatch",
              "source binding revision-content pair must appear in the "
              "receipt source_revision_content_pairs")


def _check_worker_isolation(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``two_isolated_workers``: exactly two worker attempts share
    input content hash and ensemble id while attempt/binding/session/
    independent-context identities are pairwise distinct."""
    attempts = packet.analysis_attempts
    if len(attempts) != 2:
        _fail("worker_isolation_mismatch",
              "analysis_attempts must contain exactly two workers")
    first, second = attempts
    if first.input_content_hash != second.input_content_hash:
        _fail("worker_isolation_mismatch",
              "both workers must share the same input_content_hash")
    if first.ensemble_id != second.ensemble_id:
        _fail("worker_isolation_mismatch",
              "both workers must share the same ensemble_id")
    for name in ("attempt_id", "binding_id", "session_id",
                 "independent_context_hash"):
        if getattr(first, name) == getattr(second, name):
            _fail("worker_isolation_mismatch",
                  f"workers must have pairwise distinct {name} values")


def _check_baseline_recheck_binding(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``baseline_recheck_binding``: one reference item, exactly
    two assessments each bound to that item and one-to-one to an actual
    attempt, rechecking the item's original source locators (which include
    the packet EvidenceRef locator id); item revision/snapshot equal the
    source binding and the receipt."""
    item = packet.reference_baseline_items[0]
    assessments = packet.baseline_assessments
    attempts = packet.analysis_attempts
    if len(assessments) != 2:
        _fail("baseline_recheck_binding_mismatch",
              "baseline_assessments must contain exactly two objects")
    for assessment in assessments:
        if assessment.item_id != item.item_id:
            _fail("baseline_recheck_binding_mismatch",
                  "every assessment must bind the reference baseline item")
        if assessment.source_recheck_locator_ids != item.source_locator_ids:
            _fail("baseline_recheck_binding_mismatch",
                  "assessment source_recheck_locator_ids must exactly equal "
                  "the item source_locator_ids")
    if packet.source_evidence.locator_id not in item.source_locator_ids:
        _fail("baseline_recheck_binding_mismatch",
              "the packet source_evidence.locator_id must be among the item "
              "source_locator_ids")
    attempt_ids = {attempt.attempt_id for attempt in attempts}
    assessment_attempt_ids = {a.attempt_id for a in assessments}
    if assessment_attempt_ids != attempt_ids:
        _fail("baseline_recheck_binding_mismatch",
              "assessments must map one-to-one by attempt_id to the actual "
              "analysis attempts")
    if any(attempt.claimed_date_window != item.temporal_window
           for attempt in attempts):
        _fail("baseline_recheck_binding_mismatch",
              "every worker claimed_date_window must exactly equal the "
              "packet baseline temporal_window")
    if item.source_revision_id != packet.source_binding.revision_id:
        _fail("baseline_recheck_binding_mismatch",
              "item source_revision_id must equal the source binding "
              "revision_id")
    if item.snapshot_id != packet.authority_receipt.snapshot_ref:
        _fail("baseline_recheck_binding_mismatch",
              "item snapshot_id must equal the receipt snapshot_ref")
    all_assessments = tuple(
        assessment for output in packet.worker_outputs
        for assessment in output.assessments)
    if tuple(sorted(all_assessments, key=lambda a: a.attempt_id)) != \
            tuple(sorted(assessments, key=lambda a: a.attempt_id)):
        _fail("baseline_recheck_binding_mismatch",
              "WorkerAnalysisOutput.assessments must be exactly the two "
              "baseline assessments")


def _check_worker_output_attribution(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``worker_output_attribution``: the two output attempt ids
    exactly equal the two attempt ids and each output's canonical content
    hash equals its attempt's declared output hash (R4's own
    ``worker_output_content_hash`` recipe is authoritative)."""
    attempt_by_id = {attempt.attempt_id: attempt
                     for attempt in packet.analysis_attempts}
    if len(attempt_by_id) != 2:
        _fail("worker_output_binding_mismatch",
              "analysis_attempts must have two distinct attempt ids")
    for output in packet.worker_outputs:
        attempt = attempt_by_id.get(output.attempt_id)
        if attempt is None:
            _fail("worker_output_binding_mismatch",
                  f"worker output {output.attempt_id!r} has no matching "
                  "attempt")
        actual_hash = worker_output_content_hash(output)
        if actual_hash != attempt.output_hash:
            _fail("worker_output_binding_mismatch",
                  f"worker output {output.attempt_id!r} content hash does "
                  "not equal its attempt output_hash")


def _check_verification_complete_passed(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``verification_complete_passed``: two verification records
    map one-to-one to the attempts, result=passed, no failure codes and the
    checked dimensions exactly cover all seven frozen dimensions."""
    verifications = packet.verifications
    attempts = packet.analysis_attempts
    if len(verifications) != 2:
        _fail("verification_incomplete_or_failed",
              "verifications must contain exactly two records")
    attempt_ids = {attempt.attempt_id for attempt in attempts}
    verification_attempt_ids = {v.attempt_id for v in verifications}
    if verification_attempt_ids != attempt_ids:
        _fail("verification_incomplete_or_failed",
              "verifications must map one-to-one to the attempts")
    for verification in verifications:
        if verification.result != "passed":
            _fail("verification_incomplete_or_failed",
                  f"verification {verification.verification_id!r} result "
                  f"must be passed, got {verification.result!r}")
        if verification.failure_reason_codes:
            _fail("verification_incomplete_or_failed",
                  f"verification {verification.verification_id!r} passed "
                  "must carry no failure codes")
        if set(verification.checked_dimensions) != set(
                S2_VERIFICATION_DIMENSIONS):
            _fail("verification_incomplete_or_failed",
                  f"verification {verification.verification_id!r} must "
                  "cover exactly all seven frozen dimensions")


def _check_visible_conflict(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``visible_conflict``: one conflict references both attempts,
    is never hidden, relation=mutual_negation, display_state=
    visible_conflict and monitoring_priority=high."""
    conflict = packet.conflict
    attempt_ids = tuple(sorted(
        attempt.attempt_id for attempt in packet.analysis_attempts))
    if conflict.member_attempt_ids != attempt_ids:
        _fail("conflict_hidden_or_mismatched",
              "conflict must reference both attempts exactly")
    if conflict.hidden:
        _fail("conflict_hidden_or_mismatched",
              "the S2 conflict is visible and cannot be hidden")
    if conflict.relation != "mutual_negation":
        _fail("conflict_hidden_or_mismatched",
              "conflict relation must be mutual_negation")
    if conflict.display_state != "visible_conflict":
        _fail("conflict_hidden_or_mismatched",
              "conflict display_state must be visible_conflict")
    if conflict.monitoring_priority != "high":
        _fail("conflict_hidden_or_mismatched",
              "conflict monitoring_priority must be high")


def _check_independent_adjudicator(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``independent_adjudicator``: the adjudicator binding and
    session differ from both workers and it reviewed exactly both original
    output artifacts."""
    adjudication = packet.adjudication
    attempts = packet.analysis_attempts
    worker_bindings = {attempt.binding_id for attempt in attempts}
    worker_sessions = {attempt.session_id for attempt in attempts}
    if adjudication.binding_id in worker_bindings:
        _fail("adjudicator_not_independent",
              "adjudicator binding_id must differ from both workers")
    if adjudication.session_id in worker_sessions:
        _fail("adjudicator_not_independent",
              "adjudicator session_id must differ from both workers")
    reviewed = tuple(sorted(set(adjudication.reviewed_artifact_refs)))
    expected = tuple(sorted(
        attempt.output_artifact_ref for attempt in attempts))
    if reviewed != expected:
        _fail("adjudicator_not_independent",
              "adjudicator must review exactly both original output "
              "artifact refs")


def expected_model_output_identity(
    attempts: Tuple[AnalysisAttempt, ...],
) -> str:
    """Canonical identity of the exact two worker output artifacts."""
    if len(attempts) != 2:
        raise S2ContractError(
            "ModelEvidence output identity requires exactly two attempts")
    rows = tuple(sorted(
        (attempt.attempt_id, attempt.output_artifact_ref, attempt.output_hash)
        for attempt in attempts))
    return s2_object_content_hash(rows)


def expected_model_output_hash(
    output_identity: str,
    conflict_id: str,
    adjudication_ref: str,
) -> str:
    """Canonical packet-level ensemble result hash."""
    return s2_object_content_hash({
        "adjudication_ref": adjudication_ref,
        "conflict_id": conflict_id,
        "output_identity": output_identity,
    })


def expected_model_binding_hash(
    *,
    model_evidence_id: str,
    role: str,
    model_id: str,
    model_version: str,
    ensemble_id: str,
    input_content_hash: str,
    member_analysis_refs: Tuple[str, ...],
) -> str:
    """Canonical ModelEvidence binding hash excluding the hash itself."""
    return s2_object_content_hash({
        "ensemble_id": ensemble_id,
        "input_content_hash": input_content_hash,
        "member_analysis_refs": tuple(sorted(member_analysis_refs)),
        "model_evidence_id": model_evidence_id,
        "model_id": model_id,
        "model_version": model_version,
        "role": role,
    })


def _check_model_evidence_boundary(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``model_evidence_packet_only``: the D10 ModelEvidence binds
    both attempts with source/input/output/ensemble identities matching the
    packet and receipt, and never enters the public Inspector refs."""
    model = packet.model_evidence
    attempts = packet.analysis_attempts
    if model.ensemble_size != 2:
        _fail("model_evidence_boundary_violation",
              "ModelEvidence ensemble_size must be 2")
    attempt_ids = tuple(sorted(
        attempt.attempt_id for attempt in attempts))
    if tuple(sorted(model.member_analysis_refs)) != attempt_ids:
        _fail("model_evidence_boundary_violation",
              "ModelEvidence member_analysis_refs must bind both attempts")
    first, second = attempts
    if first.input_content_hash != second.input_content_hash or \
            model.input_content_hash != first.input_content_hash:
        _fail("model_evidence_boundary_violation",
              "ModelEvidence input_content_hash must equal the shared "
              "attempt input content hash")
    if first.ensemble_id != second.ensemble_id or \
            model.ensemble_id != first.ensemble_id:
        _fail("model_evidence_boundary_violation",
              "ModelEvidence ensemble_id must equal the attempt ensemble_id")
    if (first.model_id, first.model_version) != \
            (second.model_id, second.model_version) or \
            model.model_id != first.model_id or \
            model.model_version != first.model_version:
        _fail("model_evidence_boundary_violation",
              "ModelEvidence model identity must equal the attempt model "
              "identity")
    receipt_evaluation_ids = packet.authority_receipt.evaluation_content_identities
    if len(receipt_evaluation_ids) != 1 or \
            model.evaluation_content_identity != receipt_evaluation_ids[0]:
        _fail("model_evidence_boundary_violation",
              "ModelEvidence evaluation_content_identity must equal the "
              "receipt's exact singleton evaluation identity")
    expected_source_refs = (packet.source_evidence.locator_id,)
    if model.source_refs != expected_source_refs:
        _fail("model_evidence_boundary_violation",
              "ModelEvidence source_refs must exactly equal the packet "
              "source evidence locator singleton")
    receipt_pairs = {(pair.revision_id, pair.content_hash)
                     for pair in
                     packet.authority_receipt.source_revision_content_pairs}
    model_pairs = {(pair.revision_id, pair.content_hash)
                   for pair in model.source_revision_content_pairs}
    if model_pairs != receipt_pairs:
        _fail("model_evidence_boundary_violation",
              "ModelEvidence source_revision_content_pairs must equal the "
              "receipt source pairs")
    if model.member_analysis_ref_set_hash != s2_object_content_hash(
            sorted(model.member_analysis_refs)):
        _fail("model_evidence_boundary_violation",
              "ModelEvidence member_analysis_ref_set_hash must equal the "
              "canonical hash of the member analysis refs")
    expected_output_identity = expected_model_output_identity(attempts)
    if model.output_identity != expected_output_identity:
        _fail("model_evidence_boundary_violation",
              "ModelEvidence output_identity must bind the exact two "
              "worker output artifacts")
    expected_output_hash = expected_model_output_hash(
        expected_output_identity, packet.conflict.conflict_id,
        packet.adjudication.binding_id)
    if model.output_hash != expected_output_hash:
        _fail("model_evidence_boundary_violation",
              "ModelEvidence output_hash must bind the visible conflict "
              "and independent adjudication")
    if model.adjudication_state != "adjudicated":
        _fail("model_evidence_boundary_violation",
              "ModelEvidence adjudication_state must be adjudicated")
    if model.role != "candidate_explanation" or \
            model.permitted_leaf != "model_candidate_only":
        _fail("model_evidence_boundary_violation",
              "ModelEvidence role/permitted_leaf must stay packet-only")
    expected_binding_hash = expected_model_binding_hash(
        model_evidence_id=model.model_evidence_id,
        role=model.role,
        model_id=model.model_id,
        model_version=model.model_version,
        ensemble_id=model.ensemble_id,
        input_content_hash=model.input_content_hash,
        member_analysis_refs=model.member_analysis_refs,
    )
    if model.model_binding_hash != expected_binding_hash:
        _fail("model_evidence_boundary_violation",
              "ModelEvidence model_binding_hash must match its canonical "
              "identity binding")
    if packet.inspector_binding.worker_output_refs:
        _fail("model_evidence_boundary_violation",
              "no worker output ref may enter the public Inspector refs")


def _check_inspector_ref_derivation(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``inspector_refs_from_packet_objects``: every public
    Inspector ref derives from the actual packet objects; the baseline
    assessment refs are the sorted-unique item_id singleton (never
    attempt_id) with the replacement-attack gate."""
    inspector = packet.inspector_binding
    item = packet.reference_baseline_items[0]
    attempts = packet.analysis_attempts
    attempt_ids = tuple(sorted(
        attempt.attempt_id for attempt in attempts))
    item_ids = tuple(sorted(set(
        assessment.item_id for assessment in packet.baseline_assessments)))
    expected_receipt_hash = s2_object_content_hash(packet.authority_receipt)
    if inspector.baseline_item_refs != (item.item_id,):
        _fail("inspector_ref_derivation_mismatch",
              "baseline_item_refs must be the reference item id singleton")
    if inspector.baseline_assessment_refs != item_ids or \
            set(item_ids) != {item.item_id}:
        _fail("inspector_ref_derivation_mismatch",
              "baseline_assessment_refs must be the sorted-unique item_id "
              "singleton derived from the two assessments")
    if item.item_id in set(attempt_ids):
        _fail("inspector_ref_derivation_mismatch",
              "replacement attack: baseline refs must not be attempt_id "
              "derived")
    if inspector.analysis_attempt_refs != attempt_ids:
        _fail("inspector_ref_derivation_mismatch",
              "analysis_attempt_refs must be the two attempt ids")
    if inspector.conflict_refs != (packet.conflict.conflict_id,):
        _fail("inspector_ref_derivation_mismatch",
              "conflict_refs must be the conflict id singleton")
    if inspector.adjudication_ref != packet.adjudication.binding_id:
        _fail("inspector_ref_derivation_mismatch",
              "adjudication_ref must be the adjudication binding id")
    verification_ids = tuple(sorted(
        verification.verification_id for verification in packet.verifications))
    if inspector.verification_refs != verification_ids:
        _fail("inspector_ref_derivation_mismatch",
              "verification_refs must be the two verification ids")
    if inspector.source_locator_refs != (packet.source_evidence.locator_id,):
        _fail("inspector_ref_derivation_mismatch",
              "source_locator_refs must be the source evidence locator id "
              "singleton")
    if inspector.risk_ref != packet.project_risk_binding.risk_ref:
        _fail("inspector_ref_derivation_mismatch",
              "inspector risk_ref must equal the project risk binding "
              "risk_ref")
    if inspector.domain != packet.center_binding.r5_domain:
        _fail("inspector_ref_derivation_mismatch",
              "inspector domain must equal the center domain")
    if inspector.severity != packet.center_binding.r5_severity:
        _fail("inspector_ref_derivation_mismatch",
              "inspector severity must equal the center severity")
    if inspector.authority_receipt_ref != expected_receipt_hash or \
            packet.project_risk_binding.authority_receipt_ref \
            != expected_receipt_hash:
        _fail("inspector_ref_derivation_mismatch",
              "authority_receipt_ref must equal the canonical hash of the "
              "authority receipt")


def _check_s4_deferred_empty(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``public_inspector_s4_deferred_empty``: the public Inspector
    worker/support/counter refs are exactly empty and the query draft ref is
    null; they remain S4 deferred and nothing smuggles packet data into the
    public R4 authority."""
    inspector = packet.inspector_binding
    if inspector.worker_output_refs != ():
        _fail("s4_deferred_leaf_leak",
              "public worker_output_refs must be exactly empty (S4)")
    if inspector.support_evidence_refs != ():
        _fail("s4_deferred_leaf_leak",
              "public support_evidence_refs must be exactly empty (S4)")
    if inspector.counterevidence_refs != ():
        _fail("s4_deferred_leaf_leak",
              "public counterevidence_refs must be exactly empty (S4)")
    if inspector.query_draft_ref is not None:
        _fail("s4_deferred_leaf_leak",
              "public query_draft_ref must be null (S4)")


def _check_packet_exactness(packet: R5S2AuthorityPacket) -> None:
    """Invariant ``canonical_exactness``: every packet object rejects
    extra/missing keys, enforces type/cardinality/nullability/closed enums/
    NFC/sorted-unique refs and verifies canonical SHA-256 (never ``assert``)."""
    # Imported-object exact-key gate (the R5S2 bindings and the packet ARE
    # their own frozen key sets by construction; the imported R4/R5 objects
    # are re-verified so any upstream source drift fails closed).
    objects_to_check: Tuple[Tuple[str, Any], ...] = (
        ("Member", packet.center_pattern_member),
        ("EvidenceRef", packet.source_evidence),
        ("ModelEvidence", packet.model_evidence),
        ("D10DeepLinkTarget", packet.deep_link_target),
        ("R5AuthorityReceipt", packet.authority_receipt),
        ("ReferenceBaselineItem", packet.reference_baseline_items[0]),
        ("ConflictVisibility", packet.conflict),
        ("AdjudicationBinding", packet.adjudication),
    )
    for object_name, obj in objects_to_check:
        check_imported_object_exact_keys(obj, object_name)
    for index, member in enumerate(packet.individual_members):
        check_imported_object_exact_keys(member, "Member")
    for attempt in packet.analysis_attempts:
        check_imported_object_exact_keys(attempt, "AnalysisAttempt")
    for assessment in packet.baseline_assessments:
        check_imported_object_exact_keys(assessment, "BaselineAssessment")
    for verification in packet.verifications:
        check_imported_object_exact_keys(verification, "EvidenceVerification")
    for output in packet.worker_outputs:
        check_imported_object_exact_keys(output, "WorkerAnalysisOutput")
    # Binding canonical hashes re-verified (packet identity is checked by its
    # own invariant; the five binding hashes live under canonical_exactness).
    for binding in (packet.center_binding, packet.project_risk_binding,
                    packet.source_binding, packet.temporal_binding,
                    packet.inspector_binding):
        expected = binding_content_hash(binding)
        if binding.content_hash != expected:
            _fail("packet_exactness_violation",
                  f"{type(binding).__name__}.content_hash "
                  f"{binding.content_hash!r} does not match {expected!r}")


_INVARIANT_CHECKS: Tuple[Tuple[str, Callable[[R5S2AuthorityPacket], None]], ...] = (
    ("authority_scope_violation", _check_authority_scope),
    ("packet_identity_hash_cycle_or_mismatch", _check_packet_identity),
    ("receipt_identity_mismatch", _check_receipt_identity),
    ("project_risk_binding_mismatch", _check_project_risk_binding),
    ("center_member_relation_mismatch", _check_center_member_relation),
    ("center_domain_authority_mismatch", _check_center_domain_authority),
    ("center_severity_authority_mismatch", _check_center_severity_authority),
    ("temporal_cardinality_mismatch", _check_temporal_cardinality),
    ("temporal_authority_mismatch", _check_temporal_authority),
    ("date_geometry_mismatch", _check_date_geometry),
    ("source_binding_mismatch", _check_source_binding),
    ("worker_isolation_mismatch", _check_worker_isolation),
    ("baseline_recheck_binding_mismatch", _check_baseline_recheck_binding),
    ("worker_output_binding_mismatch", _check_worker_output_attribution),
    ("verification_incomplete_or_failed",
     _check_verification_complete_passed),
    ("conflict_hidden_or_mismatched", _check_visible_conflict),
    ("adjudicator_not_independent", _check_independent_adjudicator),
    ("model_evidence_boundary_violation", _check_model_evidence_boundary),
    ("inspector_ref_derivation_mismatch", _check_inspector_ref_derivation),
    ("s4_deferred_leaf_leak", _check_s4_deferred_empty),
    ("packet_exactness_violation", _check_packet_exactness),
)

FROZEN_INVARIANT_ERROR_CODES: Tuple[str, ...] = tuple(
    code for code, _ in _INVARIANT_CHECKS)


def _validate_packet_invariants(packet: R5S2AuthorityPacket) -> None:
    """Fail-closed construction gate: every frozen invariant must hold or an
    S2InvariantError carrying the frozen error code is raised."""
    for _code, check in _INVARIANT_CHECKS:
        check(packet)


def validate_s2_authority_packet(
    packet: R5S2AuthorityPacket,
) -> Dict[str, Any]:
    """Fail-closed validator over an S2 authority packet.

    Re-runs every frozen cross-object invariant against the packet contents
    (tamper/deserialization gate) and returns
    ``{"valid": bool, "reasons": tuple of frozen error codes}`` without
    raising.  A valid packet yields ``valid=True`` with an empty ``reasons``
    tuple; any violation records the frozen schema error code.
    """
    if not isinstance(packet, R5S2AuthorityPacket):
        return {"valid": False,
                "reasons": ("packet_exactness_violation",)}
    reasons: list = []
    for code, check in _INVARIANT_CHECKS:
        try:
            check(packet)
        except (S2ContractError, S2CanonicalError):
            if code not in reasons:
                reasons.append(code)
    return {"valid": not reasons, "reasons": tuple(reasons)}


def is_s2_authority_packet(value: Any) -> bool:
    """True iff ``value`` is an ``R5S2AuthorityPacket`` typed instance."""
    return isinstance(value, R5S2AuthorityPacket)


def s2_enum_values(name: str) -> Tuple[str, ...]:
    """Closed S2 enum vocabulary by frozen schema enum name (fail closed on
    unknown names)."""
    _S2_ENUMS: Dict[str, Tuple[str, ...]] = {
        "authority_mode": AUTHORITY_MODES,
        "date_state": S2_DATE_STATES,
        "domain": S2_DOMAINS,
        "fallback_policy": FALLBACK_POLICIES,
        "journey_subtype": S2_JOURNEY_SUBTYPES,
        "model_evidence_visibility": MODEL_EVIDENCE_VISIBILITIES,
        "resolution_state": RESOLUTION_STATES,
        "severity": S2_SEVERITIES,
        "source_locator_kind": S2_SOURCE_LOCATOR_KINDS,
        "stage_status": S2_STAGE_STATUSES,
        "verification_dimension": S2_VERIFICATION_DIMENSIONS,
        "visit_kind": S2_VISIT_KINDS,
    }
    try:
        return _S2_ENUMS[name]
    except KeyError:
        raise S2ContractError(
            f"unknown S2 enum {name!r}, known: "
            f"{sorted(_S2_ENUMS)!r}") from None


__all__ = [
    "AUTHORITY_MODE_S2",
    "AUTHORITY_MODES",
    "AdjudicationBinding",
    "AnalysisAttempt",
    "BaselineAssessment",
    "ConflictVisibility",
    "D10DeepLinkTarget",
    "EvidenceRef",
    "EvidenceVerification",
    "FALLBACK_POLICIES",
    "FROZEN_INVARIANT_ERROR_CODES",
    "IMPORTED_EXACT_KEYS",
    "Member",
    "MODEL_EVIDENCE_VISIBILITIES",
    "ModelEvidence",
    "PACKET_ID_PREFIX",
    "R5AuthorityReceipt",
    "R5S2AuthorityPacket",
    "R5S2CenterBinding",
    "R5S2InspectorBinding",
    "R5S2ProjectRiskBinding",
    "R5S2SourceBinding",
    "R5S2TemporalBinding",
    "RESOLUTION_STATES",
    "ReferenceBaselineItem",
    "S2ContractError",
    "S2CanonicalError",
    "S2_DATE_STATES",
    "S2_DOMAINS",
    "S2_EXACT_OVERLAY_SHA256",
    "S2HashMismatchError",
    "S2_HUMAN_CONTRACT_SHA256",
    "S2InvariantError",
    "S2_JOURNEY_SUBTYPES",
    "S2_MANIFEST_CONTENT_SHA256",
    "S2_PACKET_SCHEMA_ID",
    "S2_PACKET_SCHEMA_SHA256",
    "S2_SEVERITIES",
    "S2_SOURCE_LOCATOR_KINDS",
    "S2_STAGE_STATUSES",
    "S2_VERIFICATION_DIMENSIONS",
    "S2_VISIT_KINDS",
    "STAGE_STATUS_S2",
    "WorkerAnalysisOutput",
    "binding_content_hash",
    "check_imported_object_exact_keys",
    "compute_packet_content_hash",
    "compute_packet_id",
    "expected_model_binding_hash",
    "expected_model_output_hash",
    "expected_model_output_identity",
    "is_s2_authority_packet",
    "s2_canonical_bytes",
    "s2_canonical_json",
    "s2_content_hash_excluding",
    "s2_enum_values",
    "s2_object_content_hash",
    "s2_sha256",
    "validate_s2_authority_packet",
]

