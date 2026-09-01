# Task Context: medical_monitoring_snapshot_read_shape_revalidation_20260805

Created: 2026-08-05 07:11:59
Objective: Harden persisted monitoring diff and rule snapshot read shape without runtime activation
Task type: `finite_code_task`
Risk: `high`
Selected agent route: Codex direct; no delegated provider or sub-agent is permitted for this slice.

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_repository.py`, persisted diff/rule
  snapshot readers and their existing repository tests.
- The filtered adjacent daily-run repository/service/analysis/router tests and
  the current read-only real-loop gate under `records/active_slices/`.
- Do not read or write real-project data, start a service/browser, invoke a
  provider, or alter product surfaces outside the scoped source/test files.

## Scope

- In scope: strict fail-closed snapshot root/input/output/payload/timestamp
  read shape; one tamper regression; non-runtime compile/test evidence and task
  records.
- Out of scope: step/event/business behavior changes, schema migrations,
  API/UI changes, external-model calls, browser/Playwright, service startup,
  real project data, B6/C14 activation, and commercial release claims.

## Success Criteria

- Diff/rule snapshots reject non-text payload/root fields, non-canonical input
  or output hashes, invalid resolution modes, and malformed timestamps without
  normalization drift.
- Focused repository and filtered adjacent daily-run suites pass; compileall
  passes; ports 8911/5174/8910/4173 remain empty.
- Codex records exact evidence and any unavailable lint check.

## Risk Boundaries

- Only the explicitly scoped source/test files and task evidence files may
  change. Keep the real-loop gate read-only/blocked; no provider, sub-agent,
  runtime, browser, login, or real-project operation is allowed.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 07:11:59: Task initialized by `tools/hermes_workflow_guard.py init-task`.
