"""Focused tests for R6 slice-04/05/06 ModeContract / ModeOutput runtime.

Slice-04: immutable three-mode ModeContract, Run gate, daily four outputs,
structured affected Query draft boundaries.

Slice-05: pre_lock four default outputs (authority/cutoff/revision/numeric).

Slice-06: post_lock_pre_cfdi fixed-total outputs — locked identity, population
totals, nested IDs, cross-output reconciliation, no overwrite, tamper, and
mode isolation (positive + fail-closed).
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from mm_r6 import contracts
from mm_r6 import mode_output as mo
from mm_r6.report_review import canonical_bytes

POC_ROOT = Path(__file__).resolve().parents[1]
MODES = ("daily", "pre_lock", "post_lock_pre_cfdi")


def _binding(mode: str = "daily", **overrides):
    base = {
        "project_id": "project-r6-synthetic",
        "run_id": "run-r6-mode-001",
        "mode": mode,
        "execution_basis": "full",
        "data_cutoff": "cutoff-2026-08-01",
        "source_revision_id": "run-source-revision-001",
        "knowledge_pack_version": "kp-1",
        "rule_activation_version": "rav-1",
        "mapping_version": "map-1",
        "identity_algorithm_version": "ia-r6-slice04-001",
        "identity_algorithm_digest": "ia-digest-r6-slice04-001",
        "schema_version": "r6-0.1",
        "carry_forward_run_ids": [],
        "mode_transition": "explicit_new_run",
        "actor": "synthetic-actor",
        "created_at": "2026-08-28T00:00:00Z",
    }
    if mode == "post_lock_pre_cfdi":
        base.update(
            {
                "data_cutoff": "cutoff-fixed-001",
                "source_revision_id": "revision-fixed-001",
                "fixed_total": True,
                "locked_snapshot_hash": "snap-hash-fixed-001",
                "output_cutoff_ref": "cutoff-fixed-001",
                "output_revision_ref": "revision-fixed-001",
                "local_os_user": "local-user-synthetic",
                "acceptance_evidence_hash": "accept-hash-fixed-001",
            }
        )
    base.update(overrides)
    return base


def _positive_gate(mode: str, **run_overrides):
    run = _binding(mode, **run_overrides)
    contract = mo.build_mode_contract(mode)
    ctx = mo.default_entry_context_for_mode(mode, run_binding=run)
    return run, contract, ctx


def _spec(output_kind: str, **overrides):
    return {
        "output_kind": output_kind,
        "eligibility": mo.default_output_eligibility(),
        **overrides,
    }


def _restamp_output_id(output):
    stamped = copy.deepcopy(output)
    stamped.pop("output_id", None)
    stamped["output_id"] = "out-" + mo.sha256_hex(canonical_bytes(stamped))
    return stamped


# ---------------------------------------------------------------------------
# ModeContract builders
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", MODES)
def test_build_mode_contract_positive(mode):
    contract = mo.build_mode_contract(mode)
    assert contract["mode"] == mode
    assert contract["immutable"] is True
    assert contract["contract_version"] == "0.1"
    assert mo.validate_mode_contract(contract) == ()


def test_build_all_mode_contracts_order_and_count(contract):
    built = mo.build_all_mode_contracts()
    assert len(built) == 3
    assert [c["mode"] for c in built] == [row["mode"] for row in contract["mode_contracts"]]
    for item in built:
        assert mo.validate_mode_contract(item) == ()


@pytest.mark.parametrize("mode", MODES)
def test_mode_contract_matches_frozen_contract_json(mode, contract):
    built = mo.build_mode_contract(mode)
    row = next(r for r in contract["mode_contracts"] if r["mode"] == mode)
    assert built["contract_id"] == row["contract_id"]
    assert built["allowed_execution_basis"] == row["allowed_execution_basis"]
    assert built["entry_conditions"] == row["entry_conditions"]
    assert built["cutoff_policy"] == row["cutoff_policy"]
    assert built["revision_policy"] == row["revision_policy"]
    assert built["carry_forward_policy"] == row["carry_forward_policy"]
    assert built["output_eligibility"]["default_outputs"] == row["default_outputs"]
    assert built["output_eligibility"]["conditional_outputs"] == row["conditional_outputs"]
    assert (
        built["output_eligibility"]["external_report_review_default"]
        == row["external_report_review_default"]
    )
    assert built["output_eligibility"]["output_requirements"] == row["output_requirements"]


@pytest.mark.parametrize("mode", MODES)
def test_mode_contract_byte_stable_across_builds(mode):
    a = mo.build_mode_contract(mode)
    b = mo.build_mode_contract(mode)
    assert canonical_bytes(a) == canonical_bytes(b)
    assert mo.mode_contract_digest(a) == mo.mode_contract_digest(b)


def test_build_mode_contract_does_not_mutate_frozen_source():
    first = mo.build_mode_contract("daily")
    first["immutable"] = False
    first["allowed_execution_basis"].append("incremental")
    second = mo.build_mode_contract("daily")
    assert second["immutable"] is True
    assert second["allowed_execution_basis"] == ["full", "incremental"]


def test_validate_mode_contract_rejects_tamper():
    contract = mo.build_mode_contract("daily")
    tampered = copy.deepcopy(contract)
    tampered["cutoff_policy"] = "mutated-policy"
    codes = mo.validate_mode_contract(tampered)
    assert mo.SILENT_MODE_CONVERSION in codes


def test_validate_mode_contract_rejects_immutable_false():
    contract = mo.build_mode_contract("pre_lock")
    tampered = copy.deepcopy(contract)
    tampered["immutable"] = False
    codes = mo.validate_mode_contract(tampered)
    assert mo.SILENT_MODE_CONVERSION in codes


def test_build_mode_contract_unknown_mode():
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_contract("lock_complete")
    assert exc.value.failure_code == mo.IDENTITY_MISMATCH


# ---------------------------------------------------------------------------
# Run gate — positive
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", MODES)
def test_run_mode_gate_positive(mode):
    run, contract, ctx = _positive_gate(mode)
    assert mo.validate_run_mode_gate(run, contract, entry_context=ctx) == ()


def test_daily_incremental_with_compatible_baseline():
    run, contract, ctx = _positive_gate(
        "daily",
        execution_basis="incremental",
        prior_baseline_ref="run-daily-prior-001",
    )
    assert mo.validate_run_mode_gate(run, contract, entry_context=ctx) == ()


# ---------------------------------------------------------------------------
# Run gate — silent conversion
# ---------------------------------------------------------------------------


def test_silent_mode_transition_fail_closed():
    run, contract, ctx = _positive_gate("daily", mode_transition="silent_in_place")
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert codes == (mo.SILENT_MODE_CONVERSION,)


def test_same_run_id_mode_change_is_silent_conversion():
    prior = _binding("daily", run_id="run-shared-001")
    run, contract, ctx = _positive_gate(
        "pre_lock",
        run_id="run-shared-001",
        mode_transition="explicit_new_run",
    )
    codes = mo.validate_run_mode_gate(
        run, contract, entry_context=ctx, prior_run=prior
    )
    assert mo.SILENT_MODE_CONVERSION in codes


def test_post_lock_cannot_silently_return_to_daily():
    prior = _binding("post_lock_pre_cfdi", run_id="run-locked-001")
    run, contract, ctx = _positive_gate("daily", run_id="run-locked-001")
    codes = mo.validate_run_mode_gate(
        run, contract, entry_context=ctx, prior_run=prior
    )
    assert mo.SILENT_MODE_CONVERSION in codes


# ---------------------------------------------------------------------------
# Run gate — execution basis / entry / cutoff / revision / carry-forward
# ---------------------------------------------------------------------------


def test_pre_lock_rejects_incremental_basis():
    run, contract, ctx = _positive_gate("pre_lock", execution_basis="incremental")
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert mo.MODE_ENTRY_BLOCKED in codes


def test_post_lock_rejects_incremental_basis():
    run, contract, ctx = _positive_gate(
        "post_lock_pre_cfdi", execution_basis="incremental"
    )
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert mo.MODE_ENTRY_BLOCKED in codes


def test_daily_incremental_without_baseline_blocked():
    run, contract, ctx = _positive_gate(
        "daily",
        execution_basis="incremental",
        prior_baseline_ref=None,
    )
    # Force missing prior baseline in entry context.
    ctx.pop("prior_baseline", None)
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert mo.MODE_ENTRY_BLOCKED in codes


def test_daily_incremental_incompatible_baseline_blocked():
    run, contract, ctx = _positive_gate(
        "daily",
        execution_basis="incremental",
        prior_baseline_ref="run-daily-prior-001",
    )
    ctx["prior_baseline"]["compatible"] = False
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert mo.MODE_ENTRY_BLOCKED in codes


def test_missing_entry_condition_blocked():
    run, contract, ctx = _positive_gate("pre_lock")
    ctx["lock_preparation_window_declared"] = False
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert mo.MODE_ENTRY_BLOCKED in codes


def test_post_lock_missing_locked_selection_blocked():
    run, contract, ctx = _positive_gate("post_lock_pre_cfdi")
    ctx.pop("locked_version_selection")
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert mo.MODE_ENTRY_BLOCKED in codes


def test_post_lock_cutoff_ref_mismatch():
    run, contract, ctx = _positive_gate(
        "post_lock_pre_cfdi",
        output_cutoff_ref="cutoff-pre-lock-001",
    )
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert mo.CUTOFF_MISMATCH in codes


def test_post_lock_revision_ref_mismatch():
    run, contract, ctx = _positive_gate(
        "post_lock_pre_cfdi",
        output_revision_ref="revision-new-002",
    )
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert mo.REVISION_MISMATCH in codes


def test_post_lock_fixed_total_false_blocked():
    run, contract, ctx = _positive_gate("post_lock_pre_cfdi", fixed_total=False)
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert mo.MODE_ENTRY_BLOCKED in codes


def test_post_lock_snapshot_hash_drift_blocked():
    run, contract, ctx = _positive_gate("post_lock_pre_cfdi")
    # Keep accepted selection hash; drift only the run binding.
    run["locked_snapshot_hash"] = "snap-hash-drifted"
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert mo.REVISION_MISMATCH in codes


def test_carry_forward_undeclared_null_source_blocked():
    run, contract, ctx = _positive_gate(
        "daily",
        carry_forward_run_ids=["run-daily-001"],
        carry_forward_source_run=None,
        carry_forward_compatibility="compatible",
    )
    ctx["cross_mode_carry_forward"] = True
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert mo.MODE_ENTRY_BLOCKED in codes


def test_carry_forward_incompatible_blocked():
    prior = _binding("daily", run_id="run-daily-001")
    run, contract, ctx = _positive_gate(
        "pre_lock",
        run_id="run-pre-lock-002",
        carry_forward_run_ids=["run-daily-001"],
        carry_forward_source_run="run-daily-001",
        carry_forward_compatibility="incompatible",
    )
    ctx["cross_mode_carry_forward"] = True
    codes = mo.validate_run_mode_gate(
        run, contract, entry_context=ctx, prior_run=prior
    )
    assert mo.MODE_ENTRY_BLOCKED in codes


def test_carry_forward_compatible_accepted():
    prior = _binding("daily", run_id="run-daily-001")
    run, contract, ctx = _positive_gate(
        "pre_lock",
        run_id="run-pre-lock-002",
        carry_forward_run_ids=["run-daily-001"],
        carry_forward_source_run="run-daily-001",
        carry_forward_target_run="run-pre-lock-002",
        carry_forward_reason="进入锁库前全量复核，复用已核验来源证据",
        reusable_artifact_hash="artifact-hash-001",
        carry_forward_compatibility="compatible",
    )
    ctx["cross_mode_carry_forward"] = True
    assert (
        mo.validate_run_mode_gate(run, contract, entry_context=ctx, prior_run=prior)
        == ()
    )


def test_mode_mismatch_between_run_and_contract_blocked():
    run, _, ctx = _positive_gate("daily")
    contract = mo.build_mode_contract("pre_lock")
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert mo.MODE_ENTRY_BLOCKED in codes


def test_missing_run_identity_fields_blocked():
    run, contract, ctx = _positive_gate("daily")
    del run["source_revision_id"]
    codes = mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert mo.IDENTITY_MISMATCH in codes


def test_validate_run_mode_gate_does_not_mutate_inputs():
    run, contract, ctx = _positive_gate("daily")
    run_bytes = canonical_bytes(run)
    contract_bytes = canonical_bytes(contract)
    ctx_bytes = canonical_bytes(ctx)
    mo.validate_run_mode_gate(run, contract, entry_context=ctx)
    assert canonical_bytes(run) == run_bytes
    assert canonical_bytes(contract) == contract_bytes
    assert canonical_bytes(ctx) == ctx_bytes


def test_allowed_execution_basis_frozen_per_mode():
    daily = mo.build_mode_contract("daily")
    pre = mo.build_mode_contract("pre_lock")
    post = mo.build_mode_contract("post_lock_pre_cfdi")
    assert daily["allowed_execution_basis"] == ["full", "incremental"]
    assert pre["allowed_execution_basis"] == ["full"]
    assert post["allowed_execution_basis"] == ["full"]


def test_contract_sha_still_accepted():
    raw = contracts.contract_raw()
    assert contracts.sha256_hex(raw) == contracts.ACCEPTED_CONTRACT_SHA256


# ---------------------------------------------------------------------------
# ModeOutput / daily four / Query draft (worker_02)
# ---------------------------------------------------------------------------


def _refs(run):
    digest = "auth-digest-r6-slice04-001"
    base = {
        "project_id": run["project_id"],
        "run_id": run["run_id"],
        "data_cutoff": run["data_cutoff"],
        "source_revision_id": run["source_revision_id"],
    }
    return (
        {**base, "authority_digest": digest, "digest": digest},
        {**base, "coverage_digest": digest, "digest": digest},
        {**base, "qc_digest": digest, "digest": digest},
    )


def _finding(**overrides):
    base = {
        "finding_id": "finding-001",
        "risk_id": "risk-ae-omission-001",
        "issue_id": "issue-001",
        "subject_id": "SUBJ-001",
        "site_id": "SITE-01",
        "scope_kind": "subject",
        "basis": "方案要求报告治疗期不良事件",
        "finding": "受试者记录出现未对应 AE 的症状描述",
        "action": "请核实是否需补充 AE 记录并说明判定理由",
        "evidence_refs": ["ev-listing-row-001"],
        "locator": {"path": "AE.SYMPTOM", "record_id": "rec-001", "field": "AETERM"},
    }
    base.update(overrides)
    return base


def test_build_daily_four_outputs_share_authority():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    outputs = mo.build_daily_mode_outputs(
        run,
        contract,
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        findings=[_finding()],
        entry_context=ctx,
    )
    assert len(outputs) == 4
    kinds = [o["output_kind"] for o in outputs]
    assert kinds == list(mo.DAILY_OUTPUT_KINDS)
    digests = {
        (o["authority_refs"]["digest"], o["coverage_refs"]["digest"], o["qc_refs"]["digest"])
        for o in outputs
    }
    assert len(digests) == 1
    for out in outputs:
        assert out["producer_kind"] == mo.PRODUCER_SYSTEM
        assert out["is_user_confirmed"] is False
        assert out["immutable"] is True
        assert mo.validate_mode_output(out, run, contract) == ()


def test_affected_query_draft_three_clause_chinese():
    run, _, _ = _positive_gate("daily")
    payload = mo.build_affected_query_draft(run, [_finding()])
    assert payload["draft_count"] == 1
    draft = payload["query_drafts"][0]
    assert draft["basis"].startswith("依据：")
    assert draft["finding"].startswith("发现：")
    assert draft["action"].startswith("行动项：")
    assert draft["display_text"] == draft["basis"] + draft["finding"] + draft["action"]
    assert draft["display_text"] == mo.project_query_display_text(
        "方案要求报告治疗期不良事件",
        "受试者记录出现未对应 AE 的症状描述",
        "请核实是否需补充 AE 记录并说明判定理由",
    )
    assert draft["draft_state"] == "draft"
    assert draft["is_sent"] is False
    assert draft["is_closed"] is False
    assert draft["is_user_confirmed"] is False
    assert draft["is_pd_recorded"] is False
    assert draft["is_pd_closed"] is False


def test_pd_finding_enters_draft_without_registration():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    finding = _finding(
        finding_id="finding-pd-001",
        risk_id="risk-pd-prohibited-cm-001",
        finding_kind="protocol_deviation_prohibited_medication",
        pd_wording_state="pending_verify_wording_only",
        basis="方案禁用药清单禁止合并使用指定药物",
        finding="检测到可能的禁用药暴露线索",
        action="请核实合并用药记录并确认是否构成方案偏离待核实线索",
    )
    out = mo.build_mode_output(
        run,
        contract,
        _spec("affected_query_draft", findings=[finding]),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    draft = out["payload"]["query_drafts"][0]
    assert draft["finding_kind"] == "protocol_deviation_prohibited_medication"
    assert draft["pd_wording_state"] == "pending_verify_wording_only"
    assert draft["is_pd_recorded"] is False
    assert draft["is_pd_closed"] is False
    assert out["payload"]["pd_registration_allowed"] is False
    assert out["payload"]["external_dispatch_allowed"] is False
    assert mo.validate_mode_output(out, run, contract) == ()


def test_query_missing_basis_fail_closed():
    run, _, _ = _positive_gate("daily")
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_affected_query_draft(run, [_finding(basis="")])
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


def test_query_cutoff_drift_fail_closed():
    run, _, _ = _positive_gate("daily")
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_affected_query_draft(
            run, [_finding(data_cutoff="cutoff-other")]
        )
    assert exc.value.failure_code == mo.CUTOFF_MISMATCH


def test_query_missing_evidence_fail_closed():
    run, _, _ = _positive_gate("daily")
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_affected_query_draft(run, [_finding(evidence_refs=[])])
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


def test_output_kind_not_eligible_for_mode():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_output(
            run,
            contract,
            _spec("full_project_report"),
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


def test_eligibility_incomplete_analysis_blocked():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_output(
            run,
            contract,
            {
                "output_kind": "change_summary",
                "eligibility": {
                    **mo.default_output_eligibility(),
                    "analysis_state": "running",
                },
            },
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


def test_authority_digest_missing_blocked():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    del auth["digest"]
    del auth["authority_digest"]
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_output(
            run,
            contract,
            _spec("change_summary"),
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc.value.failure_code == mo.AUTHORITY_MISMATCH


def test_authority_run_id_drift_blocked():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    auth["run_id"] = "run-other"
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_output(
            run,
            contract,
            _spec("change_summary"),
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc.value.failure_code == mo.AUTHORITY_MISMATCH


def test_daily_output_rejects_external_producer():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_output(
            run,
            contract,
            {
                "output_kind": "change_summary",
                "producer_kind": mo.PRODUCER_EXTERNAL,
                "eligibility": mo.default_output_eligibility(),
            },
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc.value.failure_code == mo.AUTHORITY_MISMATCH


def test_validate_mode_output_rejects_sent_query_tamper():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("affected_query_draft", findings=[_finding()]),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    tampered = copy.deepcopy(out)
    tampered["payload"]["query_drafts"][0]["is_sent"] = True
    codes = mo.validate_mode_output(tampered, run, contract)
    assert mo.OUTPUT_NOT_ELIGIBLE in codes


def test_validate_mode_output_rejects_closed_query_tamper():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("affected_query_draft", findings=[_finding()]),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    tampered = copy.deepcopy(out)
    tampered["payload"]["query_drafts"][0]["is_closed"] = True
    codes = mo.validate_mode_output(tampered, run, contract)
    assert mo.OUTPUT_NOT_ELIGIBLE in codes


def test_validate_mode_output_rejects_display_text_tamper():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("affected_query_draft", findings=[_finding()]),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    tampered = copy.deepcopy(out)
    tampered["payload"]["query_drafts"][0]["display_text"] = "被篡改"
    codes = mo.validate_mode_output(tampered, run, contract)
    assert mo.OUTPUT_NOT_ELIGIBLE in codes


def test_build_mode_output_does_not_mutate_inputs():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    finding = _finding()
    run_b = canonical_bytes(run)
    contract_b = canonical_bytes(contract)
    auth_b = canonical_bytes(auth)
    finding_b = canonical_bytes(finding)
    mo.build_mode_output(
        run,
        contract,
        _spec("affected_query_draft", findings=[finding]),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    assert canonical_bytes(run) == run_b
    assert canonical_bytes(contract) == contract_b
    assert canonical_bytes(auth) == auth_b
    assert canonical_bytes(finding) == finding_b


def test_query_draft_byte_stable():
    run, _, _ = _positive_gate("daily")
    a = mo.build_affected_query_draft(run, [_finding(), _finding(finding_id="finding-002")])
    b = mo.build_affected_query_draft(run, [_finding(finding_id="finding-002"), _finding()])
    assert canonical_bytes(a) == canonical_bytes(b)


def test_user_confirmed_true_on_build_blocked():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_output(
            run,
            contract,
            _spec("change_summary", is_user_confirmed=True),
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


# ---------------------------------------------------------------------------
# Slice-05 worker_01 — pre_lock four payloads (authority/cutoff/revision/numeric)
# ---------------------------------------------------------------------------


def _pre_lock_check_items():
    return [
        {
            "level": "project",
            "check_kind": "lock_preparation_scope",
            "status": "ready",
            "evidence_refs": ["ev-project-scope-001"],
            "locator": {"path": "project.lock_prep", "record_id": "proj-1"},
        },
        {
            "level": "site",
            "check_kind": "site_cutoff_alignment",
            "status": "ready",
            "site_id": "SITE-01",
            "evidence_refs": ["ev-site-cutoff-001"],
            "locator": {"path": "site.cutoff", "record_id": "site-01"},
        },
        {
            "level": "subject",
            "check_kind": "subject_listing_complete",
            "status": "blocked",
            "site_id": "SITE-01",
            "subject_id": "SUBJ-001",
            "coverage_missing": True,
            "evidence_refs": ["ev-subject-listing-gap-001"],
            "locator": {"path": "subject.coverage", "record_id": "SUBJ-001"},
        },
    ]


def _pre_lock_impacts():
    return [
        {
            "impact_kind": "clinical_data",
            "source_change_kind": "clinical_data",
            "affected_scope": {
                "scope_kind": "subject",
                "site_id": "SITE-01",
                "subject_id": "SUBJ-001",
            },
            "evidence_refs": ["ev-impact-listing-001"],
            "summary": "listing revision adds AE symptom row",
        },
        {
            "impact_kind": "knowledge_rule_mapping_model",
            "source_change_kind": "rule",
            "affected_scope": {"scope_kind": "project", "project_id": "project-r6-synthetic"},
            "evidence_refs": ["ev-impact-rule-001"],
            "summary": "rule pack activation bump (not clinical data)",
        },
    ]


def _pre_lock_revision_entries():
    return [
        {
            "revision_kind": "new",
            "previous_query_draft_id": None,
            "finding": _finding(),
        },
        {
            "revision_kind": "updated",
            "previous_query_draft_id": "qd-previous-001",
            "finding": _finding(
                finding_id="finding-002",
                issue_id="issue-002",
                action="请按修订后 listing 复核 AE 判定",
            ),
        },
    ]


def test_build_pre_lock_four_outputs_share_authority_cutoff_revision():
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    raw_rate = 14 / 117
    numeric = {
        "ae_rate": {
            "raw": raw_rate,
            "numerator": 14,
            "denominator": 117,
            "population": "safety",
            "data_cutoff": run["data_cutoff"],
            "source_revision_id": run["source_revision_id"],
        }
    }
    outputs = mo.build_pre_lock_mode_outputs(
        run,
        contract,
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        risks=[{
            "risk_id": "risk-ae-omission-001",
            "metric_id": "ae_rate",
            "status": "open",
            "raw_rate": raw_rate,
        }],
        numeric=numeric,
        population_scope={
            "scope_kind": "project",
            "population_id": "safety",
            "label": "accepted_full_snapshot",
        },
        from_source_revision_id="run-source-revision-000",
        revision_reason="Query-driven full listing revision before lock",
        impacts=_pre_lock_impacts(),
        check_items=_pre_lock_check_items(),
        revision_entries=_pre_lock_revision_entries(),
        entry_context=ctx,
    )
    assert len(outputs) == 4
    assert [o["output_kind"] for o in outputs] == list(mo.PRE_LOCK_OUTPUT_KINDS)
    shared = {
        (
            o["authority_refs"]["digest"],
            o["coverage_refs"]["digest"],
            o["qc_refs"]["digest"],
            o["data_cutoff"],
            o["source_revision_id"],
            o["run_id"],
            o["project_id"],
            o["mode"],
        )
        for o in outputs
    }
    assert len(shared) == 1
    for out in outputs:
        assert out["producer_kind"] == mo.PRODUCER_SYSTEM
        assert out["is_user_confirmed"] is False
        assert out["immutable"] is True
        assert out["mode"] == "pre_lock"
        assert mo.validate_mode_output(out, run, contract) == ()
        assert out["payload"]["data_cutoff"] == run["data_cutoff"]
        assert out["payload"]["source_revision_id"] == run["source_revision_id"]
        assert out["payload"]["authority_digest"] == auth["digest"]


def test_pre_lock_full_risk_numeric_metric_reconciliation():
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    raw_rate = 14 / 117
    out = mo.build_mode_output(
        run,
        contract,
        _spec(
            "full_risk",
            risks=[{
                "risk_id": "risk-ae-omission-001",
                "metric_id": "ae_rate",
                "raw_rate": raw_rate,
            }],
            numeric={
                "ae_rate": {
                    "raw": raw_rate,
                    "numerator": 14,
                    "denominator": 117,
                    "population": "safety",
                    "data_cutoff": run["data_cutoff"],
                    "source_revision_id": run["source_revision_id"],
                }
            },
            population_scope="safety",
        ),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    assert out["payload"]["output_kind"] == "full_risk"
    assert out["payload"]["population_scope"]["population_id"] == "safety"
    assert out["payload"]["numeric"]["ae_rate"]["raw"] == raw_rate
    assert out["payload"]["is_user_confirmed"] is False
    assert out["payload"]["disposition_closed"] is False
    assert mo.validate_mode_output(out, run, contract) == ()

    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_output(
            run,
            contract,
            _spec(
                "full_risk",
                risks=[{
                    "risk_id": "risk-ae-omission-001",
                    "metric_id": "ae_rate",
                    "raw_rate": 0.5,
                }],
                numeric={
                    "ae_rate": {
                        "raw": raw_rate,
                        "numerator": 14,
                        "denominator": 117,
                    }
                },
                population_scope="safety",
            ),
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc.value.failure_code == mo.AUTHORITY_MISMATCH


def test_pre_lock_revision_impact_binds_current_run_revision():
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec(
            "revision_impact",
            from_source_revision_id="run-source-revision-000",
            revision_reason="listing revision",
            impacts=_pre_lock_impacts(),
        ),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    payload = out["payload"]
    assert payload["to_source_revision_id"] == run["source_revision_id"]
    assert payload["from_source_revision_id"] != payload["to_source_revision_id"]
    assert payload["impact_count"] == 2
    assert {item["impact_kind"] for item in payload["impacts"]} == {
        "clinical_data",
        "knowledge_rule_mapping_model",
    }
    assert mo.validate_mode_output(out, run, contract) == ()

    with pytest.raises(mo.ModeOutputError) as same_rev:
        mo.build_revision_impact_payload(
            run,
            from_source_revision_id=run["source_revision_id"],
            revision_reason="noop",
            impacts=[],
            authority_refs=auth,
        )
    assert same_rev.value.failure_code == mo.REVISION_MISMATCH


def test_pre_lock_check_package_coverage_summary_recomputable():
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("check_package", check_items=_pre_lock_check_items()),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    summary = out["payload"]["coverage_summary"]
    assert summary == mo.recompute_check_coverage_summary(out["payload"]["check_items"])
    assert summary["total"] == 3
    assert summary["ready"] == 2
    assert summary["blocked"] == 1
    assert summary["by_level"]["project"]["ready"] == 1
    assert summary["by_level"]["subject"]["blocked"] == 1
    assert mo.validate_mode_output(out, run, contract) == ()

    tampered = copy.deepcopy(out)
    tampered["payload"]["coverage_summary"]["ready"] = 99
    assert mo.AUTHORITY_MISMATCH in mo.validate_mode_output(tampered, run, contract)


def test_pre_lock_query_revision_package_draft_only():
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec(
            "query_revision_package",
            revision_entries=_pre_lock_revision_entries(),
        ),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    payload = out["payload"]
    assert payload["is_sent"] is False
    assert payload["is_closed"] is False
    assert payload["is_user_confirmed"] is False
    assert payload["pd_registration_allowed"] is False
    assert payload["external_dispatch_allowed"] is False
    assert payload["entry_count"] == 2
    kinds = {entry["revision_kind"] for entry in payload["revision_entries"]}
    assert kinds == {"new", "updated"}
    for entry in payload["revision_entries"]:
        draft = entry["query_draft"]
        assert draft["is_sent"] is False
        assert draft["is_closed"] is False
        assert draft["draft_state"] == "draft"
        assert draft["data_cutoff"] == run["data_cutoff"]
        assert draft["source_revision_id"] == run["source_revision_id"]
    assert mo.validate_mode_output(out, run, contract) == ()


def test_build_pre_lock_mode_outputs_does_not_mutate_inputs():
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    risks = [{
        "risk_id": "risk-ae-omission-001",
        "metric_id": "ae_rate",
        "raw_rate": 14 / 117,
    }]
    numeric = {
        "ae_rate": {
            "raw": 14 / 117,
            "numerator": 14,
            "denominator": 117,
            "population": "safety",
            "data_cutoff": run["data_cutoff"],
            "source_revision_id": run["source_revision_id"],
        }
    }
    impacts = _pre_lock_impacts()
    checks = _pre_lock_check_items()
    entries = _pre_lock_revision_entries()
    snapshots = {
        "run": canonical_bytes(run),
        "contract": canonical_bytes(contract),
        "auth": canonical_bytes(auth),
        "risks": canonical_bytes(risks),
        "numeric": canonical_bytes(numeric),
        "impacts": canonical_bytes(impacts),
        "checks": canonical_bytes(checks),
        "entries": canonical_bytes(entries),
        "ctx": canonical_bytes(ctx),
    }
    mo.build_pre_lock_mode_outputs(
        run,
        contract,
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        risks=risks,
        numeric=numeric,
        population_scope="safety",
        from_source_revision_id="run-source-revision-000",
        revision_reason="listing revision",
        impacts=impacts,
        check_items=checks,
        revision_entries=entries,
        entry_context=ctx,
    )
    assert canonical_bytes(run) == snapshots["run"]
    assert canonical_bytes(contract) == snapshots["contract"]
    assert canonical_bytes(auth) == snapshots["auth"]
    assert canonical_bytes(risks) == snapshots["risks"]
    assert canonical_bytes(numeric) == snapshots["numeric"]
    assert canonical_bytes(impacts) == snapshots["impacts"]
    assert canonical_bytes(checks) == snapshots["checks"]
    assert canonical_bytes(entries) == snapshots["entries"]
    assert canonical_bytes(ctx) == snapshots["ctx"]


def test_pre_lock_four_outputs_byte_stable():
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    kwargs = dict(
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        risks=[],
        numeric={},
        population_scope="safety",
        from_source_revision_id="run-source-revision-000",
        revision_reason="listing revision",
        impacts=_pre_lock_impacts(),
        check_items=_pre_lock_check_items(),
        revision_entries=_pre_lock_revision_entries(),
        entry_context=ctx,
    )
    a = mo.build_pre_lock_mode_outputs(run, contract, **kwargs)
    b = mo.build_pre_lock_mode_outputs(run, contract, **kwargs)
    for left, right in zip(a, b):
        assert canonical_bytes(left) == canonical_bytes(right)


# ---------------------------------------------------------------------------
# Slice-05 worker_02 — focused negatives: revision / coverage / query /
# tamper / cross-mode
# ---------------------------------------------------------------------------


def test_revision_impact_rejects_knowledge_as_clinical_data():
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_revision_impact_payload(
            run,
            from_source_revision_id="run-source-revision-000",
            revision_reason="rule pack bump",
            impacts=[{
                "impact_kind": "clinical_data",
                "source_change_kind": "rule",
                "affected_scope": {"scope_kind": "project", "project_id": run["project_id"]},
                "evidence_refs": ["ev-rule-001"],
                "summary": "rule change mislabeled as clinical data",
            }],
            authority_refs=auth,
        )
    assert exc.value.failure_code == mo.AUTHORITY_MISMATCH


def test_revision_impact_rejects_empty_evidence_and_reason():
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    with pytest.raises(mo.ModeOutputError) as no_evidence:
        mo.build_revision_impact_payload(
            run,
            from_source_revision_id="run-source-revision-000",
            revision_reason="listing revision",
            impacts=[{
                "impact_kind": "clinical_data",
                "source_change_kind": "clinical_data",
                "affected_scope": {
                    "scope_kind": "subject",
                    "site_id": "SITE-01",
                    "subject_id": "SUBJ-001",
                },
                "evidence_refs": [],
                "summary": "missing evidence",
            }],
            authority_refs=auth,
        )
    assert no_evidence.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE

    with pytest.raises(mo.ModeOutputError) as no_reason:
        mo.build_revision_impact_payload(
            run,
            from_source_revision_id="run-source-revision-000",
            revision_reason="",
            impacts=[],
            authority_refs=auth,
        )
    assert no_reason.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


def test_revision_impact_to_revision_and_impact_id_tamper_fail_closed():
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec(
            "revision_impact",
            from_source_revision_id="run-source-revision-000",
            revision_reason="listing revision",
            impacts=_pre_lock_impacts(),
        ),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    to_tampered = copy.deepcopy(out)
    to_tampered["payload"]["to_source_revision_id"] = "revision-forged"
    assert mo.REVISION_MISMATCH in mo.validate_mode_output(to_tampered, run, contract)

    id_tampered = copy.deepcopy(out)
    id_tampered["payload"]["impacts"][0]["impact_id"] = "imp-forged"
    assert mo.IDENTITY_MISMATCH in mo.validate_mode_output(id_tampered, run, contract)

    count_tampered = copy.deepcopy(out)
    count_tampered["payload"]["impact_count"] = 99
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        count_tampered, run, contract
    )


def test_revision_impact_deterministic_across_input_order():
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    impacts = _pre_lock_impacts()
    a = mo.build_revision_impact_payload(
        run,
        from_source_revision_id="run-source-revision-000",
        revision_reason="listing revision",
        impacts=impacts,
        authority_refs=auth,
    )
    b = mo.build_revision_impact_payload(
        run,
        from_source_revision_id="run-source-revision-000",
        revision_reason="listing revision",
        impacts=list(reversed(impacts)),
        authority_refs=auth,
    )
    assert canonical_bytes(a) == canonical_bytes(b)
    assert a["to_source_revision_id"] == run["source_revision_id"]
    assert len({item["impact_id"] for item in a["impacts"]}) == len(a["impacts"])


def test_check_coverage_rejects_forbidden_status_and_missing_level():
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    items = _pre_lock_check_items()
    forged = copy.deepcopy(items)
    forged[0]["status"] = "completed"
    with pytest.raises(mo.ModeOutputError) as completed:
        mo.build_check_package_payload(run, check_items=forged, authority_refs=auth)
    assert completed.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE

    forged_passed = copy.deepcopy(items)
    forged_passed[1]["status"] = "passed"
    with pytest.raises(mo.ModeOutputError) as passed:
        mo.build_check_package_payload(
            run, check_items=forged_passed, authority_refs=auth
        )
    assert passed.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE

    missing_subject = [item for item in items if item["level"] != "subject"]
    with pytest.raises(mo.ModeOutputError) as missing_level:
        mo.build_check_package_payload(
            run, check_items=missing_subject, authority_refs=auth
        )
    assert missing_level.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


def test_check_coverage_missing_or_conflict_must_be_blocked():
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    items = _pre_lock_check_items()
    ready_missing = copy.deepcopy(items)
    ready_missing[2]["status"] = "ready"
    ready_missing[2]["coverage_missing"] = True
    ready_missing[2]["evidence_refs"] = ["ev-forged"]
    ready_missing[2]["locator"] = {"path": "subject.listing"}
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_check_package_payload(
            run, check_items=ready_missing, authority_refs=auth
        )
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE

    conflict_ready = copy.deepcopy(items)
    conflict_ready[0]["evidence_conflict"] = True
    with pytest.raises(mo.ModeOutputError) as conflict:
        mo.build_check_package_payload(
            run, check_items=conflict_ready, authority_refs=auth
        )
    assert conflict.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


def test_check_coverage_summary_recompute_and_tamper_matrix():
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    items = _pre_lock_check_items() + [{
        "level": "subject",
        "check_kind": "subject_na",
        "status": "not_applicable",
        "site_id": "SITE-01",
        "subject_id": "SUBJ-002",
        "evidence_refs": ["ev-subject-na-001"],
        "locator": {"path": "subject.applicability", "record_id": "SUBJ-002"},
    }]
    out = mo.build_mode_output(
        run,
        contract,
        _spec("check_package", check_items=items),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    expected = mo.recompute_check_coverage_summary(out["payload"]["check_items"])
    assert out["payload"]["coverage_summary"] == expected
    assert expected["total"] == 4
    assert expected["ready"] == 2
    assert expected["blocked"] == 1
    assert expected["not_applicable"] == 1
    assert canonical_bytes(expected) == canonical_bytes(
        mo.recompute_check_coverage_summary(out["payload"]["check_items"])
    )

    summary_tamper = copy.deepcopy(out)
    summary_tamper["payload"]["coverage_summary"]["blocked"] = 0
    assert mo.AUTHORITY_MISMATCH in mo.validate_mode_output(
        summary_tamper, run, contract
    )

    check_id_tamper = copy.deepcopy(out)
    check_id_tamper["payload"]["check_items"][0]["check_id"] = "chk-forged"
    assert mo.IDENTITY_MISMATCH in mo.validate_mode_output(
        check_id_tamper, run, contract
    )


def test_query_revision_draft_only_package_and_entry_flags():
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec(
            "query_revision_package",
            revision_entries=_pre_lock_revision_entries() + [{
                "revision_kind": "withdrawn_draft",
                "previous_query_draft_id": "qd-previous-withdrawn",
                "finding": _finding(
                    finding_id="finding-withdrawn-001",
                    issue_id="issue-withdrawn-001",
                    action="本地草稿退出当前包，保持未发送未关闭",
                ),
            }],
        ),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    payload = out["payload"]
    assert payload["is_sent"] is False
    assert payload["is_closed"] is False
    assert payload["pd_registration_allowed"] is False
    assert payload["external_dispatch_allowed"] is False
    withdrawn = next(
        e for e in payload["revision_entries"] if e["revision_kind"] == "withdrawn_draft"
    )
    assert withdrawn["query_draft"]["is_sent"] is False
    assert withdrawn["query_draft"]["is_closed"] is False
    assert withdrawn["query_draft"]["draft_state"] == "draft"

    for flag in (
        "is_sent",
        "is_closed",
        "is_user_confirmed",
        "pd_registration_allowed",
        "external_dispatch_allowed",
    ):
        tampered = copy.deepcopy(out)
        tampered["payload"][flag] = True
        codes = mo.validate_mode_output(tampered, run, contract)
        assert mo.OUTPUT_NOT_ELIGIBLE in codes, flag

    draft_sent = copy.deepcopy(out)
    draft_sent["payload"]["revision_entries"][0]["query_draft"]["is_sent"] = True
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        draft_sent, run, contract
    )


def test_query_revision_lifecycle_new_updated_rules_fail_closed():
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    with pytest.raises(mo.ModeOutputError) as new_with_prev:
        mo.build_query_revision_package_payload(
            run,
            revision_entries=[{
                "revision_kind": "new",
                "previous_query_draft_id": "qd-should-be-empty",
                "finding": _finding(),
            }],
            authority_refs=auth,
        )
    assert new_with_prev.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE

    with pytest.raises(mo.ModeOutputError) as updated_no_prev:
        mo.build_query_revision_package_payload(
            run,
            revision_entries=[{
                "revision_kind": "updated",
                "previous_query_draft_id": None,
                "finding": _finding(finding_id="finding-002", issue_id="issue-002"),
            }],
            authority_refs=auth,
        )
    assert updated_no_prev.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE

    with pytest.raises(mo.ModeOutputError) as bad_kind:
        mo.build_query_revision_package_payload(
            run,
            revision_entries=[{
                "revision_kind": "closed_externally",
                "finding": _finding(),
            }],
            authority_refs=auth,
        )
    assert bad_kind.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


def test_query_revision_entry_count_and_draft_id_tamper():
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec(
            "query_revision_package",
            revision_entries=_pre_lock_revision_entries(),
        ),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    count_tamper = copy.deepcopy(out)
    count_tamper["payload"]["entry_count"] = 0
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        count_tamper, run, contract
    )

    id_tamper = copy.deepcopy(out)
    id_tamper["payload"]["revision_entries"][0]["query_draft_id"] = "qd-forged"
    assert mo.IDENTITY_MISMATCH in mo.validate_mode_output(id_tamper, run, contract)

    display_tamper = copy.deepcopy(out)
    display_tamper["payload"]["revision_entries"][0]["query_draft"][
        "display_text"
    ] = "被篡改"
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        display_tamper, run, contract
    )


def test_pre_lock_cross_mode_mix_fail_closed():
    daily_run, daily_contract, daily_ctx = _positive_gate("daily")
    pre_run, pre_contract, pre_ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(pre_run)

    with pytest.raises(mo.ModeOutputError) as daily_builder:
        mo.build_pre_lock_mode_outputs(
            daily_run,
            daily_contract,
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            from_source_revision_id="run-source-revision-000",
            revision_reason="should fail",
            impacts=_pre_lock_impacts(),
            check_items=_pre_lock_check_items(),
            revision_entries=_pre_lock_revision_entries(),
            entry_context=daily_ctx,
        )
    assert daily_builder.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE

    with pytest.raises(mo.ModeOutputError) as pre_kind_on_daily:
        mo.build_mode_output(
            daily_run,
            daily_contract,
            _spec(
                "revision_impact",
                from_source_revision_id="run-source-revision-000",
                revision_reason="cross mode",
                impacts=_pre_lock_impacts(),
            ),
            authority_refs=_refs(daily_run)[0],
            coverage_refs=_refs(daily_run)[1],
            qc_refs=_refs(daily_run)[2],
            entry_context=daily_ctx,
        )
    assert pre_kind_on_daily.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE

    with pytest.raises(mo.ModeOutputError) as daily_kind_on_pre:
        mo.build_mode_output(
            pre_run,
            pre_contract,
            _spec("change_summary"),
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=pre_ctx,
        )
    assert daily_kind_on_pre.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE

    with pytest.raises(mo.ModeOutputError) as payload_on_daily_run:
        mo.build_revision_impact_payload(
            daily_run,
            from_source_revision_id="run-source-revision-000",
            revision_reason="cross mode payload",
            impacts=_pre_lock_impacts(),
            authority_refs=_refs(daily_run)[0],
        )
    assert payload_on_daily_run.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE

    # Built pre_lock output cannot be validated under a daily contract/run.
    out = mo.build_mode_output(
        pre_run,
        pre_contract,
        _spec(
            "revision_impact",
            from_source_revision_id="run-source-revision-000",
            revision_reason="listing revision",
            impacts=_pre_lock_impacts(),
        ),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=pre_ctx,
    )
    mixed = copy.deepcopy(out)
    mixed["mode"] = "daily"
    codes = mo.validate_mode_output(mixed, daily_run, daily_contract)
    assert codes
    assert set(codes) <= set(FROZEN_MODE_OUTPUT_CODES)
    assert (
        mo.MODE_ENTRY_BLOCKED in codes
        or mo.OUTPUT_NOT_ELIGIBLE in codes
        or mo.IDENTITY_MISMATCH in codes
        or mo.SILENT_MODE_CONVERSION in codes
    )


def test_pre_lock_authority_cutoff_revision_cross_output_tamper():
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    outputs = mo.build_pre_lock_mode_outputs(
        run,
        contract,
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        risks=[],
        numeric={},
        population_scope="safety",
        from_source_revision_id="run-source-revision-000",
        revision_reason="listing revision",
        impacts=_pre_lock_impacts(),
        check_items=_pre_lock_check_items(),
        revision_entries=_pre_lock_revision_entries(),
        entry_context=ctx,
    )
    shared = {
        (
            o["authority_refs"]["digest"],
            o["data_cutoff"],
            o["source_revision_id"],
            o["run_id"],
        )
        for o in outputs
    }
    assert len(shared) == 1

    for out in outputs:
        auth_tamper = copy.deepcopy(out)
        auth_tamper["payload"]["authority_digest"] = "tampered-auth"
        assert mo.AUTHORITY_MISMATCH in mo.validate_mode_output(
            auth_tamper, run, contract
        )

        cutoff_tamper = copy.deepcopy(out)
        cutoff_tamper["payload"]["data_cutoff"] = "cutoff-other"
        codes = mo.validate_mode_output(cutoff_tamper, run, contract)
        assert (
            mo.AUTHORITY_MISMATCH in codes
            or mo.CUTOFF_MISMATCH in codes
            or mo.IDENTITY_MISMATCH in codes
        )

        rev_tamper = copy.deepcopy(out)
        rev_tamper["payload"]["source_revision_id"] = "revision-other"
        codes = mo.validate_mode_output(rev_tamper, run, contract)
        assert (
            mo.AUTHORITY_MISMATCH in codes
            or mo.REVISION_MISMATCH in codes
            or mo.IDENTITY_MISMATCH in codes
        )


def test_pre_lock_negative_builders_do_not_mutate_inputs():
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    impacts = _pre_lock_impacts()
    checks = _pre_lock_check_items()
    entries = _pre_lock_revision_entries()
    snapshots = {
        "impacts": canonical_bytes(impacts),
        "checks": canonical_bytes(checks),
        "entries": canonical_bytes(entries),
        "auth": canonical_bytes(auth),
        "run": canonical_bytes(run),
    }
    with pytest.raises(mo.ModeOutputError):
        mo.build_revision_impact_payload(
            run,
            from_source_revision_id=run["source_revision_id"],
            revision_reason="noop",
            impacts=impacts,
            authority_refs=auth,
        )
    with pytest.raises(mo.ModeOutputError):
        forged = copy.deepcopy(checks)
        forged[0]["status"] = "user_confirmed"
        mo.build_check_package_payload(run, check_items=forged, authority_refs=auth)
    with pytest.raises(mo.ModeOutputError):
        mo.build_query_revision_package_payload(
            run,
            revision_entries=[{
                "revision_kind": "new",
                "previous_query_draft_id": "qd-x",
                "finding": _finding(),
            }],
            authority_refs=auth,
        )
    assert canonical_bytes(impacts) == snapshots["impacts"]
    assert canonical_bytes(checks) == snapshots["checks"]
    assert canonical_bytes(entries) == snapshots["entries"]
    assert canonical_bytes(auth) == snapshots["auth"]
    assert canonical_bytes(run) == snapshots["run"]


# Codex acceptance hardening — explicit authority, identity and nested payloads.


@pytest.mark.parametrize(
    "builder,kwargs",
    [
        (
            mo.build_full_risk_payload,
            {"risks": [], "numeric": {}, "population_scope": "safety"},
        ),
        (
            mo.build_revision_impact_payload,
            {
                "from_source_revision_id": "run-source-revision-000",
                "revision_reason": "listing revision",
                "impacts": [],
            },
        ),
        (mo.build_check_package_payload, {"check_items": _pre_lock_check_items()}),
        (
            mo.build_query_revision_package_payload,
            {"revision_entries": _pre_lock_revision_entries()},
        ),
    ],
)
def test_pre_lock_standalone_builders_require_authority_digest(builder, kwargs):
    run, _, _ = _positive_gate("pre_lock")
    with pytest.raises(mo.ModeOutputError) as exc:
        builder(run, authority_refs={"project_id": run["project_id"]}, **kwargs)
    assert exc.value.failure_code == mo.AUTHORITY_MISMATCH


def test_pre_lock_full_risk_requires_explicit_population_scope():
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_full_risk_payload(
            run,
            risks=[],
            numeric={},
            population_scope=None,
            authority_refs=auth,
        )
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


@pytest.mark.parametrize(
    "field,code",
    [
        ("output_kind", mo.OUTPUT_NOT_ELIGIBLE),
        ("project_id", mo.IDENTITY_MISMATCH),
        ("run_id", mo.IDENTITY_MISMATCH),
        ("data_cutoff", mo.CUTOFF_MISMATCH),
        ("source_revision_id", mo.REVISION_MISMATCH),
        ("authority_digest", mo.AUTHORITY_MISMATCH),
    ],
)
def test_pre_lock_payload_binding_is_mandatory_after_outer_id_restamp(field, code):
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("full_risk", risks=[], numeric={}, population_scope="safety"),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    tampered = copy.deepcopy(out)
    del tampered["payload"][field]
    tampered = _restamp_output_id(tampered)
    assert code in mo.validate_mode_output(tampered, run, contract)


def test_withdrawn_query_revision_requires_previous_and_complete_source():
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    for entry in (
        {"revision_kind": "withdrawn_draft", "finding": _finding()},
        {
            "revision_kind": "withdrawn_draft",
            "previous_query_draft_id": "qd-previous-001",
            "query_draft_id": "qd-marker-only",
        },
    ):
        with pytest.raises(mo.ModeOutputError) as exc:
            mo.build_query_revision_package_payload(
                run, revision_entries=[entry], authority_refs=auth
            )
        assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


@pytest.mark.parametrize("status", ["blocked", "not_applicable"])
@pytest.mark.parametrize("missing", ["evidence_refs", "locator"])
def test_every_check_item_requires_evidence_and_locator(status, missing):
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    items = _pre_lock_check_items()
    items[2]["status"] = status
    if status == "not_applicable":
        items[2]["coverage_missing"] = False
    items[2][missing] = [] if missing == "evidence_refs" else {}
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_check_package_payload(run, check_items=items, authority_refs=auth)
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


@pytest.mark.parametrize(
    "output_kind,path,value,code",
    [
        ("revision_impact", ("impacts", 0, "unexpected"), True, mo.IDENTITY_MISMATCH),
        ("check_package", ("check_items", 0, "unexpected"), True, mo.IDENTITY_MISMATCH),
        (
            "query_revision_package",
            ("revision_entries", 0, "query_draft", "is_sent"),
            True,
            mo.OUTPUT_NOT_ELIGIBLE,
        ),
        (
            "query_revision_package",
            ("revision_entries", 0, "query_draft", "scope_kind"),
            "project",
            mo.OUTPUT_NOT_ELIGIBLE,
        ),
    ],
)
def test_nested_pre_lock_payload_tamper_fails_after_outer_id_restamp(
    output_kind, path, value, code
):
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    specs = {
        "revision_impact": _spec(
            "revision_impact",
            from_source_revision_id="run-source-revision-000",
            revision_reason="listing revision",
            impacts=_pre_lock_impacts(),
        ),
        "check_package": _spec("check_package", check_items=_pre_lock_check_items()),
        "query_revision_package": _spec(
            "query_revision_package", revision_entries=_pre_lock_revision_entries()
        ),
    }
    out = mo.build_mode_output(
        run,
        contract,
        specs[output_kind],
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    tampered = copy.deepcopy(out)
    target = tampered["payload"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    tampered = _restamp_output_id(tampered)
    assert code in mo.validate_mode_output(tampered, run, contract)


@pytest.mark.parametrize(
    "flag",
    [
        "is_sent",
        "is_closed",
        "is_user_confirmed",
        "pd_registration_allowed",
        "external_dispatch_allowed",
    ],
)
@pytest.mark.parametrize("bad_value", [pytest.param(None, id="missing"), "true", 1])
def test_query_revision_package_requires_explicit_false_lifecycle(flag, bad_value):
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("query_revision_package", revision_entries=_pre_lock_revision_entries()),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    tampered = copy.deepcopy(out)
    if bad_value is None:
        del tampered["payload"][flag]
    else:
        tampered["payload"][flag] = bad_value
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        _restamp_output_id(tampered), run, contract
    )


@pytest.mark.parametrize(
    "flag", ["is_sent", "is_closed", "is_user_confirmed", "is_pd_recorded", "is_pd_closed"]
)
@pytest.mark.parametrize("bad_value", [pytest.param(None, id="missing"), "true", 1])
def test_query_revision_nested_draft_requires_explicit_false_lifecycle(flag, bad_value):
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("query_revision_package", revision_entries=_pre_lock_revision_entries()),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    tampered = copy.deepcopy(out)
    draft = tampered["payload"]["revision_entries"][0]["query_draft"]
    if bad_value is None:
        del draft[flag]
    else:
        draft[flag] = bad_value
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        _restamp_output_id(tampered), run, contract
    )


def test_mode_output_envelope_requires_boolean_false_user_confirmation():
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("full_risk", risks=[], numeric={}, population_scope="safety"),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    for value in ("true", 1, None):
        tampered = copy.deepcopy(out)
        tampered["is_user_confirmed"] = value
        assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
            _restamp_output_id(tampered), run, contract
        )


@pytest.mark.parametrize(
    "flag",
    ["is_user_confirmed", "disposition_closed", "medical_conclusion_final"],
)
@pytest.mark.parametrize("value", [True, "true", 1])
def test_full_risk_rejects_non_false_payload_and_risk_lifecycle(flag, value):
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    for location in ("payload", "risk"):
        payload = mo.build_full_risk_payload(
            run, risks=[{"risk_id": "risk-001"}], numeric={},
            population_scope="safety", authority_refs=auth
        )
        payload[flag] = value if location == "payload" else payload.get(flag, False)
        if location == "risk":
            payload["risks"][0][flag] = value
        codes = []
        mo._validate_full_risk_payload(payload, run, authority_refs=auth, codes=codes)
        assert mo.OUTPUT_NOT_ELIGIBLE in codes


@pytest.mark.parametrize(
    "marker", ["rate", "raw", "raw_value", "pct", "percentage", "numerator", "denominator"]
)
def test_full_risk_all_quantitative_markers_require_numeric_binding(marker):
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    value = 1 if marker in {"numerator", "denominator"} else 0.5
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_full_risk_payload(
            run,
            risks=[{"risk_id": "risk-001", "metric_id": "metric-missing", marker: value}],
            numeric={},
            population_scope="safety",
            authority_refs=auth,
        )
    assert exc.value.failure_code == mo.AUTHORITY_MISMATCH


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("population", "itt", mo.AUTHORITY_MISMATCH),
        ("data_cutoff", None, mo.CUTOFF_MISMATCH),
        ("source_revision_id", None, mo.REVISION_MISMATCH),
    ],
)
def test_pre_lock_numeric_rows_bind_population_cutoff_revision(field, value, code):
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    row = {
        "raw": 0.5,
        "numerator": 1,
        "denominator": 2,
        "population": "safety",
        "data_cutoff": run["data_cutoff"],
        "source_revision_id": run["source_revision_id"],
    }
    row[field] = value
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_full_risk_payload(
            run,
            risks=[{"risk_id": "risk-001", "metric_id": "m1", "raw_rate": 0.5}],
            numeric={"m1": row},
            population_scope="safety",
            authority_refs=auth,
        )
    assert exc.value.failure_code == code


def test_check_items_reject_uncheckable_locator_duplicate_id_and_non_bool_flags():
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    junk = _pre_lock_check_items()
    junk[0]["locator"] = {"note": "not independently checkable"}
    with pytest.raises(mo.ModeOutputError) as locator:
        mo.build_check_package_payload(run, check_items=junk, authority_refs=auth)
    assert locator.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE

    duplicated = _pre_lock_check_items()
    duplicated.append(copy.deepcopy(duplicated[0]))
    with pytest.raises(mo.ModeOutputError) as duplicate:
        mo.build_check_package_payload(run, check_items=duplicated, authority_refs=auth)
    assert duplicate.value.failure_code == mo.IDENTITY_MISMATCH

    non_bool = _pre_lock_check_items()
    non_bool[0]["coverage_missing"] = "true"
    with pytest.raises(mo.ModeOutputError) as flag:
        mo.build_check_package_payload(run, check_items=non_bool, authority_refs=auth)
    assert flag.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("missing_source", mo.OUTPUT_NOT_ELIGIBLE),
        ("reverse_masquerade", mo.AUTHORITY_MISMATCH),
        ("missing_subject", mo.OUTPUT_NOT_ELIGIBLE),
        ("duplicate", mo.IDENTITY_MISMATCH),
    ],
)
def test_revision_impact_source_scope_and_identity_fail_closed(mutation, code):
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    impacts = _pre_lock_impacts()
    if mutation == "missing_source":
        impacts[0].pop("source_change_kind")
    elif mutation == "reverse_masquerade":
        impacts[1]["source_change_kind"] = "clinical_data"
    elif mutation == "missing_subject":
        impacts[0]["affected_scope"].pop("subject_id")
    else:
        impacts.append(copy.deepcopy(impacts[0]))
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_revision_impact_payload(
            run,
            from_source_revision_id="run-source-revision-000",
            revision_reason="listing revision",
            impacts=impacts,
            authority_refs=auth,
        )
    assert exc.value.failure_code == code


def test_query_revision_rejects_duplicate_and_self_revision_identity():
    run, _, _ = _positive_gate("pre_lock")
    auth, _, _ = _refs(run)
    duplicate = [_pre_lock_revision_entries()[0], _pre_lock_revision_entries()[0]]
    with pytest.raises(mo.ModeOutputError) as dup:
        mo.build_query_revision_package_payload(
            run, revision_entries=duplicate, authority_refs=auth
        )
    assert dup.value.failure_code == mo.IDENTITY_MISMATCH

    current = mo.build_query_revision_package_payload(
        run,
        revision_entries=[_pre_lock_revision_entries()[0]],
        authority_refs=auth,
    )["revision_entries"][0]["query_draft"]
    with pytest.raises(mo.ModeOutputError) as same:
        mo.build_query_revision_package_payload(
            run,
            revision_entries=[{
                "revision_kind": "updated",
                "previous_query_draft_id": current["query_draft_id"],
                "query_draft": current,
            }],
            authority_refs=auth,
        )
    assert same.value.failure_code == mo.IDENTITY_MISMATCH


def test_standalone_pre_lock_builders_reject_incremental_run():
    run, _, _ = _positive_gate("pre_lock", execution_basis="incremental")
    auth, _, _ = _refs(run)
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_full_risk_payload(
            run, risks=[], numeric={}, population_scope="safety", authority_refs=auth
        )
    assert exc.value.failure_code == mo.MODE_ENTRY_BLOCKED


@pytest.mark.parametrize("key", sorted(mo.QUERY_FORBIDDEN_KEYS))
def test_query_revision_package_rejects_external_workflow_metadata(key):
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("query_revision_package", revision_entries=_pre_lock_revision_entries()),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    tampered = copy.deepcopy(out)
    tampered["payload"][key] = "invented-workflow-state"
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        _restamp_output_id(tampered), run, contract
    )


@pytest.mark.parametrize(
    "flag", ["is_pd_recorded", "is_pd_closed", "pd_registered", "pd_closed"]
)
def test_query_revision_package_rejects_pd_lifecycle_aliases(flag):
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("query_revision_package", revision_entries=_pre_lock_revision_entries()),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    tampered = copy.deepcopy(out)
    tampered["payload"][flag] = True
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        _restamp_output_id(tampered), run, contract
    )


@pytest.mark.parametrize("output_kind,count_key", [("revision_impact", "impact_count"), ("query_revision_package", "entry_count")])
def test_pre_lock_required_counts_cannot_be_omitted(output_kind, count_key):
    run, contract, ctx = _positive_gate("pre_lock")
    auth, cov, qc = _refs(run)
    spec = (
        _spec(
            "revision_impact",
            from_source_revision_id="run-source-revision-000",
            revision_reason="listing revision",
            impacts=_pre_lock_impacts(),
        )
        if output_kind == "revision_impact"
        else _spec(
            "query_revision_package", revision_entries=_pre_lock_revision_entries()
        )
    )
    out = mo.build_mode_output(
        run,
        contract,
        spec,
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    tampered = copy.deepcopy(out)
    del tampered["payload"][count_key]
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        _restamp_output_id(tampered), run, contract
    )


# ---------------------------------------------------------------------------
# Slice-06 worker_02 — post_lock_pre_cfdi fixed-total outputs
# ---------------------------------------------------------------------------


def _post_lock_population_totals(**overrides):
    base = {"site_count": 1, "subject_count": 1, "risk_count": 1}
    base.update(overrides)
    return base


def _post_lock_site_materials():
    return [
        {
            "site_id": "SITE-01",
            "subject_ids": ["SUBJ-001"],
            "risk_ids": ["risk-001"],
            "evidence_refs": ["ev-site-001"],
            "locator": {"path": "SITE.SITE-01", "record_id": "site-01"},
        }
    ]


def _post_lock_subject_materials():
    return [
        {
            "subject_id": "SUBJ-001",
            "site_id": "SITE-01",
            "profile_ref": {"profile_id": "prof-SUBJ-001"},
            "timeline_ref": {"timeline_id": "tl-SUBJ-001"},
            "risk_ids": ["risk-001"],
            "evidence_refs": ["ev-subj-001"],
            "locator": {"path": "SUBJ.SUBJ-001", "record_id": "subj-001"},
        }
    ]


def _post_lock_check_items(run):
    return [
        {
            "level": "project",
            "check_kind": "project_lock",
            "scope_id": run["project_id"],
            "status": "ready",
            "risk_ids": ["risk-001"],
            "evidence_refs": ["ev-chk-project"],
            "locator": {"path": "CHK.PROJECT", "record_id": "chk-p1"},
        },
        {
            "level": "site",
            "check_kind": "site_coverage",
            "scope_id": "SITE-01",
            "status": "ready",
            "risk_ids": ["risk-001"],
            "evidence_refs": ["ev-chk-site"],
            "locator": {"path": "CHK.SITE", "record_id": "chk-s1"},
        },
        {
            "level": "subject",
            "check_kind": "subject_profile",
            "scope_id": "SUBJ-001",
            "status": "blocked",
            "coverage_missing": True,
            "risk_ids": [],
            "evidence_refs": ["ev-chk-subject"],
            "locator": {"path": "CHK.SUBJ", "record_id": "chk-u1"},
        },
    ]


def _post_lock_risk_summary(**overrides):
    base = {
        "high_count": 1,
        "medium_count": 0,
        "low_count": 0,
        "risk_ids": ["risk-001"],
    }
    base.update(overrides)
    return base


def _post_lock_project_summary():
    return {"title": "synthetic post-lock draft", "status": "locked_fixed_total"}


def _build_post_lock_four(run=None, contract=None, ctx=None, **overrides):
    if run is None or contract is None or ctx is None:
        run, contract, ctx = _positive_gate("post_lock_pre_cfdi")
    auth, cov, qc = _refs(run)
    kwargs = {
        "authority_refs": auth,
        "coverage_refs": cov,
        "qc_refs": qc,
        "population_totals": _post_lock_population_totals(),
        "report_version": "v1.0.0-fixed",
        "project_summary": _post_lock_project_summary(),
        "risk_summary": _post_lock_risk_summary(),
        "evidence_refs": ["ev-report-001"],
        "site_materials": _post_lock_site_materials(),
        "subject_materials": _post_lock_subject_materials(),
        "check_items": _post_lock_check_items(run),
        "entry_context": ctx,
    }
    kwargs.update(overrides)
    outputs = mo.build_post_lock_mode_outputs(run, contract, **kwargs)
    return run, contract, auth, cov, qc, outputs


def test_build_post_lock_four_outputs_share_locked_identity_and_totals():
    run, contract, auth, _cov, _qc, outputs = _build_post_lock_four()
    assert len(outputs) == 4
    assert [o["output_kind"] for o in outputs] == list(mo.POST_LOCK_OUTPUT_KINDS)
    shared = {
        (
            o["payload"]["project_id"],
            o["payload"]["run_id"],
            o["payload"]["data_cutoff"],
            o["payload"]["source_revision_id"],
            o["payload"]["authority_digest"],
            o["payload"]["locked_snapshot_hash"],
            o["payload"]["acceptance_evidence_hash"],
            o["payload"]["fixed_total"],
            canonical_bytes(o["payload"]["population_totals"]),
            o["mode"],
            o["producer_kind"],
        )
        for o in outputs
    }
    assert len(shared) == 1
    for out in outputs:
        assert out["mode"] == "post_lock_pre_cfdi"
        assert out["producer_kind"] == mo.PRODUCER_SYSTEM
        assert out["immutable"] is True
        assert out["is_user_confirmed"] is False
        assert out["payload"]["fixed_total"] is True
        assert out["payload"]["locked_snapshot_hash"] == run["locked_snapshot_hash"]
        assert (
            out["payload"]["acceptance_evidence_hash"]
            == run["acceptance_evidence_hash"]
        )
        assert out["payload"]["population_totals"] == _post_lock_population_totals()
        assert out["payload"]["authority_digest"] == auth["digest"]
        assert mo.validate_mode_output(out, run, contract) == ()
    assert mo.validate_post_lock_output_set(*outputs) == ()


def test_post_lock_full_project_report_draft_only_and_nested_ids():
    run, contract, auth, cov, qc, outputs = _build_post_lock_four()
    report, sites, subjects, checklist = outputs
    payload = report["payload"]
    assert payload["output_kind"] == "full_project_report"
    assert payload["report_id"].startswith("fpr-")
    assert payload["report_version"] == "v1.0.0-fixed"
    for flag in mo.POST_LOCK_FORBIDDEN_TRUE_FLAGS:
        assert payload[flag] is False
    assert payload["site_material_ids"] == sorted(
        m["site_material_id"] for m in sites["payload"]["materials"]
    )
    assert payload["subject_material_ids"] == sorted(
        m["subject_material_id"] for m in subjects["payload"]["materials"]
    )
    assert payload["checklist_id"] == checklist["payload"]["checklist_id"]
    assert payload["risk_summary"]["high_count"] == 1
    assert sorted(payload["risk_summary"]["risk_ids"]) == ["risk-001"]
    site_item = sites["payload"]["materials"][0]
    subject_item = subjects["payload"]["materials"][0]
    assert site_item["site_material_id"].startswith("smat-")
    assert subject_item["subject_material_id"].startswith("submat-")
    assert subject_item["profile_ref"]["profile_id"] == "prof-SUBJ-001"
    assert subject_item["timeline_ref"]["timeline_id"] == "tl-SUBJ-001"
    assert checklist["payload"]["checklist_id"].startswith("cl-")
    for item in checklist["payload"]["check_items"]:
        assert item["check_id"].startswith("plchk-")
    # Standalone rebuild with same materials yields identical nested IDs.
    rebuilt_sites = mo.build_site_materials_payload(
        run,
        materials=_post_lock_site_materials(),
        population_totals=_post_lock_population_totals(),
        authority_refs=auth,
    )
    assert rebuilt_sites["materials"][0]["site_material_id"] == site_item[
        "site_material_id"
    ]
    assert mo.validate_mode_output(report, run, contract) == ()


def test_post_lock_checklist_coverage_summary_recomputable():
    run, contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    checklist = outputs[3]
    summary = checklist["payload"]["coverage_summary"]
    assert summary == mo.recompute_check_coverage_summary(
        checklist["payload"]["check_items"]
    )
    assert summary["total"] == 3
    assert summary["ready"] == 2
    assert summary["blocked"] == 1
    assert checklist["payload"]["item_count"] == 3
    assert {item["level"] for item in checklist["payload"]["check_items"]} == {
        "project",
        "site",
        "subject",
    }
    assert mo.validate_mode_output(checklist, run, contract) == ()

    tampered = copy.deepcopy(checklist)
    tampered["payload"]["coverage_summary"]["ready"] = 99
    assert mo.AUTHORITY_MISMATCH in mo.validate_mode_output(tampered, run, contract)


def test_post_lock_cross_output_reconciliation_positive():
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    assert mo.validate_post_lock_output_set(*outputs) == ()
    # Bare payloads also reconcile.
    bare = [o["payload"] for o in outputs]
    assert mo.validate_post_lock_output_set(*bare) == ()


def test_build_post_lock_mode_outputs_does_not_mutate_inputs():
    run, contract, ctx = _positive_gate("post_lock_pre_cfdi")
    auth, cov, qc = _refs(run)
    sites = _post_lock_site_materials()
    subjects = _post_lock_subject_materials()
    checks = _post_lock_check_items(run)
    totals = _post_lock_population_totals()
    risk = _post_lock_risk_summary()
    project = _post_lock_project_summary()
    evidence = ["ev-report-001"]
    snap = {
        "sites": copy.deepcopy(sites),
        "subjects": copy.deepcopy(subjects),
        "checks": copy.deepcopy(checks),
        "totals": copy.deepcopy(totals),
        "risk": copy.deepcopy(risk),
        "project": copy.deepcopy(project),
        "evidence": copy.deepcopy(evidence),
        "run": copy.deepcopy(run),
        "auth": copy.deepcopy(auth),
    }
    mo.build_post_lock_mode_outputs(
        run,
        contract,
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        population_totals=totals,
        report_version="v1.0.0-fixed",
        project_summary=project,
        risk_summary=risk,
        evidence_refs=evidence,
        site_materials=sites,
        subject_materials=subjects,
        check_items=checks,
        entry_context=ctx,
    )
    assert sites == snap["sites"]
    assert subjects == snap["subjects"]
    assert checks == snap["checks"]
    assert totals == snap["totals"]
    assert risk == snap["risk"]
    assert project == snap["project"]
    assert evidence == snap["evidence"]
    assert run == snap["run"]
    assert auth == snap["auth"]


def test_post_lock_four_outputs_byte_stable():
    run, contract, ctx = _positive_gate("post_lock_pre_cfdi")
    auth, cov, qc = _refs(run)
    kwargs = dict(
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        population_totals=_post_lock_population_totals(),
        report_version="v1.0.0-fixed",
        project_summary=_post_lock_project_summary(),
        risk_summary=_post_lock_risk_summary(),
        evidence_refs=["ev-report-001"],
        site_materials=_post_lock_site_materials(),
        subject_materials=_post_lock_subject_materials(),
        check_items=_post_lock_check_items(run),
        entry_context=ctx,
    )
    a = mo.build_post_lock_mode_outputs(run, contract, **kwargs)
    b = mo.build_post_lock_mode_outputs(run, contract, **kwargs)
    for left, right in zip(a, b):
        assert canonical_bytes(left) == canonical_bytes(right)
        assert left["output_id"] == right["output_id"]


def test_post_lock_rejects_bool_as_int_population_totals():
    run, _, _ = _positive_gate("post_lock_pre_cfdi")
    auth, _, _ = _refs(run)
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_site_materials_payload(
            run,
            materials=_post_lock_site_materials(),
            population_totals={
                "site_count": True,
                "subject_count": 1,
                "risk_count": 1,
            },
            authority_refs=auth,
        )
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


@pytest.mark.parametrize(
    "totals",
    [
        {"site_count": 2, "subject_count": 1, "risk_count": 1},
        {"site_count": 1, "subject_count": 0, "risk_count": 1},
        {"site_count": 1, "subject_count": 1, "risk_count": 0},
    ],
)
def test_post_lock_population_totals_must_match_materials(totals):
    run, contract, ctx = _positive_gate("post_lock_pre_cfdi")
    auth, cov, qc = _refs(run)
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_post_lock_mode_outputs(
            run,
            contract,
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            population_totals=totals,
            report_version="v1.0.0-fixed",
            project_summary=_post_lock_project_summary(),
            risk_summary=_post_lock_risk_summary(
                high_count=totals["risk_count"],
                risk_ids=["risk-001"][: totals["risk_count"]],
            ),
            evidence_refs=["ev-report-001"],
            site_materials=_post_lock_site_materials(),
            subject_materials=_post_lock_subject_materials(),
            check_items=_post_lock_check_items(run),
            entry_context=ctx,
        )
    assert exc.value.failure_code in {
        mo.AUTHORITY_MISMATCH,
        mo.OUTPUT_NOT_ELIGIBLE,
        mo.IDENTITY_MISMATCH,
    }


def test_post_lock_rejects_stale_nested_identity_reuse():
    run, _, _ = _positive_gate("post_lock_pre_cfdi")
    auth, _, _ = _refs(run)
    forged_site = _post_lock_site_materials()[0]
    forged_site["site_material_id"] = "smat-stale-caller-reuse-001"
    with pytest.raises(mo.ModeOutputError) as site_exc:
        mo.build_site_materials_payload(
            run,
            materials=[forged_site],
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    assert site_exc.value.failure_code == mo.IDENTITY_MISMATCH

    forged_subject = _post_lock_subject_materials()[0]
    forged_subject["subject_material_id"] = "submat-stale-caller-reuse-001"
    with pytest.raises(mo.ModeOutputError) as subject_exc:
        mo.build_subject_materials_payload(
            run,
            materials=[forged_subject],
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    assert subject_exc.value.failure_code == mo.IDENTITY_MISMATCH

    forged_check = _post_lock_check_items(run)[0]
    forged_check["check_id"] = "plchk-stale-caller-reuse-001"
    with pytest.raises(mo.ModeOutputError) as check_exc:
        mo.build_checklist_payload(
            run,
            check_items=[forged_check] + _post_lock_check_items(run)[1:],
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    assert check_exc.value.failure_code == mo.IDENTITY_MISMATCH

    sites = mo.build_site_materials_payload(
        run,
        materials=_post_lock_site_materials(),
        population_totals=_post_lock_population_totals(),
        authority_refs=auth,
    )
    subjects = mo.build_subject_materials_payload(
        run,
        materials=_post_lock_subject_materials(),
        population_totals=_post_lock_population_totals(),
        authority_refs=auth,
    )
    checklist = mo.build_checklist_payload(
        run,
        check_items=_post_lock_check_items(run),
        population_totals=_post_lock_population_totals(),
        authority_refs=auth,
    )
    with pytest.raises(mo.ModeOutputError) as report_exc:
        mo.build_full_project_report_payload(
            run,
            report_version="v1.0.0-fixed",
            project_summary=_post_lock_project_summary(),
            risk_summary=_post_lock_risk_summary(),
            site_material_ids=[m["site_material_id"] for m in sites["materials"]],
            subject_material_ids=[
                m["subject_material_id"] for m in subjects["materials"]
            ],
            checklist_id=checklist["checklist_id"],
            evidence_refs=["ev-report-001"],
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
            report_id="fpr-stale-caller-reuse-001",
        )
    assert report_exc.value.failure_code == mo.IDENTITY_MISMATCH


@pytest.mark.parametrize("meta_key", sorted(mo.POST_LOCK_OVERWRITE_META_KEYS))
def test_post_lock_rejects_overwrite_metadata(meta_key):
    run, _, _ = _positive_gate("post_lock_pre_cfdi")
    auth, _, _ = _refs(run)
    material = _post_lock_site_materials()[0]
    material[meta_key] = "old-output-id-001"
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_site_materials_payload(
            run,
            materials=[material],
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


@pytest.mark.parametrize("status", sorted(mo.CHECK_FORBIDDEN_STATUSES))
def test_post_lock_checklist_rejects_forbidden_status(status):
    run, _, _ = _positive_gate("post_lock_pre_cfdi")
    auth, _, _ = _refs(run)
    items = _post_lock_check_items(run)
    items[0]["status"] = status
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_checklist_payload(
            run,
            check_items=items,
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


def test_post_lock_checklist_coverage_conflict_requires_blocked():
    run, _, _ = _positive_gate("post_lock_pre_cfdi")
    auth, _, _ = _refs(run)
    items = _post_lock_check_items(run)
    items[2]["status"] = "ready"
    items[2]["coverage_missing"] = True
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_checklist_payload(
            run,
            check_items=items,
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


@pytest.mark.parametrize("flag", mo.POST_LOCK_FORBIDDEN_TRUE_FLAGS)
def test_post_lock_report_rejects_true_lifecycle_flags(flag):
    run, contract, auth, cov, qc, outputs = _build_post_lock_four()
    report = copy.deepcopy(outputs[0])
    report["payload"][flag] = True
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        _restamp_output_id(report), run, contract
    )


def test_post_lock_cross_mode_mix_fail_closed():
    daily_run, daily_contract, daily_ctx = _positive_gate("daily")
    post_run, post_contract, post_ctx = _positive_gate("post_lock_pre_cfdi")
    auth, cov, qc = _refs(post_run)
    with pytest.raises(mo.ModeOutputError) as mix_exc:
        mo.build_post_lock_mode_outputs(
            daily_run,
            post_contract,
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            population_totals=_post_lock_population_totals(),
            report_version="v1.0.0-fixed",
            project_summary=_post_lock_project_summary(),
            risk_summary=_post_lock_risk_summary(),
            evidence_refs=["ev-report-001"],
            site_materials=_post_lock_site_materials(),
            subject_materials=_post_lock_subject_materials(),
            check_items=_post_lock_check_items(post_run),
            entry_context=daily_ctx,
        )
    assert mix_exc.value.failure_code in {
        mo.OUTPUT_NOT_ELIGIBLE,
        mo.MODE_ENTRY_BLOCKED,
        mo.IDENTITY_MISMATCH,
    }

    outputs = mo.build_post_lock_mode_outputs(
        post_run,
        post_contract,
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        population_totals=_post_lock_population_totals(),
        report_version="v1.0.0-fixed",
        project_summary=_post_lock_project_summary(),
        risk_summary=_post_lock_risk_summary(),
        evidence_refs=["ev-report-001"],
        site_materials=_post_lock_site_materials(),
        subject_materials=_post_lock_subject_materials(),
        check_items=_post_lock_check_items(post_run),
        entry_context=post_ctx,
    )
    # Built post_lock output cannot validate under a daily contract/run.
    for out in outputs:
        codes = mo.validate_mode_output(out, daily_run, daily_contract)
        assert codes
        assert set(codes) & {
            mo.IDENTITY_MISMATCH,
            mo.OUTPUT_NOT_ELIGIBLE,
            mo.MODE_ENTRY_BLOCKED,
            mo.SILENT_MODE_CONVERSION,
            mo.CUTOFF_MISMATCH,
            mo.REVISION_MISMATCH,
            mo.AUTHORITY_MISMATCH,
        }

    # pre_lock batch builder rejects post_lock run.
    with pytest.raises(mo.ModeOutputError):
        mo.build_pre_lock_mode_outputs(
            post_run,
            mo.build_mode_contract("pre_lock"),
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            risks=[],
            numeric={},
            population_scope="safety",
            from_source_revision_id="run-source-revision-000",
            revision_reason="cross-mode probe",
            impacts=[],
            check_items=[],
            revision_entries=[],
            entry_context=post_ctx,
        )


def test_post_lock_cross_output_identity_and_ref_tamper():
    run, contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    report, sites, subjects, checklist = [copy.deepcopy(o) for o in outputs]

    sites["payload"]["locked_snapshot_hash"] = "snap-tampered"
    assert mo.IDENTITY_MISMATCH in mo.validate_post_lock_output_set(
        report, sites, subjects, checklist
    )

    report2, sites2, subjects2, checklist2 = [copy.deepcopy(o) for o in outputs]
    report2["payload"]["population_totals"]["risk_count"] = 99
    assert mo.AUTHORITY_MISMATCH in mo.validate_post_lock_output_set(
        report2, sites2, subjects2, checklist2
    )

    report3, sites3, subjects3, checklist3 = [copy.deepcopy(o) for o in outputs]
    report3["payload"]["site_material_ids"] = ["smat-not-in-batch"]
    assert mo.AUTHORITY_MISMATCH in mo.validate_post_lock_output_set(
        report3, sites3, subjects3, checklist3
    )

    report4, sites4, subjects4, checklist4 = [copy.deepcopy(o) for o in outputs]
    report4["payload"]["checklist_id"] = "cl-not-matching"
    assert mo.IDENTITY_MISMATCH in mo.validate_post_lock_output_set(
        report4, sites4, subjects4, checklist4
    )

    report5, sites5, subjects5, checklist5 = [copy.deepcopy(o) for o in outputs]
    subjects5["payload"]["materials"][0]["site_id"] = "SITE-UNKNOWN"
    assert mo.AUTHORITY_MISMATCH in mo.validate_post_lock_output_set(
        report5, sites5, subjects5, checklist5
    )


@pytest.mark.parametrize(
    "kind,mutate",
    [
        (
            "full_project_report",
            lambda p: p.__setitem__("locked_snapshot_hash", "snap-drift"),
        ),
        (
            "site_materials",
            lambda p: p.__setitem__("acceptance_evidence_hash", "accept-drift"),
        ),
        (
            "subject_materials",
            lambda p: p.__setitem__("authority_digest", "auth-drift"),
        ),
        (
            "checklist",
            lambda p: p.__setitem__("fixed_total", False),
        ),
    ],
)
def test_nested_post_lock_payload_tamper_fails_after_outer_id_restamp(kind, mutate):
    run, contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    by_kind = {o["output_kind"]: o for o in outputs}
    tampered = copy.deepcopy(by_kind[kind])
    mutate(tampered["payload"])
    restamped = _restamp_output_id(tampered)
    codes = mo.validate_mode_output(restamped, run, contract)
    assert codes
    assert set(codes) & {
        mo.IDENTITY_MISMATCH,
        mo.AUTHORITY_MISMATCH,
        mo.OUTPUT_NOT_ELIGIBLE,
        mo.CUTOFF_MISMATCH,
        mo.REVISION_MISMATCH,
    }


@pytest.mark.parametrize(
    "field,code",
    [
        ("data_cutoff", mo.CUTOFF_MISMATCH),
        ("source_revision_id", mo.REVISION_MISMATCH),
        ("authority_digest", mo.AUTHORITY_MISMATCH),
        ("project_id", mo.IDENTITY_MISMATCH),
        ("run_id", mo.IDENTITY_MISMATCH),
    ],
)
def test_post_lock_payload_binding_mandatory_after_outer_id_restamp(field, code):
    run, contract, auth, cov, qc, outputs = _build_post_lock_four()
    out = copy.deepcopy(outputs[1])  # site_materials
    if field == "authority_digest":
        out["payload"][field] = "auth-digest-tampered"
    elif field == "data_cutoff":
        out["payload"][field] = "cutoff-tampered"
    elif field == "source_revision_id":
        out["payload"][field] = "revision-tampered"
    else:
        out["payload"][field] = f"{field}-tampered"
    assert code in mo.validate_mode_output(_restamp_output_id(out), run, contract)


def test_post_lock_risk_summary_must_reconcile_totals():
    run, _, _ = _positive_gate("post_lock_pre_cfdi")
    auth, _, _ = _refs(run)
    sites = mo.build_site_materials_payload(
        run,
        materials=_post_lock_site_materials(),
        population_totals=_post_lock_population_totals(),
        authority_refs=auth,
    )
    subjects = mo.build_subject_materials_payload(
        run,
        materials=_post_lock_subject_materials(),
        population_totals=_post_lock_population_totals(),
        authority_refs=auth,
    )
    checklist = mo.build_checklist_payload(
        run,
        check_items=_post_lock_check_items(run),
        population_totals=_post_lock_population_totals(),
        authority_refs=auth,
    )
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_full_project_report_payload(
            run,
            report_version="v1.0.0-fixed",
            project_summary=_post_lock_project_summary(),
            risk_summary={
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "risk_ids": [],
            },
            site_material_ids=[m["site_material_id"] for m in sites["materials"]],
            subject_material_ids=[
                m["subject_material_id"] for m in subjects["materials"]
            ],
            checklist_id=checklist["checklist_id"],
            evidence_refs=["ev-report-001"],
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    assert exc.value.failure_code == mo.AUTHORITY_MISMATCH


def test_standalone_post_lock_builders_require_post_lock_run():
    daily_run, _, _ = _positive_gate("daily")
    auth, _, _ = _refs(daily_run)
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_site_materials_payload(
            daily_run,
            materials=[],
            population_totals={"site_count": 0, "subject_count": 0, "risk_count": 0},
            authority_refs=auth,
        )
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


def test_post_lock_negative_builders_do_not_mutate_inputs():
    run, _, _ = _positive_gate("post_lock_pre_cfdi")
    auth, _, _ = _refs(run)
    sites = _post_lock_site_materials()
    subjects = _post_lock_subject_materials()
    checks = _post_lock_check_items(run)
    snap_sites = copy.deepcopy(sites)
    snap_subjects = copy.deepcopy(subjects)
    snap_checks = copy.deepcopy(checks)
    forged = copy.deepcopy(sites[0])
    forged["site_material_id"] = "smat-bad"
    with pytest.raises(mo.ModeOutputError):
        mo.build_site_materials_payload(
            run,
            materials=[forged],
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    with pytest.raises(mo.ModeOutputError):
        mo.build_subject_materials_payload(
            run,
            materials=[
                {
                    **subjects[0],
                    "subject_material_id": "submat-bad",
                }
            ],
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    bad_checks = copy.deepcopy(checks)
    bad_checks[0]["status"] = "completed"
    with pytest.raises(mo.ModeOutputError):
        mo.build_checklist_payload(
            run,
            check_items=bad_checks,
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    assert sites == snap_sites
    assert subjects == snap_subjects
    assert checks == snap_checks


@pytest.mark.parametrize(
    "builder,kwargs",
    [
        (
            mo.build_site_materials_payload,
            {
                "materials": None,
                "population_totals": {
                    "site_count": 0,
                    "subject_count": 0,
                    "risk_count": 0,
                },
            },
        ),
        (
            mo.build_subject_materials_payload,
            {
                "materials": None,
                "population_totals": {
                    "site_count": 0,
                    "subject_count": 0,
                    "risk_count": 0,
                },
            },
        ),
        (
            mo.build_checklist_payload,
            {
                "check_items": [
                    {
                        "level": "project",
                        "check_kind": "project_lock",
                        "scope_id": "project-r6-synthetic",
                        "status": "ready",
                        "risk_ids": [],
                        "evidence_refs": ["ev"],
                        "locator": {"path": "X", "record_id": "1"},
                    },
                    {
                        "level": "site",
                        "check_kind": "site_coverage",
                        "scope_id": "SITE-01",
                        "status": "ready",
                        "risk_ids": [],
                        "evidence_refs": ["ev"],
                        "locator": {"path": "Y", "record_id": "2"},
                    },
                    {
                        "level": "subject",
                        "check_kind": "subject_profile",
                        "scope_id": "SUBJ-001",
                        "status": "ready",
                        "risk_ids": [],
                        "evidence_refs": ["ev"],
                        "locator": {"path": "Z", "record_id": "3"},
                    },
                ],
                "population_totals": {
                    "site_count": 0,
                    "subject_count": 0,
                    "risk_count": 0,
                },
            },
        ),
    ],
)
def test_post_lock_standalone_builders_require_authority_digest(builder, kwargs):
    run, _, _ = _positive_gate("post_lock_pre_cfdi")
    with pytest.raises(mo.ModeOutputError):
        builder(run, authority_refs={"project_id": run["project_id"]}, **kwargs)


# ---------------------------------------------------------------------------
# Slice-06 worker_02 follow-up — Codex probe regressions (worker_01 closures)
# ---------------------------------------------------------------------------


def test_post_lock_reconcile_rejects_site_declared_ghost_subject():
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    report, sites, subjects, checklist = [copy.deepcopy(o) for o in outputs]
    sites["payload"]["materials"][0]["subject_ids"] = ["SUBJ-001", "SUBJ-GHOST"]
    assert mo.AUTHORITY_MISMATCH in mo.validate_post_lock_output_set(
        report, sites, subjects, checklist
    )


def test_post_lock_reconcile_rejects_checklist_only_risk_when_report_risks_empty():
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    report, sites, subjects, checklist = [copy.deepcopy(o) for o in outputs]
    for out in (report, sites, subjects, checklist):
        out["payload"]["population_totals"] = {
            "site_count": 1,
            "subject_count": 1,
            "risk_count": 0,
        }
    report["payload"]["risk_summary"] = {
        "high_count": 0,
        "medium_count": 0,
        "low_count": 0,
        "risk_ids": [],
    }
    sites["payload"]["materials"][0]["risk_ids"] = []
    subjects["payload"]["materials"][0]["risk_ids"] = []
    checklist["payload"]["check_items"][0]["risk_ids"] = ["risk-checklist-only"]
    assert mo.AUTHORITY_MISMATCH in mo.validate_post_lock_output_set(
        report, sites, subjects, checklist
    )


@pytest.mark.parametrize(
    "kind",
    ["site_materials", "subject_materials", "checklist"],
)
def test_post_lock_restamped_non_report_rejects_confirmed_and_external_identity(kind):
    run, contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    by_kind = {o["output_kind"]: o for o in outputs}
    tampered = copy.deepcopy(by_kind[kind])
    tampered["payload"]["is_user_confirmed"] = True
    tampered["payload"]["report_lineage_id"] = "ext-lineage-forbidden"
    codes = mo.validate_mode_output(_restamp_output_id(tampered), run, contract)
    assert mo.OUTPUT_NOT_ELIGIBLE in codes
    assert mo.AUTHORITY_MISMATCH in codes


@pytest.mark.parametrize(
    "summary,code",
    [
        ({"title": "t", "site_count": 9}, mo.AUTHORITY_MISMATCH),
        ({"title": "t", "subject_count": True}, mo.OUTPUT_NOT_ELIGIBLE),
        ({"title": "t", "risk_count": -1}, mo.OUTPUT_NOT_ELIGIBLE),
    ],
)
def test_post_lock_project_summary_count_drift_bool_negative_rejected(summary, code):
    run, _, auth, _cov, _qc, outputs = _build_post_lock_four()
    sites, subjects, checklist = outputs[1], outputs[2], outputs[3]
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_full_project_report_payload(
            run,
            report_version="v1.0.0-fixed",
            project_summary=summary,
            risk_summary=_post_lock_risk_summary(),
            site_material_ids=[
                m["site_material_id"] for m in sites["payload"]["materials"]
            ],
            subject_material_ids=[
                m["subject_material_id"] for m in subjects["payload"]["materials"]
            ],
            checklist_id=checklist["payload"]["checklist_id"],
            evidence_refs=["ev-report-001"],
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    assert exc.value.failure_code == code


def test_post_lock_project_summary_matching_counts_pass():
    run, contract, auth, cov, qc, outputs = _build_post_lock_four(
        project_summary={
            "title": "synthetic post-lock draft",
            "status": "locked_fixed_total",
            "site_count": 1,
            "subject_count": 1,
            "risk_count": 1,
        }
    )
    report = outputs[0]
    assert report["payload"]["project_summary"]["site_count"] == 1
    assert report["payload"]["project_summary"]["subject_count"] == 1
    assert report["payload"]["project_summary"]["risk_count"] == 1
    assert mo.validate_mode_output(report, run, contract) == ()
    assert mo.validate_post_lock_output_set(*outputs) == ()


def test_post_lock_reversed_evidence_refs_yield_identical_nested_ids_and_bytes():
    run, _, _ = _positive_gate("post_lock_pre_cfdi")
    auth, _, _ = _refs(run)
    totals = _post_lock_population_totals()
    forward = {
        "site_id": "SITE-01",
        "subject_ids": ["SUBJ-001"],
        "risk_ids": ["risk-001"],
        "evidence_refs": ["ev-a", "ev-b"],
        "locator": {"path": "SITE.SITE-01", "record_id": "site-01"},
    }
    reversed_refs = {
        **forward,
        "evidence_refs": ["ev-b", "ev-a"],
    }
    a = mo.build_site_materials_payload(
        run, materials=[forward], population_totals=totals, authority_refs=auth
    )
    b = mo.build_site_materials_payload(
        run, materials=[reversed_refs], population_totals=totals, authority_refs=auth
    )
    assert a["materials"][0]["site_material_id"] == b["materials"][0]["site_material_id"]
    assert a["materials"][0]["evidence_refs"] == b["materials"][0]["evidence_refs"]
    assert canonical_bytes(a) == canonical_bytes(b)


# Second source correction (worker_01): newly expanded aliases / envelope / Profile bind.
_NEW_POST_LOCK_TRUE_ALIASES = (
    "user_confirmed",
    "signed",
    "sent",
    "is_closed",
    "pd_registered",
    "pd_closed",
    "is_pd_recorded",
    "is_pd_closed",
)
_NON_REPORT_POST_LOCK_KINDS = ("site_materials", "subject_materials", "checklist")


@pytest.mark.parametrize("kind", _NON_REPORT_POST_LOCK_KINDS)
@pytest.mark.parametrize(
    "field,value",
    [(flag, True) for flag in _NEW_POST_LOCK_TRUE_ALIASES]
    + [(key, "forbidden-value") for key in sorted(mo.POST_LOCK_FORBIDDEN_WORKFLOW_KEYS)],
)
def test_post_lock_restamped_non_report_rejects_new_lifecycle_pd_workflow_keys(
    kind, field, value
):
    run, contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    by_kind = {o["output_kind"]: o for o in outputs}
    tampered = copy.deepcopy(by_kind[kind])
    tampered["payload"][field] = value
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        _restamp_output_id(tampered), run, contract
    )


def test_validate_post_lock_rejects_outer_inner_kind_mismatch_keeps_bare_ok():
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    bare = [o["payload"] for o in outputs]
    assert mo.validate_post_lock_output_set(*bare) == ()

    mismatched = [copy.deepcopy(o) for o in outputs]
    mismatched[1]["output_kind"] = "checklist"  # outer wrong; inner remains site_materials
    assert mismatched[1]["payload"]["output_kind"] == "site_materials"
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_post_lock_output_set(*mismatched)


def test_post_lock_subject_materials_bind_profile_timeline_subject_id():
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    item = outputs[2]["payload"]["materials"][0]
    assert item["profile_ref"]["subject_id"] == item["subject_id"]
    assert item["timeline_ref"]["subject_id"] == item["subject_id"]


@pytest.mark.parametrize("ref_field", ["profile_ref", "timeline_ref"])
def test_post_lock_rejects_cross_subject_profile_or_timeline_ref(ref_field):
    run, _, _ = _positive_gate("post_lock_pre_cfdi")
    auth, _, _ = _refs(run)
    material = _post_lock_subject_materials()[0]
    material[ref_field] = {
        **material[ref_field],
        "subject_id": "SUBJ-OTHER",
    }
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_subject_materials_payload(
            run,
            materials=[material],
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    assert exc.value.failure_code == mo.IDENTITY_MISMATCH


@pytest.mark.parametrize("ref_field", ["profile_ref", "timeline_ref"])
def test_post_lock_missing_profile_timeline_subject_bind_fails_after_restamp(ref_field):
    run, contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    tampered = copy.deepcopy(outputs[2])
    del tampered["payload"]["materials"][0][ref_field]["subject_id"]
    codes = mo.validate_mode_output(_restamp_output_id(tampered), run, contract)
    assert mo.IDENTITY_MISMATCH in codes


# ---------------------------------------------------------------------------
# Slice-06 worker_02 follow-up 3 — conference R1 accepted repairs
# ---------------------------------------------------------------------------

# Representative Grok envelope restamp matrix (true / non-false / non-empty).
_ENVELOPE_CLAIM_MATRIX = (
    ("is_signed", True, mo.OUTPUT_NOT_ELIGIBLE),
    ("is_sent", True, mo.OUTPUT_NOT_ELIGIBLE),
    ("pd_registered", True, mo.OUTPUT_NOT_ELIGIBLE),
    ("is_user_confirmed", 1, mo.OUTPUT_NOT_ELIGIBLE),  # non-false int
    ("sent_at", "2026-08-28T00:00:00Z", mo.OUTPUT_NOT_ELIGIBLE),
    ("pd_record_id", "pd-001", mo.OUTPUT_NOT_ELIGIBLE),
    ("overwrites_output_id", "old-output-id", mo.OUTPUT_NOT_ELIGIBLE),
    ("report_lineage_id", "ext-lineage", mo.AUTHORITY_MISMATCH),
)


@pytest.mark.parametrize("field,value,code", _ENVELOPE_CLAIM_MATRIX)
def test_post_lock_envelope_restamp_rejects_lifecycle_pd_workflow_overwrite_external(
    field, value, code
):
    run, contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    tampered = copy.deepcopy(outputs[1])  # site_materials envelope
    tampered[field] = value
    assert code in mo.validate_mode_output(_restamp_output_id(tampered), run, contract)


def test_post_lock_envelope_allows_explicit_false_and_empty_claim_keys():
    run, contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    allowed = copy.deepcopy(outputs[1])
    allowed["is_signed"] = False
    allowed["is_sent"] = False
    allowed["sent_at"] = ""
    allowed["overwrites_output_id"] = None
    allowed["pd_record_id"] = False
    assert mo.validate_mode_output(_restamp_output_id(allowed), run, contract) == ()


def test_post_lock_build_mode_output_rejects_envelope_claim_on_spec():
    run, contract, ctx = _positive_gate("post_lock_pre_cfdi")
    auth, cov, qc = _refs(run)
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_output(
            run,
            contract,
            _spec(
                "site_materials",
                population_totals=_post_lock_population_totals(),
                materials=_post_lock_site_materials(),
                is_signed=True,
            ),
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


def test_post_lock_check_id_includes_coverage_and_evidence_flags():
    base = {
        "level": "subject",
        "check_kind": "subject_profile",
        "scope_id": "SUBJ-001",
        "status": "blocked",
        "risk_ids": [],
        "evidence_refs": ["ev-chk-subject"],
        "locator": {"path": "CHK.SUBJ", "record_id": "chk-u1"},
        "coverage_missing": True,
        "evidence_conflict": False,
    }
    flipped_coverage = {**base, "coverage_missing": False, "evidence_conflict": False}
    flipped_conflict = {**base, "coverage_missing": True, "evidence_conflict": True}
    id_base = mo._post_lock_check_id(base)
    assert id_base != mo._post_lock_check_id(flipped_coverage)
    assert id_base != mo._post_lock_check_id(flipped_conflict)


def test_post_lock_stale_check_id_after_flag_flip_fails_validation():
    run, contract, ctx = _positive_gate("post_lock_pre_cfdi")
    auth, cov, qc = _refs(run)
    items = _post_lock_check_items(run)
    # Force blocked + coverage_missing on subject item for a stable baseline id.
    items[2] = {
        **items[2],
        "status": "blocked",
        "coverage_missing": True,
        "evidence_conflict": False,
    }
    out = mo.build_mode_output(
        run,
        contract,
        _spec(
            "checklist",
            population_totals=_post_lock_population_totals(),
            check_items=items,
        ),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    stale_id = out["payload"]["check_items"][2]["check_id"]
    tampered = copy.deepcopy(out)
    tampered["payload"]["check_items"][2]["evidence_conflict"] = True
    tampered["payload"]["check_items"][2]["check_id"] = stale_id
    tampered["payload"]["coverage_summary"] = mo.recompute_check_coverage_summary(
        tampered["payload"]["check_items"]
    )
    assert mo.IDENTITY_MISMATCH in mo.validate_mode_output(
        _restamp_output_id(tampered), run, contract
    )


@pytest.mark.parametrize("ref_field,primary_key", [
    ("profile_ref", "profile_id"),
    ("timeline_ref", "timeline_id"),
])
def test_post_lock_dual_primary_ref_conflict_or_empty_rejected(ref_field, primary_key):
    run, _, _ = _positive_gate("post_lock_pre_cfdi")
    auth, _, _ = _refs(run)
    material = _post_lock_subject_materials()[0]
    conflicting = copy.deepcopy(material)
    conflicting[ref_field] = {
        primary_key: "id-a",
        "ref": "id-b",
        "subject_id": "SUBJ-001",
    }
    with pytest.raises(mo.ModeOutputError) as conflict_exc:
        mo.build_subject_materials_payload(
            run,
            materials=[conflicting],
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    assert conflict_exc.value.failure_code == mo.IDENTITY_MISMATCH

    empty_dual = copy.deepcopy(material)
    empty_dual[ref_field] = {
        primary_key: "",
        "ref": "",
        "subject_id": "SUBJ-001",
    }
    with pytest.raises(mo.ModeOutputError) as empty_exc:
        mo.build_subject_materials_payload(
            run,
            materials=[empty_dual],
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    assert empty_exc.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


@pytest.mark.parametrize(
    "ref_field,primary_key,primary_value,ref_value",
    [
        ("profile_ref", "profile_id", "", "prof-only-ref"),
        ("profile_ref", "profile_id", "prof-only-primary", ""),
        ("timeline_ref", "timeline_id", "", "tl-only-ref"),
        ("timeline_ref", "timeline_id", "tl-only-primary", ""),
    ],
)
def test_post_lock_dual_keys_reject_one_empty_one_nonempty(
    ref_field, primary_key, primary_value, ref_value
):
    """Both dual keys present: empty+non-empty rejected in either direction."""
    run, _, _ = _positive_gate("post_lock_pre_cfdi")
    auth, _, _ = _refs(run)
    material = copy.deepcopy(_post_lock_subject_materials()[0])
    material[ref_field] = {
        primary_key: primary_value,
        "ref": ref_value,
        "subject_id": "SUBJ-001",
    }
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_subject_materials_payload(
            run,
            materials=[material],
            population_totals=_post_lock_population_totals(),
            authority_refs=auth,
        )
    assert exc.value.failure_code == mo.IDENTITY_MISMATCH


def test_post_lock_dual_primary_ref_equal_with_subject_bind_passes():
    run, _, _ = _positive_gate("post_lock_pre_cfdi")
    auth, _, _ = _refs(run)
    material = {
        **_post_lock_subject_materials()[0],
        "profile_ref": {
            "profile_id": "prof-SUBJ-001",
            "ref": "prof-SUBJ-001",
            "subject_id": "SUBJ-001",
        },
        "timeline_ref": {
            "timeline_id": "tl-SUBJ-001",
            "ref": "tl-SUBJ-001",
            "subject_id": "SUBJ-001",
        },
    }
    payload = mo.build_subject_materials_payload(
        run,
        materials=[material],
        population_totals=_post_lock_population_totals(),
        authority_refs=auth,
    )
    item = payload["materials"][0]
    assert item["profile_ref"]["profile_id"] == item["profile_ref"]["ref"]
    assert item["timeline_ref"]["timeline_id"] == item["timeline_ref"]["ref"]
    assert item["profile_ref"]["subject_id"] == "SUBJ-001"
    assert item["timeline_ref"]["subject_id"] == "SUBJ-001"


def _bare_post_lock_set(outputs):
    return [copy.deepcopy(o["payload"]) for o in outputs]


def test_validate_post_lock_set_rejects_duplicate_site_and_subject_identity():
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    report, sites, subjects, checklist = _bare_post_lock_set(outputs)

    dup_sites = copy.deepcopy(sites)
    dup_sites["materials"] = [
        copy.deepcopy(sites["materials"][0]),
        copy.deepcopy(sites["materials"][0]),
    ]
    dup_sites["material_count"] = 2
    for payload in (report, dup_sites, subjects, checklist):
        payload["population_totals"] = {
            "site_count": 2,
            "subject_count": 1,
            "risk_count": 1,
        }
    report["site_material_ids"] = [
        dup_sites["materials"][0]["site_material_id"],
        dup_sites["materials"][0]["site_material_id"],
    ]
    assert mo.IDENTITY_MISMATCH in mo.validate_post_lock_output_set(
        report, dup_sites, subjects, checklist
    )

    report2, sites2, subjects2, checklist2 = _bare_post_lock_set(outputs)
    dup_subjects = copy.deepcopy(subjects2)
    dup_subjects["materials"] = [
        copy.deepcopy(subjects2["materials"][0]),
        copy.deepcopy(subjects2["materials"][0]),
    ]
    dup_subjects["material_count"] = 2
    for payload in (report2, sites2, dup_subjects, checklist2):
        payload["population_totals"] = {
            "site_count": 1,
            "subject_count": 2,
            "risk_count": 1,
        }
    report2["subject_material_ids"] = [
        dup_subjects["materials"][0]["subject_material_id"],
        dup_subjects["materials"][0]["subject_material_id"],
    ]
    assert mo.IDENTITY_MISMATCH in mo.validate_post_lock_output_set(
        report2, sites2, dup_subjects, checklist2
    )


def test_validate_post_lock_set_rejects_totals_and_count_drift():
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    report, sites, subjects, checklist = _bare_post_lock_set(outputs)

    drifted = [copy.deepcopy(p) for p in (report, sites, subjects, checklist)]
    for payload in drifted:
        payload["population_totals"] = {
            "site_count": 2,
            "subject_count": 1,
            "risk_count": 1,
        }
    assert mo.AUTHORITY_MISMATCH in mo.validate_post_lock_output_set(*drifted)

    report2, sites2, subjects2, checklist2 = _bare_post_lock_set(outputs)
    sites2["material_count"] = 99
    assert mo.AUTHORITY_MISMATCH in mo.validate_post_lock_output_set(
        report2, sites2, subjects2, checklist2
    )

    report3, sites3, subjects3, checklist3 = _bare_post_lock_set(outputs)
    checklist3["item_count"] = 0
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_post_lock_output_set(
        report3, sites3, subjects3, checklist3
    )


def test_validate_post_lock_set_rejects_wrong_project_scope_and_missing_report_fields():
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    report, sites, subjects, checklist = _bare_post_lock_set(outputs)

    bad_scope = copy.deepcopy(checklist)
    for item in bad_scope["check_items"]:
        if item["level"] == "project":
            item["scope_id"] = "not-the-project"
    assert mo.validate_post_lock_output_set(report, sites, subjects, bad_scope)

    missing = copy.deepcopy(report)
    del missing["report_version"]
    assert mo.validate_post_lock_output_set(missing, sites, subjects, checklist)


def test_validate_post_lock_set_rejects_missing_or_cross_profile_timeline_bind():
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    report, sites, subjects, checklist = _bare_post_lock_set(outputs)

    missing = copy.deepcopy(subjects)
    del missing["materials"][0]["profile_ref"]["subject_id"]
    assert mo.IDENTITY_MISMATCH in mo.validate_post_lock_output_set(
        report, sites, missing, checklist
    )

    crossed = copy.deepcopy(subjects)
    crossed["materials"][0]["timeline_ref"]["subject_id"] = "SUBJ-OTHER"
    assert mo.IDENTITY_MISMATCH in mo.validate_post_lock_output_set(
        report, sites, crossed, checklist
    )


def test_post_lock_site_only_risk_and_exported_state_and_three_key_totals_ok():
    """Codex R1 decisions: site-only risk OK; exported OK; extras outside 3-key projection."""
    run, contract, ctx = _positive_gate("post_lock_pre_cfdi")
    auth, cov, qc = _refs(run)
    site_materials = [
        {
            "site_id": "SITE-01",
            "subject_ids": ["SUBJ-001"],
            "risk_ids": ["risk-001"],
            "evidence_refs": ["ev-site-001"],
            "locator": {"path": "SITE.SITE-01", "record_id": "site-01"},
        }
    ]
    subject_materials = [
        {
            "subject_id": "SUBJ-001",
            "site_id": "SITE-01",
            "profile_ref": {"profile_id": "prof-SUBJ-001"},
            "timeline_ref": {"timeline_id": "tl-SUBJ-001"},
            "risk_ids": [],
            "evidence_refs": ["ev-subj-001"],
            "locator": {"path": "SUBJ.SUBJ-001", "record_id": "subj-001"},
        }
    ]
    outputs = mo.build_post_lock_mode_outputs(
        run,
        contract,
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        population_totals={
            "site_count": 1,
            "subject_count": 1,
            "risk_count": 1,
            "event_count": 99,  # extra dropped from canonical projection
        },
        report_version="v1.0.0-fixed",
        project_summary=_post_lock_project_summary(),
        risk_summary=_post_lock_risk_summary(),
        evidence_refs=["ev-report-001"],
        site_materials=site_materials,
        subject_materials=subject_materials,
        check_items=_post_lock_check_items(run),
        entry_context=ctx,
    )
    assert mo.validate_post_lock_output_set(*outputs) == ()
    for out in outputs:
        assert set(out["payload"]["population_totals"]) == {
            "site_count",
            "subject_count",
            "risk_count",
        }
        out["output_state"] = "exported"
        assert mo.validate_mode_output(_restamp_output_id(out), run, contract) == ()


# ---------------------------------------------------------------------------
# Slice-06 worker_02 follow-up 5 — conference R2 envelope identity set-gate
# ---------------------------------------------------------------------------

_ENVELOPE_IDENTITY_TAMPERS = (
    ("project_id", "project-OTHER", mo.IDENTITY_MISMATCH),
    ("run_id", "run-OTHER", mo.IDENTITY_MISMATCH),
    ("mode", "daily", mo.IDENTITY_MISMATCH),
    ("execution_basis", "incremental", mo.IDENTITY_MISMATCH),
    ("data_cutoff", "cutoff-OTHER", mo.CUTOFF_MISMATCH),
    ("source_revision_id", "revision-OTHER", mo.REVISION_MISMATCH),
    ("identity_algorithm_digest", "digest-OTHER", mo.IDENTITY_MISMATCH),
)


def _assert_codes_include(codes, *expected):
    """Assert canonical failure categories without overfitting tuple order."""
    observed = set(codes)
    for code in expected:
        assert code in observed, f"missing {code!r} in {codes!r}"


@pytest.mark.parametrize("field,value,code", _ENVELOPE_IDENTITY_TAMPERS)
def test_validate_post_lock_set_rejects_restamped_envelope_identity_field(
    field, value, code
):
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    set4 = [copy.deepcopy(o) for o in outputs]
    set4[1][field] = value
    set4[1] = _restamp_output_id(set4[1])
    _assert_codes_include(mo.validate_post_lock_output_set(*set4), code)


def test_validate_post_lock_set_rejects_four_wrappers_drifting_together():
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    set4 = [copy.deepcopy(o) for o in outputs]
    for env in set4:
        env["project_id"] = "project-DRIFT-TOGETHER"
        env["mode"] = "daily"
    set4 = [_restamp_output_id(env) for env in set4]
    _assert_codes_include(
        mo.validate_post_lock_output_set(*set4), mo.IDENTITY_MISMATCH
    )


def test_validate_post_lock_set_rejects_wrappers_drifting_differently():
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    set4 = [copy.deepcopy(o) for o in outputs]
    for idx, env in enumerate(set4):
        env["project_id"] = f"project-DIFF-{idx}"
    set4 = [_restamp_output_id(env) for env in set4]
    _assert_codes_include(
        mo.validate_post_lock_output_set(*set4), mo.IDENTITY_MISMATCH
    )


@pytest.mark.parametrize(
    "ref_key,mutate",
    [
        (
            "authority_refs",
            lambda refs: {**refs, "project_id": "project-OTHER"},
        ),
        (
            "coverage_refs",
            lambda refs: {**refs, "project_id": "project-OTHER"},
        ),
        (
            "qc_refs",
            lambda refs: {**refs, "project_id": "project-OTHER"},
        ),
    ],
)
def test_validate_post_lock_set_rejects_invalid_authority_coverage_qc_refs(
    ref_key, mutate
):
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    set4 = [copy.deepcopy(o) for o in outputs]
    set4[1][ref_key] = mutate(set4[1][ref_key])
    set4[1] = _restamp_output_id(set4[1])
    _assert_codes_include(
        mo.validate_post_lock_output_set(*set4), mo.AUTHORITY_MISMATCH
    )


def test_validate_post_lock_set_rejects_stale_outer_output_id():
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    set4 = [copy.deepcopy(o) for o in outputs]
    set4[1]["output_id"] = "out-stale-noncanonical"
    _assert_codes_include(
        mo.validate_post_lock_output_set(*set4), mo.IDENTITY_MISMATCH
    )


def test_validate_post_lock_set_accepts_all_envelope_bare_and_mixed():
    _run, _contract, _auth, _cov, _qc, outputs = _build_post_lock_four()
    assert mo.validate_post_lock_output_set(*outputs) == ()
    bare = [o["payload"] for o in outputs]
    assert mo.validate_post_lock_output_set(*bare) == ()
    mixed = [outputs[0], bare[1], outputs[2], bare[3]]
    assert mo.validate_post_lock_output_set(*mixed) == ()


# ---------------------------------------------------------------------------
# worker_03 independent verification gates
# ---------------------------------------------------------------------------

import hashlib
import json
import os
import re
import socket
import stat
import subprocess
import sys

from mm_r6 import fixtures, validator

WORKBENCH_ROOT = contracts.WORKBENCH_ROOT

REQUIRED_MODE_OUTPUT_APIS = (
    "build_mode_contract",
    "build_all_mode_contracts",
    "validate_mode_contract",
    "mode_contract_digest",
    "validate_run_mode_gate",
    "default_entry_context_for_mode",
    "build_mode_output",
    "build_daily_mode_outputs",
    "build_pre_lock_mode_outputs",
    "build_full_risk_payload",
    "build_revision_impact_payload",
    "build_check_package_payload",
    "build_query_revision_package_payload",
    "recompute_check_coverage_summary",
    "build_affected_query_draft",
    "project_query_display_text",
    "validate_mode_output",
    "default_output_eligibility",
    "POST_LOCK_OUTPUT_KINDS",
    "build_post_lock_mode_outputs",
    "build_full_project_report_payload",
    "build_site_materials_payload",
    "build_subject_materials_payload",
    "build_checklist_payload",
    "validate_post_lock_output_set",
)

SLICE04_CREATE_ONLY_RELATIVE = frozenset(
    {
        "src/mm_r6/__init__.py",
        "src/mm_r6/contracts.py",
        "src/mm_r6/fixtures.py",
        "src/mm_r6/validator.py",
        "src/mm_r6/report_review.py",
        "src/mm_r6/report_bundle.py",
        "src/mm_r6/mode_output.py",
        "src/mm_r6/agent_harness.py",
        "tests/conftest.py",
        "tests/test_contracts.py",
        "tests/test_validator.py",
        "tests/test_challenge_matrix.py",
        "tests/test_report_review.py",
        "tests/test_report_bundle.py",
        "tests/test_mode_output.py",
        "tests/test_agent_harness.py",
        "evidence/r6_contract_runtime_receipt.json",
        "evidence/r6_report_review_runtime_receipt.json",
        "evidence/r6_report_bundle_runtime_receipt.json",
        "evidence/r6_mode_output_runtime_receipt.json",
        "evidence/r6_pre_lock_output_runtime_receipt.json",
        "evidence/r6_post_lock_output_runtime_receipt.json",
        "evidence/r6_agent_harness_runtime_receipt.json",
        "README.md",
    }
)

MEDICAL_WRITING_ROOTS = ("deploy", "frontend", "packages", "runtime", "services")
MEDICAL_WRITING_PATTERN = re.compile(r"medical[-_]writing")
EXPECTED_MEDICAL_WRITING_COUNT = 445
EXPECTED_MEDICAL_WRITING_AGGREGATE = (
    "59dd4628eeedd376ab60e54806d0b9eeb3486ba444b5316fcfef8f9829863299"
)
EXPECTED_CONTRACT_SHA = contracts.ACCEPTED_CONTRACT_SHA256
EXPECTED_MATRIX_SHA = contracts.ACCEPTED_MATRIX_SHA256
EXPECTED_PROSE_SHA = contracts.ACCEPTED_PROSE_SHA256
EXPECTED_SLICE01_SRC = {
    "src/mm_r6/contracts.py": (
        "f5ce93629bd008d438095fd9b23ab1f335b951087bf916b85ac990a350e8fcfa"
    ),
    "src/mm_r6/fixtures.py": (
        "e8064ad358e0a215d6b428bc1c48e97a4ef55a20131261e5b6a9c21eac44e56c"
    ),
    "src/mm_r6/validator.py": (
        "8c9bb8c60c64c1a102d37f5e4e49263844061fd5b37cce01060bbd4133d891d0"
    ),
}
PROTECTED_PORTS = (8911, 5174)
FROZEN_MODE_OUTPUT_CODES = (
    mo.MODE_ENTRY_BLOCKED,
    mo.SILENT_MODE_CONVERSION,
    mo.OUTPUT_NOT_ELIGIBLE,
    mo.AUTHORITY_MISMATCH,
    mo.IDENTITY_MISMATCH,
    mo.CUTOFF_MISMATCH,
    mo.REVISION_MISMATCH,
)


def _poc_files() -> set:
    found = set()
    for path in POC_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(POC_ROOT).as_posix()
        if "__pycache__" in rel.split("/") or ".pytest_cache" in rel.split("/"):
            continue
        if rel.endswith(".pyc"):
            continue
        found.add(rel)
    return found


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _medical_writing_boundary(root: Path) -> dict:
    matched = {}
    errors = []
    for root_relative in MEDICAL_WRITING_ROOTS:
        base = root / root_relative
        if not base.is_dir():
            errors.append(f"MISSING_MEDICAL_WRITING_ROOT:{root_relative}")
            continue
        for directory, dirnames, filenames in os.walk(
            base, topdown=True, followlinks=False
        ):
            dirnames.sort()
            filenames.sort()
            for filename in filenames:
                path = Path(directory) / filename
                relative = path.relative_to(root).as_posix()
                if MEDICAL_WRITING_PATTERN.search(relative) is None:
                    continue
                try:
                    mode = path.stat().st_mode
                except OSError as exc:
                    errors.append(
                        f"MEDICAL_WRITING_STAT_ERROR:{relative}:{type(exc).__name__}"
                    )
                    continue
                if not stat.S_ISREG(mode):
                    continue
                try:
                    matched[relative] = (
                        hashlib.sha256(path.read_bytes()).hexdigest().lower()
                    )
                except (OSError, UnicodeError) as exc:
                    errors.append(
                        f"MEDICAL_WRITING_READ_ERROR:{relative}:{type(exc).__name__}"
                    )
    aggregate = hashlib.sha256()
    for relative in sorted(matched, key=lambda value: value.encode("utf-8")):
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(matched[relative].encode("ascii"))
        aggregate.update(b"\n")
    return {
        "file_count": len(matched),
        "aggregate_sha256": aggregate.hexdigest(),
        "errors": errors,
    }


def _port_connect_ex(port: int) -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.2)
    try:
        return sock.connect_ex(("127.0.0.1", port))
    finally:
        sock.close()


def _numeric_near(a, b) -> bool:
    """Canonical raw numeric equality with contract float tolerance."""
    if a == b:
        return True
    try:
        fa = float(a)
        fb = float(b)
    except (TypeError, ValueError):
        return False
    return abs(fa - fb) <= max(1e-12, 1e-9 * max(abs(fa), abs(fb), 1.0))


def test_mode_output_apis_required_for_slice04_completion():
    missing = [name for name in REQUIRED_MODE_OUTPUT_APIS if not hasattr(mo, name)]
    assert missing == [], (
        "worker_01/02 ModeOutput APIs absent from mode_output.py: "
        + ", ".join(missing)
    )


def test_positive_daily_four_and_query_surface_clean():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    numeric = {
        "ae_rate": {
            "raw": 14 / 117,
            "numerator": 14,
            "denominator": 117,
            "population": "safety",
            "data_cutoff": run["data_cutoff"],
        }
    }
    outputs = mo.build_daily_mode_outputs(
        run,
        contract,
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        findings=[_finding()],
        risks=[{
            "risk_id": "risk-ae-omission-001",
            "metric_id": "ae_rate",
            "status": "open",
            "raw_rate": 14 / 117,
        }],
        numeric=numeric,
        entry_context=ctx,
    )
    assert len(outputs) == 4
    for out in outputs:
        assert mo.validate_mode_output(out, run, contract) == ()
        assert out["producer_kind"] == mo.PRODUCER_SYSTEM
        assert out["immutable"] is True
    query = outputs[2]
    assert query["payload"]["draft_count"] == 1
    draft = query["payload"]["query_drafts"][0]
    assert draft["display_text"] == draft["basis"] + draft["finding"] + draft["action"]
    assert draft["is_sent"] is False and draft["is_closed"] is False


def test_output_and_query_ids_are_content_addressed_and_tamper_detected():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("affected_query_draft", findings=[_finding()]),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    bad_output = copy.deepcopy(out)
    bad_output["payload"]["query_drafts"][0]["action"] = "行动项：已被篡改。"
    codes = mo.validate_mode_output(bad_output, run, contract)
    assert mo.IDENTITY_MISMATCH in codes

    bad_query_id = copy.deepcopy(out)
    bad_query_id["payload"]["query_drafts"][0]["query_draft_id"] = "qd-forged"
    codes2 = mo.validate_mode_output(bad_query_id, run, contract)
    assert mo.IDENTITY_MISMATCH in codes2

    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_output(
            run,
            contract,
            _spec("change_summary", output_id="out-caller-forged"),
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc.value.failure_code == mo.IDENTITY_MISMATCH


def test_numeric_raw_must_match_numerator_denominator_and_identity():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_output(
            run,
            contract,
            {
                "output_kind": "current_full_risk",
                "eligibility": mo.default_output_eligibility(),
                "numeric": {
                    "ae_rate": {
                        "raw": 0.5,
                        "numerator": 14,
                        "denominator": 117,
                        "data_cutoff": run["data_cutoff"],
                        "source_revision_id": run["source_revision_id"],
                    }
                },
            },
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc.value.failure_code == mo.AUTHORITY_MISMATCH


def test_eligibility_tamper_is_detected_even_when_envelope_identity_is_restamped():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("change_summary"),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    tampered = copy.deepcopy(out)
    tampered["eligibility"]["analysis_state"] = "partial"
    tampered.pop("output_id")
    tampered["output_id"] = "out-" + mo.sha256_hex(canonical_bytes(tampered))
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        tampered, run, contract
    )


def test_cross_mode_contract_isolation_and_byte_stability():
    digests = {}
    for mode in MODES:
        a = mo.build_mode_contract(mode)
        b = mo.build_mode_contract(mode)
        assert canonical_bytes(a) == canonical_bytes(b)
        digests[mode] = mo.mode_contract_digest(a)
        assert mo.validate_mode_contract(a) == ()
    assert len(set(digests.values())) == 3
    # Mixing a daily run with a pre_lock contract fails closed.
    run, _, ctx = _positive_gate("daily")
    pre = mo.build_mode_contract("pre_lock")
    codes = mo.validate_run_mode_gate(run, pre, entry_context=ctx)
    assert mo.MODE_ENTRY_BLOCKED in codes or mo.SILENT_MODE_CONVERSION in codes


def test_cross_cutoff_revision_mix_fail_closed():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    auth_drift = copy.deepcopy(auth)
    auth_drift["data_cutoff"] = "cutoff-other"
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_output(
            run,
            contract,
            _spec("change_summary"),
            authority_refs=auth_drift,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc.value.failure_code in (mo.CUTOFF_MISMATCH, mo.AUTHORITY_MISMATCH)

    rev_drift = copy.deepcopy(auth)
    rev_drift["source_revision_id"] = "revision-other"
    with pytest.raises(mo.ModeOutputError) as exc2:
        mo.build_mode_output(
            run,
            contract,
            _spec("change_summary"),
            authority_refs=rev_drift,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc2.value.failure_code in (mo.REVISION_MISMATCH, mo.AUTHORITY_MISMATCH)


def test_identity_mix_across_outputs_detected():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("change_summary"),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    mixed = copy.deepcopy(out)
    mixed["run_id"] = "run-mixed"
    codes = mo.validate_mode_output(mixed, run, contract)
    assert mo.IDENTITY_MISMATCH in codes


def test_producer_kind_authority_separation():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    # system daily kind cannot claim external producer.
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_output(
            run,
            contract,
            {
                "output_kind": "current_full_risk",
                "producer_kind": mo.PRODUCER_EXTERNAL,
                "eligibility": mo.default_output_eligibility(),
            },
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc.value.failure_code == mo.AUTHORITY_MISMATCH

    out = mo.build_mode_output(
        run,
        contract,
        _spec("change_summary"),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    tampered = copy.deepcopy(out)
    tampered["producer_kind"] = mo.PRODUCER_EXTERNAL
    codes = mo.validate_mode_output(tampered, run, contract)
    assert mo.AUTHORITY_MISMATCH in codes


def test_numeric_consistency_across_daily_outputs():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    raw_rate = 0.11965811965811966
    numeric = {
        "ae_rate": {
            "raw": raw_rate,
            "numerator": 14,
            "denominator": 117,
            "population": "safety",
            "data_cutoff": run["data_cutoff"],
            "source_revision_id": run["source_revision_id"],
        }
    }
    outputs = mo.build_daily_mode_outputs(
        run,
        contract,
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        findings=[_finding()],
        risks=[{
            "risk_id": "risk-ae-omission-001",
            "metric_id": "ae_rate",
            "status": "open",
            "raw_rate": raw_rate,
        }],
        numeric=numeric,
        entry_context=ctx,
    )
    # Shared authority/coverage/QC digests — no silent drift across the four.
    auth_set = {
        (
            o["authority_refs"]["digest"],
            o["coverage_refs"]["digest"],
            o["qc_refs"]["digest"],
            o["data_cutoff"],
            o["source_revision_id"],
        )
        for o in outputs
    }
    assert len(auth_set) == 1
    risk_out = outputs[1]
    payload_numeric = risk_out["payload"]["numeric"]["ae_rate"]
    assert payload_numeric["raw"] == raw_rate
    assert payload_numeric["numerator"] == 14
    assert payload_numeric["denominator"] == 117
    assert payload_numeric["numerator"] <= payload_numeric["denominator"]
    assert _numeric_near(payload_numeric["raw"], 14 / 117)
    assert risk_out["payload"]["risks"][0]["raw_rate"] == raw_rate
    assert payload_numeric["data_cutoff"] == run["data_cutoff"]
    # Tampering numeric raw after build must fail validation if mirrored into authority payload digest field.
    tampered = copy.deepcopy(risk_out)
    tampered["payload"]["authority_digest"] = "tampered-digest"
    codes = mo.validate_mode_output(tampered, run, contract)
    assert mo.AUTHORITY_MISMATCH in codes


def test_query_forbidden_external_state_and_pd_registration_blocked():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        {
            "output_kind": "affected_query_draft",
            "eligibility": mo.default_output_eligibility(),
            "findings": [
                _finding(
                    finding_kind="protocol_deviation_prohibited_medication",
                    pd_wording_state="pending_verify_wording_only",
                )
            ],
        },
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    draft = out["payload"]["query_drafts"][0]
    assert draft["is_pd_recorded"] is False
    assert draft["is_pd_closed"] is False
    assert out["payload"]["pd_registration_allowed"] is False
    for flag in ("is_sent", "is_closed", "is_user_confirmed"):
        tampered = copy.deepcopy(out)
        tampered["payload"]["query_drafts"][0][flag] = True
        codes = mo.validate_mode_output(tampered, run, contract)
        assert mo.OUTPUT_NOT_ELIGIBLE in codes, flag


def test_frozen_mode_output_blocking_codes_only():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    out = mo.build_mode_output(
        run,
        contract,
        _spec("affected_query_draft", findings=[_finding()]),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    tampered = copy.deepcopy(out)
    tampered["payload"]["query_drafts"][0]["display_text"] = "x"
    tampered["run_id"] = "run-x"
    tampered["data_cutoff"] = "cutoff-x"
    codes = mo.validate_mode_output(tampered, run, contract)
    assert codes
    assert set(codes) <= set(FROZEN_MODE_OUTPUT_CODES)


def test_build_requires_explicit_entry_context_and_full_eligibility():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    with pytest.raises(mo.ModeOutputError) as missing_ctx:
        mo.build_mode_output(
            run,
            contract,
            _spec("change_summary"),
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
        )
    assert missing_ctx.value.failure_code == mo.MODE_ENTRY_BLOCKED

    with pytest.raises(mo.ModeOutputError) as missing_gates:
        mo.build_mode_output(
            run,
            contract,
            {
                "output_kind": "change_summary",
                "eligibility": {"analysis_state": "complete"},
            },
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert missing_gates.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE


@pytest.mark.parametrize(
    "missing",
    [
        "carry_forward_target_run",
        "carry_forward_reason",
        "reusable_artifact_hash",
        "carry_forward_compatibility",
    ],
)
def test_carry_forward_requires_complete_provenance(missing):
    prior = _binding("daily", run_id="run-daily-001")
    run, contract, ctx = _positive_gate(
        "pre_lock",
        run_id="run-pre-lock-002",
        carry_forward_run_ids=["run-daily-001"],
        carry_forward_source_run="run-daily-001",
        carry_forward_target_run="run-pre-lock-002",
        carry_forward_reason="进入锁库前全量复核",
        reusable_artifact_hash="artifact-hash-001",
        carry_forward_compatibility="compatible",
    )
    del run[missing]
    ctx["cross_mode_carry_forward"] = True
    assert mo.MODE_ENTRY_BLOCKED in mo.validate_run_mode_gate(
        run, contract, entry_context=ctx, prior_run=prior
    )


@pytest.mark.parametrize(
    "missing",
    ["locked_snapshot_hash", "local_os_user", "acceptance_evidence_hash"],
)
def test_post_lock_requires_complete_locked_identity(missing):
    run, contract, ctx = _positive_gate("post_lock_pre_cfdi")
    del run[missing]
    assert mo.MODE_ENTRY_BLOCKED in mo.validate_run_mode_gate(
        run, contract, entry_context=ctx
    )


def test_numeric_count_semantics_and_risk_alignment_fail_closed():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    unique = {
        "risk_rate": {
            "raw": 5 / 3,
            "numerator": 5,
            "denominator": 3,
            "count_kind": "unique_subject",
        }
    }
    with pytest.raises(mo.ModeOutputError) as bad_unique:
        mo.build_mode_output(
            run,
            contract,
            _spec("current_full_risk", risks=[], numeric=unique),
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert bad_unique.value.failure_code == mo.AUTHORITY_MISMATCH

    event = copy.deepcopy(unique)
    event["risk_rate"]["count_kind"] = "event"
    accepted = mo.build_mode_output(
        run,
        contract,
        _spec("current_full_risk", risks=[], numeric=event),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    assert mo.validate_mode_output(accepted, run, contract) == ()

    aligned_numeric = {
        "risk_rate": {"raw": 1 / 3, "numerator": 1, "denominator": 3}
    }
    with pytest.raises(mo.ModeOutputError) as drift:
        mo.build_mode_output(
            run,
            contract,
            _spec(
                "current_full_risk",
                risks=[{
                    "risk_id": "risk-1",
                    "metric_id": "risk_rate",
                    "raw_rate": 0.9,
                }],
                numeric=aligned_numeric,
            ),
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert drift.value.failure_code == mo.AUTHORITY_MISMATCH


def test_malformed_numeric_and_query_payloads_return_codes_not_exceptions():
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    risk = mo.build_mode_output(
        run,
        contract,
        _spec(
            "current_full_risk",
            risks=[],
            numeric={"rate": {"raw": 0.5, "numerator": 1, "denominator": 2}},
        ),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    malformed_risk = copy.deepcopy(risk)
    malformed_risk["payload"]["numeric"]["rate"]["numerator"] = "bad_num"
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        malformed_risk, run, contract
    )

    query = mo.build_mode_output(
        run,
        contract,
        _spec("affected_query_draft", findings=[_finding()]),
        authority_refs=auth,
        coverage_refs=cov,
        qc_refs=qc,
        entry_context=ctx,
    )
    malformed_query = copy.deepcopy(query)
    malformed_query["payload"]["query_drafts"][0]["basis"] = 123
    assert mo.OUTPUT_NOT_ELIGIBLE in mo.validate_mode_output(
        malformed_query, run, contract
    )


def test_query_requires_explicit_issue_and_supports_site_scope():
    run, _, _ = _positive_gate("daily")
    with pytest.raises(mo.ModeOutputError) as missing_issue:
        mo.build_affected_query_draft(run, [_finding(issue_id="")])
    assert missing_issue.value.failure_code == mo.OUTPUT_NOT_ELIGIBLE

    payload = mo.build_affected_query_draft(
        run,
        [_finding(scope_kind="site", subject_id="", site_id="SITE-01")],
    )
    draft = payload["query_drafts"][0]
    assert draft["scope_kind"] == "site"
    assert draft["subject_id"] == ""


@pytest.mark.parametrize("field", ["changes", "change_notes"])
def test_change_entries_require_explicit_change_kind(field):
    run, contract, ctx = _positive_gate("daily")
    auth, cov, qc = _refs(run)
    output_kind = (
        "change_summary"
        if field == "changes"
        else "data_knowledge_rule_model_change_note"
    )
    with pytest.raises(mo.ModeOutputError) as exc:
        mo.build_mode_output(
            run,
            contract,
            _spec(output_kind, **{field: [{"text": "未标明变化来源"}]}),
            authority_refs=auth,
            coverage_refs=cov,
            qc_refs=qc,
            entry_context=ctx,
        )
    assert exc.value.failure_code == mo.AUTHORITY_MISMATCH


def test_slice01_frozen_inputs_and_oracle_clean(contract, matrix):
    assert _sha256_file(contracts.contract_path()) == EXPECTED_CONTRACT_SHA
    assert _sha256_file(contracts.matrix_path()) == EXPECTED_MATRIX_SHA
    assert _sha256_file(contracts.prose_path()) == EXPECTED_PROSE_SHA
    for rel, digest in EXPECTED_SLICE01_SRC.items():
        assert _sha256_file(POC_ROOT / rel) == digest, rel
    report = validator.oracle_parity_report(matrix["rows"], contract, matrix)
    assert report["mismatch_count"] == 0
    assert report["row_count"] == 86
    catalog = fixtures.build_fixture_catalog(matrix["rows"])
    assert catalog["catalog_sha256"] == (
        "76b43076d896001fb4b393f43329a194b32d9091625101d8eed2ba2ece940b53"
    )


def test_slice02_03_04_05_adjacency_receipts_present():
    review = POC_ROOT / "evidence" / "r6_report_review_runtime_receipt.json"
    bundle = POC_ROOT / "evidence" / "r6_report_bundle_runtime_receipt.json"
    mode_out = POC_ROOT / "evidence" / "r6_mode_output_runtime_receipt.json"
    pre_lock = POC_ROOT / "evidence" / "r6_pre_lock_output_runtime_receipt.json"
    assert review.is_file()
    assert bundle.is_file()
    assert mode_out.is_file()
    assert pre_lock.is_file()
    review_payload = json.loads(review.read_text(encoding="utf-8"))
    bundle_payload = json.loads(bundle.read_text(encoding="utf-8"))
    mode_payload = json.loads(mode_out.read_text(encoding="utf-8"))
    pre_lock_payload = json.loads(pre_lock.read_text(encoding="utf-8"))
    assert review_payload["slice"]["id"] == "r6_runtime_slice_02"
    assert bundle_payload["slice"]["id"] == "r6_runtime_slice_03"
    assert mode_payload["slice"]["id"] == "r6_runtime_slice_04"
    assert pre_lock_payload["slice"]["id"] == "r6_runtime_slice_05"
    assert review_payload["boundaries"]["medical_writing_unchanged"] is True
    assert bundle_payload["boundaries"]["medical_writing_unchanged"] is True
    assert mode_payload["boundaries"]["medical_writing_unchanged"] is True
    assert pre_lock_payload["boundaries"]["medical_writing_unchanged"] is True
    # Adjacent modules remain importable beside mode_output.
    from mm_r6 import report_bundle as rb
    from mm_r6 import report_review as rr

    assert hasattr(rr, "build_report_review_matrix")
    assert hasattr(rb, "build_report_review_bundle")


def test_medical_writing_aggregate_unchanged():
    boundary = _medical_writing_boundary(WORKBENCH_ROOT)
    assert boundary["errors"] == []
    assert boundary["file_count"] == EXPECTED_MEDICAL_WRITING_COUNT
    assert boundary["aggregate_sha256"] == EXPECTED_MEDICAL_WRITING_AGGREGATE


@pytest.mark.parametrize("port", PROTECTED_PORTS)
def test_protected_port_stopped(port):
    assert _port_connect_ex(port) != 0


def test_slice05_create_only_allowlist_exact():
    found = _poc_files()
    optional_receipts = {
        "evidence/r6_report_bundle_runtime_receipt.json",
        "evidence/r6_mode_output_runtime_receipt.json",
        "evidence/r6_pre_lock_output_runtime_receipt.json",
        "evidence/r6_post_lock_output_runtime_receipt.json",
        "evidence/r6_agent_harness_runtime_receipt.json",
    }
    extras = found - SLICE04_CREATE_ONLY_RELATIVE
    missing_required = (SLICE04_CREATE_ONLY_RELATIVE - optional_receipts) - found
    assert extras == set()
    assert missing_required == set()
    assert found <= SLICE04_CREATE_ONLY_RELATIVE


_REPRO_PROBE = r"""
import copy, os, sys
sys.path.insert(0, os.environ["MM_R6_SRC"])
from mm_r6 import mode_output as mo
from mm_r6.report_review import canonical_bytes

