# Task Context: medical_monitoring_assurance_principal_host_adapter_20260803

Created: 2026-08-03 22:46:00
Objective: 为医学监查保障路由提供只读取 verified request.state principal 的主应用接线点，不解析凭据，不伪造登录，并保持无中间件时 fail-closed
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/main.py` (production dependency-injection registration)
- `services/api/app/monitoring_assurance_router.py` (fail-closed route boundary)
- `services/api/app/monitoring_runtime_principal.py` (verified principal envelope)
- `services/api/app/monitoring_runtime_route_context.py` (route binding and validation)
- `services/api/app/monitoring_identity_authorization.py` (role/action ACL)
- `tests/test_monitoring_assurance_principal_route.py` (route boundary contract)
- `tests/test_monitoring_runtime_principal.py` and
  `tests/test_monitoring_runtime_route_context.py` (identity contract)
- Official Starlette request/middleware documentation consulted for the host
  seam: https://www.starlette.io/requests/ and
  https://www.starlette.io/middleware/
- No production data, credentials, live service, browser session, or real
  project source was needed for this provider-neutral adapter.

## Scope

- In scope: add a provider-neutral adapter that reads only an already verified
  `MonitoringAuthenticatedPrincipal` from `request.state`; wire it into the
  assurance router registration; add positive/negative and static wiring tests.
- Out of scope: authentication/session middleware, token/cookie/header
  parsing, principal construction from unverified claims, default identities,
  authorization policy changes, durable audit/e-signature, migrations,
  service/browser/provider startup, real-project ingestion, and frontend
  product work.

## Success Criteria

- Missing or wrong-type request state resolves to `None`, leaving the existing
  route-level 503 fail-closed response intact.
- A verified principal object is returned unchanged and is the only value
  passed to the route's existing authorization boundary.
- `main.py` injects the adapter explicitly while retaining
  `require_server_principal=True` and no fallback actor.
- New adapter/wiring tests and the existing assurance/identity contracts pass;
  formatting/compile checks are run with any pre-existing main.py lint drift
  reported separately.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 22:46:00: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 22:55:00: Re-anchored current AGENTS hashes, upstream gates and
  main.py registration. Confirmed no host authentication provider exists; a
  narrow request.state seam is the next safe action.
- 2026-08-03 23:02:00: Added the state-only adapter, explicit main.py injection,
  and positive/negative/static tests. Focused suite passed; broad validation
  remains pending.
