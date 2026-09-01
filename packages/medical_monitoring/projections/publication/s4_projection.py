"""R5-S4 Risk Inspector runtime projection (synthetic, offline).

This module is the second half of the renderer-neutral runtime thin slice.
It is a pure function of the typed build state produced by
:mod:`mm_r5.s4_authority_builder`: it rebuilds the plain-Chinese audience
plane, the private audit plane and the six-node acyclic hash DAG, and
assembles the frozen :class:`mm_r5.s4_contracts.R5S4AuthorityPacket`.

Rules (accepted runtime contract section 6):

* every Chinese phrase comes from the closed immutable tables declared once
  in ``s4_contracts`` (ordinal/domain/severity/change/baseline/recheck/
  verification/conflict/outcome/PD/consensus/adjudication/history/basis/
  journey); the five ``R5S4SyntheticAudienceLabels`` display values are the
  only free display text and can never influence identity/domain/severity/
  verification/conflict/adjudication/Query/authority or any hash;
* support evidence takes only supported findings' source locators, counter
  evidence only unsupported findings and gap candidates' source locators --
  each item is ``来源 {locator} 已定位`` (sorted, deduplicated) and the
  one-hop summary is ``来源 {locators，以顿号连接} 已在一跳内定位`` (``""``
  when empty);
* finding summaries are ``发现 {finding_id}（来源 {locators}）`` and gap
  summaries ``待核实 {gap_id}（来源 {locators}）`` -- never free-formed;
* the audience plane contains no audit-only leaf (no model/provider/
  binding/session/hash/raw bytes/audit leaf/ModelEvidence/forbidden token);
* the six-node hash DAG is acyclic: audience hash covers every audience
  leaf, audit hash excludes only ``packet_fingerprints``, packet id is
  ``r5-s4-contract:<audience_content_hash>``, fingerprints are the four
  sorted independent hashes, and the integrity hash covers both planes
  while excluding every hash/id/schema/status/authority-mode leaf.

Only :func:`project_s4_authority_packet` and :func:`build_s4_authority_packet`
are public here; every helper carries an underscore prefix.
"""

from __future__ import annotations

import dataclasses
from typing import Dict, Optional, Tuple

from ...risks.d10_contracts import ModelEvidence
from ...risks.ensemble import EvidenceDigestContext
from . import s4_contracts as s4
from .s4_authority_builder import build_s4_authority_state

__all__ = ["project_s4_authority_packet", "build_s4_authority_packet"]

#: Closed fallback reason for a ``not_evaluable`` verification leaf.  The R4
#: verifier only ever emits ``passed``/``failed``, so this deterministic
#: phrase is unreachable for valid typed inputs but keeps the verification
#: wording a total closed function.
_NOT_EVALUABLE_REASON_ZH = "核对条件不完整"


def _verification_zh(ver: s4.R5S4VerificationRow) -> str:
    """Closed Chinese verification wording from the recomputed row."""
    if ver.result == "passed":
        return s4.VERIFICATION_RESULT_ZH["passed"]
    if ver.result == "failed":
        items = "、".join(
            s4.VERIFICATION_FAILURE_ZH[code]
            for code in sorted(ver.failure_reason_codes))
        return f"核对未通过：{items}"
    if ver.result == "not_evaluable":
        return f"暂无法核对：{_NOT_EVALUABLE_REASON_ZH}"
    raise s4.S4RuntimeImplementationError(
        f"unknown verification result {ver.result!r}")


def _evidence_planes(
    state: s4.R5S4BuildState,
) -> Tuple[Tuple[str, ...], Tuple[str, ...], str]:
    """Support/counter evidence and the one-hop summary (closed templates).

    Support takes only supported findings' source locators; counter takes
    unsupported findings and gap candidates' source locators.
    """
    support: set = set()
    counter: set = set()
    for output in state.worker_outputs:
        for finding in output.findings:
            locators = set(finding.source_locator_ids)
            if finding.supported:
                support |= locators
            else:
                counter |= locators
        for gap in output.gap_candidates:
            counter |= set(gap.source_locator_ids)
    support_evidence = tuple(sorted(
        f"来源 {locator} 已定位" for locator in support))
    counter_evidence = tuple(sorted(
        f"来源 {locator} 已定位" for locator in counter))
    located = support | counter
    if not located:
        one_hop = ""
    else:
        one_hop = "来源 " + "、".join(sorted(located)) + " 已在一跳内定位"
    return support_evidence, counter_evidence, one_hop


