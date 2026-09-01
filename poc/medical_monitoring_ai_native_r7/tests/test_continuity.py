"""Focused synthetic/offline tests for Slice-08A continuity."""
from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from mm_r7.continuity import (
    CarryForwardItem,
    CarryForwardPlan,
    DecisionBaseline,
    PlanValidationError,
    RiskChangeKind,
    RiskProjectionError,
    RuleScope,
    BaselineValidationError,
    build_carry_forward_item,
    build_carry_forward_plan,
    build_decision_baseline,
    canonical_digest,
    canonical_json,
    determine_disposition,
    project_risk_change,
)

NOW = "2026-08-29T04:00:00.000+00:00"


def baseline() -> DecisionBaseline:
    return DecisionBaseline(
        project_id="SYNTHETIC-PROJECT", mode="daily",
        source_run_id="run-n", source_snapshot_id="snapshot-n",
        source_data_cutoff="2026-08-28", source_rule_revision_ids=("rule-b", "rule-a"),
        source_decision_version="decision-n", target_run_id="run-n1",
        target_snapshot_id="snapshot-n1", target_data_cutoff="2026-08-29",
        target_rule_revision_ids=("rule-a", "rule-b"), target_decision_version="decision-n1",
        r5_authority_digest="r5-authority-n", r6_publication_digest="r6-publication-n",
        r6_receipt_digest="r6-receipt-n", source_publication_id="publication-n",
        source_public_run_token="public-run-n", source_publication_state="available",
        created_at=NOW,
    )


def reuse_item(**overrides) -> CarryForwardItem:
    data = {
        "object_type": "risk_instance", "object_ref": "risk-001", "disposition": "reuse_unchanged",
        "ordinal": 0, "source_run_id": "run-n", "source_publication_id": "publication-n",
        "source_public_run_token": "public-run-n", "target_run_id": "run-n1",
        "source_object_id": "risk-001", "target_object_id": "risk-001",
        "source_identity": "identity-001", "target_identity": "identity-001",
        "source_project_id": "SYNTHETIC-PROJECT", "target_project_id": "SYNTHETIC-PROJECT",
        "source_mode": "daily", "target_mode": "daily", "source_publication_state": "available",
        "source_artifact_id": "artifact-risk", "source_artifact_sha256": "a" * 64,
        "artifact_verified": True, "artifact_member_verified": True, "reuse_reviewed": True,
        "data_change_kind": "unchanged", "current_present": True,
        "governing_rule_revision_ids": ("rule-b",), "changed_applicable_rule_ids": (),
        "rule_applicability_known": True, "reason": "沿用上次有效分析",
    }
    data.update(overrides)
    return CarryForwardItem(**data)


def test_canonical_json_and_digest_are_order_independent():
    left = {"z": ["合成", 1], "a": {"b": True, "a": None}}
    right = {"a": {"a": None, "b": True}, "z": ["合成", 1]}
    assert canonical_json(left) == canonical_json(right)
    assert canonical_digest(left) == canonical_digest(right)
    assert canonical_json(left) == '{"a":{"a":null,"b":true},"z":["合成",1]}'


def test_baseline_factory_accepts_only_available_complete_publication():
    pub = {
        "project_id": "SYNTHETIC-PROJECT", "mode": "daily", "run_id": "run-n",
        "snapshot_token": "snapshot-n", "data_cutoff": "2026-08-28",
        "rule_tokens": ["rule-b", "rule-a"], "decision_version": "decision-n",
        "r5_authority_packet_digest": "r5", "publication_fingerprint": "r6",
        "receipt_set_digest": "receipt", "publication_id": "publication-n",
        "public_run_token": "public-run-n", "publication_state": "available",
        "created_at": NOW,
    }
    item = build_decision_baseline(
        pub, target_run_id="run-n1", target_snapshot_id="snapshot-n1",
        target_data_cutoff="2026-08-29", target_decision_version="decision-n1",
        target_rule_revision_ids=("rule-a", "rule-b"),
    )
    assert item.source_rule_revision_ids == ("rule-a", "rule-b")
    assert item.digest == item.compute_digest()
    for mode in ("daily", "pre_lock", "post_lock_pre_cfdi"):
        candidate = build_decision_baseline(
            {**pub, "mode": mode},
            target_run_id="r2",
            target_snapshot_id="s2",
            target_data_cutoff="d2",
            target_decision_version="v2",
        )
        assert candidate.mode == mode
    with pytest.raises(BaselineValidationError):
        build_decision_baseline({**pub, "publication_state": "publishing"}, target_run_id="r2", target_snapshot_id="s2", target_data_cutoff="d2", target_decision_version="v2")
    with pytest.raises(BaselineValidationError):
        build_decision_baseline({**pub, "coverage_complete": False}, target_run_id="r2", target_snapshot_id="s2", target_data_cutoff="d2", target_decision_version="v2")
    for field in ("identity_closed", "coverage_complete"):
        with pytest.raises(BaselineValidationError):
            build_decision_baseline({**pub, field: None}, target_run_id="r2", target_snapshot_id="s2", target_data_cutoff="d2", target_decision_version="v2")


