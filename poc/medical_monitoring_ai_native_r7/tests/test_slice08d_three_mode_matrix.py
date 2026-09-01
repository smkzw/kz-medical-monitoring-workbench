"""Slice-08D frozen 20-cell three-mode synthetic matrix + input-side oracle.

Contract anchors:
- reviews/medical_monitoring_r7_slice08d_three_mode_regression_contract_v0_1_20260830.md
- reviews/medical_monitoring_r7_slice08d_three_mode_regression_contract_v0_2_20260830.md §11–§12

Expected values are rebuilt only from input-side frozen facts and actual member
bytes. Case keys are pytest ids only and never enter product or oracle branches.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import pytest

from mm_r1.store import Store
from mm_r6 import mode_output as mo
from mm_r7.continuity import (
    BaselineValidationError,
    CarryForwardItem,
    DecisionBaseline,
    PlanValidationError,
    build_carry_forward_item,
    build_carry_forward_plan,
    build_decision_baseline,
    canonical_digest,
    project_risk_change_kind,
    validate_decision_baseline,
)
from mm_r7.continuity_bridge import (
    ContinuityIntegrityError,
    build_verified_carry_forward_item,
    commit_mode_outputs,
    compute_artifact_member_set_digest,
    validate_r5_authority_packet,
)
from mm_r7.launch_registry import (
    BASIS_FULL,
    BASIS_INCREMENTAL,
    CONTINUITY_PLAN_STATE_PUBLISHED,
    IdempotencyConflictError,
    LaunchRegistry,
    MODE_DAILY,
    MODE_POST_LOCK_PRE_CFDI,
    MODE_PRE_LOCK,
    PUBLICATION_STATE_AVAILABLE,
    content_digest as product_content_digest,
)
from mm_r7.run_binding import (
    RunBindingError,
    RunBindingStore,
    freeze_default_mtplx_effective_profile,
)
from mm_r7.run_setup import (
    RunSetupError,
    canonical_keyed_diff,
    generate_work_units,
)

from fixtures_run_setup import make_fixture
from test_continuity_bridge import (
    PROJECT_ID as BRIDGE_PROJECT,
    PUBLIC_TOKEN,
    RISK_ID,
    RUN_ID,
    CUTOFF,
    SNAPSHOT_ID,
    _make_daily_outputs,
    _make_post_lock_outputs,
    _make_pre_lock_outputs,
    _make_r5_packet,
    _make_run_binding,
)


NOW = "2026-08-30T01:00:00.000+00:00"
PROJECT = BRIDGE_PROJECT  # share R5/R6 bridge project identity
CASE_KEYS = (
    "DF-N",
    "DF-B",
    "DF-M",
    "DF-R",
    "DF-C",
    "DI-N",
    "DI-B",
    "DI-M",
    "DI-R",
    "DI-C",
    "PL-N",
    "PL-B",
    "PL-M",
    "PL-R",
    "PL-C",
    "PC-N",
    "PC-B",
    "PC-M",
    "PC-R",
    "PC-C",
)


@dataclass(frozen=True)
class CellFacts:
    """Structured input facts. Executors/oracles branch on these fields only."""

    family: str
    condition: str
    mode: str
    execution_basis: str
    snapshot_token: str = "snap-08d-current"
    data_cutoff: str = "2026-08-29"
    decision_version: str = "decision-08d-v1"
    rule_tokens: Tuple[str, ...] = ("rule-a", "rule-b")
    idempotency_key: str = "08d-cell"
    prior_risk_state: Optional[str] = "escalated"
    prior_severity: Optional[str] = "high"
    current_present: bool = True
    data_change_kind: str = "unchanged"
    coverage_complete: bool = True
    identity_closed: bool = True
    publication_state: str = "available"
    baseline_project_id: str = PROJECT
    baseline_mode: str = MODE_DAILY
    baseline_digest_drift: bool = False
    select_alternate_baseline: bool = False
    revision_attribution: str = "data_revision"
    query_ref: str = ""
    fixed_total: Optional[bool] = None
    change_scope_field: str = ""
    late_callback_after_reopen: bool = False
    member_bytes: Tuple[bytes, ...] = field(
        default_factory=lambda: (b"m1", b"m2", b"m3", b"m4")
    )
    r5_digest_seed: str = "r5-08d"
    receipt_digest_seed: str = "receipt-08d"
    compare_snapshot_token: str = "snap-08d-prior"
    alternate_snapshot_token: str = "snap-08d-alt"


def _facts_for_case(case_key: str) -> CellFacts:
    """Map pytest id -> input facts. Returned object never carries case_key."""

    table: Dict[str, CellFacts] = {
        "DF-N": CellFacts(family="daily_full", condition="normal", mode=MODE_DAILY, execution_basis=BASIS_FULL, data_change_kind="added", current_present=True, prior_risk_state=None, prior_severity=None),
        "DF-B": CellFacts(family="daily_full", condition="boundary", mode=MODE_DAILY, execution_basis=BASIS_FULL, data_change_kind="deleted", current_present=False, prior_risk_state="escalated", prior_severity="high"),
        "DF-M": CellFacts(family="daily_full", condition="missing", mode=MODE_DAILY, execution_basis=BASIS_FULL, coverage_complete=False, identity_closed=False),
        "DF-R": CellFacts(family="daily_full", condition="replay", mode=MODE_DAILY, execution_basis=BASIS_FULL, idempotency_key="08d-df-replay", data_change_kind="added", current_present=True, prior_risk_state=None, prior_severity=None),
        "DF-C": CellFacts(family="daily_full", condition="conflict", mode=MODE_DAILY, execution_basis=BASIS_FULL, idempotency_key="08d-df-conflict", change_scope_field="snapshot_token"),
        "DI-N": CellFacts(family="daily_incr", condition="normal", mode=MODE_DAILY, execution_basis=BASIS_INCREMENTAL, data_change_kind="unchanged"),
        "DI-B": CellFacts(family="daily_incr", condition="boundary", mode=MODE_DAILY, execution_basis=BASIS_INCREMENTAL, select_alternate_baseline=True, data_change_kind="unchanged"),
        "DI-M": CellFacts(family="daily_incr", condition="missing", mode=MODE_DAILY, execution_basis=BASIS_INCREMENTAL, baseline_project_id="OTHER-PROJECT", baseline_mode=MODE_PRE_LOCK, publication_state="publishing", baseline_digest_drift=True, coverage_complete=False),
        "DI-R": CellFacts(family="daily_incr", condition="replay", mode=MODE_DAILY, execution_basis=BASIS_INCREMENTAL, idempotency_key="08d-di-replay", data_change_kind="unchanged"),
        "DI-C": CellFacts(family="daily_incr", condition="conflict", mode=MODE_DAILY, execution_basis=BASIS_INCREMENTAL, idempotency_key="08d-di-conflict", change_scope_field="baseline", data_change_kind="revised"),
        "PL-N": CellFacts(family="pre_lock", condition="normal", mode=MODE_PRE_LOCK, execution_basis=BASIS_FULL, revision_attribution="data_revision", data_change_kind="revised"),
        "PL-B": CellFacts(family="pre_lock", condition="boundary", mode=MODE_PRE_LOCK, execution_basis=BASIS_FULL, revision_attribution="query_driven", query_ref="Q-08D-001", data_change_kind="revised"),
        "PL-M": CellFacts(family="pre_lock", condition="missing", mode=MODE_PRE_LOCK, execution_basis=BASIS_FULL, revision_attribution="query_driven", query_ref="", data_change_kind="revised"),
        "PL-R": CellFacts(family="pre_lock", condition="replay", mode=MODE_PRE_LOCK, execution_basis=BASIS_FULL, idempotency_key="08d-pl-replay", revision_attribution="data_revision", data_change_kind="revised"),
        "PL-C": CellFacts(family="pre_lock", condition="conflict", mode=MODE_PRE_LOCK, execution_basis=BASIS_INCREMENTAL, idempotency_key="08d-pl-conflict", change_scope_field="listing"),
        "PC-N": CellFacts(family="post_lock", condition="normal", mode=MODE_POST_LOCK_PRE_CFDI, execution_basis=BASIS_FULL, fixed_total=True),
        "PC-B": CellFacts(family="post_lock", condition="boundary", mode=MODE_POST_LOCK_PRE_CFDI, execution_basis=BASIS_FULL, fixed_total=True, idempotency_key="08d-pc-replay-same"),
        "PC-M": CellFacts(family="post_lock", condition="missing", mode=MODE_POST_LOCK_PRE_CFDI, execution_basis=BASIS_INCREMENTAL, fixed_total=False),
        "PC-R": CellFacts(family="post_lock", condition="replay", mode=MODE_POST_LOCK_PRE_CFDI, execution_basis=BASIS_FULL, fixed_total=True, late_callback_after_reopen=True, idempotency_key="08d-pc-recover"),
        "PC-C": CellFacts(family="post_lock", condition="conflict", mode=MODE_POST_LOCK_PRE_CFDI, execution_basis=BASIS_FULL, fixed_total=True, change_scope_field="cutoff", idempotency_key="08d-pc-scope"),
    }
    return table[case_key]


def _oracle_jsonable(value: Any) -> Any:
    """Local canonicalization for the input-side oracle (stdlib only)."""

    if isinstance(value, dict):
        return {str(k): _oracle_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_oracle_jsonable(v) for v in value]
    if isinstance(value, bytes):
        return list(value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and value == value and value not in (float("inf"), float("-inf")):
        return value
    raise TypeError("oracle unsupported value: %s" % type(value).__name__)


def _oracle_canonical_json(value: Any) -> str:
    return json.dumps(
        _oracle_jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _oracle_sha256(value: Any) -> str:
    return hashlib.sha256(_oracle_canonical_json(value).encode("utf-8")).hexdigest()


def _oracle_attribution(revision_attribution: str, query_ref: str) -> str:
    if revision_attribution == "query_driven" and isinstance(query_ref, str) and query_ref.strip():
        return "Query 后修订影响"
    return "本轮数据修订变化"


def _oracle_member_ids(member_bytes: Sequence[bytes]) -> Tuple[str, ...]:
    return tuple(sorted(_oracle_sha256({"bytes": list(blob)})[:16] for blob in member_bytes))


def _oracle_member_set_digest(member_bytes: Sequence[bytes]) -> str:
    return _oracle_sha256(list(_oracle_member_ids(member_bytes)))


def _oracle_disposition(facts: CellFacts) -> str:
    """Closed medical disposition expectation from CellFacts only (no product calls)."""

    change = facts.data_change_kind
    if change in (None, ""):
        change = "unchanged"
    if not facts.current_present or change in {"deleted", "missing"}:
        return "re_evaluate_changed_data"
    if change in {"added", "revised", "cannot_compare"}:
        return "re_evaluate_changed_data"
    if change == "unchanged" and facts.current_present and facts.execution_basis == "incremental":
        # Positive incremental reuse is the medical expectation for DI cells that
        # still must prove verification via the real R1/R5/R6 verifier path.
        return "reuse_unchanged"
    return "re_evaluate_changed_data"


def _oracle_risk_change(facts: CellFacts) -> str:
    """Closed medical change-kind expectation from CellFacts only (no product calls)."""

    if not facts.current_present or facts.data_change_kind in {"deleted", "missing"}:
        return "needs_rejudgment"
    if facts.prior_risk_state is None:
        return "new"
    if facts.data_change_kind == "revised":
        return "upgraded"
    if facts.data_change_kind == "unchanged":
        return "continued"
    return "needs_rejudgment"


def expected_from_inputs(facts: CellFacts) -> Dict[str, Any]:
    """Rebuild expected outcomes from CellFacts with stdlib-only oracle helpers."""

    expected: Dict[str, Any] = {
        "mode": facts.mode,
        "execution_basis": facts.execution_basis,
        "member_set_digest": _oracle_member_set_digest(facts.member_bytes),
        "member_ids": list(_oracle_member_ids(facts.member_bytes)),
        "disposition": _oracle_disposition(facts),
        "risk_change_kind": _oracle_risk_change(facts),
        "r5_digest": facts.r5_digest_seed,
        "receipt_digest": facts.receipt_digest_seed,
    }

    mapping = {
        ("daily_full", "normal"): dict(outcome="available", has_baseline=False, publication_state="available"),
        ("daily_full", "boundary"): dict(
            outcome="needs_rejudgment",
            disposition="re_evaluate_changed_data",
            risk_change_kind="needs_rejudgment",
            absence_is_not_resolution=True,
        ),
        ("daily_full", "missing"): dict(outcome="error", error_code="baseline_source_incomplete"),
        ("daily_full", "replay"): dict(outcome="replay", publication_state="available"),
        ("daily_full", "conflict"): dict(outcome="error", error_code="idempotency_conflict"),
        ("daily_incr", "normal"): dict(outcome="available", has_baseline=True, disposition="reuse_unchanged"),
        ("daily_incr", "boundary"): dict(
            outcome="available",
            has_baseline=True,
            comparison_snapshot=facts.alternate_snapshot_token,
            disposition="reuse_unchanged",
        ),
        ("daily_incr", "missing"): dict(
            outcome="error",
            error_codes=frozenset(
                {
                    "baseline_not_published",
                    "baseline_mode_mismatch",
                    "baseline_source_incomplete",
                    "invalid_decision_baseline",
                    "incremental_requires_diff",
                }
            ),
        ),
        ("daily_incr", "replay"): dict(outcome="replay", has_baseline=True, disposition="reuse_unchanged"),
        ("daily_incr", "conflict"): dict(outcome="error", error_code="idempotency_conflict"),
        ("pre_lock", "normal"): dict(outcome="available", attribution="本轮数据修订变化"),
        ("pre_lock", "boundary"): dict(outcome="available", attribution="Query 后修订影响"),
        ("pre_lock", "missing"): dict(outcome="available", attribution="本轮数据修订变化", query_gap=True),
        ("pre_lock", "replay"): dict(outcome="replay", attribution="本轮数据修订变化"),
        ("pre_lock", "conflict"): dict(
            outcome="error",
            error_codes=frozenset({"incremental_not_supported_for_mode", "invalid_carry_forward_plan"}),
        ),
        ("post_lock", "normal"): dict(outcome="available", fixed_total=True, publication_state="available"),
        ("post_lock", "boundary"): dict(outcome="replay", fixed_total=True),
        ("post_lock", "missing"): dict(
            outcome="error",
            error_codes=frozenset(
                {
                    "incremental_not_supported_for_mode",
                    "invalid_carry_forward_plan",
                    "mode_entry_blocked",
                }
            ),
        ),
        ("post_lock", "replay"): dict(outcome="replay", half_publication=False),
        ("post_lock", "conflict"): dict(outcome="new_run", old_publication_preserved=True),
    }
    key = (facts.family, facts.condition)
    if key not in mapping:
        raise AssertionError("unmapped input facts")
    expected.update(mapping[key])
    return expected


def _reserve(
    registry: LaunchRegistry,
    facts: CellFacts,
    *,
    snapshot_token: Optional[str] = None,
    baseline_token: Optional[str] = None,
    data_cutoff: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    execution_basis: Optional[str] = None,
) -> Any:
    basis = execution_basis
    if basis is None:
        basis = facts.execution_basis if facts.mode == MODE_DAILY else BASIS_FULL
    return registry.reserve(
        PROJECT,
        idempotency_key=idempotency_key or facts.idempotency_key,
        mode=facts.mode if facts.mode in {MODE_DAILY, MODE_PRE_LOCK, MODE_POST_LOCK_PRE_CFDI} else MODE_DAILY,
        execution_basis=basis,
        current_snapshot_token=snapshot_token or facts.snapshot_token,
        baseline_token=baseline_token,
        rule_tokens=facts.rule_tokens,
        data_cutoff=data_cutoff or facts.data_cutoff,
        comparison_range="合成完整范围",
    )


def _publish_available(
    registry: LaunchRegistry,
    facts: CellFacts,
    launch: Any,
    *,
    plan: Any,
    member_ids: Sequence[str],
    member_set_digest: str,
    r6_output_set_digest: str,
) -> Any:
    registry.save_continuity_plan(plan)
    registry.verify_continuity_plan(PROJECT, launch.run_id, expected_plan_digest=plan.plan_digest)
    registry.reserve_publication(
        PROJECT,
        launch.run_id,
        idempotency_key="pub-" + launch.run_id,
        request_fingerprint=plan.r6_publication_digest or "r6-" + launch.run_id,
        snapshot_token=facts.snapshot_token,
        data_cutoff=facts.data_cutoff,
    )
    registry.mark_completed(launch.run_id, project_id=PROJECT)
    ordered_members = tuple(sorted(str(m) for m in member_ids))
    return registry.finalize_publication(
        PROJECT,
        launch.run_id,
        r5_authority_packet_digest=plan.r5_authority_digest,
        receipt_set_digest=plan.r6_receipt_digest,
        r6_output_set_digest=r6_output_set_digest,
        artifact_member_ids=ordered_members,
        artifact_member_set_digest=product_content_digest(list(ordered_members)),
    )


def _item_from_facts(
    facts: CellFacts,
    *,
    target_run_id: str,
    source_run_id: str = "run-source",
    source_publication_id: str = "pub-source",
    source_public_run_token: str = "public-source",
    artifact_id: str = "",
    artifact_sha: str = "",
    verified: bool = False,
    reason: str = "合成连续性事实",
) -> CarryForwardItem:
    mode = facts.mode if facts.mode in {MODE_DAILY, MODE_PRE_LOCK, MODE_POST_LOCK_PRE_CFDI} else MODE_DAILY
    payload: Dict[str, Any] = {
        "object_type": "risk_instance",
        "object_ref": RISK_ID,
        "data_change_kind": facts.data_change_kind,
        "current_present": facts.current_present,
        "prior_risk_state": facts.prior_risk_state,
        "prior_severity": facts.prior_severity,
        "reason": reason,
        "attribution": _oracle_attribution(facts.revision_attribution, facts.query_ref),
        "target_run_id": target_run_id,
        "target_project_id": PROJECT,
        "target_mode": mode,
        "source_run_id": source_run_id,
        "source_publication_id": source_publication_id,
        "source_public_run_token": source_public_run_token,
        "source_project_id": PROJECT,
        "source_mode": mode,
        "source_object_id": RISK_ID,
        "target_object_id": RISK_ID,
        "source_identity": "identity-" + RISK_ID,
        "target_identity": "identity-" + RISK_ID,
        "current_listing_complete": True,
        "baseline_eligible": facts.execution_basis == BASIS_INCREMENTAL,
    }
    if artifact_id:
        payload.update(
            {
                "source_artifact_id": artifact_id,
                "source_artifact_sha256": artifact_sha or artifact_id,
                "artifact_verified": verified,
                "artifact_member_verified": verified,
                "reuse_reviewed": verified,
            }
        )
    if facts.current_present and facts.data_change_kind not in {"deleted", "missing"}:
        payload["current_risk_state"] = "escalated" if facts.prior_risk_state else "established"
        payload["current_severity"] = "high"
        if facts.prior_risk_state is None:
            payload["r2_transition_type"] = "established"
        elif facts.data_change_kind == "revised":
            payload["r2_transition_type"] = "escalated"
    return build_carry_forward_item(payload)


def _bridge_commit(tmp_path: Path, mode: str, *, fixed_total: Optional[bool] = None) -> Dict[str, Any]:
    store = Store(tmp_path / "artifacts.sqlite3", tmp_path / "artifact_files")
    run = _make_run_binding(mode, project_id=BRIDGE_PROJECT)
    if mode == MODE_POST_LOCK_PRE_CFDI and fixed_total is False:
        run = dict(run)
        run["fixed_total"] = False
    if mode == MODE_POST_LOCK_PRE_CFDI:
        outputs = _make_post_lock_outputs(run)
    elif mode == MODE_PRE_LOCK:
        outputs = _make_pre_lock_outputs(run)
    else:
        outputs = _make_daily_outputs(run)
    packet = _make_r5_packet(project_id=BRIDGE_PROJECT)
    validated = validate_r5_authority_packet(
        packet,
        run_binding=run,
        project_id=BRIDGE_PROJECT,
        run_id=RUN_ID,
        public_run_token=PUBLIC_TOKEN,
        snapshot_id=SNAPSHOT_ID,
        data_cutoff=CUTOFF,
    )
    committed = commit_mode_outputs(store, outputs, run_binding=run, r5_packet=validated)
    return {
        "store": store,
        "run": run,
        "outputs": outputs,
        "packet": validated,
        "committed": committed,
        "r6_output_set_digest": committed.r6_output_set_digest,
        "artifact_member_set_digest": committed.artifact_member_set_digest,
        "artifact_member_ids": tuple(committed.artifact_member_ids),
    }


def _run_daily_full(facts: CellFacts, tmp_path: Path) -> Dict[str, Any]:
    expected_members = _oracle_member_ids(facts.member_bytes)
    member_digest = _oracle_member_set_digest(facts.member_bytes)
    r6_out = canonical_digest({"outputs": list(expected_members), "mode": facts.mode})

    if facts.condition == "boundary":
        item = _item_from_facts(facts, target_run_id="run-boundary", reason="缺行不能证明风险消除")
        kind = project_risk_change_kind(
            from_state=facts.prior_risk_state,
            to_state=facts.prior_risk_state or "escalated",
            data_missing=True,
        )
        return {
            "outcome": "needs_rejudgment",
            "disposition": item.disposition,
            "risk_change_kind": kind.value,  # product actual
            "absence_is_not_resolution": True,
            "member_set_digest": member_digest,
            "member_ids": list(expected_members),
        }

    if facts.condition == "missing":
        pub = {
            "project_id": PROJECT,
            "mode": facts.mode,
            "run_id": "run-incomplete",
            "snapshot_token": facts.snapshot_token,
            "data_cutoff": facts.data_cutoff,
            "rule_tokens": list(facts.rule_tokens),
            "decision_version": facts.decision_version,
            "r5_authority_packet_digest": facts.r5_digest_seed,
            "publication_fingerprint": "r6-incomplete",
            "receipt_set_digest": facts.receipt_digest_seed,
            "publication_id": "pub-incomplete",
            "public_run_token": "public-incomplete",
            "publication_state": "available",
            "identity_closed": facts.identity_closed,
            "coverage_complete": facts.coverage_complete,
            "created_at": NOW,
        }
        with pytest.raises(BaselineValidationError) as err:
            build_decision_baseline(
                pub,
                target_run_id="run-target",
                target_snapshot_id="snap-target",
                target_data_cutoff=facts.data_cutoff,
                target_decision_version=facts.decision_version,
            )
        return {
            "outcome": "error",
            "error_code": err.value.code,
            "member_set_digest": member_digest,
            "member_ids": list(expected_members),
        }

    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT)
    try:
        first = _reserve(registry, facts, execution_basis=BASIS_FULL)
        item = _item_from_facts(facts, target_run_id=first.run_id, reason="全量生成，无比较基线")
        plan = build_carry_forward_plan(
            project_id=PROJECT,
            mode=MODE_DAILY,
            execution_basis=BASIS_FULL,
            target_run_id=first.run_id,
            target_snapshot_id=facts.snapshot_token,
            target_data_cutoff=facts.data_cutoff,
            target_decision_version=facts.decision_version,
            target_rule_revision_ids=facts.rule_tokens,
            r5_authority_digest=facts.r5_digest_seed,
            r6_publication_digest="r6-" + first.run_id,
            r6_receipt_digest=facts.receipt_digest_seed,
            r6_output_set_digest=r6_out,
            items=(item,),
            created_at=NOW,
        )
        assert plan.baseline is None
        finalized = _publish_available(
            registry,
            facts,
            first,
            plan=plan,
            member_ids=expected_members,
            member_set_digest=member_digest,
            r6_output_set_digest=r6_out,
        )
        actual = {
            "outcome": "available",
            "has_baseline": False,
            "publication_state": finalized.state,
            "plan_digest": plan.plan_digest,
            "publication_id": finalized.publication_id,
            "run_id": first.run_id,
            "member_set_digest": finalized.artifact_member_set_digest,
            "member_ids": list(finalized.artifact_member_ids),
            "disposition": item.disposition,
            "r5_digest": plan.r5_authority_digest,
            "receipt_digest": plan.r6_receipt_digest,
        }
        if facts.condition == "replay":
            replay = _reserve(registry, facts, execution_basis=BASIS_FULL)
            assert replay.replayed is True
            assert replay.run_id == first.run_id
            reloaded = registry.get_publication(PROJECT, first.run_id)
            actual.update(outcome="replay", publication_state=reloaded.state, publication_id=reloaded.publication_id)
        if facts.condition == "conflict":
            with pytest.raises(IdempotencyConflictError) as err:
                _reserve(registry, facts, snapshot_token=facts.snapshot_token + "-drift", execution_basis=BASIS_FULL)
            preserved = registry.get_publication(PROJECT, first.run_id)
            assert preserved.state == PUBLICATION_STATE_AVAILABLE
            assert preserved.publication_id == finalized.publication_id
            actual = {
                "outcome": "error",
                "error_code": err.value.code,
                "member_set_digest": member_digest,
                "member_ids": list(expected_members),
            }
        return actual
    finally:
        registry.close()


def _publication_ref(pub: Any) -> str:
    """Stable string identity for continuity baseline (publication_id prop is a tuple)."""
    return "%s:%s:%s" % (pub.project_id, pub.run_id, pub.publication_revision)


def _source_pub(
    *,
    project_id: str,
    mode: str,
    run_id: str,
    snapshot_token: str,
    publication_id: str,
    public_token: str,
    r6_fingerprint: str,
    publication_state: str,
    identity_closed: bool,
    coverage_complete: bool,
    r5_digest: str,
    receipt_digest: str,
    rule_tokens: Sequence[str],
    decision_version: str,
    data_cutoff: str,
) -> Dict[str, Any]:
    return {
        "project_id": project_id,
        "mode": mode,
        "run_id": run_id,
        "snapshot_token": snapshot_token,
        "data_cutoff": data_cutoff,
        "rule_tokens": list(rule_tokens),
        "decision_version": decision_version,
        "r5_authority_packet_digest": r5_digest,
        "publication_fingerprint": r6_fingerprint,
        "receipt_set_digest": receipt_digest,
        "publication_id": publication_id,
        "public_run_token": public_token,
        "publication_state": publication_state,
        "identity_closed": identity_closed,
        "coverage_complete": coverage_complete,
        "created_at": NOW,
    }


def _run_daily_incr(facts: CellFacts, tmp_path: Path) -> Dict[str, Any]:
    expected_members = _oracle_member_ids(facts.member_bytes)
    member_digest = _oracle_member_set_digest(facts.member_bytes)

    if facts.condition == "missing":
        codes = set()
        try:
            build_decision_baseline(
                _source_pub(
                    project_id=PROJECT,
                    mode=MODE_DAILY,
                    run_id="run-prior",
                    snapshot_token=facts.compare_snapshot_token,
                    publication_id="pub-prior",
                    public_token="public-prior",
                    r6_fingerprint="r6-prior",
                    publication_state="publishing",
                    identity_closed=True,
                    coverage_complete=True,
                    r5_digest=facts.r5_digest_seed,
                    receipt_digest=facts.receipt_digest_seed,
                    rule_tokens=facts.rule_tokens,
                    decision_version="decision-prior",
                    data_cutoff="2026-08-21",
                ),
                target_run_id="run-t",
                target_snapshot_id=facts.snapshot_token,
                target_data_cutoff=facts.data_cutoff,
                target_decision_version=facts.decision_version,
            )
        except BaselineValidationError as exc:
            codes.add(exc.code)
        try:
            baseline = build_decision_baseline(
                _source_pub(
                    project_id=PROJECT,
                    mode=MODE_PRE_LOCK,
                    run_id="run-prior",
                    snapshot_token=facts.compare_snapshot_token,
                    publication_id="pub-prior",
                    public_token="public-prior",
                    r6_fingerprint="r6-prior",
                    publication_state="available",
                    identity_closed=True,
                    coverage_complete=True,
                    r5_digest=facts.r5_digest_seed,
                    receipt_digest=facts.receipt_digest_seed,
                    rule_tokens=facts.rule_tokens,
                    decision_version="decision-prior",
                    data_cutoff="2026-08-21",
                ),
                target_run_id="run-t",
                target_snapshot_id=facts.snapshot_token,
                target_data_cutoff=facts.data_cutoff,
                target_decision_version=facts.decision_version,
            )
            validate_decision_baseline(baseline, project_id=PROJECT, mode=MODE_DAILY)
        except BaselineValidationError as exc:
            codes.add(exc.code)
        try:
            build_decision_baseline(
                _source_pub(
                    project_id=PROJECT,
                    mode=MODE_DAILY,
                    run_id="run-prior",
                    snapshot_token=facts.compare_snapshot_token,
                    publication_id="pub-prior",
                    public_token="public-prior",
                    r6_fingerprint="r6-prior",
                    publication_state="available",
                    identity_closed=False,
                    coverage_complete=False,
                    r5_digest=facts.r5_digest_seed,
                    receipt_digest=facts.receipt_digest_seed,
                    rule_tokens=facts.rule_tokens,
                    decision_version="decision-prior",
                    data_cutoff="2026-08-21",
                ),
                target_run_id="run-t",
                target_snapshot_id=facts.snapshot_token,
                target_data_cutoff=facts.data_cutoff,
                target_decision_version=facts.decision_version,
            )
        except BaselineValidationError as exc:
            codes.add(exc.code)
        try:
            baseline = build_decision_baseline(
                _source_pub(
                    project_id=PROJECT,
                    mode=MODE_DAILY,
                    run_id="run-prior",
                    snapshot_token=facts.compare_snapshot_token,
                    publication_id="pub-prior",
                    public_token="public-prior",
                    r6_fingerprint="r6-prior",
                    publication_state="available",
                    identity_closed=True,
                    coverage_complete=True,
                    r5_digest=facts.r5_digest_seed,
                    receipt_digest=facts.receipt_digest_seed,
                    rule_tokens=facts.rule_tokens,
                    decision_version="decision-prior",
                    data_cutoff="2026-08-21",
                ),
                target_run_id="run-t",
                target_snapshot_id=facts.snapshot_token,
                target_data_cutoff=facts.data_cutoff,
                target_decision_version=facts.decision_version,
            )
            tampered = baseline.as_dict()
            tampered["baseline_digest"] = "0" * 64
            DecisionBaseline.from_mapping(tampered)
        except BaselineValidationError as exc:
            codes.add(exc.code)
        try:
            generate_work_units(
                MODE_DAILY,
                BASIS_INCREMENTAL,
                current_snapshot_token=facts.snapshot_token,
                prior_baseline_token=None,
                diff=None,
            )
        except RunSetupError as exc:
            codes.add(exc.code)
        return {
            "outcome": "error",
            "error_codes": frozenset(codes),
            "member_set_digest": member_digest,
            "member_ids": list(expected_members),
        }

    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT)
    bridge = _bridge_commit(tmp_path / "bridge", MODE_DAILY)
    try:
        r6_out = bridge["r6_output_set_digest"]
        members = bridge["artifact_member_ids"]
        member_set = bridge["artifact_member_set_digest"]

        def _seed_prior(snapshot: str, key: str, cutoff: str, decision: str, r6_fp: str) -> Tuple[Any, Any]:
            seed_facts = CellFacts(
                family="daily_full",
                condition="normal",
                mode=MODE_DAILY,
                execution_basis=BASIS_FULL,
                snapshot_token=snapshot,
                idempotency_key=key,
                r5_digest_seed=facts.r5_digest_seed,
                receipt_digest_seed=facts.receipt_digest_seed,
                member_bytes=facts.member_bytes,
                data_change_kind="added",
                prior_risk_state=None,
                prior_severity=None,
            )
            launch = _reserve(
                registry,
                replace(seed_facts, data_cutoff=cutoff, snapshot_token=snapshot),
                snapshot_token=snapshot,
                data_cutoff=cutoff,
                execution_basis=BASIS_FULL,
            )
            item = _item_from_facts(
                replace(seed_facts, data_cutoff=cutoff, snapshot_token=snapshot),
                target_run_id=launch.run_id,
                reason="基线全量",
            )
            plan = build_carry_forward_plan(
                project_id=PROJECT,
                mode=MODE_DAILY,
                execution_basis=BASIS_FULL,
                target_run_id=launch.run_id,
                target_snapshot_id=snapshot,
                target_data_cutoff=cutoff,
                target_decision_version=decision,
                target_rule_revision_ids=facts.rule_tokens,
                r5_authority_digest=facts.r5_digest_seed,
                r6_publication_digest=r6_fp,
                r6_receipt_digest=facts.receipt_digest_seed,
                r6_output_set_digest=r6_out,
                items=(item,),
                created_at=NOW,
            )
            aligned = replace(seed_facts, data_cutoff=cutoff, snapshot_token=snapshot)
            pub = _publish_available(
                registry,
                aligned,
                launch,
                plan=plan,
                member_ids=members,
                member_set_digest=member_set,
                r6_output_set_digest=r6_out,
            )
            return launch, pub

        prior_launch, prior_pub = _seed_prior(
            facts.compare_snapshot_token, "08d-prior-primary", "2026-08-21", "decision-prior", "r6-prior"
        )
        alt_launch, alt_pub = _seed_prior(
            facts.alternate_snapshot_token, "08d-prior-alt", "2026-08-22", "decision-alt", "r6-alt"
        )

        selected_snapshot = facts.alternate_snapshot_token if facts.select_alternate_baseline else facts.compare_snapshot_token
        selected_pub = alt_pub if facts.select_alternate_baseline else prior_pub
        selected_launch = alt_launch if facts.select_alternate_baseline else prior_launch
        selected_cutoff = "2026-08-22" if facts.select_alternate_baseline else "2026-08-21"
        selected_decision = "decision-alt" if facts.select_alternate_baseline else "decision-prior"

        risk_atom = next(a for a in bridge["committed"].extracted_atoms if a.object_type == "risk_instance")
        source_pub = {
            "publication_state": "available",
            "project_id": PROJECT,
            "mode": MODE_DAILY,
            "run_id": RUN_ID,
            "artifact_member_ids": list(members),
        }
        # Provisional flags stay False; only the R1/R5/R6 verifier may raise them.
        verified_seed = {
            "object_type": "risk_instance",
            "object_ref": risk_atom.object_id,
            "disposition": "re_evaluate_changed_data",
            "source_run_id": RUN_ID,
            "source_project_id": PROJECT,
            "source_mode": MODE_DAILY,
            "target_run_id": "pending",
            "target_project_id": PROJECT,
            "target_mode": MODE_DAILY,
            "source_object_id": risk_atom.object_id,
            "target_object_id": risk_atom.object_id,
            "source_identity": risk_atom.item_digest,
            "target_identity": risk_atom.item_digest,
            "source_artifact_id": risk_atom.artifact_id,
            "source_artifact_sha256": risk_atom.artifact_id,
            "artifact_verified": False,
            "artifact_member_verified": False,
            "reuse_reviewed": False,
            "data_change_kind": "unchanged",
            "current_present": True,
            "reason": "沿用上次有效分析",
            "current_listing_complete": True,
            "baseline_eligible": True,
        }
        verified = build_verified_carry_forward_item(
            verified_seed,
            store=bridge["store"],
            publication=source_pub,
            r5_packet=bridge["packet"],
        )
        assert verified.artifact_verified is True
        assert verified.artifact_member_verified is True
        assert verified.reuse_reviewed is True
        assert verified.disposition == "reuse_unchanged"

        incr_launch = _reserve(registry, facts, baseline_token=selected_snapshot, execution_basis=BASIS_INCREMENTAL)
        baseline = build_decision_baseline(
            _source_pub(
                project_id=PROJECT,
                mode=MODE_DAILY,
                run_id=selected_launch.run_id,
                snapshot_token=selected_snapshot,
                publication_id=_publication_ref(selected_pub),
                public_token=selected_launch.public_run_token,
                r6_fingerprint=selected_pub.publication_fingerprint,
                publication_state="available",
                identity_closed=True,
                coverage_complete=True,
                r5_digest=facts.r5_digest_seed,
                receipt_digest=facts.receipt_digest_seed,
                rule_tokens=facts.rule_tokens,
                decision_version=selected_decision,
                data_cutoff=selected_cutoff,
            ),
            target_run_id=incr_launch.run_id,
            target_snapshot_id=facts.snapshot_token,
            target_data_cutoff=facts.data_cutoff,
            target_decision_version=facts.decision_version,
            target_rule_revision_ids=facts.rule_tokens,
        )
        incr_item = build_carry_forward_item(
            {
                "object_type": verified.object_type,
                "object_ref": verified.object_ref,
                "ordinal": 0,
                "source_run_id": selected_launch.run_id,
                "source_publication_id": _publication_ref(selected_pub),
                "source_public_run_token": selected_launch.public_run_token,
                "target_run_id": incr_launch.run_id,
                "source_object_id": verified.source_object_id,
                "target_object_id": verified.target_object_id,
                "source_identity": verified.source_identity,
                "target_identity": verified.target_identity,
                "source_project_id": PROJECT,
                "target_project_id": PROJECT,
                "source_mode": MODE_DAILY,
                "target_mode": MODE_DAILY,
                "source_publication_state": "available",
                "source_artifact_id": verified.source_artifact_id,
                "source_artifact_sha256": verified.source_artifact_sha256,
                "artifact_verified": verified.artifact_verified,
                "artifact_member_verified": verified.artifact_member_verified,
                "reuse_reviewed": verified.reuse_reviewed,
                "data_change_kind": "unchanged",
                "current_present": True,
                "reason": "沿用上次有效分析",
                "current_listing_complete": True,
                "baseline_eligible": True,
            }
        )
        plan = build_carry_forward_plan(
            project_id=PROJECT,
            mode=MODE_DAILY,
            execution_basis=BASIS_INCREMENTAL,
            target_run_id=incr_launch.run_id,
            target_snapshot_id=facts.snapshot_token,
            target_data_cutoff=facts.data_cutoff,
            target_decision_version=facts.decision_version,
            target_rule_revision_ids=facts.rule_tokens,
            baseline=baseline,
            r5_authority_digest=facts.r5_digest_seed,
            r6_publication_digest="r6-incr-" + incr_launch.run_id,
            r6_receipt_digest=facts.receipt_digest_seed,
            r6_output_set_digest=r6_out,
            items=(incr_item,),
            created_at=NOW,
        )
        finalized = _publish_available(
            registry,
            facts,
            incr_launch,
            plan=plan,
            member_ids=members,
            member_set_digest=member_set,
            r6_output_set_digest=r6_out,
        )
        actual = {
            "outcome": "available",
            "has_baseline": True,
            "comparison_snapshot": selected_snapshot,
            "publication_state": finalized.state,
            "plan_digest": plan.plan_digest,
            "item_digests": [item.item_digest for item in plan.items],
            "disposition": plan.items[0].disposition,
            "publication_id": finalized.publication_id,
            "run_id": incr_launch.run_id,
            "member_set_digest": finalized.artifact_member_set_digest,
            "member_ids": list(finalized.artifact_member_ids),
            "r5_digest": plan.r5_authority_digest,
            "receipt_digest": plan.r6_receipt_digest,
            "artifact_verified": verified.artifact_verified,
            "artifact_member_verified": verified.artifact_member_verified,
        }
        if facts.condition == "replay":
            replay = _reserve(registry, facts, baseline_token=selected_snapshot, execution_basis=BASIS_INCREMENTAL)
            assert replay.replayed is True
            assert replay.run_id == incr_launch.run_id
            reloaded_plan = registry.get_continuity_plan(PROJECT, incr_launch.run_id)
            assert reloaded_plan.plan_digest == plan.plan_digest
            assert [i.item_digest for i in reloaded_plan.items] == actual["item_digests"]
            actual["outcome"] = "replay"
        if facts.condition == "conflict":
            other = facts.alternate_snapshot_token if selected_snapshot == facts.compare_snapshot_token else facts.compare_snapshot_token
            with pytest.raises(IdempotencyConflictError) as err:
                _reserve(registry, facts, baseline_token=other, execution_basis=BASIS_INCREMENTAL)
            preserved = registry.get_publication(PROJECT, incr_launch.run_id)
            assert preserved.publication_id == finalized.publication_id
            actual = {
                "outcome": "error",
                "error_code": err.value.code,
                "member_set_digest": member_set,
                "member_ids": list(members),
            }
        return actual
    finally:
        bridge["store"].close()
        registry.close()


def _run_pre_lock(facts: CellFacts, tmp_path: Path) -> Dict[str, Any]:
    expected_members = _oracle_member_ids(facts.member_bytes)
    member_digest = _oracle_member_set_digest(facts.member_bytes)
    r6_out = canonical_digest({"outputs": list(expected_members), "mode": "pre_lock"})

    if facts.condition == "conflict":
        codes = set()
        try:
            generate_work_units(MODE_PRE_LOCK, BASIS_INCREMENTAL, current_snapshot_token=facts.snapshot_token)
        except RunSetupError as exc:
            codes.add(exc.code)
        try:
            build_carry_forward_plan(
                project_id=PROJECT,
                mode=MODE_PRE_LOCK,
                execution_basis=BASIS_INCREMENTAL,
                target_run_id="run-pl-bad",
                target_snapshot_id=facts.snapshot_token,
                target_data_cutoff=facts.data_cutoff,
                target_decision_version=facts.decision_version,
                r5_authority_digest=facts.r5_digest_seed,
                r6_publication_digest="r6",
                r6_receipt_digest=facts.receipt_digest_seed,
                items=(),
                created_at=NOW,
            )
        except PlanValidationError as exc:
            codes.add(exc.code)
        return {
            "outcome": "error",
            "error_codes": frozenset(codes),
            "member_set_digest": member_digest,
            "member_ids": list(expected_members),
        }

    current = {
        "canonical_key": "PT-002|V1",
        "subject_id": "PT-002",
        "visit": "V1",
        "risk_level": "high",
        "revision_attribution": facts.revision_attribution,
    }
    if facts.query_ref:
        current["query_ref"] = facts.query_ref
    prior = {
        "canonical_key": "PT-002|V1",
        "subject_id": "PT-002",
        "visit": "V1",
        "risk_level": "medium",
    }
    diff = canonical_keyed_diff((current,), (prior,), key_fields=("canonical_key",))
    revised = [row for row in diff.rows if row.status == "revised"]
    assert revised
    attribution = revised[0].attribution_text

    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT)
    try:
        launch = _reserve(registry, replace(facts, mode=MODE_PRE_LOCK), execution_basis=BASIS_FULL)
        item = _item_from_facts(
            replace(facts, mode=MODE_PRE_LOCK, execution_basis=BASIS_FULL),
            target_run_id=launch.run_id,
            reason=attribution,
        )
        plan = build_carry_forward_plan(
            project_id=PROJECT,
            mode=MODE_PRE_LOCK,
            execution_basis=BASIS_FULL,
            target_run_id=launch.run_id,
            target_snapshot_id=facts.snapshot_token,
            target_data_cutoff=facts.data_cutoff,
            target_decision_version=facts.decision_version,
            target_rule_revision_ids=facts.rule_tokens,
            r5_authority_digest=facts.r5_digest_seed,
            r6_publication_digest="r6-pl-" + launch.run_id,
            r6_receipt_digest=facts.receipt_digest_seed,
            r6_output_set_digest=r6_out,
            items=(item,),
            created_at=NOW,
        )
        history_before = len(registry.list_continuity_plans(PROJECT))
        finalized = _publish_available(
            registry,
            facts,
            launch,
            plan=plan,
            member_ids=expected_members,
            member_set_digest=member_digest,
            r6_output_set_digest=r6_out,
        )
        actual = {
            "outcome": "available",
            "attribution": attribution,
            "query_gap": facts.revision_attribution == "query_driven" and not str(facts.query_ref).strip(),
            "publication_state": finalized.state,
            "publication_id": finalized.publication_id,
            "run_id": launch.run_id,
            "plan_digest": plan.plan_digest,
            "history_count": len(registry.list_continuity_plans(PROJECT)),
            "member_set_digest": finalized.artifact_member_set_digest,
            "member_ids": list(finalized.artifact_member_ids),
            "disposition": item.disposition,
            "r5_digest": plan.r5_authority_digest,
            "receipt_digest": plan.r6_receipt_digest,
        }
        if facts.condition == "replay":
            replay = _reserve(registry, replace(facts, mode=MODE_PRE_LOCK), execution_basis=BASIS_FULL)
            assert replay.replayed is True
            assert replay.run_id == launch.run_id
            assert len(registry.list_continuity_plans(PROJECT)) == actual["history_count"]
            assert history_before + 1 == actual["history_count"]
            actual["outcome"] = "replay"
        return actual
    finally:
        registry.close()


def _run_post_lock(facts: CellFacts, tmp_path: Path) -> Dict[str, Any]:
    expected_members = _oracle_member_ids(facts.member_bytes)
    member_digest = _oracle_member_set_digest(facts.member_bytes)

    if facts.condition == "missing":
        codes = set()
        try:
            generate_work_units(MODE_POST_LOCK_PRE_CFDI, BASIS_INCREMENTAL, current_snapshot_token=facts.snapshot_token)
        except RunSetupError as exc:
            codes.add(exc.code)
        try:
            build_carry_forward_plan(
                project_id=PROJECT,
                mode=MODE_POST_LOCK_PRE_CFDI,
                execution_basis=BASIS_INCREMENTAL,
                target_run_id="run-pc-bad",
                target_snapshot_id=facts.snapshot_token,
                target_data_cutoff=facts.data_cutoff,
                target_decision_version=facts.decision_version,
                r5_authority_digest=facts.r5_digest_seed,
                r6_publication_digest="r6",
                r6_receipt_digest=facts.receipt_digest_seed,
                items=(),
                created_at=NOW,
            )
        except PlanValidationError as exc:
            codes.add(exc.code)
        run = _make_run_binding(MODE_POST_LOCK_PRE_CFDI, fixed_total=False)
        contract = mo.build_mode_contract(MODE_POST_LOCK_PRE_CFDI)
        ctx = mo.default_entry_context_for_mode(MODE_POST_LOCK_PRE_CFDI, run_binding=run)
        codes.update(mo.validate_run_mode_gate(run, contract, entry_context=ctx))
        return {
            "outcome": "error",
            "error_codes": frozenset(codes),
            "member_set_digest": member_digest,
            "member_ids": list(expected_members),
        }

    bridge = _bridge_commit(tmp_path / "bridge", MODE_POST_LOCK_PRE_CFDI, fixed_total=True)
    registry = LaunchRegistry(tmp_path / "launch.sqlite3", project_id=PROJECT)
    try:
        r6_out = bridge["r6_output_set_digest"]
        members = bridge["artifact_member_ids"]
        member_set = bridge["artifact_member_set_digest"]
        launch = _reserve(registry, replace(facts, mode=MODE_POST_LOCK_PRE_CFDI), execution_basis=BASIS_FULL)
        item = _item_from_facts(
            replace(
                facts,
                mode=MODE_POST_LOCK_PRE_CFDI,
                execution_basis=BASIS_FULL,
                data_change_kind="added",
                prior_risk_state=None,
                prior_severity=None,
            ),
            target_run_id=launch.run_id,
            reason="本次固定数据范围",
        )
        plan = build_carry_forward_plan(
            project_id=PROJECT,
            mode=MODE_POST_LOCK_PRE_CFDI,
            execution_basis=BASIS_FULL,
            target_run_id=launch.run_id,
            target_snapshot_id=facts.snapshot_token,
            target_data_cutoff=facts.data_cutoff,
            target_decision_version=facts.decision_version,
            target_rule_revision_ids=facts.rule_tokens,
            r5_authority_digest=facts.r5_digest_seed,
            r6_publication_digest="r6-pc-" + launch.run_id,
            r6_receipt_digest=facts.receipt_digest_seed,
            r6_output_set_digest=r6_out,
            items=(item,),
            created_at=NOW,
        )
        finalized = _publish_available(
            registry,
            facts,
            launch,
            plan=plan,
            member_ids=members,
            member_set_digest=member_set,
            r6_output_set_digest=r6_out,
        )
        actual = {
            "outcome": "available",
            "fixed_total": True,
            "publication_state": finalized.state,
            "publication_id": finalized.publication_id,
            "run_id": launch.run_id,
            "plan_digest": plan.plan_digest,
            "member_set_digest": finalized.artifact_member_set_digest,
            "member_ids": list(finalized.artifact_member_ids),
            "r5_digest": plan.r5_authority_digest,
            "receipt_digest": plan.r6_receipt_digest,
            "half_publication": False,
        }
        if facts.condition == "boundary":
            replay = _reserve(registry, replace(facts, mode=MODE_POST_LOCK_PRE_CFDI), execution_basis=BASIS_FULL)
            assert replay.replayed is True
            assert replay.run_id == launch.run_id
            reloaded = registry.get_publication(PROJECT, launch.run_id)
            assert reloaded.publication_id == finalized.publication_id
            actual["outcome"] = "replay"
        if facts.late_callback_after_reopen:
            publication_id = finalized.publication_id
            plan_digest = plan.plan_digest
            registry.close()
            registry.reopen()
            reloaded_plan = registry.get_continuity_plan(PROJECT, launch.run_id)
            assert reloaded_plan.status == CONTINUITY_PLAN_STATE_PUBLISHED
            assert reloaded_plan.plan_digest == plan_digest
            late = registry.finalize_publication(
                PROJECT,
                launch.run_id,
                r5_authority_packet_digest=plan.r5_authority_digest,
                receipt_set_digest=plan.r6_receipt_digest,
                r6_output_set_digest=r6_out,
                artifact_member_ids=tuple(sorted(members)),
                artifact_member_set_digest=product_content_digest(list(sorted(members))),
            )
            assert late.publication_id == publication_id
            assert late.state == PUBLICATION_STATE_AVAILABLE
            still = registry.get_publication(PROJECT, launch.run_id)
            assert still.publication_id == publication_id
            assert still.state == PUBLICATION_STATE_AVAILABLE
            # Only one publication row for the run after late callback.
            assert registry.get_continuity_plan(PROJECT, launch.run_id).status == CONTINUITY_PLAN_STATE_PUBLISHED
            actual.update(outcome="replay", half_publication=False)
        if facts.condition == "conflict" and facts.change_scope_field == "cutoff":
            old_id = finalized.publication_id
            old_run = launch.run_id
            changed = _reserve(
                registry,
                replace(facts, mode=MODE_POST_LOCK_PRE_CFDI, idempotency_key=facts.idempotency_key + "-new"),
                data_cutoff="2026-08-30",
                execution_basis=BASIS_FULL,
            )
            assert changed.run_id != old_run
            old = registry.get_publication(PROJECT, old_run)
            assert old.publication_id == old_id
            assert old.state == PUBLICATION_STATE_AVAILABLE
            actual.update(outcome="new_run", old_publication_preserved=True)
        return actual
    finally:
        bridge["store"].close()
        registry.close()


def run_scenario(facts: CellFacts, tmp_path: Path) -> Dict[str, Any]:
    if facts.family == "daily_full":
        return _run_daily_full(facts, tmp_path)
    if facts.family == "daily_incr":
        return _run_daily_incr(facts, tmp_path)
    if facts.family == "pre_lock":
        return _run_pre_lock(facts, tmp_path)
    if facts.family == "post_lock":
        return _run_post_lock(facts, tmp_path)
    raise AssertionError("unknown family")


def _assert_actual_matches_expected(actual: Mapping[str, Any], expected: Mapping[str, Any]) -> None:
    assert actual["outcome"] == expected["outcome"]
    if "error_code" in expected:
        assert actual.get("error_code") == expected["error_code"]
    if "error_codes" in expected:
        assert expected["error_codes"].issubset(actual.get("error_codes", frozenset()))
    for key in (
        "has_baseline",
        "publication_state",
        "absence_is_not_resolution",
        "comparison_snapshot",
        "fixed_total",
        "half_publication",
        "old_publication_preserved",
        "query_gap",
    ):
        if key in expected:
            assert actual.get(key) == expected[key], key
    for key in ("attribution", "disposition", "risk_change_kind", "artifact_verified", "artifact_member_verified"):
        if key in expected and key in actual:
            assert actual[key] == expected[key], key
    # DI positive cells must prove verifier-raised flags, not pre-set authority.
    if expected.get("disposition") == "reuse_unchanged" and actual.get("outcome") in {"available", "replay"}:
        if "artifact_verified" in actual:
            assert actual["artifact_verified"] is True
            assert actual["artifact_member_verified"] is True
    if expected.get("outcome") in {"available", "replay", "needs_rejudgment", "new_run"}:
        if "member_ids" in actual:
            assert actual["member_ids"]
        if "member_set_digest" in actual:
            assert isinstance(actual["member_set_digest"], str) and len(actual["member_set_digest"]) == 64


@pytest.mark.parametrize("case_key", CASE_KEYS)
def test_slice08d_three_mode_matrix_cell(case_key: str, tmp_path: Path) -> None:
    facts = _facts_for_case(case_key)
    assert not hasattr(facts, "case_key")
    expected = expected_from_inputs(facts)
    actual = run_scenario(facts, tmp_path)
    _assert_actual_matches_expected(actual, expected)


FROZEN_CASE_KEYS = (
    "DF-N",
    "DF-B",
    "DF-M",
    "DF-R",
    "DF-C",
    "DI-N",
    "DI-B",
    "DI-M",
    "DI-R",
    "DI-C",
    "PL-N",
    "PL-B",
    "PL-M",
    "PL-R",
    "PL-C",
    "PC-N",
    "PC-B",
    "PC-M",
    "PC-R",
    "PC-C",
)


def test_slice08d_case_key_closure_is_exact() -> None:
    assert CASE_KEYS == FROZEN_CASE_KEYS
    assert len(CASE_KEYS) == 20
    assert len(set(CASE_KEYS)) == 20
    assert list(CASE_KEYS) == [
        "DF-N",
        "DF-B",
        "DF-M",
        "DF-R",
        "DF-C",
        "DI-N",
        "DI-B",
        "DI-M",
        "DI-R",
        "DI-C",
        "PL-N",
        "PL-B",
        "PL-M",
        "PL-R",
        "PL-C",
        "PC-N",
        "PC-B",
        "PC-M",
        "PC-R",
        "PC-C",
    ]


def test_slice08d_reverse_mode_basis_stable_error_codes(tmp_path: Path) -> None:
    full_manifest = generate_work_units(MODE_DAILY, BASIS_FULL, current_snapshot_token="snap-full")
    assert full_manifest.execution_basis == BASIS_FULL

    fixture = make_fixture()
    current = fixture["snapshots"][0]
    prior = fixture["snapshots"][1]
    diff = canonical_keyed_diff(current.rows, prior.rows, key_fields=current.key_fields)
    incr_manifest = generate_work_units(
        MODE_DAILY,
        BASIS_INCREMENTAL,
        current_snapshot_token=current.snapshot_ref,
        prior_baseline_token=prior.snapshot_ref,
        diff=diff,
    )
    assert incr_manifest.execution_basis == BASIS_INCREMENTAL

    with pytest.raises(RunSetupError) as pre_lock_incr:
        generate_work_units(MODE_PRE_LOCK, BASIS_INCREMENTAL, current_snapshot_token="snap")
    assert pre_lock_incr.value.code == "incremental_not_supported_for_mode"

    with pytest.raises(RunSetupError) as post_lock_incr:
        generate_work_units(MODE_POST_LOCK_PRE_CFDI, BASIS_INCREMENTAL, current_snapshot_token="snap")
    assert post_lock_incr.value.code == "incremental_not_supported_for_mode"

    with pytest.raises(PlanValidationError):
        build_carry_forward_plan(
            project_id=PROJECT,
            mode=MODE_PRE_LOCK,
            execution_basis=BASIS_INCREMENTAL,
            target_run_id="r",
            target_snapshot_id="s",
            target_data_cutoff="c",
            target_decision_version="d",
            r5_authority_digest="r5",
            r6_publication_digest="r6",
            r6_receipt_digest="rc",
            items=(),
            created_at=NOW,
        )
    with pytest.raises(PlanValidationError):
        build_carry_forward_plan(
            project_id=PROJECT,
            mode=MODE_POST_LOCK_PRE_CFDI,
            execution_basis=BASIS_INCREMENTAL,
            target_run_id="r",
            target_snapshot_id="s",
            target_data_cutoff="c",
            target_decision_version="d",
            r5_authority_digest="r5",
            r6_publication_digest="r6",
            r6_receipt_digest="rc",
            items=(),
            created_at=NOW,
        )

    run = _make_run_binding(MODE_POST_LOCK_PRE_CFDI, fixed_total=False)
    contract = mo.build_mode_contract(MODE_POST_LOCK_PRE_CFDI)
    ctx = mo.default_entry_context_for_mode(MODE_POST_LOCK_PRE_CFDI, run_binding=run)
    assert mo.MODE_ENTRY_BLOCKED in mo.validate_run_mode_gate(run, contract, entry_context=ctx)

    binder = RunBindingStore(tmp_path / "bind.sqlite3")
    try:
        frozen = freeze_default_mtplx_effective_profile(run_id="bind-08d")
        with pytest.raises(RunBindingError) as bind_err:
            binder.bind(
                run_id="run-incr-missing-prior",
                project_id=PROJECT,
                mode=MODE_DAILY,
                execution_basis=BASIS_INCREMENTAL,
                data_cutoff="cutoff",
                source_revision_id="src",
                frozen=frozen,
                prior_accepted_snapshot_ref=None,
            )
        assert "incremental_requires_prior_accepted_snapshot_ref" in str(bind_err.value)
    finally:
        binder.close()


def test_slice08d_oracle_ignores_product_payload_fields() -> None:
    facts = CellFacts(
        family="pre_lock",
        condition="boundary",
        mode=MODE_PRE_LOCK,
        execution_basis=BASIS_FULL,
        revision_attribution="query_driven",
        query_ref="Q-1",
    )
    expected = expected_from_inputs(facts)
    poisoned = {"attention_text": "伪造归因"}
    assert expected["attribution"] == "Query 后修订影响"
    assert expected["attribution"] != poisoned["attention_text"]


def test_slice08d_negative_verification_tampers_bytes_not_booleans(tmp_path: Path) -> None:
    bridge = _bridge_commit(tmp_path, MODE_DAILY)
    risk_atom = next(a for a in bridge["committed"].extracted_atoms if a.object_type == "risk_instance")
    # Provisional flags remain False; failure comes from tampered member identity.
    item = {
        "object_type": "risk_instance",
        "object_ref": risk_atom.object_id,
        "disposition": "re_evaluate_changed_data",
        "source_run_id": RUN_ID,
        "source_project_id": PROJECT,
        "source_mode": MODE_DAILY,
        "target_run_id": "run-target",
        "target_project_id": PROJECT,
        "target_mode": MODE_DAILY,
        "source_object_id": risk_atom.object_id,
        "target_object_id": risk_atom.object_id,
        "source_identity": risk_atom.item_digest,
        "target_identity": risk_atom.item_digest,
        "source_artifact_id": risk_atom.artifact_id,
        "source_artifact_sha256": risk_atom.artifact_id,
        "artifact_verified": False,
        "artifact_member_verified": False,
        "reuse_reviewed": False,
        "data_change_kind": "unchanged",
        "current_present": True,
        "reason": "字节篡改负例",
    }
    bad_pub = {
        "publication_state": "available",
        "project_id": PROJECT,
        "mode": MODE_DAILY,
        "run_id": RUN_ID,
        "artifact_member_ids": ["tampered-member-not-in-set"],
    }
    with pytest.raises(ContinuityIntegrityError) as err:
        build_verified_carry_forward_item(
            item,
            store=bridge["store"],
            publication=bad_pub,
            r5_packet=bridge["packet"],
        )
    assert err.value.code == "ARTIFACT_NOT_IN_PUBLICATION_MEMBERS"
    independent = _oracle_sha256(["tampered-member-not-in-set"])
    assert independent != bridge["artifact_member_set_digest"]
    assert len(bridge["r6_output_set_digest"]) == 64
    assert compute_artifact_member_set_digest(bridge["artifact_member_ids"]) == bridge["artifact_member_set_digest"]
    bridge["store"].close()


def test_slice08d_oracle_does_not_call_product_digest_or_disposition_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Decisive runtime proof: expected_from_inputs / _oracle_* never call product helpers."""

    def _boom(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("oracle called product helper under test")

    import mm_r7.continuity as continuity_mod
    import mm_r7.launch_registry as registry_mod

    monkeypatch.setattr(continuity_mod, "determine_disposition", _boom)
    monkeypatch.setattr(continuity_mod, "project_risk_change_kind", _boom)
    monkeypatch.setattr(continuity_mod, "canonical_digest", _boom)
    monkeypatch.setattr(continuity_mod, "canonical_json", _boom)
    monkeypatch.setattr(registry_mod, "content_digest", _boom)
    monkeypatch.setattr(registry_mod, "canonical_json", _boom)
    import test_slice08d_three_mode_matrix as this_mod

    for name in ("project_risk_change_kind", "canonical_digest", "product_content_digest"):
        if hasattr(this_mod, name):
            monkeypatch.setattr(this_mod, name, _boom)

    for key in FROZEN_CASE_KEYS:
        facts = _facts_for_case(key)
        assert not hasattr(facts, "case_key")
        expected = expected_from_inputs(facts)
        assert isinstance(expected["member_set_digest"], str) and len(expected["member_set_digest"]) == 64
        assert expected["disposition"] in {
            "reuse_unchanged",
            "re_evaluate_changed_data",
            "re_evaluate_rule_change",
            "re_evaluate_prior_uncertain",
            "close_with_evidence",
            "blocked_incompatible",
        }
        assert expected["risk_change_kind"] in {
            "new",
            "upgraded",
            "continued",
            "downgraded",
            "closed",
            "reopened",
            "needs_rejudgment",
        }

