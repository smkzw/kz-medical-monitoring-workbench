# Task Context: medical_monitoring_p4_ai_evidence_revalidation_20260803

Created: 2026-08-03 03:59:54
Objective: Add a pure read-only P4 AI evidence revalidation contract and current blocked artifact that reopens commercial coverage and explicitly detects missing real observations, evaluation matrix and release snapshot without runtime/provider authority
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current commercial coverage: `records/active_slices/medical_monitoring_release_evidence_coverage_20260802/CURRENT_RELEASE_COVERAGE.json`.
- P4 offline contracts: `services/api/app/monitoring_ai_quality.py`,
  `monitoring_ai_evaluation_matrix.py`, `monitoring_ai_release.py` and
  `monitoring_ai_release_gate.py`, with their focused tests and P4 task records.
- The current coverage row is `independent_product_ai=partial`; the persisted
  coverage decision is `blocked`, `release_ready=false`, `authority_granted=false`.

## Scope

- In scope: a pure, read-only revalidator for the current commercial coverage
  JSON and declared source files; explicit detection of missing real product-AI
  observations, evaluation matrix snapshot and prompt/model release snapshot;
  deterministic current blocked artifact and focused tests.
- Out of scope: provider calls, AI queue/job writes, runtime activation, SQLite,
  prompt registry changes, source registration, browser/API login, real projects,
  medical conclusions, frontend changes and commercial approval.

## Success Criteria

- Reopen coverage sources with direct regular-file bytes/SHA-256 and fail closed
  on drift, missing files, symlinks, unsafe paths or invalid JSON.
- Verify that coverage's independent-AI row and overall decision remain blocked/
  partial/read-only; no optimistic status is synthesized.
- Detect absence of persisted real observations, evaluation matrix and release
  snapshot as typed issues; absence must not be confused with zero findings.
- Persist a replayable report with all authority/runtime/provider/write flags false;
  replay and focused tests must be exact.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 03:59:54: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Completed the pure revalidator and persisted the current blocked artifact. Six
  coverage sources are exact; three required P4 artifact identities are absent. Focused 8,
  adjacent 639 and combined 652 regressions passed; no provider/runtime/write action occurred.