def _consensus_zh(state: s4.R5S4BuildState) -> str:
    """Gated consensus phrase (0/1/N; conflict relations in frozen order)."""
    n = len(state.worker_views)
    if n == 0:
        return s4.CONSENSUS_ZH["no_ensemble"]
    if n == 1:
        return s4.CONSENSUS_ZH["single_analysis"]
    relations = sorted(
        {row.relation for row in state.conflict_rows},
        key=lambda relation: s4.CONFLICT_RELATION_ORDER.index(relation))
    if not relations:
        return s4.CONSENSUS_ZH["multi_consistent"]
    joined = "、".join(s4.CONFLICT_RELATION_ZH[relation]
                       for relation in relations)
    return s4.CONSENSUS_ZH["multi_conflict"].format(conflicts=joined)


def _adjudication_leaves(
    state: s4.R5S4BuildState,
) -> Tuple[str, Optional[str]]:
    """Adjudication status/explanation (outcome mapped, never new medicine)."""
    n = len(state.worker_views)
    if n < 2:
        return s4.ADJUDICATION_STATUS_ZH["none"], None
    outcome = state.adjudication_row.outcome
    if outcome is None:
        raise s4.S4RuntimeImplementationError(
            "multi_analysis adjudication row must carry an outcome")
    return s4.ADJUDICATION_STATUS_ZH["done"], s4.ADJUDICATION_OUTCOME_ZH[outcome]


