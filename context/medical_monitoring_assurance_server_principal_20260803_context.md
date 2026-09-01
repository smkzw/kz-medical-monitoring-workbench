# Task Context: medical_monitoring_assurance_server_principal_20260803

Created: 2026-08-03 22:36:39
Objective: 接入医学监查保障写路径的服务器派生 principal 契约，禁止 client actor 作为身份，并保持无身份时 fail-closed
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_assurance_router.py`
- `services/api/app/monitoring_runtime_principal.py`
- `services/api/app/monitoring_runtime_route_context.py`
- `services/api/app/main.py` assurance-router registration
- `frontend/src/features/medical-monitoring/MedicalMonitoringAssurancePanel.jsx`
- `tests/test_monitoring_assurance.py` and focused principal-route tests
- FastAPI official dependency/security documentation consulted for the injected
  server-side resolver seam; no executable dependency was adopted.

## Scope

- In scope: make assurance write endpoints derive `created_by`/mutation actor
  from an injected server-verified `MonitoringAuthenticatedPrincipal`; reject
  missing providers, invalid project scope and any client actor; keep reads and
  the medical-writing module unchanged; remove the client actor from the
  assurance creation payload; add focused negative/positive API evidence.
- Out of scope: token/cookie parsing, authentication-provider implementation,
  SQLite migration, e-signature persistence, aggregate/CAS writes, real project
  ingestion, browser login, service startup, external model dispatch, and
  medical-writing changes.

## Success Criteria

- Production main registration explicitly enables `require_server_principal`.
- With no resolver, assurance writes return a visible 503 and do not create a
  task; with a verified in-scope principal, the task records the principal ID;
  a client-supplied actor is rejected even when it matches that ID.
- Focused API, principal/runtime, frontend contract, Node frontend suite and
  Vite build pass; no service or browser is started.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- The current main app intentionally has no provider resolver, so assurance
  writes remain blocked until the host authentication adapter is implemented.
- Existing legacy assurance-router tests opt out explicitly in their isolated
  harness; that opt-out is not used by `main.py`.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-03 22:36:39: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-03 22:37-22:40: Added fail-closed server-principal resolver seam,
  removed frontend client actor, added positive/negative route tests.
- 2026-08-03 22:40-22:43: Focused/adjacent Python tests 130 passed; complete
  frontend Node suite 37 passed; Vite build passed; ports remained empty.
- 2026-08-03 22:43: Hermes review-gate passed with no warnings.
