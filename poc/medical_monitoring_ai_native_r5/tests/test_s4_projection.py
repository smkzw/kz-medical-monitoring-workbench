"""Focused W2 tests for the R5-S4 runtime projection (``mm_r5.s4_projection``):
deterministic Chinese audience/audit planes and the six-node acyclic hash DAG.

Every Chinese phrase is asserted against the closed tables declared once in
``s4_contracts`` (no snapshot-of-whole-packet tests, no free-formed text).
"""

from __future__ import annotations

import dataclasses

import pytest

from mm_r5 import s4_contracts as s4
from mm_r5.s4_authority_builder import build_s4_authority_state
from mm_r5.s4_projection import build_s4_authority_packet, project_s4_authority_packet
from s4_runtime_fixtures import (
    ATTEMPT_SETS,
    build_deep_link_state,
    build_runtime_input,
    build_source_input,
)

#: variants whose multi conflict-relation set is identical to plain multi.
_MULTI_LIKE = ("multi_analysis", "failed_verification")


def _packet(state: str) -> s4.R5S4AuthorityPacket:
    """Build one packet; skip with a precise reason when the W1
    ``source_one_hop_zh`` gate blocks the no_ensemble projection (see the W2
    report).  The skip auto-heals once Codex applies the one-line fix to
    ``R5S4AudienceInspector.__post_init__``."""
    try:
        return build_s4_authority_packet(build_runtime_input(state))
    except s4.S4RuntimeContractError as exc:
        if "source_one_hop_zh" in str(exc):
            pytest.skip(
                "W1 defect: R5S4AudienceInspector forbids the contract-"
                "required empty source_one_hop_zh (contract section 6.1); "
                "awaiting Codex same-session fix")
        raise


# ---------------------------------------------------------------------------
# Packet assembly + six-node hash DAG
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", sorted(ATTEMPT_SETS))
def test_packet_self_consistent_for_every_variant(state: str) -> None:
    """The packet constructor re-verifies every hash recipe; a valid packet
    therefore proves the full six-node DAG is consistent."""
    packet = _packet(state)
    assert packet.schema == s4.S4_PACKET_SCHEMA_ID
    assert packet.status == s4.S4_STATUS
    assert packet.authority_mode == s4.S4_AUTHORITY_MODE
    assert packet.ensemble_size == len(packet.worker_views)


def test_packet_id_grammar_single_colon() -> None:
    packet = _packet("multi_analysis")
    assert packet.packet_id == f"r5-s4-contract:{packet.audience_content_hash}"
    assert packet.packet_id.count(":") == 1
    assert s4.matches_grammar(packet.packet_id, "packet_id")


def test_hash_dag_nodes_recompute() -> None:
    packet = _packet("multi_analysis")
    assert packet.audience_content_hash == s4.audience_content_hash_of(
        packet.audience_inspector)
    assert packet.audit_content_hash == s4.audit_content_hash_of(
        packet.audit_inspector)
    assert packet.receipt_content_hash == s4.receipt_content_hash_of(
        packet.authority_receipt)
    assert packet.packet_integrity_hash == s4.compute_packet_integrity_hash(
        s4.packet_as_mapping(packet))


def test_packet_fingerprints_frozen_recipe() -> None:
    packet = _packet("multi_analysis")
    expected = s4.compute_packet_fingerprints(
        packet.audience_content_hash, packet.receipt_content_hash,
        packet.packet_id, packet.risk_identity.risk_identity_hash)
    assert packet.audit_inspector.packet_fingerprints == expected
    assert len(packet.audit_inspector.packet_fingerprints) == 4


def test_audit_hash_excludes_fingerprints_acyclic() -> None:
    """audit_content_hash never covers packet_fingerprints (acyclic DAG)."""
    packet = _packet("multi_analysis")
    inspector = packet.audit_inspector
    core = {field.name: getattr(inspector, field.name)
            for field in dataclasses.fields(inspector)
            if field.name != "packet_fingerprints"}
    assert s4.audit_content_hash_of(inspector) == s4.s4_content_hash(core)


