# Task Context: medical_monitoring_daily_run_read_authorization_20260804

Created: 2026-08-04 00:08:18
Objective: 为日常增量运行的列表、就绪、详情和 AI 进度读取面接入 READ_MONITORING 服务器身份边界，生产无 principal 继续 503，保留明确隔离的旧测试 harness
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_router.py`: daily-run route table and
  injected router dependencies.
- `services/api/app/monitoring_assurance_router.py`: the accepted
  provider-neutral server-principal/ACL pattern used by the preceding slice.
- `services/api/app/monitoring_identity_authorization.py`: canonical
  `READ_MONITORING` action and role/project scope rules.
- `services/api/app/monitoring_runtime_route_context.py`,
  `services/api/app/monitoring_runtime_principal.py` and
  `services/api/app/monitoring_principal_host_adapter.py`: server-verified
  principal seam; no token/cookie/header parsing is allowed here.
- `services/api/app/main.py`: production router wiring, where the principal
  resolver is already available for assurance and the host middleware remains
  absent.
- `tests/test_monitoring_daily_run_router.py` and
  `tests/test_monitoring_assurance_principal_route.py`: legacy harness and
  production boundary test patterns.
- Current filesystem and the upstream P10/B6/C14 gates are authoritative;
  no live service or real project may be started in this slice.

## Scope

- In scope: protect the four daily-run read surfaces (`GET /`,
  `GET /readiness`, `GET /{run_id}`, `GET /{run_id}/ai-progress`) with the
  existing `READ_MONITORING` server-principal/tenant/project/ACL decision;
  add an injected provider-neutral resolver and an explicit offline harness
  switch; add missing/unauthorized/scoped-principal tests; keep project
  canonicalization and 404 semantics.
- The production `main.py` route must use `require_server_principal=True` and
  `resolve_monitoring_principal_from_request`; absent identity remains 503.
- Out of scope: authentication/session middleware, IdP/JWT/cookie/header
  parsing, denied-attempt persistence, any new ACL action, all daily-run write
  routes, schema/repository/service changes, frontend, service/browser/provider
  login, runtime DB, real projects, B6/C14/approved-input gates, or product
  visual/UAT work.

## Success Criteria

- Every in-scope read route accepts `Request`, calls the shared provider-neutral
  identity seam before repository/service lookup, and uses `READ_MONITORING`.
- Missing or malformed server principal returns 503; an authenticated
  principal without project scope or role returns 403; a scoped medical
  manager preserves existing 200/404 responses.
- The explicit legacy offline harness remains usable without a fake production
  identity and is not used by `main.py`; no route accepts a client actor as
  read identity or mutates state.
- Dedicated and adjacent tests, Ruff/py_compile, a full monitoring regression
  and the Hermes review-gate pass; reserved ports remain empty.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 00:08:18: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 00:09:xx: Read the daily-run route table and confirmed its list,
  readiness, detail and AI-progress reads had no server identity seam, while
  the preceding assurance route already provides the accepted fail-closed
  pattern. No host authentication middleware exists yet.
