"""Worker_03 tests: deterministic adapters, immutable modes and report ledger."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from mm_r1.domain import (
    AnalysisState,
    ArtifactCompleteness,
    CoverageUnit,
    CoverageUnitStatus,
    EvidenceState,
    ExecutionBasis,
    MonitoringRun,
    NodeType,
    ReportUnitRef,
    RunMode,
    SourceRevision,
    content_hash,
)
from mm_r1.adapters import (
    AdapterPromotionError,
    AdapterState,
    ImmutableAdapterBinding,
    persist_adapter_run,
    ScriptedAdapter,
    ScriptedOutput,
)
from mm_r1.modes import (
    DAILY_INCREMENTAL_CONTRACT,
    POST_LOCK_PRE_CFDI_CONTRACT,
    PRE_LOCK_CONTRACT,
    ModeEntryContext,
    switch_mode,
)
from mm_r1.report_review import (
    AtomicClaim,
    ClaimCoverageLedger,
    EvidenceRecord,
    build_claim_coverage_ledger,
    compare_claim_to_evidence,
    review_report,
    synthetic_report_fixture,
)


def _binding() -> ImmutableAdapterBinding:
    return ImmutableAdapterBinding(
        binding_id="binding-synthetic-1",
        capability="risk-candidate-generation",
        provider="deterministic-script",
        model="fake-model-r1",
        selector="script-1",
        effort="fixed",
        allowed_tools=(),
        isolation="fresh_context",
    )


def _covered_output(status=AdapterState.COMPLETE, **kwargs):
    unit = CoverageUnit(scope="subject", key="SYN-S001")
    produced = CoverageUnit(
        scope="subject",
        key="SYN-S001",
        status=kwargs.pop("produced_status", CoverageUnitStatus.COVERED),
        reason=kwargs.pop("reason", None),
    )
    return ScriptedOutput(
        status=status,
        payload={"risk_candidate": "synthetic candidate"},
        raw_output={"candidate": "synthetic raw output"},
        expected_units=(unit,),
        produced_units=(produced,),
        **kwargs
    )


def test_adapter_binding_is_immutable_and_configured_state_is_explicit():
    adapter = ScriptedAdapter(_binding())
    assert adapter.contract.status == AdapterState.CONFIGURED
    assert adapter.contract.authority.may_promote_facts is False
    with pytest.raises(FrozenInstanceError):
        adapter.binding.model = "other-model"

    running = adapter.start_run({"input": "SYNTHETIC"}, monitoring_run_id="monitoring-1")
    assert running.status == AdapterState.RUNNING
    assert running.binding.input_hash
    assert running.analysis.parse_state == "running"


def test_adapter_complete_output_has_raw_provenance_and_candidate_only_artifact():
    adapter = ScriptedAdapter(_binding(), [_covered_output()])
    result = adapter.run({"input": "SYNTHETIC"}, monitoring_run_id="monitoring-1", node_id="ai-node")
    assert result.status == AdapterState.COMPLETE
    assert result.raw_output is not None
    assert result.raw_output.raw_output_ref in result.candidate_artifact.evidence_refs
    assert result.candidate_artifact.node_type == NodeType.AI_CANDIDATE
    assert result.candidate_artifact.payload_role == "candidate"
    assert result.is_candidate_only()
    assert result.can_promote is False
    assert result.is_complete_and_covered()
    assert result.candidate_artifact.payload["authority"]["may_publish"] is False


def test_adapter_incomplete_coverage_fails_closed_and_preserves_candidate_role():
    for requested, produced_status, expected_state in (
        (AdapterState.COMPLETE, CoverageUnitStatus.PARTIAL, AdapterState.PARTIAL),
        (AdapterState.TRUNCATED, CoverageUnitStatus.TRUNCATED, AdapterState.TRUNCATED),
    ):
        adapter = ScriptedAdapter(
            _binding(),
            [_covered_output(requested, produced_status=produced_status)],
        )
        result = adapter.run({"input": "SYNTHETIC"})
        assert result.status == expected_state
        assert result.candidate_artifact is not None
        assert result.candidate_artifact.is_publishable()[0] is False
        assert result.is_complete_and_covered() is False

    explicit_partial = ScriptedAdapter(_binding(), [_covered_output(AdapterState.PARTIAL)])
    partial_result = explicit_partial.run({"input": "SYNTHETIC"})
    assert partial_result.status == AdapterState.PARTIAL
    assert partial_result.candidate_artifact.completeness == ArtifactCompleteness.PARTIAL
    assert partial_result.candidate_artifact.is_publishable()[0] is False


def test_adapter_states_include_failure_timeout_and_cancelled_without_artifact():
    for state, method in (
        (AdapterState.FAILED, "fail_run"),
        (AdapterState.TIMEOUT, "timeout_run"),
        (AdapterState.CANCELLED, "cancel_run"),
    ):
        adapter = ScriptedAdapter(_binding())
        running = adapter.start_run({"input": "SYNTHETIC"})
        result = getattr(adapter, method)(running.run_id)
        assert result.status == state
        assert result.candidate_artifact is None
        assert result.analysis.raw_output_ref == ""


def test_adapter_runs_are_independent_and_terminal_runs_are_not_rewritten():
    adapter = ScriptedAdapter(_binding(), [_covered_output(), _covered_output()])
    first, second = adapter.run_independently({"input": "SYNTHETIC"}, count=2)
    assert first.run_id != second.run_id
    assert first.analysis.analysis_id != second.analysis.analysis_id
    assert first.raw_output.raw_output_ref != second.raw_output.raw_output_ref
    with pytest.raises(ValueError):
        adapter.finish_run(first.run_id, _covered_output())
    with pytest.raises(AdapterPromotionError):
        adapter.promote_facts(first.candidate_artifact)
    with pytest.raises(AdapterPromotionError):
        adapter.set_baseline_eligible("snapshot")
    with pytest.raises(AdapterPromotionError):
        adapter.confirm_user()
    with pytest.raises(AdapterPromotionError):
        adapter.publish()


def test_adapter_resume_creates_new_run_and_keeps_timeout_history():
    adapter = ScriptedAdapter(
        _binding(),
        [
            _covered_output(AdapterState.TRUNCATED, produced_status=CoverageUnitStatus.TRUNCATED),
            _covered_output(),
        ],
    )
    truncated = adapter.run({"input": "SYNTHETIC"})
    resumed = adapter.resume_run(truncated.run_id)
    assert resumed.run_id != truncated.run_id
    assert resumed.continued_from == truncated.run_id
    assert resumed.status == AdapterState.COMPLETE
    assert truncated.status == AdapterState.TRUNCATED


def _daily_context(**overrides):
    values = dict(
        project_id="synthetic-project",
        mode=RunMode.DAILY,
        execution_basis=ExecutionBasis.INCREMENTAL,
        data_cutoff="SYNTHETIC-CUTOFF-2",
        source_revision_id="synthetic-revision-2",
        full_listing=True,
        snapshot_accepted=True,
        baseline_eligible=True,
        previous_baseline_run_id="daily-run-1",
    )
    values.update(overrides)
    return ModeEntryContext(**values)


def test_three_mode_contracts_are_immutable_and_have_distinct_policies():
    assert DAILY_INCREMENTAL_CONTRACT.mode == RunMode.DAILY
    assert DAILY_INCREMENTAL_CONTRACT.execution_basis == ExecutionBasis.INCREMENTAL
    assert PRE_LOCK_CONTRACT.mode == RunMode.PRE_LOCK
    assert POST_LOCK_PRE_CFDI_CONTRACT.mode == RunMode.POST_LOCK_PRE_CFDI
    assert PRE_LOCK_CONTRACT.output_eligibility != POST_LOCK_PRE_CFDI_CONTRACT.output_eligibility
    with pytest.raises(FrozenInstanceError):
        DAILY_INCREMENTAL_CONTRACT.cutoff_policy = "changed"
    assert DAILY_INCREMENTAL_CONTRACT.entry_allowed(_daily_context())
    assert not DAILY_INCREMENTAL_CONTRACT.entry_allowed(_daily_context(ambiguity=("identity",)))
    assert not DAILY_INCREMENTAL_CONTRACT.entry_allowed(_daily_context(previous_baseline_run_id=None))


def _complete_run(run_id, mode, cutoff, revision, basis):
    return MonitoringRun(
        run_id=run_id,
        project_id="synthetic-project",
        mode=mode,
        data_cutoff=cutoff,
        source_revision_id=revision,
        execution_basis=basis,
        analysis_state=AnalysisState.COMPLETE,
        evidence_state=EvidenceState.COMPLETE,
    )


def test_mode_switch_creates_new_run_and_explicit_carry_forward_without_mutation():
    previous = _complete_run(
        "daily-run-1", RunMode.DAILY, "SYNTHETIC-CUTOFF-1", "synthetic-revision-1", ExecutionBasis.INCREMENTAL
    )
    context = ModeEntryContext(
        project_id="synthetic-project",
        mode=RunMode.PRE_LOCK,
        execution_basis=ExecutionBasis.FULL,
        data_cutoff="SYNTHETIC-CUTOFF-2",
        source_revision_id="synthetic-revision-2",
        full_listing=True,
        snapshot_accepted=True,
        lock_window_confirmed=True,
        cutoff_confirmed=True,
    )
    replacement = switch_mode(
        previous,
        PRE_LOCK_CONTRACT,
        entry_context=context,
        data_cutoff="SYNTHETIC-CUTOFF-2",
        source_revision_id="synthetic-revision-2",
    )
    assert replacement.previous_run_id == previous.run_id
    assert replacement.new_run.run_id != previous.run_id
    assert replacement.new_run.mode == RunMode.PRE_LOCK
    assert replacement.new_run.analysis_state == AnalysisState.NOT_STARTED
    assert replacement.carry_forward.allowed
    assert previous.mode == RunMode.DAILY
    assert previous.data_cutoff == "SYNTHETIC-CUTOFF-1"


def test_mode_switch_rejects_entry_cutoff_or_source_revision_mismatch():
    previous = _complete_run(
        "daily-run-1", RunMode.DAILY, "SYNTHETIC-CUTOFF-1", "synthetic-revision-1", ExecutionBasis.INCREMENTAL
    )
    context = ModeEntryContext(
        project_id="synthetic-project",
        mode=RunMode.PRE_LOCK,
        execution_basis=ExecutionBasis.FULL,
        data_cutoff="SYNTHETIC-CUTOFF-2",
        source_revision_id="synthetic-revision-2",
        full_listing=True,
        snapshot_accepted=True,
        lock_window_confirmed=True,
        cutoff_confirmed=True,
    )
    with pytest.raises(ValueError, match="entry cutoff does not match"):
        switch_mode(
            previous,
            PRE_LOCK_CONTRACT,
            entry_context=context,
            data_cutoff="SYNTHETIC-CUTOFF-OLD",
            source_revision_id="synthetic-revision-2",
        )
    with pytest.raises(ValueError, match="entry source revision does not match"):
        switch_mode(
            previous,
            PRE_LOCK_CONTRACT,
            entry_context=context,
            data_cutoff="SYNTHETIC-CUTOFF-2",
            source_revision_id="synthetic-revision-OLD",
        )
    assert previous.run_id == "daily-run-1"
    assert previous.data_cutoff == "SYNTHETIC-CUTOFF-1"


def test_mode_switch_missing_or_ambiguous_entry_fails_closed():
    previous = _complete_run(
        "daily-run-1", RunMode.DAILY, "SYNTHETIC-CUTOFF-1", "synthetic-revision-1", ExecutionBasis.INCREMENTAL
    )
    with pytest.raises(ValueError, match="entry"):
        switch_mode(
            previous,
            PRE_LOCK_CONTRACT,
            entry_context=None,
            data_cutoff="SYNTHETIC-CUTOFF-2",
            source_revision_id="synthetic-revision-2",
        )
    context = ModeEntryContext(
        project_id="synthetic-project",
        mode=RunMode.POST_LOCK_PRE_CFDI,
        data_cutoff="SYNTHETIC-CUTOFF-2",
        source_revision_id="synthetic-revision-2",
        full_listing=True,
        snapshot_accepted=True,
        baseline_eligible=True,
        cutoff_confirmed=True,
        fixed_total_confirmed=True,
        identity_ambiguous=True,
    )
    with pytest.raises(ValueError, match="ambiguous"):
        switch_mode(
            previous,
            POST_LOCK_PRE_CFDI_CONTRACT,
            entry_context=context,
            data_cutoff="SYNTHETIC-CUTOFF-2",
            source_revision_id="synthetic-revision-2",
        )


def test_mode_output_eligibility_consumes_orthogonal_states_and_entry_context():
    run = _complete_run(
        "pre-lock-run-1", RunMode.PRE_LOCK, "SYNTHETIC-CUTOFF-2", "synthetic-revision-2", ExecutionBasis.FULL
    )
    assert not PRE_LOCK_CONTRACT.output_gate(run, True, qc_passed=True).eligible
    context = ModeEntryContext(
        project_id="synthetic-project",
        mode=RunMode.PRE_LOCK,
        execution_basis=ExecutionBasis.FULL,
        data_cutoff="SYNTHETIC-CUTOFF-2",
        source_revision_id="synthetic-revision-2",
        full_listing=True,
        snapshot_accepted=True,
        lock_window_confirmed=True,
        cutoff_confirmed=True,
    )
    eligible = PRE_LOCK_CONTRACT.output_gate(run, True, qc_passed=True, entry_context=context)
    assert eligible.eligible
    assert eligible.outputs == PRE_LOCK_CONTRACT.output_eligibility
    wrong_cutoff = PRE_LOCK_CONTRACT.output_gate(
        run,
        True,
        qc_passed=True,
        entry_context=context,
        expected_cutoff="SYNTHETIC-CUTOFF-OLD",
    )
    assert not wrong_cutoff.eligible


def test_report_fixture_covers_all_unit_types_and_atomic_claims():
    fixture = synthetic_report_fixture()
    result = review_report(fixture)
    assert result.full_report_reviewed
    assert result.ledger.full_report_reviewed
    assert {unit.unit_type for unit in result.ledger.expected_units} == {"body", "table", "figure", "footnote"}
    assert {claim.unit_type for claim in fixture.claims} == {"body", "table", "figure"}
    assert all(comparison.status == "supported" for comparison in result.comparisons)
    artifact = result.ledger.to_artifact_envelope()
    assert artifact.node_type == NodeType.DETERMINISTIC_SERVICE
    assert artifact.payload_role == "ledger"
    assert artifact.is_publishable()[0]


def test_report_ledger_blocks_absent_partial_truncated_and_unreasoned_not_evaluable():
    fixture = synthetic_report_fixture()
    complete_entries = list(build_claim_coverage_ledger(fixture).entries)
    cases = []

    cases.append(complete_entries[:-1])
    cases.append(
        [
            entry
            if entry.unit.unit_type != "table"
            else type(entry)(unit=entry.unit, claim_id=entry.claim_id, status="partial")
            for entry in complete_entries
        ]
    )
    cases.append(
        [
            entry
            if entry.unit.unit_type != "figure"
            else type(entry)(unit=entry.unit, claim_id=entry.claim_id, status="truncated")
            for entry in complete_entries
        ]
    )
    cases.append(
        [
            entry
            if entry.unit.unit_type != "footnote"
            else type(entry)(unit=entry.unit, status="not_evaluable")
            for entry in complete_entries
        ]
    )

    for entries in cases:
        result = review_report(fixture, entries)
        assert result.full_report_reviewed is False
        assert result.reasons
        assert result.ledger.to_artifact_envelope().is_publishable()[0] is False


def test_report_evidence_wrong_cutoff_blocks_full_report_reviewed():
    fixture = synthetic_report_fixture(cutoff="SYNTHETIC-CUTOFF-1")
    wrong = tuple(
        EvidenceRecord(
            evidence_id=evidence.evidence_id,
            claim_id=evidence.claim_id,
            cutoff="SYNTHETIC-CUTOFF-OLD",
            status="supported",
        )
        for evidence in fixture.evidence
    )
    wrong_fixture = type(fixture)(
        report_artifact_id=fixture.report_artifact_id,
        run_id=fixture.run_id,
        cutoff=fixture.cutoff,
        units=fixture.units,
        claims=fixture.claims,
        evidence=wrong,
    )
    result = review_report(wrong_fixture)
    assert result.full_report_reviewed is False
    assert any(comparison.status == "outdated_wrong_cutoff" for comparison in result.comparisons)
    assert any("wrong cutoff" in reason for reason in result.reasons)
    wrong_cutoff_envelope = result.ledger.to_artifact_envelope()
    assert wrong_cutoff_envelope.completeness == ArtifactCompleteness.PARTIAL
    assert wrong_cutoff_envelope.is_publishable()[0] is False


def test_report_ledger_blocks_orphan_claim_no_claim_conflict_and_unknown_evidence():
    fixture = synthetic_report_fixture()
    orphan_claim = AtomicClaim(
        "claim-orphan",
        "body",
        "body-not-in-report",
        "Synthetic orphan claim",
        fixture.cutoff,
    )
    orphan_fixture = type(fixture)(
        report_artifact_id=fixture.report_artifact_id,
        run_id=fixture.run_id,
        cutoff=fixture.cutoff,
        units=fixture.units,
        claims=fixture.claims + (orphan_claim,),
        evidence=fixture.evidence,
    )
    orphan_result = review_report(orphan_fixture)
    assert not orphan_result.full_report_reviewed
    assert any("orphan claim" in reason for reason in orphan_result.reasons)
    orphan_envelope = orphan_result.ledger.to_artifact_envelope()
    assert orphan_envelope.completeness == ArtifactCompleteness.PARTIAL
    assert orphan_envelope.is_publishable()[0] is False

    entries = list(build_claim_coverage_ledger(fixture).entries)
    body = entries[0]
    entries[0] = type(body)(unit=body.unit, status="no_claim")
    no_claim_result = review_report(fixture, entries)
    assert not no_claim_result.full_report_reviewed
    assert any("no_claim despite extracted claim" in reason for reason in no_claim_result.reasons)
    no_claim_envelope = no_claim_result.ledger.to_artifact_envelope()
    assert no_claim_envelope.completeness == ArtifactCompleteness.PARTIAL
    assert no_claim_envelope.is_publishable()[0] is False

    unknown_evidence_fixture = type(fixture)(
        report_artifact_id=fixture.report_artifact_id,
        run_id=fixture.run_id,
        cutoff=fixture.cutoff,
        units=fixture.units,
        claims=fixture.claims,
        evidence=fixture.evidence
        + (EvidenceRecord("evidence-unknown", "claim-unknown", fixture.cutoff),),
    )
    unknown_evidence_result = review_report(unknown_evidence_fixture)
    assert not unknown_evidence_result.full_report_reviewed
    assert any("unknown claim" in reason for reason in unknown_evidence_result.reasons)
    unknown_evidence_envelope = unknown_evidence_result.ledger.to_artifact_envelope()
    assert unknown_evidence_envelope.completeness == ArtifactCompleteness.PARTIAL
    assert unknown_evidence_envelope.is_publishable()[0] is False


def test_ledger_identity_includes_units_claims_evidence_comparisons_cutoffs_and_entries():
    fixture = synthetic_report_fixture(cutoff="SYNTHETIC-CUTOFF-1")
    first = build_claim_coverage_ledger(fixture)
    old_evidence = tuple(
        EvidenceRecord(item.evidence_id, item.claim_id, "SYNTHETIC-CUTOFF-OLD", item.status, item.note)
        for item in fixture.evidence
    )
    changed_fixture = type(fixture)(
        report_artifact_id=fixture.report_artifact_id,
        run_id=fixture.run_id,
        cutoff=fixture.cutoff,
        units=fixture.units,
        claims=fixture.claims,
        evidence=old_evidence,
    )
    second = build_claim_coverage_ledger(changed_fixture)
    assert first.entries == second.entries
    assert first.ledger_id != second.ledger_id

    changed_cutoff = build_claim_coverage_ledger(
        fixture,
        expected_cutoff="SYNTHETIC-CUTOFF-OLD",
        report_cutoff="SYNTHETIC-CUTOFF-OLD",
    )
    assert first.entries == changed_cutoff.entries
    assert first.ledger_id != changed_cutoff.ledger_id


def test_unsupported_but_fully_processed_claim_counts_as_reviewed_coverage():
    fixture = synthetic_report_fixture()
    issue_evidence = tuple(
        EvidenceRecord(
            item.evidence_id,
            item.claim_id,
            item.cutoff,
            "unsupported" if item.claim_id == "claim-table-1" else item.status,
            item.note,
        )
        for item in fixture.evidence
    )
    issue_fixture = type(fixture)(
        report_artifact_id=fixture.report_artifact_id,
        run_id=fixture.run_id,
        cutoff=fixture.cutoff,
        units=fixture.units,
        claims=fixture.claims,
        evidence=issue_evidence,
    )
    result = review_report(issue_fixture)
    assert result.full_report_reviewed
    assert any(item.status == "unsupported" for item in result.comparisons)
    assert result.ledger.to_artifact_envelope().is_publishable()[0]


def test_reasoned_not_evaluable_is_explicitly_accounted_for_but_unreasoned_is_not():
    fixture = synthetic_report_fixture()
    entries = list(build_claim_coverage_ledger(fixture).entries)
    entries[-1] = type(entries[-1])(
        unit=entries[-1].unit,
        status="not_evaluable",
        reason="footnote contains no atomic claim in synthetic fixture",
    )
    result = review_report(fixture, entries)
    assert result.full_report_reviewed
    assert result.ledger.coverage_manifest().is_fully_covered()[0]


def test_claim_comparison_without_evidence_is_not_evaluable():
    claim = AtomicClaim("claim-1", "body", "body-1", "Synthetic claim", "SYNTHETIC-CUTOFF-1")
    comparison = compare_claim_to_evidence(claim, (), expected_cutoff="SYNTHETIC-CUTOFF-1")
    assert comparison.status == "not_evaluable"
    assert comparison.reasons


def test_persist_adapter_run_uses_shared_store_without_authority_promotion(r1_store):
    project_id = "synthetic-worker03-project"
    revision_id = "synthetic-worker03-revision"
    monitoring_run_id = "synthetic-worker03-monitoring-run"
    r1_store.create_project(project_id, "SYNTHETIC worker03 project")
    r1_store.add_source_revision(
        SourceRevision(
            revision_id=revision_id,
            project_id=project_id,
            source_type="listing",
            version="SYNTHETIC-1",
            content_hash=content_hash({"synthetic": True, "revision": revision_id}),
        )
    )
    r1_store.create_run(
        MonitoringRun(
            run_id=monitoring_run_id,
            project_id=project_id,
            mode=RunMode.DAILY,
            data_cutoff="SYNTHETIC-CUTOFF-1",
            source_revision_id=revision_id,
            execution_basis=ExecutionBasis.FULL,
        )
    )
    adapter = ScriptedAdapter(_binding(), [_covered_output()])
    result = adapter.run(
        {"input": "SYNTHETIC"},
        monitoring_run_id=monitoring_run_id,
        node_id="worker03-ai-candidate",
    )
    receipt = persist_adapter_run(r1_store, result)
    replay = persist_adapter_run(r1_store, result)
    assert receipt.artifact_id
    assert replay.artifact_id == receipt.artifact_id
    assert r1_store.verify_artifact(receipt.artifact_id)
    assert r1_store.list_facts(monitoring_run_id) == []
    assert r1_store.list_domain_objects("adapter_binding")
    assert r1_store.list_domain_objects("adapter_run")
    assert r1_store.list_domain_objects("adapter_analysis")
    assert r1_store.list_domain_objects("adapter_raw_output")
    persisted_run = r1_store.get_run(monitoring_run_id)
    assert persisted_run.analysis_state == AnalysisState.NOT_STARTED
    assert persisted_run.output_state.value == "not_published"
    assert persisted_run.review_state.value == "not_required"
