# Task Context: medical_monitoring_ai_retryable_bool_20260803

Created: 2026-08-03 11:04:11
Objective: Harden persisted AI job retryable Boolean hydration with deterministic regressions while keeping B6/C14, providers, browser, services and real projects stopped.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Workbench source under `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Primary module: `services/api/app/monitoring_ai_repository.py`.
- Primary regression: `tests/test_monitoring_ai_repository.py`.
- P10 authority: `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md` and
  `REQUIREMENTS_TRACEABILITY.md`.
- Gate authority remains B6 `pending_review` and C14
  `blocked_pending_b6_review`.

## Scope

- In scope: strict SQLite Boolean hydration for the persisted AI-job
  `retryable` flag; deterministic malformed-value and valid 0/1 regressions;
  focused/adjacent/full monitoring tests and static checks; task records.
- Out of scope: provider calls, browser/API login, service starts, real-project
  data, queue policy changes, schema/migration changes, B6 reviewer outcomes,
  CAS/source-token activation, frontend work, and medical conclusions.

## Success Criteria

- Only actual Boolean or SQLite integer 0/1 values hydrate `MonitoringAiJob.retryable`;
  persisted text/other integers fail with `MonitoringAiRepositoryError` rather
  than Python truthiness.
- Existing create/claim/fail/retry behavior and valid 0/1 persistence remain green.
- Focused AI-repository tests, adjacent AI contract tests, full monitoring suite,
  Ruff check and compile pass without formatter churn.
- Review and metrics pass Hermes workflow `review-gate --require-verification`;
  P10 ledger/traceability record a compact 4.89 entry.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- No B6 outcome may be created or inferred; authority flags remain false.
- No provider/browser/API/service/CAS/project operation; synthetic temporary
  SQLite fixtures only. Keep 8911/5174 stopped and unrelated 8900 untouched.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 11:04:11: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Residual `bool(...)` audit found one direct persisted AI-job flag
  bridge: `_job()` coerces SQLite `retryable` with `bool(row["retryable"])`.
  This is the sole same-cause queue/retry boundary in the repository.
- 2026-08-03: Added `_sqlite_bool` and synthetic valid 0/1 plus malformed
  string/invalid-integer regressions. AI repository 42 passed; all
  `tests/test_monitoring_ai_*.py` 645 passed; Ruff/compile passed.
- 2026-08-03: Full monitoring recheck completed with **1818 passed, 25 warnings,
  515.18s**. The surrounding zsh wrapper reported a read-only-variable error
  after pytest output, so the acceptance evidence is the captured pytest summary
  in `/tmp/medical_monitoring_full_489_recheck_20260803.log`, verified by an
  independent assertion; no test failure was reported.