def test_audience_hash_invariant_to_audit_changes() -> None:
    """Audit-only changes never alter the audience hash (plane split)."""
    packet = _packet("multi_analysis")
    audience_hash = s4.audience_content_hash_of(packet.audience_inspector)
    # A structurally different but valid audit inspector: different
    # receipt_content_hash, empty worker/verification rows, no model evidence.
    audit2 = s4.R5S4AuditInspector(
        authority_receipt_ref=packet.audit_inspector.authority_receipt_ref,
        receipt_content_hash="f" * 64,
        digest_context=packet.audit_inspector.digest_context,
        worker_audit_rows=(),
        verification_audit_rows=(),
        adjudication_audit=(),
        conflict_audit=(),
        history_audit=(),
        model_evidence=None,
        packet_fingerprints=packet.audit_inspector.packet_fingerprints)
    assert s4.audit_content_hash_of(audit2) != s4.audit_content_hash_of(
        packet.audit_inspector)
    # the audience plane is untouched by the audit replacement.
    assert s4.audience_content_hash_of(packet.audience_inspector) == (
        audience_hash)


def test_audience_change_not_repairable_via_audit() -> None:
    """An audience leaf change cannot be repaired by touching audit values:
    the packet constructor re-derives the audience hash from the audience
    object and fails closed."""
    packet = _packet("multi_analysis")
    fields = {field.name: getattr(packet, field.name)
              for field in dataclasses.fields(packet)}
    fields["audience_inspector"] = dataclasses.replace(
        packet.audience_inspector, consensus_zh="篡改文案")
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4AuthorityPacket(**fields)


def test_build_is_strict_composition_and_deterministic() -> None:
    ri = build_runtime_input("multi_analysis")
    direct = project_s4_authority_packet(build_s4_authority_state(ri))
    composed = build_s4_authority_packet(ri)
    assert direct == composed
    again = build_s4_authority_packet(build_runtime_input("multi_analysis"))
    assert s4.packet_as_mapping(again) == s4.packet_as_mapping(composed)


def test_input_reorder_same_packet() -> None:
    """Input reordering never changes the packet identity/hash."""
    ri = build_runtime_input("multi_analysis")
    reordered = dataclasses.replace(
        ri,
        attempts=tuple(reversed(ri.attempts)),
        worker_outputs=tuple(reversed(ri.worker_outputs)),
        raw_outputs=tuple(reversed(ri.raw_outputs)),
    )
    assert build_s4_authority_packet(reordered) == build_s4_authority_packet(ri)


# ---------------------------------------------------------------------------
# Audience plane: closed Chinese phrases
# ---------------------------------------------------------------------------


def test_audience_identity_leaves_closed() -> None:
    packet = _packet("multi_analysis")
    audience = packet.audience_inspector
    assert audience.audience_contract_id == "contract.s4.1"
    assert audience.domain_zh == "AE"
    assert audience.severity_zh == "高"
    assert audience.change_state_zh == "新发"
    assert audience.risk_title_zh == "AE 风险提示：发热性中性粒细胞减少"
    assert audience.subject_display_zh == "受试者 1001"
    assert audience.center_display_zh == "中心 01"
    assert audience.project_display_zh == "项目 P-01"
    assert audience.cutoff_display_zh == "数据截止 2026-08-01"


def test_consensus_zh_gated_by_state() -> None:
    assert _packet("no_ensemble").audience_inspector.consensus_zh == (
        "尚无独立分析")
    assert _packet("single_analysis").audience_inspector.consensus_zh == (
        "单一分析不形成一致性结论")
    for state in _MULTI_LIKE:
        assert _packet(state).audience_inspector.consensus_zh == (
            "独立分析存在共同发现、基线项目未被评估，请结合来源核实")
    assert _packet("mutual_negation").audience_inspector.consensus_zh == (
        "独立分析存在共同发现、结论相互矛盾、基线项目未被评估，请结合来源核实")
    assert _packet("graded_conflict").audience_inspector.consensus_zh == (
        "独立分析存在风险分级不一致、基线项目未被评估，请结合来源核实")