def binding(mode="daily", **o):
    b = {
        "project_id": "project-r6-synthetic",
        "run_id": "run-r6-mode-001",
        "mode": mode,
        "execution_basis": "full",
        "data_cutoff": "cutoff-2026-08-01",
        "source_revision_id": "run-source-revision-001",
        "knowledge_pack_version": "kp-1",
        "rule_activation_version": "rav-1",
        "mapping_version": "map-1",
        "identity_algorithm_version": "ia-r6-slice04-001",
        "identity_algorithm_digest": "ia-digest-r6-slice04-001",
        "schema_version": "r6-0.1",
        "carry_forward_run_ids": [],
        "mode_transition": "explicit_new_run",
        "actor": "synthetic-actor",
        "created_at": "2026-08-28T00:00:00Z",
    }
    b.update(o)
    return b

run = binding()
contract = mo.build_mode_contract("daily")
if mo.validate_mode_contract(contract):
    raise SystemExit("contract_invalid")
ctx = mo.default_entry_context_for_mode("daily", run_binding=run)
if mo.validate_run_mode_gate(run, contract, entry_context=ctx):
    raise SystemExit("gate_fail")
digest = "auth-digest-r6-slice04-001"
base = {
    "project_id": run["project_id"],
    "run_id": run["run_id"],
    "data_cutoff": run["data_cutoff"],
    "source_revision_id": run["source_revision_id"],
}
auth = dict(base, authority_digest=digest, digest=digest)
cov = dict(base, coverage_digest=digest, digest=digest)
qc = dict(base, qc_digest=digest, digest=digest)
finding = {
    "finding_id": "finding-001",
    "risk_id": "risk-ae-omission-001",
    "issue_id": "issue-001",
    "subject_id": "SUBJ-001",
    "site_id": "SITE-01",
    "scope_kind": "subject",
    "basis": "方案要求报告治疗期不良事件",
    "finding": "受试者记录出现未对应 AE 的症状描述",
    "action": "请核实是否需补充 AE 记录并说明判定理由",
    "evidence_refs": ["ev-listing-row-001"],
    "locator": {"path": "AE.SYMPTOM", "record_id": "rec-001", "field": "AETERM"},
}
raw_rate = 0.11965811965811966
numeric = {
    "ae_rate": {
        "raw": raw_rate,
        "numerator": 14,
        "denominator": 117,
        "population": "safety",
        "data_cutoff": run["data_cutoff"],
    }
}
a = mo.build_daily_mode_outputs(
    run, contract, authority_refs=auth, coverage_refs=cov, qc_refs=qc,
    findings=[finding], risks=[{
        "risk_id": "risk-ae-omission-001",
        "metric_id": "ae_rate",
        "status": "open",
        "raw_rate": raw_rate,
    }],
    numeric=numeric, entry_context=ctx,
)
b = mo.build_daily_mode_outputs(
    run, contract, authority_refs=auth, coverage_refs=cov, qc_refs=qc,
    findings=[finding], risks=[{
        "risk_id": "risk-ae-omission-001",
        "metric_id": "ae_rate",
        "status": "open",
        "raw_rate": raw_rate,
    }],
    numeric=numeric, entry_context=ctx,
)
for left, right in zip(a, b):
    if canonical_bytes(left) != canonical_bytes(right):
        raise SystemExit("output_bytes_diverge:%s" % left.get("output_kind"))
    codes = mo.validate_mode_output(left, run, contract)
    if codes:
        raise SystemExit("validate_fail:%s:%s" % (left.get("output_kind"), codes))
