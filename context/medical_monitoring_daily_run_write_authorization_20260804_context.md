# Task Context: medical_monitoring_daily_run_write_authorization_20260804

Created: 2026-08-04 00:21:17
Objective: 为日常增量运行的准备、处理、规则执行、AI提交、风险汇总、部分确认和替代写入动作接入既有服务器 principal/ACL 边界，生产无 principal 继续 503，不新增认证供应商或绕过上游门禁
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_router.py`: daily-run write route
  table and the read guard completed immediately before this task.
- `services/api/app/monitoring_identity_authorization.py`: existing role/action
  ACL; this task must reuse actions and add no new action.
- `services/api/app/monitoring_runtime_principal.py`,
  `services/api/app/monitoring_runtime_route_context.py` and
  `services/api/app/monitoring_principal_host_adapter.py`: verified-principal
  seam and server-derived actor contract.
- `services/api/app/main.py`: production router wiring.
- `tests/test_monitoring_daily_run_router.py` plus assurance principal-route
  tests: accepted fail-closed and explicit legacy-harness patterns.
- Current filesystem and upstream P10/B6/C14 gates are authoritative; no live
  service, provider, browser or real project may be started.

## Scope

- In scope: protect daily-run writes before repository/service mutation and
  derive the actor from the verified server principal. Map existing routes to
  existing ACL actions: prepare→`INTAKE_BATCH`; process/execute-rules→
  `RUN_DETERMINISTIC_RULES`; submit-AI/assemble-risks/acknowledge-partial/
  ready-to-confirm→`REVIEW_AI_CANDIDATE`; supersede/confirm→
  `CHANGE_RISK_DISPOSITION`. Transitional request actor/confirmed_by fields
  may remain for compatibility but are ignored for production identity.
- Keep the explicit offline factory bypass for current repository/service tests;
  production `main.py` must remain `require_server_principal=True` with the
  existing host adapter. Preserve CAS, lease, idempotency and downstream error
  semantics. Add missing-principal, unauthorized-role, project-scope and
  server-actor tests.
- Out of scope: authentication/session middleware, IdP/JWT/cookie/header
  parsing, denied-attempt persistence, new ACL actions, e-signature/reauth
  schema redesign for confirmation, repository/service/schema changes,
  frontend visual work, service/browser/provider login, runtime DB, real
  projects, B6/C14/approved-input gates or live test-provider dispatch.

## Success Criteria

- Every daily-run write route fails closed before mutation when the production
  principal is absent or invalid and rejects roles/scopes without the mapped
  action with 403.
- A scoped medical manager can reach the existing service path, while a
  payload-supplied actor cannot become the persisted event actor; the actor is
  the verified principal ID. Legacy harness tests continue to use their
  explicit bypass only.
- Existing read guard remains intact; focused, adjacent and full monitoring
  tests, Ruff/py_compile and review-gate pass. Reserved ports stay empty.
- Confirmation is protected by role/project identity but remains explicitly
  unclaimed as a final e-signature/reauth acceptance until its request contract
  is expanded in a separate controlled slice.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 00:21:17: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 00:22:xx: Existing ACL actions were inspected; no new route action
  or authentication provider will be invented.