def _query_leaves(
    state: s4.R5S4BuildState,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """The four Query Chinese leaves (all null when no draft exists)."""
    row = state.query_draft_row
    if row is None:
        return None, None, None, None
    return (row.basis_zh, row.finding_zh, row.action_zh,
            s4.PD_WORDING_ZH[row.pd_wording_state])


def _audience_baseline_rows(
    state: s4.R5S4BuildState,
    ordinal_by_attempt: Dict[str, int],
) -> Tuple[s4.R5S4AudienceBaselineRow, ...]:
    """Closed mapping of every typed baseline row (sorted by row_ref)."""
    rows: list = []
    for row in sorted(state.baseline_rows, key=lambda r: r.row_ref):
        ordinal = ordinal_by_attempt[row.attempt_id]
        rows.append(s4.R5S4AudienceBaselineRow(
            row_ref=row.row_ref,
            item_anchor_zh=f"基线条目 {row.item_id}",
            ordinal_zh=s4.ORDINAL_ZH[ordinal - 1],
            state_zh=s4.BASELINE_STATE_ZH[row.state],
            recheck_zh=s4.RECHECK_ZH[bool(row.source_recheck_locator_ids)],
        ))
    return tuple(rows)


def _audience_worker_summaries(
    state: s4.R5S4BuildState,
) -> Tuple[s4.R5S4AudienceWorkerSummary, ...]:
    """One closed summary per worker (ordinal-sorted)."""
    verification_by_attempt = {row.attempt_id: row
                               for row in state.verification_rows}
    output_by_attempt = {out.attempt_id: out
                         for out in state.worker_outputs}
    summaries: list = []
    for view in sorted(state.worker_views, key=lambda v: v.ordinal):
        output = output_by_attempt[view.attempt_id]
        ver = verification_by_attempt[view.attempt_id]
        finding_summary = tuple(sorted(
            f"发现 {finding.finding_id}（来源 "
            f"{'、'.join(sorted(finding.source_locator_ids))}）"
            for finding in output.findings))
        gap_summary = tuple(sorted(
            f"待核实 {gap.gap_id}（来源 "
            f"{'、'.join(sorted(gap.source_locator_ids))}）"
            for gap in output.gap_candidates))
        summaries.append(s4.R5S4AudienceWorkerSummary(
            ordinal_zh=view.ordinal_zh,
            finding_summary_zh=finding_summary,
            verification_zh=_verification_zh(ver),
            gap_zh=gap_summary,
        ))
    return tuple(summaries)


def _project_audience(state: s4.R5S4BuildState) -> s4.R5S4AudienceInspector:
    """Rebuild the plain-Chinese audience plane (no audit leaf)."""
    labels = state.audience_labels
    support_evidence, counter_evidence, one_hop = _evidence_planes(state)
    ordinal_by_attempt = {view.attempt_id: view.ordinal
                          for view in state.worker_views}
    status_zh, explanation_zh = _adjudication_leaves(state)
    query_leaves = _query_leaves(state)
    journey = state.journey_link
    return s4.R5S4AudienceInspector(
        audience_contract_id=s4.AUDIENCE_CONTRACT_ID,
        risk_title_zh=labels.risk_title_zh,
        domain_zh=state.risk_identity.domain_zh,
        severity_zh=state.risk_identity.severity_zh,
        change_state_zh=s4.CHANGE_KIND_ZH[state.change_band.change_kind],
        subject_display_zh=labels.subject_display_zh,
        center_display_zh=labels.center_display_zh,
        project_display_zh=labels.project_display_zh,
        cutoff_display_zh=labels.cutoff_display_zh,
        basis_zh=s4.BASIS_ZH[state.ensemble_projection_state],
        support_evidence_zh=support_evidence,
        counterevidence_zh=counter_evidence,
        source_one_hop_zh=one_hop,
        baseline_rows_zh=_audience_baseline_rows(
            state, ordinal_by_attempt),
        worker_ordinal_summaries=_audience_worker_summaries(state),
        consensus_zh=_consensus_zh(state),
        adjudication_status_zh=status_zh,
        adjudication_explanation_zh=explanation_zh,
        query_basis_zh=query_leaves[0],
        query_finding_zh=query_leaves[1],
        query_action_zh=query_leaves[2],
        query_pd_wording_zh=query_leaves[3],
        history_summary_zh=s4.HISTORY_SUMMARY_ZH[
            state.ensemble_projection_state],
        journey_available=journey.journey_available,
        journey_link_zh=(
            s4.JOURNEY_LINK_ZH if journey.journey_available else None),
        journey_unavailable_reason_zh=journey.unavailable_reason_zh,
    )


def _digest_context_view(
    digest_context: Optional[EvidenceDigestContext],
) -> Optional[s4.R5S4DigestContextView]:
    """Audit-plane view of the R4 EvidenceDigestContext (never on audience)."""
    if digest_context is None:
        return None
    return s4.R5S4DigestContextView(
        input_content_hash=digest_context.input_content_hash,
        output_digests=dict(digest_context.output_digests),
        evidence_digests=tuple(sorted(digest_context.evidence_digests)),
        expected_ensemble_identity=digest_context.expected_ensemble_identity,
        artifact_date_windows=dict(digest_context.artifact_date_windows),
        artifact_unit_contracts=dict(digest_context.artifact_unit_contracts),
        artifact_source_versions=dict(digest_context.artifact_source_versions),
        artifact_model_versions=dict(digest_context.artifact_model_versions),
        artifact_rule_ids=dict(digest_context.artifact_rule_ids),
        artifact_rule_versions=dict(digest_context.artifact_rule_versions),
        artifact_finding_identities={
            key: tuple(sorted(values))
            for key, values in digest_context.artifact_finding_identities.items()},
        artifact_authorized_source_locators={
            key: tuple(sorted(values))
            for key, values
            in digest_context.artifact_authorized_source_locators.items()},
    )


def _audit_worker_rows(
    state: s4.R5S4BuildState,
) -> Tuple[s4.R5S4AuditWorkerRow, ...]:
    """One audit worker row per view (root view + raw artifact mirror)."""
    raw_by_attempt = {artifact.attempt_id: artifact
                      for artifact in state.raw_artifacts}
    rows: list = []
    for view in sorted(state.worker_views, key=lambda v: v.attempt_id):
        raw = raw_by_attempt[view.attempt_id]
        rows.append(s4.R5S4AuditWorkerRow(
            attempt_id=view.attempt_id,
            binding_id=view.binding_id,
            session_id=view.session_id,
            model_id=view.model_id,
            model_version=view.model_version,
            role="worker",
            independent_context_hash=view.independent_context_hash,
            input_content_hash=view.input_content_hash,
            output_artifact_ref=view.output_artifact_ref,
            declared_output_hash=view.declared_output_hash,
            raw_bytes_sha256=raw.raw_bytes_sha256,
            parsed_output_hash=raw.parsed_output_hash,
        ))
    return tuple(rows)


def _model_evidence_ref(
    model_evidence: Optional[ModelEvidence],
) -> Optional[s4.R5S4ModelEvidenceRef]:
    """Audit/packet-only D10 ModelEvidence provenance, bound via dataclass
    field introspection so a future upstream field fails closed (the accepted
    packet schema covers exactly the current 18 fields)."""
    if model_evidence is None:
        return None
    me_fields = {field.name for field in dataclasses.fields(ModelEvidence)}
    ref_fields = {field.name for field in
                  dataclasses.fields(s4.R5S4ModelEvidenceRef)}
    if me_fields != ref_fields:
        raise s4.S4RuntimeImplementationError(
            "ModelEvidence field set does not match the accepted "
            "R5S4ModelEvidenceRef packet schema; fail closed until coverage "
            f"({sorted(me_fields - ref_fields)!r} vs "
            f"{sorted(ref_fields - me_fields)!r})")
    kwargs = {
        field.name: getattr(model_evidence, field.name)
        for field in dataclasses.fields(ModelEvidence)
        if field.name != "source_revision_content_pairs"
    }
    kwargs["source_revision_content_pairs"] = tuple(
        s4.S4SourceRevisionPair(revision_id=pair.revision_id,
                                content_hash=pair.content_hash)
        for pair in model_evidence.source_revision_content_pairs)
    return s4.R5S4ModelEvidenceRef(**kwargs)


def _project_audit(
    state: s4.R5S4BuildState,
    packet_fingerprints: Tuple[str, ...],
) -> s4.R5S4AuditInspector:
    """Rebuild the private audit plane (fingerprints excluded from its hash)."""
    receipt_hash = s4.receipt_content_hash_of(state.authority_receipt)
    digest_view = None
    if state.ensemble_projection_state != "no_ensemble":
        digest_view = _digest_context_view(state.digest_context)
    history_audit = tuple(sorted(
        entry.entry_hash for entry in state.history_log.entries))
    n = len(state.worker_views)
    return s4.R5S4AuditInspector(
        authority_receipt_ref=s4.RECEIPT_REF_PREFIX + receipt_hash,
        receipt_content_hash=receipt_hash,
        digest_context=digest_view,
        worker_audit_rows=_audit_worker_rows(state),
        verification_audit_rows=tuple(
            s4.R5S4VerificationAuditRow(
                verification_id=row.verification_id,
                attempt_id=row.attempt_id,
                checked_dimensions=row.checked_dimensions,
                result=row.result,
                failure_reason_codes=row.failure_reason_codes,
                recomputed=True,
            )
            for row in sorted(state.verification_rows,
                              key=lambda r: r.verification_id)),
        adjudication_audit=(
            (s4.ADJUDICATION_RECORD_REF,) if n >= 2 else ()),
        conflict_audit=tuple(sorted(
            row.conflict_id for row in state.conflict_rows)),
        history_audit=history_audit,
        model_evidence=_model_evidence_ref(state.model_evidence),
        packet_fingerprints=packet_fingerprints,
    )


def project_s4_authority_packet(
    build_state: s4.R5S4BuildState,
) -> s4.R5S4AuthorityPacket:
    """Pure-function rebuild of the audience/audit planes and the six-node
    acyclic hash DAG, then assemble the frozen typed packet.

    The packet constructor re-verifies every hash recipe; nothing here trusts
    a stored audience/audit/hash leaf (the build state carries none).
    """
    audience = _project_audience(build_state)
    audience_hash = s4.audience_content_hash_of(audience)
    receipt_hash = s4.receipt_content_hash_of(build_state.authority_receipt)
    packet_id = s4.compute_packet_id(audience_hash)
    fingerprints = s4.compute_packet_fingerprints(
        audience_hash, receipt_hash, packet_id,
        build_state.risk_identity.risk_identity_hash)
    audit = _project_audit(build_state, fingerprints)
    audit_hash = s4.audit_content_hash_of(audit)
    anchor = build_state.anchor
    body = {
        "packet_id": packet_id,
        "schema": s4.S4_PACKET_SCHEMA_ID,
        "status": s4.S4_STATUS,
        "authority_mode": s4.S4_AUTHORITY_MODE,
        "authority_anchor_ref": s4.ANCHOR_REF_PREFIX
        + anchor.anchor_identity_hash,
        "anchor_identity_hash": anchor.anchor_identity_hash,
        "ensemble_projection_state": build_state.ensemble_projection_state,
        "ensemble_id": build_state.ensemble_id,
        "ensemble_size": len(build_state.worker_views),
        "input_content_hash": build_state.input_content_hash,
        "risk_identity": build_state.risk_identity,
        "authority_receipt": build_state.authority_receipt,
        "receipt_content_hash": receipt_hash,
        "baseline_items": build_state.baseline_items,
        "baseline_rows": build_state.baseline_rows,
        "worker_views": build_state.worker_views,
        "raw_artifacts": build_state.raw_artifacts,
        "verification_rows": build_state.verification_rows,
        "conflict_rows": build_state.conflict_rows,
        "adjudication_row": build_state.adjudication_row,
        "query_draft_row": build_state.query_draft_row,
        "journey_link": build_state.journey_link,
        "history_log": build_state.history_log,
        "audience_inspector": audience,
        "audit_inspector": audit,
        "audience_content_hash": audience_hash,
        "audit_content_hash": audit_hash,
    }
    integrity_hash = s4.compute_packet_integrity_hash(body)
    return s4.R5S4AuthorityPacket(**body, packet_integrity_hash=integrity_hash)


def build_s4_authority_packet(
    runtime_input: s4.R5S4RuntimeInput,
) -> s4.R5S4AuthorityPacket:
    """Strict composition: ``project_s4_authority_packet(
    build_s4_authority_state(runtime_input))``."""
    return project_s4_authority_packet(build_s4_authority_state(runtime_input))