if a[1]["payload"]["numeric"]["ae_rate"]["raw"] != raw_rate:
    raise SystemExit("numeric_drift")
if abs(a[1]["payload"]["numeric"]["ae_rate"]["raw"] - (14 / 117)) > 1e-12:
    raise SystemExit("numeric_ratio_mismatch")
draft = a[2]["payload"]["query_drafts"][0]
if draft["display_text"] != draft["basis"] + draft["finding"] + draft["action"]:
    raise SystemExit("display_text_mismatch")
tampered = copy.deepcopy(a[2])
tampered["payload"]["query_drafts"][0]["is_sent"] = True
codes2 = mo.validate_mode_output(tampered, run, contract)
if "output_not_eligible" not in codes2:
    raise SystemExit("tamper_miss:%s" % (codes2,))
# Cross-mode silent conversion must fail closed.
prior = binding("post_lock_pre_cfdi", run_id="run-locked-001",
                data_cutoff="cutoff-fixed-001", source_revision_id="revision-fixed-001",
                fixed_total=True, locked_snapshot_hash="snap-hash-fixed-001",
                output_cutoff_ref="cutoff-fixed-001", output_revision_ref="revision-fixed-001")
silent = binding("daily", run_id="run-locked-001")
ctx2 = mo.default_entry_context_for_mode("daily", run_binding=silent)
codes3 = mo.validate_run_mode_gate(
    silent, mo.build_mode_contract("daily"), entry_context=ctx2, prior_run=prior
)
if "silent_mode_conversion" not in codes3:
    raise SystemExit("silent_miss:%s" % (codes3,))
print("ok")
"""


@pytest.mark.parametrize("opt_flag", ["", "-O", "-OO"])
@pytest.mark.parametrize("hash_seed", ["0", "1", "42"])
def test_repro_mode_output_raise_based(opt_flag, hash_seed):
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = hash_seed
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["MM_R6_SRC"] = str(POC_ROOT / "src")
    cmd = [sys.executable]
    if opt_flag:
        cmd.append(opt_flag)
    cmd.extend(["-c", _REPRO_PROBE])
    proc = subprocess.run(
        cmd,
        cwd=str(WORKBENCH_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, (
        f"opt={opt_flag!r} seed={hash_seed} rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    assert "ok" in proc.stdout
