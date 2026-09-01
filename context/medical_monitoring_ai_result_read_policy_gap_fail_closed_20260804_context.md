# Task Context: medical_monitoring_ai_result_read_policy_gap_fail_closed_20260804

Created: 2026-08-04 06:21:25
Objective: 为 canonical/reference medical monitoring projects 的 ai-runs list/detail/artifacts GET 增加身份/项目范围后的显式 policy-gap fail-closed；不复用现有读取 action 作为 AI 结果授权，不新增 action/role，不影响直接 runner/service projection
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/main.py` generic AI run list/detail/artifact GET handlers,
  `_reject_legacy_monitoring_read_policy_gap`, and current source-driven
  execution denial.
- `services/api/app/ai_task_runner.py` public run/artifact projections and
  `tests/test_ai_execution_policy.py`, plus frontend AI-run identity contract.
- Current action matrix and P10/B6/C14 records: no exact AI-result read action
  exists; source-evidence/monitoring reads must not be widened into it.

## Scope

- In scope: canonical/reference project `GET /ai-runs`, `GET /ai-runs/{run_id}`
  and `GET /ai-runs/{run_id}/artifacts`: authenticate/project-scope-check then
  explicit `monitoring_read_action_unconfigured` 403 before runner reads.
- In scope: no-principal 503 and scoped-principal 403/no-runner regressions;
  retain direct `AiTaskRunner` and public projection service tests.
- Out of scope: new AI read/execute action, provider/runtime, source registry,
  inbox/dashboard, user-created medical-writing routes, frontend, DB/schema/
  migration, auth middleware/provider, browser/API login, external models,
  real projects and B6/C14 activation.

## Success Criteria

- Missing principal returns 503 before `ai_task_runner` access.
- A valid scoped principal receives explicit AI-read policy-gap 403 and the
  patched runner is not called.
- Direct runner/provider/public projection behavior remains covered.
- Focused/adjacent/full monitoring tests and Hermes review-gate pass; ports
  remain stopped/empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 06:21:25: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Generic AI run reads were classified as a separate result-access
  boundary; no existing monitoring/source action is semantically exact.
- 2026-08-04 pause checkpoint: source code and focused tests are complete;
  focused AI policy/source-registry selection passed **4** with **17 existing
  warnings** in **1.53s**; adjacent AI/source/frontend suite passed **51** with
  **17 existing warnings** in **17.41s**. The full monitoring run was started
  once as session `47401`, reached approximately **73%**, then was interrupted
  at the user's explicit pause request. Its log is
  `/private/tmp/medical_monitoring_ai_result_read_gap_full_20260804.log`; no
  `.rc` result was produced, so the slice was not closed and no review-gate was
  run. Resume by rerunning the full suite once, then record the result and run
  the review-gate; do not redo the focused suites unless the source changes.
- 2026-08-04 resume: one clean full `tests/test_monitoring*.py` run completed
  with **1948 passed, 25 warnings, 485.14s**, exit code **0**. The earlier
  session `47401` remains historical only. The slice is ready for the Hermes
  `review-gate --require-verification`; no service, browser, provider,
  migration, real-project or reserved-port action was run.
- 2026-08-04 closure: Hermes `review-gate --require-verification` returned
  `{"ok": true, "warnings": [], "errors": []}`. LOOP 5.84 is closed; next
  bounded action is dashboard policy-gap inventory. Guarded AI-result reads
  remain closed until a named exact action and its source/CAS, audit and
  runtime contracts are defined.
