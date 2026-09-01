# Task Context: medical_monitoring_daily_run_verified_owner_20260805

Created: 2026-08-05 00:31:34
Objective: 使日常运行生产路由的租约 owner 与事件 actor 仅来自服务器验证 principal，保留显式离线 harness 兼容并完成聚焦回归
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_router.py`: production daily-run route
  authorization and the four worker-mediated write routes.
- `services/api/app/monitoring_daily_run_service.py` and
  `services/api/app/monitoring_daily_run_analysis_service.py`: lease ownership,
  persisted event actor, CAS and risk-assembly behavior.
- `services/api/app/monitoring_runtime_principal.py`,
  `services/api/app/monitoring_runtime_route_context.py` and
  `services/api/app/monitoring_identity_authorization.py`: verified server
  principal seam and existing ACL contract.
- `tests/test_monitoring_daily_run_router.py`: production boundary and explicit
  offline-harness regressions.
- Current P10/B6/C14 and release-gate records: no live runtime, provider,
  browser, Playwright, API login or real-project action is allowed in this
  slice.

## Scope

- In scope: make production `process`, `execute-rules`, `submit-ai` and
  `assemble-risks` pass the verified `server_actor` as the orchestration owner;
  keep the `require_server_principal=False` harness behavior explicit; add
  regression coverage that a payload `owner` cannot become a lease/event actor;
  run focused and adjacent offline validation.
- Out of scope: authentication middleware, new ACL actions, provider or
  signature verification, repository schema changes, frontend, B6/C14,
  approved-input or runtime activation, services, browser/Playwright/API login,
  real projects, medical-writing files, and external model dispatch.

## Success Criteria

- In the production router branch, all four worker-mediated write routes pass
  the verified principal actor to their service; request-body `owner` remains
  only a compatibility field and cannot control lease ownership or persisted
  event actor.
- The explicit offline harness continues to pass its legacy request owner to
  the service, preserving isolated unit-test semantics without weakening the
  production branch.
- Focused router tests, adjacent daily-run contracts, compile/lint checks and
  the review gate pass; reserved service ports remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- This is a source-only authorization-boundary repair; it does not create
  medical authority or imply a real reviewer outcome.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 00:31:34: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 00:32:xx: Narrow source review found that `authorize_write`
  returned the verified principal actor but four production routes still passed
  the payload `owner` into lease/event orchestration. This slice targets only
  that identity propagation gap.
- 2026-08-05 00:4x: The router and regression were updated. Focused 42 and
  adjacent 124 tests passed under `.venv`; compile, Ruff, port checks and the
  Hermes review-gate passed. Live/runtime/medical authority remains closed.
