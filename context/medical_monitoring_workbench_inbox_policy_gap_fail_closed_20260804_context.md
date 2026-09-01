# Task Context: medical_monitoring_workbench_inbox_policy_gap_fail_closed_20260804

Created: 2026-08-04 06:06:13
Objective: 为已注册医学监查项目的复合 workbench-inbox GET 与 mark-read HTTP 写入增加身份/项目范围后的显式 policy-gap fail-closed；不复用 READ_MONITORING 作为完整收件箱权限，不新增 action/role，不影响医学写作绿地项目
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/main.py` `GET /workbench-inbox` and generic inbox-action
  handlers; `_authorize_legacy_monitoring_action` and the existing policy-gap
  helper.
- `services/api/app/workbench_inbox.py` composite item builder and mark-read
  state store; monitoring risk-disposition routes remain separately guarded.
- `tests/test_rux_monitoring_service.py`, `tests/test_my009_monitoring_service.py`,
  `tests/test_monitoring_risk_index_api.py`, frontend identity contracts and
  current P10/B6/C14 records.
- Current action matrix: `READ_MONITORING` protects risk/subject evidence, but
  no exact composite workbench-inbox read or cross-module mark-read action is
  configured.

## Scope

- In scope: for canonical projects registered with
  `monitoring_project_registry` (and the MG-K10 demo project), require a
  server principal/project scope and then return explicit
  `monitoring_read_action_unconfigured` 403 for inbox GET, or
  `monitoring_write_action_unconfigured` 403 for generic mark-read POST,
  before inbox construction or store mutation.
- In scope: preserve direct `WorkbenchInboxService.inbox/apply_action` tests;
  keep risk-disposition endpoints on their existing exact high-risk action.
- Out of scope: user-created medical-writing projects, dashboard, AI-run
  reads/writes, safety/TFL/medical-writing specialized actions, service/store
  contract, frontend, DB/schema/migration, auth middleware/provider,
  browser/API login, external models, real projects and B6/C14 activation.

## Success Criteria

- Missing principal returns 503 before inbox service access.
- A scoped principal for a registered monitoring project receives the explicit
  read/write policy-gap code and patched inbox service/store is not called.
- Direct inbox composition and mark-read semantics remain covered.
- Targeted compile/focused/adjacent/full monitoring tests and Hermes
  review-gate pass; reserved ports remain stopped/empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 06:06:13: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04: Inventory classified the inbox as a cross-module composite, so
  neither `READ_MONITORING` nor a generic write action is semantically exact.
