# Task Context: medical_monitoring_lifecycle_policy_gap_fail_closed_20260804

Created: 2026-08-04 05:19:09
Objective: 为医学监查批次 confirm-full-snapshot 与 transition 两个无精确 action 的生命周期写路由增加显式 fail-closed policy-gap 403，不新增 action/role、不执行状态变更；更新 API 回归并完整验证
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/main.py` batch lifecycle handlers
  `confirm-full-snapshot` and `transition`.
- `services/api/app/medical_monitoring_router.py` existing
  `reject_unconfigured_write` pattern and explicit
  `monitoring_write_action_unconfigured` contract.
- `services/api/app/monitoring_identity_authorization.py`: no existing action
  precisely describes full-snapshot confirmation or generic batch state
  transition.
- `tests/test_monitoring_batch_api.py`, lifecycle repository tests and the
  current P10/B6/C14 gate records.

## Scope

- In scope: fail closed before repository/service mutation for the two legacy
  lifecycle routes; require a server principal and project read scope only to
  distinguish unauthenticated access from the explicit policy-gap 403; update
  route tests to prove no mutation and preserve service-layer lifecycle tests.
- Out of scope: new action/role, action-matrix changes, lifecycle state-machine
  redesign, source registration, inbox/AI/dashboard routes, auth middleware,
  frontend, DB/schema/migration, services/browser/API login, external model,
  real projects, B6/C14 or Playwright/UAT activation.

## Success Criteria

- Missing principal returns 503 before batch repository/service lookup.
- A project-scoped principal receives 403 with
  `monitoring_write_action_unconfigured` and no batch state mutation.
- Existing lifecycle service/repository unit behavior remains covered without
  treating the HTTP route as authorized.
- Focused/adjacent/full monitoring tests, `py_compile` and Hermes review-gate
  pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 05:19:09: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Policy inventory confirmed no exact lifecycle action; selected
  explicit fail-closed denial, following the existing nested monitoring-router
  contract, without adding generic write permission.
- 2026-08-04: Focused suite passed 16; full `tests/test_monitoring*.py`
  passed 1947 with 25 existing warnings in 543.26s (exit code 0). Hermes
  review-gate passed; slice closed.
