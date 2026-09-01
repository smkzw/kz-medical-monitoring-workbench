# Task Context: medical_monitoring_release_evidence_revalidation_contract_20260803

Created: 2026-08-03 01:13:40
Objective: Build and verify a pure read-only release-evidence revalidation contract that reopens declared evidence files, binds all commercial gate rows to actual hashes, and preserves blocked release state.
Task type: `code_open_audit`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `records/active_slices/medical_monitoring_release_evidence_coverage_20260802/CURRENT_RELEASE_COVERAGE.json`
- `records/active_slices/medical_monitoring_goal_p10_20260730/RELEASE_GATE_AUDIT_20260802.md`
- `runs/execution/medical_monitoring_phase_b6_review_gate_20260801/B6_REVIEW_OUTCOME_GATE.json`
- `runs/execution/medical_monitoring_phase_c14_b6_activation_gate_20260802/B6_TO_C13_ACTIVATION_GATE_REPORT.json`
- `services/api/app/monitoring_release_gate.py`
- `services/api/app/monitoring_release_dossier.py`
- Existing read-only revalidation evidence:
  `records/active_slices/medical_monitoring_release_evidence_revalidation_20260803/RELEASE_EVIDENCE_REVALIDATION.json`

## Scope

- In scope: add a pure in-memory contract that consumes declared release-source
  rows and 16 gate rows, reopens direct files, checks byte/SHA drift, verifies
  every gate evidence hash is bound to a revalidated source, checks decision-row
  order and B6 snapshot consistency, and returns diagnostic-only evidence.
- Out of scope: release decision changes, B6/C14 updates, runtime/API/provider/
  browser/SQLite writes, source registry/batch mutation, frontend or medical-
  writing changes, and real-project LOOP execution.

## Success Criteria

- Current coverage fixture produces a deterministic `blocked` report with zero
  source drift and zero unbound gate hashes.
- Missing files, symlinks, byte/SHA drift, unbound gate hashes, decision order
  drift, and B6 snapshot mismatches fail closed with typed issues.
- The report cannot grant release, write, migration, provider, runtime or medical
  authority; focused and adjacent regressions plus Ruff/compile/review-gate pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 01:13:40: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Prior one-off read-only revalidation found 6/6 source hashes,
  16/16 gate bindings and B6 snapshot consistency valid; release remained blocked.
- 2026-08-03: Implemented the pure contract
  `services/api/app/monitoring_release_evidence_revalidation.py` and five focused
  tests. The current fixture returns `fresh`, 6/6 source matches, 16/16 gate
  bindings, matching B6/C14 snapshot and observed release `blocked`; report SHA
  `ae835aeaa9cb5fd723affed1130d2b7b843859194c5d8b82059093ed46ac0cfd`.