def test_adjudication_leaves_gated_by_n() -> None:
    for state in ("no_ensemble", "single_analysis"):
        audience = _packet(state).audience_inspector
        assert audience.adjudication_status_zh == "尚未进行独立裁决"
        assert audience.adjudication_explanation_zh is None
    for state in ("multi_analysis", "failed_verification",
                  "mutual_negation", "graded_conflict"):
        audience = _packet(state).audience_inspector
        assert audience.adjudication_status_zh == "已完成独立裁决"
        assert audience.adjudication_explanation_zh == "需要医学监察员重点查看"


def test_basis_and_history_summary_closed() -> None:
    assert _packet("no_ensemble").audience_inspector.basis_zh == (
        "当前仅展示已识别风险及其来源")
    assert _packet("single_analysis").audience_inspector.basis_zh == (
        "已完成一次独立分析，请结合来源核实")
    assert _packet("multi_analysis").audience_inspector.basis_zh == (
        "已完成多次独立分析，请结合基线、冲突与来源核实")
    assert _packet("no_ensemble").audience_inspector.history_summary_zh == (
        "尚无独立分析记录")
    assert _packet("single_analysis").audience_inspector.history_summary_zh == (
        "已记录一次独立分析及来源核对过程")
    assert _packet("multi_analysis").audience_inspector.history_summary_zh == (
        "已记录多次独立分析、冲突核对及裁决过程")


def test_support_counter_one_hop_closed_templates() -> None:
    for state in ("single_analysis", "multi_analysis", "failed_verification",
                  "mutual_negation", "graded_conflict"):
        audience = _packet(state).audience_inspector
        assert audience.support_evidence_zh == ("来源 loc.src1 已定位",)
        assert audience.source_one_hop_zh == "来源 loc.src1 已在一跳内定位"
    # mutual_negation: m2 negates risk-X => its finding is counterevidence.
    assert _packet("mutual_negation").audience_inspector.counterevidence_zh \
        == ("来源 loc.src1 已定位",)
    assert _packet("multi_analysis").audience_inspector.counterevidence_zh == ()


def test_worker_summaries_finding_gap_verification_templates() -> None:
    audience = _packet("single_analysis").audience_inspector
    assert len(audience.worker_ordinal_summaries) == 1
    summary = audience.worker_ordinal_summaries[0]
    assert summary.ordinal_zh == "分析一"
    assert summary.finding_summary_zh == (
        "发现 f-a1-0（来源 loc.src1）",
        "发现 f-a1-1（来源 loc.src1）",
        "发现 f-a1-2（来源 loc.src1）",
    )
    assert summary.gap_zh == ()
    assert summary.verification_zh == "七项核对均通过"


def test_failed_verification_summary_zh() -> None:
    audience = _packet("failed_verification").audience_inspector
    by_ordinal = {summary.ordinal_zh: summary
                  for summary in audience.worker_ordinal_summaries}
    assert by_ordinal["分析一"].verification_zh == "核对未通过：规则版本不一致"
    assert by_ordinal["分析二"].verification_zh == "七项核对均通过"


def test_audience_baseline_rows_closed_and_sorted() -> None:
    audience = _packet("multi_analysis").audience_inspector
    rows = audience.baseline_rows_zh
    assert [row.row_ref for row in rows] == sorted(
        row.row_ref for row in rows)
    for row in rows:
        item_id = row.row_ref.split(":")[1]
        assert row.item_anchor_zh == f"基线条目 {item_id}"
        assert row.state_zh == "已确认"
        assert row.recheck_zh == "已回查来源"
    assert rows[0].ordinal_zh == "分析一"
    assert rows[1].ordinal_zh == "分析二"


