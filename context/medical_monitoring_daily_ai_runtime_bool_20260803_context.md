# Task Context: medical_monitoring_daily_ai_runtime_bool_20260803

Created: 2026-08-03 11:29:50
Objective: Harden the daily monitoring AI runtime availability Boolean boundary with deterministic regressions while keeping B6/C14, providers, browser, services and real projects stopped.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Workbench source under `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`.
- Primary module: `services/api/app/monitoring_daily_run_service.py`.
- Primary regression: `tests/test_monitoring_daily_run_service.py`.
- P10 authority: `records/active_slices/medical_monitoring_goal_p10_20260730/LOOP_LEDGER.md` and
  `REQUIREMENTS_TRACEABILITY.md`.
- Gate authority remains B6 `pending_review` and C14
  `blocked_pending_b6_review`.

## Scope

- In scope: strict literal-Boolean handling for the AI runtime resolver's
  `available` status in `_require_ai_runtime`; add synthetic malformed-value
  regressions; run focused/adjacent/full monitoring tests and static checks;
  record evidence.
- Out of scope: provider calls, runtime starts, browser/API login, real-project
  data, AI routing/policy changes, schema/migration work, B6 reviewer outcomes,
  CAS/source-token activation, frontend work and medical conclusions.

## Success Criteria

- Literal `True` continues to pass the availability gate; `False`, missing,
  string and numeric values fail with `monitoring_ai_not_ready` before any AI
  operation.
- Existing transport and diagnostic checks remain unchanged.
- Focused daily-run tests, adjacent AI/daily-run contracts, full monitoring
  suite, Ruff and compile pass without formatter churn.
- Review/metrics pass Hermes workflow `review-gate --require-verification` and
  P10 records a compact 4.91 entry.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- No provider call or real runtime invocation; only synthetic resolver objects.
- No B6 outcome may be created or inferred; authority flags remain false.
  Keep 8911/5174 stopped and unrelated 8900 untouched.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 11:29:50: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Residual scan found `_require_ai_runtime` using
  `bool(getattr(ai_runtime, "available", False))`, which could treat a truthy
  string as AI readiness and bypass a safety block.
- 2026-08-03: Changed the guard to literal `True` and added malformed string/
  integer regressions. Daily-run/AI/repository/router set 65 passed; record-rule
  and release-chain adjacent set 51 passed; Ruff and compile passed. No provider
  or runtime call was made.
