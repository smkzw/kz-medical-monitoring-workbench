# Task Context: medical_monitoring_ai_execution_policy_gap_fail_closed_20260804

Created: 2026-08-04 05:32:46
Objective: 为 legacy ai-runs/from-sources 入口增加显式 fail-closed policy-gap 403，身份/项目范围检查后不得调用 runner/provider；不新增 action/role、不改 AI service contract，更新 API 回归并完整验证
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/main.py` `POST /api/projects/{project_id}/ai-runs/from-sources`.
- `services/api/app/ai_task_runner.py` and `ai_execution_policy.py` for the
  downstream execution/provider boundary.
- `services/api/app/medical_monitoring_router.py` existing explicit
  `monitoring_write_action_unconfigured` policy-gap pattern.
- `tests/test_ai_execution_policy.py`, `tests/test_source_registry.py` and
  current P10/B6/C14 gate records.

## Scope

- In scope: require server principal/project scope and return explicit
  `monitoring_write_action_unconfigured` 403 before
  `ai_task_runner.submit_registered`; preserve direct runner/service tests and
  the already-blocked direct `/ai-runs` endpoint; add no-principal and scoped
  no-runner regressions.
- Out of scope: new AI action/role, provider/runtime configuration, AI result
  read authorization, source registration, dashboard/inbox, frontend,
  DB/schema/migration, auth middleware/provider, browser/API login, external
  model, real projects, B6/C14 or Playwright/UAT activation.

## Success Criteria

- Missing principal returns 503 before runner/provider invocation.
- A scoped principal receives 403 with
  `monitoring_write_action_unconfigured`; patched runner is not called.
- Direct runner/service source-fidelity and policy tests remain covered.
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

- 2026-08-04 05:32:46: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Existing action matrix has candidate review and deterministic rule
  execution, but no exact generic AI execution action for this cross-module
  source-driven endpoint; selected explicit fail-closed denial.
