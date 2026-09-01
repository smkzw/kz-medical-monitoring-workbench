# Task Context: medical_monitoring_ai_router_principal_gate_20260805

Created: 2026-08-05 23:24:26
Objective: Harden all production medical-monitoring AI HTTP routes with server-derived principal authorization and explicit action boundaries, preserving offline test opt-out, then run focused/adjacent verification without starting services or providers.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_router.py`
- `services/api/app/monitoring_metric_configuration_router.py` and the
  already-hardened daily-run/assurance routes as the route boundary reference
- `services/api/app/monitoring_runtime_principal.py`
- `services/api/app/monitoring_runtime_route_context.py`
- `services/api/app/monitoring_identity_authorization.py`
- `services/api/app/main.py` production AI-router wiring
- `tests/test_monitoring_ai_api.py` and
  `tests/test_monitoring_ai_v7_deterministic_repair.py`
- current real-loop gate:
  `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

## Scope

- In scope: add injected host-principal resolution and fail-closed route
  authorization to every monitoring AI read/write endpoint; bind canonical
  project/tenant/action/request identity; derive actor/confirmed-by values from
  the verified principal; preserve an explicit offline-test opt-out; wire the
  production main app; add focused route-boundary tests and update evidence.
- Out of scope: authentication middleware or token parsing, AI provider/model
  behavior, prompt changes, persistence migrations, real jobs, runtime SQLite,
  service/provider/browser startup, real projects, medical writing, B6/C14 or
  release-state changes, and broad refactors of the AI service itself.

## Success Criteria

- Production default requires `MonitoringAuthenticatedPrincipal` for all AI
  routes and fails closed before repository/service/provider wake access.
- Reads use explicit read actions; job/candidate/mapping mutations use an
  explicit existing monitoring write action. Client actor fields never become
  the persisted service identity.
- Existing AI API and deterministic-repair tests continue only through an
  explicit offline opt-out; no production wiring opts out.
- Focused/adjacent tests, py_compile, Ruff, review-gate, source hashes and
  listener checks pass; the real-loop gate remains blocked/read-only.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 23:24:26: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 23:24: route selected after closing the adjacent protocol/rule
  candidate identity gap; the AI router remained the largest unauthenticated
  monitoring surface.
- 2026-08-05: all AI read/write route handlers now call the shared local
  fail-closed authorization seam; offline AI API tests explicitly opt out, and
  focused route/API regression passed without runtime/provider access.