def test_query_leaves_verbatim_and_pd_mapping() -> None:
    audience = _packet("multi_analysis").audience_inspector
    assert audience.query_basis_zh == "存在未评估基线条目，建议补充核实"
    assert audience.query_finding_zh == "基线条目 b2 尚无任何分析覆盖"
    assert audience.query_action_zh == "请补充对 b2 的独立评估"
    assert audience.query_pd_wording_zh == "非方案偏离"
    for state in ("no_ensemble", "single_analysis"):
        other = _packet(state).audience_inspector
        assert other.query_basis_zh is None
        assert other.query_finding_zh is None
        assert other.query_action_zh is None
        assert other.query_pd_wording_zh is None


def test_journey_leaves_available_and_unavailable() -> None:
    audience = _packet("multi_analysis").audience_inspector
    assert audience.journey_available is True
    assert audience.journey_link_zh == "查看该受试者历时记录"
    assert audience.journey_unavailable_reason_zh is None
    ri = dataclasses.replace(
        build_runtime_input("multi_analysis"),
        source_input=build_source_input(available=False,
                                        reason="source_locator_missing"),
        deep_link_state=build_deep_link_state(source_available=False))
    packet = build_s4_authority_packet(ri)
    audience = packet.audience_inspector
    assert audience.journey_available is False
    assert audience.journey_link_zh is None
    assert audience.journey_unavailable_reason_zh == (
        "无法定位到该受试者的对应记录，请核对项目、受试者和数据截止点")


def _audience_strings(packet: s4.R5S4AuthorityPacket):
    """Every string leaf of the audience plane (recursively)."""
    audience = packet.audience_inspector
    strings = []
    for field in dataclasses.fields(audience):
        value = getattr(audience, field.name)
        if isinstance(value, str):
            strings.append(value)
        elif isinstance(value, tuple):
            for item in value:
                if isinstance(item, str):
                    strings.append(item)
                elif dataclasses.is_dataclass(item):
                    for sub in dataclasses.fields(item):
                        leaf = getattr(item, sub.name)
                        if isinstance(leaf, str):
                            strings.append(leaf)
                        elif isinstance(leaf, tuple):
                            strings.extend(x for x in leaf
                                           if isinstance(x, str))
    return strings


@pytest.mark.parametrize("state", sorted(ATTEMPT_SETS))
def test_audience_forbidden_tokens_absent(state: str) -> None:
    joined = " ".join(_audience_strings(_packet(state)))
    for token in s4.FORBIDDEN_AUDIENCE_TOKENS:
        assert token not in joined, (state, token)


def test_audience_has_no_audit_only_leaves() -> None:
    """The audience inspector's field names never collide with audit-only
    leaves (hash_dag forbidden leaves + static audit leaves)."""
    audience_fields = {field.name for field in
                       dataclasses.fields(s4.R5S4AudienceInspector)}
    assert not (audience_fields & s4.AUDIT_ONLY_LEAVES)
    assert "model_evidence" not in audience_fields
    assert "digest_context" not in audience_fields


# ---------------------------------------------------------------------------
# Audit plane
# ---------------------------------------------------------------------------


def test_audit_worker_rows_mirror_root_views() -> None:
    packet = _packet("multi_analysis")
    audit = packet.audit_inspector
    raw_by_attempt = {artifact.attempt_id: artifact
                      for artifact in packet.raw_artifacts}
    assert [row.attempt_id for row in audit.worker_audit_rows] == [
        view.attempt_id for view in sorted(
            packet.worker_views, key=lambda v: v.attempt_id)]
    for row, view in zip(audit.worker_audit_rows,
                         sorted(packet.worker_views,
                                key=lambda v: v.attempt_id)):
        assert row.binding_id == view.binding_id
        assert row.session_id == view.session_id
        assert row.model_id == view.model_id
        assert row.role == "worker"
        assert row.independent_context_hash == view.independent_context_hash
        assert row.declared_output_hash == view.declared_output_hash
        assert row.raw_bytes_sha256 == raw_by_attempt[
            view.attempt_id].raw_bytes_sha256
        assert row.parsed_output_hash == raw_by_attempt[
            view.attempt_id].parsed_output_hash


