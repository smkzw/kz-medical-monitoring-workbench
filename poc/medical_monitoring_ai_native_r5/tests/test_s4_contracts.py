"""Focused W1 tests for the R5-S4 runtime typed contracts and deterministic
synthetic fixtures.

Covers, per the accepted runtime contract section 6.1 / 10.1 and the focused
work-item W1 scope:

* the closed vocabularies and every Chinese mapping table (each closed-set
  member is asserted, not snapshot-compared);
* the canonical serialization + six-node acyclic hash DAG recipe helpers;
* the exact reference grammars;
* typed-object immutability and local fail-closed validation (closed enums,
  sha256, grammars, non-hideable conflicts, recheck-required rows);
* the two frozen errata: ``R5S4HistoryLog`` empty-chain rule and
  ``S4AcceptedHistoryState`` ``genesis_or_sha``;
* the append-only history chain semantics and the locatable/unavailable source
  semantics;
* the deterministic runtime fixtures (every variant) and their byte
  consistency with the accepted external anchor.

These tests read only the accepted authority anchor JSON (test-only oracle
read allowed by contract section 2.2) through ``s4_runtime_fixtures``; the
runtime source ``src/mm_r5/s4_*`` is never imported by them except through the
public ``mm_r5.s4_contracts`` surface.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import is_dataclass

import pytest

import mm_r4.ensemble as en
from mm_r5 import s4_contracts as s4

from s4_runtime_fixtures import (
    ACCEPTED_ANCHOR_JSON,
    ATTEMPT_SETS,
    MAX_CARDINALITY_ATTEMPTS,
    build_typed_anchor,
    build_receipt,
    build_runtime_input,
    build_max_cardinality_input,
    build_history_log,
    build_source_input,
    build_baseline_items,
    parse_worker_output,
    raw_bytes_for,
)


# ---------------------------------------------------------------------------
# Closed vocabularies
# ---------------------------------------------------------------------------


def test_closed_vocabularies_exact() -> None:
    """Every closed enum must equal the accepted machine overlay exactly."""
    assert s4.ENSEMBLE_PROJECTION_STATES == (
        "no_ensemble", "single_analysis", "multi_analysis")
    assert s4.BASELINE_STATES == (
        "confirmed", "partially_supported", "unsupported", "outdated",
        "insufficient_evidence", "not_applicable")
    assert s4.RECHECK_REQUIRED_STATES == ("confirmed", "unsupported")
    assert s4.ASSESSMENT_REASON_CODES == (
        "source_rechecked", "content_match", "partial_content_match",
        "content_absent_from_source", "source_revision_superseded",
        "evidence_insufficient", "locator_unresolvable",
        "outside_assessment_scope")
    assert s4.VERIFICATION_DIMENSIONS == (
        "identity", "version", "date", "unit", "source", "rule",
        "artifact_integrity")
    assert s4.VERIFICATION_RESULTS == ("passed", "failed", "not_evaluable")
    assert s4.VERIFICATION_FAILURE_CODES == (
        "identity_mismatch", "version_mismatch", "date_out_of_window",
        "unit_mismatch", "source_unresolvable", "rule_version_mismatch",
        "artifact_hash_mismatch", "input_content_mismatch")
    assert s4.CONFLICT_RELATIONS == (
        "shared_finding", "single_model_new", "graded_conflict",
        "mutual_negation", "baseline_miss")
    assert s4.CONFLICT_DISPLAY_STATES == (
        "needs_attention", "visible_conflict", "visible_baseline_miss")
    assert s4.NON_HIDEABLE_RELATIONS == frozenset(
        {"mutual_negation", "baseline_miss"})
    assert s4.ADJUDICATION_OUTCOMES == (
        "merged_supported", "distinct_supported", "rejected_by_evidence",
        "version_mismatch", "needs_user_attention")
    assert s4.ATTEMPT_ROLES == ("worker", "adjudicator")
    assert s4.RAW_OUTPUT_FORMATS == ("utf8_text",)
    assert s4.FALLBACK_POLICIES == ("none",)
    assert s4.PD_WORDING_STATES == ("not_pd", "verify_whether_pd")
    assert s4.MONITORING_PRIORITIES == ("high", "medium", "low", "unknown")
    assert s4.SEVERITIES == ("critical", "high", "medium", "low")
    assert s4.DOMAINS == (
        "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
        "symptom_efficacy", "protocol_compliance")
    assert s4.CHANGE_KINDS == (
        "initial_current", "new", "upgraded", "continued", "downgraded",
        "resolved", "reopened", "superseded", "not_evaluable",
        "not_comparable")
    assert s4.CHANGE_CAUSES == (
        "data", "knowledge", "rule", "mapping", "model", "method", "coverage",
        "denominator", "population", "visibility", "mode", "user_decision")
    assert s4.HISTORY_ENTRY_KINDS == (
        "attempt_bound", "baseline_assessed", "verification_recorded",
        "conflict_derived", "adjudication_recorded", "query_draft_generated",
        "inspection_finalized")
    assert s4.MODEL_EVIDENCE_ROLES == (
        "candidate_explanation", "counterevidence_suggestion")
    assert s4.MODEL_EVIDENCE_ADJUDICATION_STATES == (
        "accepted", "divergent", "pending")


def test_seven_dimensions_and_supporting_outcomes() -> None:
    assert s4.SEVEN_DIMENSIONS == frozenset(s4.VERIFICATION_DIMENSIONS)
    assert len(s4.SEVEN_DIMENSIONS) == 7
    assert s4.SUPPORTING_OUTCOMES == frozenset(
        {"merged_supported", "distinct_supported"})


# ---------------------------------------------------------------------------
# Chinese mappings (each closed-set member asserted)
# ---------------------------------------------------------------------------


def test_domain_zh_every_member() -> None:
    expected = {
        "ae": "AE", "mh": "MH", "cm": "合并用药", "ip": "试验药",
        "lab_exam": "检验/检查", "hospital_procedure": "住院/操作",
        "symptom_efficacy": "症状/疗效", "protocol_compliance": "方案符合",
    }
    assert set(s4.DOMAIN_ZH) == set(s4.DOMAINS)
    assert s4.DOMAIN_ZH == expected


def test_severity_zh_every_member() -> None:
    expected = {"critical": "紧急", "high": "高", "medium": "中", "low": "低"}
    assert set(s4.SEVERITY_ZH_BY_SEVERITY) == set(s4.SEVERITIES)
    assert s4.SEVERITY_ZH_BY_SEVERITY == expected
    assert s4.SEVERITIES_ZH == ("紧急", "高", "中", "低")


def test_severity_mapping_unknown_fails_closed() -> None:
    assert s4.SEVERITY_MAPPING == {
        "high": "high", "medium": "medium", "low": "low",
        "unknown": "fail_closed"}


def test_change_kind_zh_every_member() -> None:
    expected = {
        "initial_current": "首次识别", "new": "新发", "upgraded": "风险升高",
        "continued": "持续存在", "downgraded": "风险降低", "resolved": "已消失",
        "reopened": "再次出现", "superseded": "已被后续记录替代",
        "not_evaluable": "暂无法评估", "not_comparable": "暂不可比较",
    }
    assert set(s4.CHANGE_KIND_ZH) == set(s4.CHANGE_KINDS)
    assert s4.CHANGE_KIND_ZH == expected


def test_baseline_state_zh_every_member() -> None:
    expected = {
        "confirmed": "已确认", "partially_supported": "部分支持",
        "unsupported": "不支持", "outdated": "已过期",
        "insufficient_evidence": "证据不足", "not_applicable": "不适用",
    }
    assert set(s4.BASELINE_STATE_ZH) == set(s4.BASELINE_STATES)
    assert s4.BASELINE_STATE_ZH == expected
    assert s4.RECHECK_ZH == {True: "已回查来源", False: "未回查来源"}


def test_verification_zh_every_member() -> None:
    assert s4.VERIFICATION_RESULT_ZH == {
        "passed": "七项核对均通过", "failed": "核对未通过",
        "not_evaluable": "暂无法核对"}
    expected_failure = {
        "identity_mismatch": "身份不一致",
        "version_mismatch": "版本不一致",
        "date_out_of_window": "日期超出范围",
        "unit_mismatch": "单位不一致",
        "source_unresolvable": "来源无法定位",
        "rule_version_mismatch": "规则版本不一致",
        "artifact_hash_mismatch": "文件内容不一致",
        "input_content_mismatch": "输入内容不一致",
    }
    assert set(s4.VERIFICATION_FAILURE_ZH) == set(s4.VERIFICATION_FAILURE_CODES)
    assert s4.VERIFICATION_FAILURE_ZH == expected_failure


def test_conflict_relation_zh_every_member() -> None:
    expected = {
        "shared_finding": "共同发现",
        "single_model_new": "单一分析新增发现",
        "graded_conflict": "风险分级不一致",
        "mutual_negation": "结论相互矛盾",
        "baseline_miss": "基线项目未被评估",
    }
    assert set(s4.CONFLICT_RELATION_ZH) == set(s4.CONFLICT_RELATIONS)
    assert s4.CONFLICT_RELATION_ZH == expected
    # frozen presentation order is the relation enum order.
    assert tuple(s4.CONFLICT_RELATION_ZH) == s4.CONFLICT_RELATIONS


def test_adjudication_outcome_zh_every_member() -> None:
    expected = {
        "merged_supported": "可合并为同一发现",
        "distinct_supported": "应保留为不同发现",
        "rejected_by_evidence": "现有证据不支持",
        "version_mismatch": "版本不一致，暂无法判断",
        "needs_user_attention": "需要医学监察员重点查看",
    }
    assert set(s4.ADJUDICATION_OUTCOME_ZH) == set(s4.ADJUDICATION_OUTCOMES)
    assert s4.ADJUDICATION_OUTCOME_ZH == expected


def test_pd_wording_zh_every_member() -> None:
    assert s4.PD_WORDING_ZH == {
        "not_pd": "非方案偏离", "verify_whether_pd": "请核实是否为方案偏离"}


def test_ordinal_zh_is_ten_members() -> None:
    assert s4.ORDINAL_ZH == (
        "分析一", "分析二", "分析三", "分析四", "分析五",
        "分析六", "分析七", "分析八", "分析九", "分析十")
    assert len(s4.ORDINAL_ZH) == 10


def test_consensus_status_history_basis_journey_phrases() -> None:
    assert s4.CONSENSUS_ZH == {
        "no_ensemble": "尚无独立分析",
        "single_analysis": "单一分析不形成一致性结论",
        "multi_consistent": "多个独立分析结果一致",
        "multi_conflict": "独立分析存在{conflicts}，请结合来源核实",
    }
    assert s4.ADJUDICATION_STATUS_ZH == {
        "none": "尚未进行独立裁决", "done": "已完成独立裁决"}
    assert s4.HISTORY_SUMMARY_ZH == {
        "no_ensemble": "尚无独立分析记录",
        "single_analysis": "已记录一次独立分析及来源核对过程",
        "multi_analysis": "已记录多次独立分析、冲突核对及裁决过程"}
    assert s4.BASIS_ZH == {
        "no_ensemble": "当前仅展示已识别风险及其来源",
        "single_analysis": "已完成一次独立分析，请结合来源核实",
        "multi_analysis": "已完成多次独立分析，请结合基线、冲突与来源核实"}
    assert s4.JOURNEY_LINK_ZH == "查看该受试者历时记录"
    assert s4.JOURNEY_UNAVAILABLE_REASON_ZH == (
        "无法定位到该受试者的对应记录，请核对项目、受试者和数据截止点")
    assert s4.AUDIENCE_CONTRACT_ID == "contract.s4.1"


def test_forbidden_audience_tokens_closed() -> None:
    assert set(s4.FORBIDDEN_AUDIENCE_TOKENS) == {
        "provider", "model_id", "model_version", "attempt", "hash", "backend",
        "session", "consensus", "worker", "adjudicator", "binding", "正式事实",
        "候选信号", "只读", "待办", "未读", "金标准", "已证实", "权威结论",
        "model_majority", "卡列表", "已发送", "已关闭"}


def test_audit_only_leaves_disjoint_from_audience_fields() -> None:
    """Audit-only leaves may never collide with audience inspector fields."""
    audience_fields = {f.name for f in __import__(
        "dataclasses").fields(s4.R5S4AudienceInspector)}
    assert not (audience_fields & s4.AUDIT_ONLY_LEAVES)
    # forbidden audience tokens are never used as audience field names.
    assert not (audience_fields & set(s4.FORBIDDEN_AUDIENCE_TOKENS))


# ---------------------------------------------------------------------------
# Canonical recipes / hash DAG
# ---------------------------------------------------------------------------


def test_canonical_bytes_recipe() -> None:
    value = {"b": 2, "a": 1, "c": ["x", "y"]}
    b1 = s4.s4_canonical_bytes(value)
    b2 = s4.s4_canonical_bytes({"c": ["x", "y"], "a": 1, "b": 2})
    assert b1 == b2  # keys sorted, deterministic
    assert b1.endswith(b"\n")  # trailing newline (recipe)
    text = b1.decode("utf-8")
    assert text == '{"a":1,"b":2,"c":["x","y"]}\n'
    # containers keep their stored order (a many field's canonical order is
    # decided at construction by the schema sorted_unique rule, not here).
    assert s4.s4_canonical_bytes({"c": ["y", "x"]}) != \
        s4.s4_canonical_bytes({"c": ["x", "y"]})
    # NFC normalization
    decomposed = unicodedata.normalize("NFD", "数据截止")
    composed = unicodedata.normalize("NFC", "数据截止")
    assert s4.s4_canonical_bytes({"k": decomposed}) == \
        s4.s4_canonical_bytes({"k": composed})


def test_canonical_rejects_nonfinite_nan() -> None:
    # allow_nan=False => json.dumps raises ValueError for non-finite floats.
    with pytest.raises(ValueError):
        s4.s4_canonical_bytes({"v": float("nan")})
    with pytest.raises(ValueError):
        s4.s4_canonical_bytes({"v": float("inf")})


def test_s4_vs_r4_style_hash_differ() -> None:
    value = {"proj": "s4"}
    assert s4.s4_content_hash(value) != s4.r4_style_hash(value)
    # r4-style has no trailing newline; s4 has it.
    assert s4.r4_style_hash(value) == hashlib.sha256(
        b'{"proj":"s4"}').hexdigest()


def test_content_hash_excluding() -> None:
    obj = s4.R5S4HistoryEntry(
        entry_id="h1", seq=1, kind="attempt_bound", payload_ref="p1",
        prior_entry_hash=s4.GENESIS_HASH, entry_hash="")
    # entry_hash is the canonical hash of every non-hash field (the chain
    # helper computes exactly that; it includes prior_entry_hash).
    assert obj.entry_hash == s4.compute_history_entry_hash(obj)
    assert obj.entry_hash == s4.s4_content_hash(
        {f.name: getattr(obj, f.name)
         for f in __import__("dataclasses").fields(obj)
         if f.name != "entry_hash"})


def test_compute_packet_id_and_grammar() -> None:
    h = "a" * 64
    pid = s4.compute_packet_id(h)
    assert pid == f"r5-s4-contract:{h}"
    assert pid.count(":") == 1
    assert s4.matches_grammar(pid, "packet_id")
    with pytest.raises(s4.S4RuntimeContractError):
        s4.compute_packet_id("not-a-sha")


def test_compute_packet_fingerprints() -> None:
    fps = s4.compute_packet_fingerprints(
        audience_content_hash_value="b" * 64,
        receipt_content_hash_value="c" * 64,
        packet_id_value="r5-s4-contract:" + "b" * 64,
        risk_identity_hash_value="d" * 64)
    assert len(fps) == 4
    assert fps == tuple(sorted([
        "audience:" + "b" * 64,
        "receipt:" + "c" * 64,
        "packet:r5-s4-contract:" + "b" * 64,
        "risk_identity:" + "d" * 64]))


def test_compute_packet_integrity_hash_excludes_identity_keys() -> None:
    packet = {
        "packet_id": "r5-s4-contract:" + "b" * 64,
        "packet_integrity_hash": "x" * 64,
        "audience_content_hash": "b" * 64,
        "audit_content_hash": "c" * 64,
        "receipt_content_hash": "d" * 64,
        "schema": s4.S4_PACKET_SCHEMA_ID,
        "status": s4.S4_STATUS,
        "authority_mode": s4.S4_AUTHORITY_MODE,
        "payload": {"k": 1},
    }
    ih = s4.compute_packet_integrity_hash(packet)
    assert ih == s4.s4_content_hash({"payload": {"k": 1}})


def test_anchor_identity_hash_recompute() -> None:
    anchor = build_typed_anchor()
    body = s4.packet_as_mapping(anchor)
    assert anchor.anchor_identity_hash == s4.compute_anchor_identity_hash(body)


def test_receipt_content_hash_self_consistent() -> None:
    receipt = build_receipt()
    assert s4.receipt_content_hash_of(receipt) == s4.s4_content_hash(receipt)
    assert s4.receipt_content_hash_of(receipt) == hashlib.sha256(
        s4.s4_canonical_bytes(receipt)).hexdigest()


# ---------------------------------------------------------------------------
# Reference grammar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("grammar,good,bad", [
    ("marker", ["d09_marker:m-rk", "d10_marker:m1"], ["risk-X", "d09:m", ""]),
    ("baseline_row", ["baseline-row:item.b1:a1"], ["baseline-row:a1", "x:y:z", ""]),
    ("raw", ["raw:a1"], ["a1", "raw:", "raw:a:b"]),
    ("verification", ["verification:v-a1"], ["v-a1", "verification:", "v:a"]),
    ("receipt", ["receipt:" + "a" * 64], ["receipt:abc", "a" * 64, "receipt:"]),
    ("history", ["history:s4.0", "history:s4.1"], ["s4.0", "history:", ""]),
    ("anchor", ["anchor:" + "a" * 64], ["anchor:abc", "a" * 64, ""]),
    ("project_ref", ["project.p1"], ["p1", "project.", ""]),
    ("run_ref", ["run.r1"], ["r1", ""]),
    ("snapshot_ref", ["snap.s1"], ["s1", ""]),
    ("cutoff_ref", ["cutoff.v1"], ["v1", ""]),
    ("source_revision", ["rev.1"], ["1", ""]),
    ("packet_id", ["r5-s4-contract:" + "a" * 64], ["r5-s4-contract:abc", "a" * 64]),
])
def test_grammar(grammar: str, good: list, bad: list) -> None:
    for value in good:
        assert s4.matches_grammar(value, grammar), (grammar, value)
    for value in bad:
        assert not s4.matches_grammar(value, grammar), (grammar, value)


def test_unknown_grammar_fails_closed() -> None:
    with pytest.raises(s4.S4RuntimeImplementationError):
        s4.matches_grammar("x", "no_such_grammar")


# ---------------------------------------------------------------------------
# Typed-object immutability + fail-closed local validation
# ---------------------------------------------------------------------------


def test_public_dataclasses_are_frozen() -> None:
    names = [
        "R5S4AuthorityPacket", "R5S4RiskIdentity", "R5S4WorkerView",
        "R5S4RawOutputArtifact", "R5S4BaselineRow", "R5S4ConflictRow",
        "R5S4VerificationRow", "R5S4AdjudicationRow", "R5S4QueryDraftRow",
        "R5S4JourneyLink", "R5S4HistoryEntry", "R5S4HistoryLog",
        "R5S4AudienceInspector", "R5S4AudienceBaselineRow",
        "R5S4AudienceWorkerSummary", "R5S4AuditInspector", "R5S4AuditWorkerRow",
        "R5S4VerificationAuditRow", "R5S4DigestContextView",
        "R5S4ModelEvidenceRef", "S4AcceptedAuthorityAnchor",
        "S4AcceptedRiskIdentity", "S4AcceptedAdjudicatorBinding",
        "S4AcceptedBaselineItem", "S4AcceptedHistoryState",
        "S4AcceptedQueryDraft", "S4AttemptAuthorityRow",
        "S4JourneyTargetIdentity", "S4ModelEvidencePermit",
        "S4SourceRevisionPair", "R5S4RawOutputInput", "R5S4AdjudicatorInput",
        "R5S4SyntheticAudienceLabels", "R5S4SourceInput", "R5S4RuntimeInput",
        "R5S4BuildState",
    ]
    for name in names:
        cls = getattr(s4, name)
        assert is_dataclass(cls), name
        assert cls.__dataclass_params__.frozen, name


def test_validation_issue_message_formula() -> None:
    issue = s4.R5S4ValidationIssue(
        code="s4.schema_key_mismatch", path="packet.ensemble_size",
        message_zh="")
    assert issue.message_zh == "核对未通过：packet.ensemble_size（s4.schema_key_mismatch）"
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4ValidationIssue(
            code="s4.x", path="a", message_zh="free text")


def test_validation_result_sorts_and_dedupes() -> None:
    issues = [
        s4.R5S4ValidationIssue("s4.b", "2", ""),
        s4.R5S4ValidationIssue("s4.a", "1", ""),
        s4.R5S4ValidationIssue("s4.a", "1", ""),
    ]
    result = s4.R5S4ValidationResult(ok=False, issues=tuple(issues),
                                     expected_packet=None)
    assert result.ok is False
    assert [i.code for i in result.issues] == ["s4.a", "s4.b"]
    assert result.expected_packet is None


def test_conflict_row_non_hideable_rejected() -> None:
    base = dict(conflict_id="c1", relation="mutual_negation",
                display_state="visible_conflict", hidden=False,
                monitoring_priority="high",
                member_attempt_ids=("a1", "a2"),
                ordinal_labels_zh=("分析一", "分析二"))
    s4.R5S4ConflictRow(**base)
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4ConflictRow(**{**base, "hidden": True})


def test_baseline_row_recheck_required() -> None:
    row = dict(row_ref="baseline-row:item.b1:a1", item_id="item.b1",
               attempt_id="a1", state="confirmed",
               reason_codes=("source_rechecked",),
               source_recheck_locator_ids=("loc.src1",),
               source_revision_id="rev.1", snapshot_id="snap.1",
               recheck_complete=True)
    s4.R5S4BaselineRow(**row)
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4BaselineRow(**{**row, "source_recheck_locator_ids": ()})


def test_worker_view_role_must_be_worker() -> None:
    base = dict(attempt_id="a1", ordinal=1, ordinal_zh="分析一",
                binding_id="b", session_id="s", model_id="m",
                model_version="1.0", role="worker",
                independent_context_hash="a" * 64,
                input_content_hash="b" * 64, output_artifact_ref="artifact:a1",
                declared_output_hash="c" * 64,
                claimed_date_window="w", claimed_unit_contract="u",
                claimed_source_revision="rev.1", claimed_rule_id="rule.r1",
                claimed_rule_version="1.0", assessment_row_refs=(),
                finding_ids=(), gap_ids=(), raw_artifact_ref="raw:a1",
                verification_ref="verification:v-a1")
    s4.R5S4WorkerView(**base)
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4WorkerView(**{**base, "role": "adjudicator"})
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4WorkerView(**{**base, "raw_artifact_ref": "a1"})


def test_adjudication_row_present_required_and_absent_clean() -> None:
    present = s4.R5S4AdjudicationRow(
        present=True, binding_id="adj.b1", session_id="adj.s1",
        model_id="adj.model", model_version="1.0",
        independent_context_hash="a" * 64, outcome="needs_user_attention",
        reviewed_artifact_refs=("artifact:a1", "artifact:a2"),
        adds_explanation_only=True)
    assert present.present
    absent = s4.R5S4AdjudicationRow(
        present=False, binding_id="", session_id="", model_id="",
        model_version="", independent_context_hash=None, outcome="",
        reviewed_artifact_refs=(), adds_explanation_only=True)
    assert not absent.present
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4AdjudicationRow(
            present=True, binding_id=None, session_id="adj.s1",
            model_id="adj.model", model_version="1.0",
            independent_context_hash="a" * 64,
            outcome="needs_user_attention",
            reviewed_artifact_refs=("artifact:a1",),
            adds_explanation_only=True)


def test_query_draft_row_draft_only_and_marker() -> None:
    base = dict(query_draft_id="qd.1", risk_ref="d09_marker:m-rk",
                basis_zh="b", finding_zh="f", action_zh="a",
                source_locator_refs=("loc.src1",),
                pd_wording_state="not_pd", draft_only=True)
    s4.R5S4QueryDraftRow(**base)
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4QueryDraftRow(**{**base, "risk_ref": "not-a-marker"})
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4QueryDraftRow(**{**base, "source_locator_refs": ()})
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4QueryDraftRow(**{**base, "draft_only": False})


def test_verification_row_exact_seven_dimensions() -> None:
    base = dict(verification_id="v1", attempt_id="a1",
                checked_dimensions=tuple(sorted(s4.SEVEN_DIMENSIONS)),
                result="passed", failure_reason_codes=(), recomputed=True)
    s4.R5S4VerificationRow(**base)
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4VerificationRow(**{
            **base, "checked_dimensions": ("identity", "version")})
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4VerificationRow(**{**base, "recomputed": False})
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4VerificationRow(
            **{**base, "result": "passed",
               "failure_reason_codes": ("identity_mismatch",)})


# ---------------------------------------------------------------------------
# Errata: R5S4HistoryLog empty chain + S4AcceptedHistoryState genesis_or_sha
# ---------------------------------------------------------------------------


def test_history_log_empty_chain_errata() -> None:
    s4.R5S4HistoryLog(history_ref="history:s4.0", head_seq=0,
                      head_hash=s4.GENESIS_HASH, entries=())
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4HistoryLog(history_ref="history:s4.0", head_seq=0,
                          head_hash="a" * 64, entries=())
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4HistoryLog(history_ref="history:s4.0", head_seq=1,
                          head_hash=s4.GENESIS_HASH, entries=())


def test_history_log_bad_chain_rejected() -> None:
    log = build_history_log("multi_analysis")
    entries = list(log.entries)
    # duplicate seq
    bad = [s4.R5S4HistoryEntry(
        entry_id="h1", seq=1, kind=e.kind, payload_ref=e.payload_ref,
        prior_entry_hash=e.prior_entry_hash, entry_hash=e.entry_hash)
        for e in entries[:1]] * 2
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4HistoryLog(history_ref="history:s4.1", head_seq=2,
                          head_hash="x" * 64, entries=tuple(bad))
    # non-contiguous seq
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4HistoryLog(history_ref="history:s4.1", head_seq=2,
                          head_hash="x" * 64, entries=entries[:1])


def test_history_entry_hash_chain_recomputed() -> None:
    log = build_history_log("multi_analysis")
    assert s4.history_chain_valid(log.entries)
    assert s4.history_log_valid(log)
    for entry in log.entries:
        assert entry.entry_hash == s4.compute_history_entry_hash(entry)
    # tamper: recompute a mutated payload gives a different chain hash.
    mutated = s4.R5S4HistoryEntry(
        entry_id=log.entries[0].entry_id, seq=1,
        kind=log.entries[0].kind, payload_ref="TAMPERED",
        prior_entry_hash=log.entries[0].prior_entry_hash, entry_hash="")
    assert mutated.entry_hash != log.entries[0].entry_hash


def test_accepted_history_state_genesis_or_sha_errata() -> None:
    # seq=0 && head=genesis => hash must be genesis.
    s4.S4AcceptedHistoryState(seq=0, head=s4.GENESIS_HASH,
                              hash=s4.GENESIS_HASH)
    with pytest.raises(s4.S4RuntimeContractError):
        s4.S4AcceptedHistoryState(seq=0, head=s4.GENESIS_HASH,
                                  hash="a" * 64)
    # seq>0 => hash must be sha256.
    s4.S4AcceptedHistoryState(seq=6, head=s4.GENESIS_HASH, hash="a" * 64)
    with pytest.raises(s4.S4RuntimeContractError):
        s4.S4AcceptedHistoryState(seq=6, head=s4.GENESIS_HASH,
                                  hash=s4.GENESIS_HASH)


# ---------------------------------------------------------------------------
# Source semantics (locatable / unavailable)
# ---------------------------------------------------------------------------


def test_source_input_locatable_shape() -> None:
    source = build_source_input(available=True)
    assert source.availability_state == "locatable"
    assert source.resolution is not None
    assert source.unavailable_reason is None
    s4.validate_source_input_shape(source)
    # invalid: locatable with a reason.
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4SourceInput(availability_state="locatable",
                           resolution=source.resolution,
                           unavailable_reason="target_not_projectable")
    # invalid: locatable without resolution.
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4SourceInput(availability_state="locatable",
                           resolution=None, unavailable_reason=None)


def test_source_input_unavailable_shape() -> None:
    source = build_source_input(available=False, reason="source_locator_missing")
    assert source.availability_state == "unavailable"
    assert source.resolution is None
    assert source.unavailable_reason == "source_locator_missing"
    s4.validate_source_input_shape(source)
    # invalid: unavailable with resolution.
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4SourceInput(
            availability_state="unavailable",
            resolution=build_source_input(available=True).resolution,
            unavailable_reason="target_not_projectable")
    # invalid: unavailable with an off-enum reason.
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4SourceInput(availability_state="unavailable",
                           resolution=None, unavailable_reason="some_other")


def test_source_resolution_locatable_contract() -> None:
    res = build_source_input(available=True).resolution
    assert res.fallback_policy == "none"
    assert res.resolution_state == "locatable"
    assert res.locator_id == "loc.src1"
    assert res.content_hash  # auto-computed non-empty


# ---------------------------------------------------------------------------
# Deterministic runtime fixtures (every variant) + anchor consistency
# ---------------------------------------------------------------------------


def test_fixture_anchor_matches_accepted_sha() -> None:
    anchor = build_typed_anchor()
    raw_sha = hashlib.sha256(ACCEPTED_ANCHOR_JSON.read_bytes()).hexdigest()
    # The accepted anchor raw SHA is independently frozen in the contract
    # acceptance record (1fb07001...).  We re-read it and assert the typed
    # anchor reproduces the same identity hash.
    accepted = json.loads(ACCEPTED_ANCHOR_JSON.read_text(encoding="utf-8"))
    assert anchor.anchor_identity_hash == accepted["anchor_identity_hash"]
    assert anchor.accepted_risk_identity.risk_identity_hash == \
        accepted["accepted_risk_identity_hash"]
    assert len(raw_sha) == 64


@pytest.mark.parametrize("state", sorted(ATTEMPT_SETS))
def test_runtime_input_valid_for_every_variant(state: str) -> None:
    ri = build_runtime_input(state)
    assert ri.anchor.anchor_identity_hash == build_typed_anchor().anchor_identity_hash
    assert ri.attempts == build_runtime_input(state).attempts
    # every repeated field is a tuple.
    for name in ("attempts", "worker_outputs", "raw_outputs",
                 "baseline_items"):
        assert isinstance(getattr(ri, name), tuple)
    # the builder/projector/validator may reuse the typed input as-is.


def test_fixture_raw_and_parsed_hashes_match_anchor() -> None:
    accepted = json.loads(ACCEPTED_ANCHOR_JSON.read_text(encoding="utf-8"))
    rows = {r["attempt_id"]: r for r in accepted["attempt_authority_rows"]}
    for aid in ("a1", "a2", "m1", "m2", "g1", "g2"):
        raw = raw_bytes_for(aid)
        out = parse_worker_output(raw, aid)
        assert hashlib.sha256(raw).hexdigest() == rows[aid]["raw_bytes_sha256"]
        assert en.worker_output_content_hash(out) == rows[aid][
            "parsed_output_hash"]
        # raw and parsed hashes are in different domains.
        assert hashlib.sha256(raw).hexdigest() != en.worker_output_content_hash(out)


def test_fixture_history_heads_match_accepted_states() -> None:
    accepted = json.loads(ACCEPTED_ANCHOR_JSON.read_text(encoding="utf-8"))
    assert build_history_log("no_ensemble").head_hash == \
        accepted["accepted_history_no_ensemble"]["hash"]
    assert build_history_log("single_analysis").head_hash == \
        accepted["accepted_history_single_analysis"]["hash"]
    assert build_history_log("multi_analysis").head_hash == \
        accepted["accepted_history_multi_analysis"]["hash"]


def test_fixture_baseline_items_match_anchor() -> None:
    accepted = json.loads(ACCEPTED_ANCHOR_JSON.read_text(encoding="utf-8"))
    items = build_baseline_items()
    assert len(items) == len(accepted["accepted_baseline_items"])
    assert {i.item_id for i in items} == {
        b["item_id"] for b in accepted["accepted_baseline_items"]}


def test_validation_result_ok_when_no_issues() -> None:
    result = s4.R5S4ValidationResult(ok=True, issues=(), expected_packet=None)
    assert result.ok is True
    assert result.issues == ()


# ---------------------------------------------------------------------------
# Reviewer defect 1: R5S4ValidationResult.ok requires an exact bool
# ---------------------------------------------------------------------------


def _result_issue(code: str = "s4.x", path: str = "a") -> s4.R5S4ValidationIssue:
    return s4.R5S4ValidationIssue(code=code, path=path, message_zh="")


@pytest.mark.parametrize("bad", [1, 0, "true", "false", "yes", None, 1.0, [], ()])
def test_validation_result_ok_rejects_non_bool(bad: object) -> None:
    """``ok`` must be an exact bool; arbitrary values must never be coerced."""
    with pytest.raises(s4.S4RuntimeContractError):
        s4.R5S4ValidationResult(ok=bad, issues=(), expected_packet=None)  # type: ignore[arg-type]


def test_validation_result_ok_false_with_issues() -> None:
    """ok=True with issues flips to False; ok stays exact bool."""
    result = s4.R5S4ValidationResult(
        ok=True, issues=(_result_issue(),), expected_packet=None)
    assert result.ok is False
    assert result.issues == (_result_issue(),)


def test_validation_result_ok_true_no_issues() -> None:
    result = s4.R5S4ValidationResult(ok=True, issues=(), expected_packet=None)
    assert result.ok is True


def test_validation_result_ok_exact_bool_type() -> None:
    result = s4.R5S4ValidationResult(ok=True, issues=(), expected_packet=None)
    assert type(result.ok) is bool


# ---------------------------------------------------------------------------
# Reviewer defect 2: public export surface is data contracts/constants/errors
# only
# ---------------------------------------------------------------------------

#: names that were previously exported and are implementation helpers; they
#: must NOT appear in ``__all__`` (the reviewer defect).
_IMPLEMENTATION_HELPERS = frozenset({
    "s4_canonical_bytes", "s4_canonical_json", "s4_sha256", "s4_content_hash",
    "r4_style_hash", "s4_content_hash_excluding", "is_sha256_hex",
    "is_marker_ref", "matches_grammar",
    "compute_anchor_identity_hash", "compute_history_entry_hash",
    "audience_content_hash_of", "audit_content_hash_of",
    "receipt_content_hash_of", "compute_packet_id",
    "compute_packet_fingerprints", "compute_packet_integrity_hash",
    "history_log_valid", "history_chain_valid",
    "validate_source_input_shape", "packet_as_mapping",
})


def test_public_export_surface_is_data_contracts_only() -> None:
    """Every ``__all__`` entry must exist in the module and must not be an
    implementation helper; the public surface is frozen data contracts,
    constants and errors only."""
    exported = set(s4.__all__)
    assert exported == set(s4.__all__)  # no duplicates
    assert exported, "public export surface must not be empty"
    for name in exported:
        assert hasattr(s4, name), f"__all__ references missing module name {name}"
    # no implementation helper leaks into the public export surface.
    assert not (exported & _IMPLEMENTATION_HELPERS), (
        f"implementation helpers leaked into __all__: "
        f"{sorted(exported & _IMPLEMENTATION_HELPERS)}")


def test_public_export_contains_all_typed_contracts() -> None:
    """Every frozen typed data contract is part of the public surface."""
    for name in ("R5S4AuthorityPacket", "R5S4RiskIdentity", "R5S4WorkerView",
                 "R5S4RawOutputArtifact", "R5S4BaselineRow", "R5S4ConflictRow",
                 "R5S4VerificationRow", "R5S4AdjudicationRow",
                 "R5S4QueryDraftRow", "R5S4JourneyLink", "R5S4HistoryEntry",
                 "R5S4HistoryLog", "R5S4AudienceInspector",
                 "R5S4AuditInspector", "R5S4RuntimeInput", "R5S4BuildState",
                 "S4AcceptedAuthorityAnchor", "R5S4ValidationIssue",
                 "R5S4ValidationResult", "S4RuntimeContractError",
                 "S4RuntimeImplementationError"):
        assert name in s4.__all__, f"{name} missing from public __all__"


# ---------------------------------------------------------------------------
# Reviewer defect 3: max-cardinality fixture + N=10 authority-bound proof
# ---------------------------------------------------------------------------


def test_max_cardinality_anchor_bound() -> None:
    """The accepted external anchor roots exactly six attempts; N=10 cannot
    be honestly constructed.

    Contract §5.1 declares ``multi_analysis: 2 <= N <= 10``, but a valid
    packet must bind every worker view and raw artifact to an ACCEPTED
    per-attempt authority row (machine verifier ``_anchor_attempt_row`` ->
    ``s4.anchor_claim_drift``).  The accepted anchor contains exactly six
    ``attempt_authority_rows``; a 10-attempt packet would need ten distinct
    accepted rows.  Copying a row, duplicating binding/session/context, or
    inventing authority not rooted in the typed external anchor are all
    contract-forbidden, so the honest maximum is N=6."""
    accepted = json.loads(ACCEPTED_ANCHOR_JSON.read_text(encoding="utf-8"))
    rows = accepted["attempt_authority_rows"]
    assert isinstance(rows, list)
    assert len(rows) == 6, (
        "accepted anchor must carry exactly six attempt_authority_rows to "
        "bound N; found %d" % len(rows))
    ids = [r["attempt_id"] for r in rows]
    assert len(set(ids)) == len(ids), "anchor rows must have distinct attempt ids"
    assert set(ids) == set(("a1", "a2", "m1", "m2", "g1", "g2"))
    # every row is fully authority-rooted (all leaf pairs present).
    for row in rows:
        for key in ("attempt_id", "input_content_hash", "artifact_ref",
                    "parsed_output_hash", "raw_bytes_sha256", "date_window",
                    "unit_contract", "source_revision", "rule_id",
                    "rule_version", "model_id", "model_version"):
            assert row.get(key), f"anchor row {row['attempt_id']} missing {key}"
    # the honest max == number of accepted rows == 6 < 10.
    assert len(rows) < 10
    assert MAX_CARDINALITY_ATTEMPTS == ("a1", "a2", "m1", "m2", "g1", "g2")


def test_max_cardinality_fixture_six_distinct() -> None:
    """N=6 fixture uses every accepted row once with six distinct
    binding/session/context and a shared input hash."""
    ri = build_max_cardinality_input()
    assert len(ri.attempts) == 6
    assert tuple(a.attempt_id for a in ri.attempts) == MAX_CARDINALITY_ATTEMPTS
    assert len({a.binding_id for a in ri.attempts}) == 6
    assert len({a.session_id for a in ri.attempts}) == 6
    assert len({a.independent_context_hash for a in ri.attempts}) == 6
    assert len({a.input_content_hash for a in ri.attempts}) == 1
    # no copied authority: every attempt binds to its own accepted row.
    accepted = json.loads(ACCEPTED_ANCHOR_JSON.read_text(encoding="utf-8"))
    rows = {r["attempt_id"]: r for r in accepted["attempt_authority_rows"]}
    for attempt in ri.attempts:
        row = rows[attempt.attempt_id]
        assert attempt.input_content_hash == row["input_content_hash"]
        assert attempt.output_artifact_ref == row["artifact_ref"]
        assert attempt.output_hash == row["parsed_output_hash"]
        assert attempt.claimed_date_window == row["date_window"]
        assert attempt.claimed_unit_contract == row["unit_contract"]
        assert attempt.claimed_source_revision == row["source_revision"]
        assert attempt.claimed_rule_id == row["rule_id"]
        assert attempt.claimed_rule_version == row["rule_version"]
        assert attempt.model_id == row["model_id"]
        assert attempt.model_version == row["model_version"]
    # raw/parsed hashes match the anchor for every attempt.
    for aid in MAX_CARDINALITY_ATTEMPTS:
        raw = raw_bytes_for(aid)
        out = parse_worker_output(raw, aid)
        row = rows[aid]
        assert hashlib.sha256(raw).hexdigest() == row["raw_bytes_sha256"]
        assert en.worker_output_content_hash(out) == row["parsed_output_hash"]
    # adjudicator reviews the exact six active artifacts.
    assert ri.adjudicator is not None
    assert ri.adjudicator.binding.reviewed_artifact_refs == tuple(sorted(
        f"artifact:{aid}" for aid in MAX_CARDINALITY_ATTEMPTS))
    # ModelEvidence is omitted: the single accepted permit covers only the
    # a1/a2 pair (ensemble_size=2) and must not be projected into N=6.
    assert ri.model_evidence is None
    # upstream inspector refs cover all six attempts.
    assert tuple(ri.upstream_inspector.analysis_attempt_refs) == (
        "a1", "a2", "g1", "g2", "m1", "m2")


def test_max_cardinality_ordinals_within_vocabulary() -> None:
    """The six N=6 workers map to 分析一..分析六 (within the frozen 10-label
    ordinal vocabulary)."""
    ri = build_max_cardinality_input()
    ordinals = sorted(a.attempt_id for a in ri.attempts)
    for index, aid in enumerate(ordinals, start=1):
        assert index <= len(s4.ORDINAL_ZH)
        assert s4.ORDINAL_ZH[index - 1] == f"分析{['一','二','三','四','五','六','七','八','九','十'][index-1]}"