def test_baseline_is_immutable_and_tamper_detected_on_round_trip():
    item = baseline()
    with pytest.raises(FrozenInstanceError):
        item.target_run_id = "other"  # type: ignore[misc]
    forged = item.as_dict()
    forged["baseline_digest"] = "0" * 64
    with pytest.raises(BaselineValidationError):
        DecisionBaseline.from_mapping(forged)


def test_rule_scope_only_invalidates_governed_objects():
    assert RuleScope(("rule-b",), ("rule-a",), True).changed_rule_applies is False
    assert RuleScope(("rule-a",), ("rule-a",), True).changed_rule_applies is True
    assert RuleScope((), ("rule-a",), False).changed_rule_applies is True
    common = dict(source_artifact_id="a", source_artifact_sha256="a" * 64, artifact_verified=True, artifact_member_verified=True, reuse_reviewed=True)
    assert determine_disposition(object_type="risk_instance", governing_rule_revision_ids=("rule-b",), changed_applicable_rule_ids=("rule-a",), **common) == "reuse_unchanged"
    assert determine_disposition(object_type="risk_instance", governing_rule_revision_ids=("rule-a",), changed_applicable_rule_ids=("rule-a",), **common) == "re_evaluate_rule_change"
    assert determine_disposition(object_type="risk_instance", governing_rule_revision_ids=(), changed_applicable_rule_ids=("rule-a",), rule_applicability_known=False, **common) == "re_evaluate_rule_change"


def test_missing_high_risk_row_never_closes_from_absence():
    assert determine_disposition(object_type="risk_instance", data_change_kind="deleted", current_present=False, prior_risk_state="escalated", prior_severity="high", current_listing_complete=True, baseline_eligible=True) == "re_evaluate_changed_data"
    item = build_carry_forward_item({
        "object_type": "risk_instance", "object_ref": "risk-high", "data_change_kind": "deleted",
        "current_present": False, "prior_risk_state": "escalated", "reason": "缺行不能证明风险消除",
    })
    assert item.disposition == "re_evaluate_changed_data"
    assert item.absence_is_not_resolution


def test_close_requires_current_evidence_and_gates():
    item = build_carry_forward_item({
        "object_type": "risk_instance", "object_ref": "risk-close", "data_change_kind": "unchanged",
        "current_present": True, "closure_allowed": True, "closure_evidence_refs": ("current-evidence",),
        "current_listing_complete": True, "baseline_eligible": True, "current_risk_state": "closed",
        "r2_transition_type": "closed", "reason": "已有证据支持结案",
    })
    assert item.disposition == "close_with_evidence"
    with pytest.raises(PlanValidationError):
        CarryForwardItem(object_type="risk_instance", object_ref="risk-close", disposition="close_with_evidence", current_present=False, data_change_kind="missing", closure_allowed=True, closure_evidence_refs=("evidence",), reason="证据")


def test_reuse_requires_artifact_member_and_object_review():
    assert reuse_item().disposition == "reuse_unchanged"
    for field in ("artifact_verified", "artifact_member_verified", "reuse_reviewed"):
        with pytest.raises(PlanValidationError):
            reuse_item(**{field: False})
    with pytest.raises(PlanValidationError):
        reuse_item(source_identity="a", target_identity="b")


def test_object_types_and_query_drafts_are_narrow():
    with pytest.raises(PlanValidationError):
        CarryForwardItem(object_type="subject_timeline", object_ref="timeline", disposition="re_evaluate_changed_data", reason="x")
    with pytest.raises(PlanValidationError):
        CarryForwardItem(object_type="query_draft", object_ref="query", disposition="re_evaluate_changed_data", query_status="sent", reason="x")
    item = build_carry_forward_item({"object_type": "query_draft", "object_ref": "query", "data_change_kind": "revised", "reason": "本轮数据修订变化"})
    assert item.disposition == "re_evaluate_changed_data"