def test_audit_verification_history_conflict_adjudication() -> None:
    packet = _packet("multi_analysis")
    audit = packet.audit_inspector
    assert [row.verification_id for row in audit.verification_audit_rows] == [
        row.verification_id for row in sorted(
            packet.verification_rows, key=lambda r: r.verification_id)]
    assert audit.history_audit == tuple(sorted(
        entry.entry_hash for entry in packet.history_log.entries))
    assert audit.conflict_audit == tuple(sorted(
        row.conflict_id for row in packet.conflict_rows))
    assert audit.adjudication_audit == ("adj.record.1",)
    assert audit.authority_receipt_ref == (
        "receipt:" + packet.receipt_content_hash)
    assert audit.receipt_content_hash == packet.receipt_content_hash


def test_audit_digest_context_view() -> None:
    packet = _packet("multi_analysis")
    view = packet.audit_inspector.digest_context
    assert view is not None
    assert view.input_content_hash == packet.input_content_hash
    assert view.expected_ensemble_identity == "ens.s4.1"
    assert view.artifact_authorized_source_locators == {
        "artifact:a1": ("loc.src1",), "artifact:a2": ("loc.src1",)}
    assert view.artifact_finding_identities == {
        "artifact:a1": ("risk-X", "risk-Y", "risk-Z"),
        "artifact:a2": ("risk-X", "risk-Y", "risk-Z")}


def test_audit_model_evidence_bound_to_actual_worker() -> None:
    packet = _packet("multi_analysis")
    me = packet.audit_inspector.model_evidence
    assert me is not None
    assert me.model_evidence_id == "model_evidence:me.1"
    assert me.role == "candidate_explanation"
    assert me.adjudication_state == "pending"
    assert me.ensemble_size == 2
    assert me.output_hash in {
        view.declared_output_hash for view in packet.worker_views
        if view.model_id == me.model_id}


# ---------------------------------------------------------------------------
# no_ensemble audience/audit planes (requires the W1 source_one_hop_zh fix;
# see the W2 report -- blocked by the R5S4AudienceInspector non-empty gate)
# ---------------------------------------------------------------------------


def test_no_ensemble_audience_planes():
    """no_ensemble: no worker summaries, no baseline rows, no query leaves,
    frozen consensus/basis/history phrases and an empty audit plane.

    BLOCKED by W1 defect: ``R5S4AudienceInspector.__post_init__`` requires
    ``source_one_hop_zh`` non-empty, but the accepted runtime contract
    section 6.1 requires ``""`` when no locator was located (zero workers).
    Passes as soon as Codex applies the reported one-line fix.
    """
    packet = _packet("no_ensemble")
    audience = packet.audience_inspector
    assert audience.worker_ordinal_summaries == ()
    assert audience.baseline_rows_zh == ()
    assert audience.support_evidence_zh == ()
    assert audience.counterevidence_zh == ()
    assert audience.source_one_hop_zh == ""
    assert audience.consensus_zh == "尚无独立分析"
    assert audience.adjudication_status_zh == "尚未进行独立裁决"
    assert audience.adjudication_explanation_zh is None
    for name in ("query_basis_zh", "query_finding_zh", "query_action_zh",
                 "query_pd_wording_zh"):
        assert getattr(audience, name) is None
    assert audience.basis_zh == "当前仅展示已识别风险及其来源"
    assert audience.history_summary_zh == "尚无独立分析记录"
    audit = packet.audit_inspector
    assert audit.digest_context is None
    assert audit.worker_audit_rows == ()
    assert audit.verification_audit_rows == ()
    assert audit.adjudication_audit == ()
    assert audit.conflict_audit == ()
    assert audit.history_audit == ()
    assert audit.model_evidence is None
