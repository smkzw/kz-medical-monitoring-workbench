# Task Context: medical_monitoring_runtime_route_context_20260803

Created: 2026-08-03 15:30:10
Objective: Add a provider-neutral route-context contract that binds the server-verified monitoring principal to canonical tenant/project/action without wiring FastAPI or runtime writes
Task type: `finite_code_task`
Risk: `high`
Selected agent route: `opencode-go` / `deepseek-v4-flash` / `max`

## Trigger Reason

Phase G follow-up after the offline principal envelope and visible frontend gate:
the future API route needs one immutable seam that binds server identity to the
canonical tenant/project/action before authorization, audit and mutation are wired.

## Source Of Truth

- `services/api/app/monitoring_runtime_principal.py`
- `services/api/app/monitoring_runtime_route_context.py`
- `tests/test_monitoring_runtime_route_context.py`
- Existing B6/C14 gate JSON, P10 ledger and route source inspection.

## Scope

- In scope: provider-neutral route context, tenant/project/action binding, client-actor rejection,
  safe public handoff and focused/full regression evidence.
- Out of scope: token/cookie/header parsing, provider/IdP integration, FastAPI dependency wiring,
  authorization decision, audit append, CAS/source revision checks, runtime writes, B6/C14 action,
  service/browser/API login and real projects.

## Success Criteria

- A live server principal must be validated before a context can be built.
- Tenant and canonical project must match the principal; client actor values are never authoritative.
- The context stops before `authorize_monitoring_action`, audit or mutation.
- Focused, full monitoring regression, compileall and Ruff pass; B6/C14 and ports are unchanged.

## Risk Boundaries

- This seam is an offline contract only; it cannot authenticate a caller or grant write permission.
- Do not wire a route or replace default actors until the formal B6 chain and actual provider mapping pass.
- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The workflow route was recorded but not dispatched; Codex owns verification and acceptance.

## Verification

- Route context/identity/audit/authorization focused set: 31 passed.
- Complete `tests/test_monitoring_*.py`: **1833 passed, 25 existing warnings in 485.87s**.
- `compileall` and Ruff passed for the new module/test.
- No service/provider/browser/API login, runtime DB, B6/C14 action or real project ran.

## Route map captured for the next controlled seam

- The first isolated write candidate is `POST /api/projects/{project_id}/monitoring/assurance/tasks`
  in `services/api/app/monitoring_assurance_router.py:164-188`, mounted by `main.py:3075-3084`.
- It currently accepts `actor: str = Field(default="medical_manager")` and passes that value directly
  to `service.create_task`; this remains an explicitly recorded P1 residual and was not changed here.
- The next controlled implementation must canonicalize `project_id`, inject the actual server principal,
  build this route context with `MonitoringAction.COMPLETE_ASSURANCE`, evaluate authorization, append the
  audit event and only then call the service. The request's actor/owner contract must be redesigned in that
  same change; the frontend's transitional actor payload must not be promoted as identity.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 15:30:10: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03: Added immutable route context and negative bindings; full monitoring regression passed.