def test_plan_build_validate_round_trip_and_stable_status_digest():
    plan = build_carry_forward_plan(
        project_id="SYNTHETIC-PROJECT", mode="daily", target_run_id="run-n1",
        target_snapshot_id="snapshot-n1", target_data_cutoff="2026-08-29",
        target_decision_version="decision-n1", baseline=baseline(),
        items=(reuse_item(ordinal=0), reuse_item(ordinal=1, object_ref="risk-002")),
        created_at=NOW,
    )
    for mode in ("pre_lock", "post_lock_pre_cfdi"):
        with pytest.raises(PlanValidationError):
            build_carry_forward_plan(
                project_id="SYNTHETIC-PROJECT",
                mode=mode,
                execution_basis="incremental",
                target_run_id="run-n1",
                target_snapshot_id="snapshot-n1",
                target_data_cutoff="2026-08-29",
                target_decision_version="decision-n1",
                r5_authority_digest="r5",
                r6_publication_digest="r6",
                r6_receipt_digest="receipt",
                items=(),
                created_at=NOW,
            )
    assert isinstance(plan.as_dict()["baseline"], dict)
    assert plan.as_dict()["baseline"]["baseline_digest"] == plan.baseline.digest
    assert plan.counts["reuse_unchanged"] == 2
    assert plan.compute_digest() == plan.digest
    verified = plan.with_status("verified")
    published = verified.with_status("published")
    assert verified.digest == published.digest == plan.digest
    assert CarryForwardPlan.from_mapping(published.as_dict()).digest == plan.digest
    with pytest.raises(PlanValidationError):
        plan.with_status("published")


def test_risk_change_projection_covers_seven_kinds_and_no_parallel_continued_transition():
    common = dict(risk_identity_id="risk-1", project_id="SYNTHETIC-PROJECT", reason="reason", current_source_ref="run-n1/risk-1", comparison_source_ref="run-n/risk-1", created_at=NOW)
    cases = [
        (dict(from_state=None, to_state="established", transition_type="established"), RiskChangeKind.NEW),
        (dict(from_state="established", to_state="escalated", transition_type="escalated", from_severity="medium", to_severity="high"), RiskChangeKind.UPGRADED),
        (dict(from_state="escalated", to_state="escalated"), RiskChangeKind.CONTINUED),
        (dict(from_state="escalated", to_state="deescalated", transition_type="deescalated", from_severity="high", to_severity="medium"), RiskChangeKind.DOWNGRADED),
        (dict(from_state="deescalated", to_state="closed", transition_type="closed", evidence_refs=("close",)), RiskChangeKind.CLOSED),
        (dict(from_state="closed", to_state="reopened", transition_type="reopened"), RiskChangeKind.REOPENED),
        (dict(from_state="escalated", to_state="escalated", data_missing=True), RiskChangeKind.NEEDS_REJUDGMENT),
    ]
    for facts, expected in cases:
        projected = project_risk_change(**common, **facts)
        assert projected.risk_change_kind is expected
        if expected is RiskChangeKind.CONTINUED:
            assert projected.transition_type == ""
    with pytest.raises(RiskProjectionError):
        project_risk_change(**common, from_state="closed", to_state="escalated", transition_type="escalated")
    with pytest.raises(RiskProjectionError):
        project_risk_change(**common, from_state="closed", to_state="closed")

def test_r2_projection_does_not_infer_downgrade_without_r2_transition():
    common = dict(risk_identity_id="risk-1", project_id="SYNTHETIC-PROJECT", reason="reason", current_source_ref="run-n1/risk-1", comparison_source_ref="run-n/risk-1", created_at=NOW)
    for facts in (
        dict(from_state="established", to_state="established", from_severity="high", to_severity="medium"),
        dict(from_state="escalated", to_state="deescalated", from_severity="high", to_severity="high"),
    ):
        projected = project_risk_change(**common, **facts)
        assert projected.risk_change_kind is RiskChangeKind.NEEDS_REJUDGMENT

def test_identity_ambiguity_resolution_stays_needs_rejudgment():
    common = dict(risk_identity_id="risk-1", project_id="SYNTHETIC-PROJECT", reason="reason", current_source_ref="run-n1/risk-1", comparison_source_ref="run-n/risk-1", created_at=NOW)
    projected = project_risk_change(**common, from_state="identity_ambiguous", to_state="established", transition_type="established")
    assert projected.risk_change_kind is RiskChangeKind.NEEDS_REJUDGMENT
    with pytest.raises(RiskProjectionError):
        project_risk_change(**common, from_state="established", to_state="established", transition_type="established")


def test_terminal_r2_identity_cannot_be_restaged():
    with pytest.raises(RiskProjectionError):
        project_risk_change(
            risk_identity_id="risk-old",
            project_id="SYNTHETIC-PROJECT",
            from_state="superseded",
            to_state="escalated",
            transition_type="escalated",
            reason="identity is terminal",
            current_source_ref="run-n1/risk-old",
            comparison_source_ref="run-n/risk-old",
            created_at=NOW,
        )
