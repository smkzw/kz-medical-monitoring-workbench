# Task Context: medical_monitoring_daily_run_root_read_shape_revalidation_20260805

Created: 2026-08-05 07:00:40
Objective: Harden persisted monitoring daily-run root read shape without runtime activation
Task type: `finite_code_task`
Risk: `high`
Selected agent route: Codex direct; no delegated provider or sub-agent is permitted for this slice.

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_repository.py`, especially `_run` and the
  persisted `monitoring_daily_runs` read path.
- `tests/test_monitoring_daily_run_repository.py` and the adjacent daily-run
  service/analysis/router tests.
- Existing task records and the current read-only real-loop gate under
  `records/active_slices/` are evidence and constraints, not activation authority.
- Do not read or write real-project data, start a service/browser, invoke a provider,
  or alter the product outside the two source/test files named above.

## Scope

- In scope: strict fail-closed validation of persisted daily-run root fields;
  focused regression coverage; non-runtime compile/test evidence and task records.
- Out of scope: daily-run business behavior changes, API/UI changes, schema
  migrations, external-model calls, browser/Playwright, service startup, real
  project data, B6/C14 activation, and commercial release claims.

## Success Criteria

- Persisted root reads reject text/bool/invalid versions and non-canonical root
  text/hash/time fields without coercion or normalization drift.
- The focused repository test and the filtered adjacent daily-run suite pass;
  compileall passes; ports 8911/5174/8910/4173 remain empty.
- Codex records exact evidence, any unavailable lint check, and residual risks.

## Risk Boundaries

- Only the explicitly scoped source/test files and task evidence files may change.
- Keep the real-loop gate read-only/blocked; no provider, sub-agent, runtime,
  browser, login, or real-project operation is allowed.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 07:00:40: Task initialized by `tools/hermes_workflow_guard.py init-task`.
