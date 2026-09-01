# Task Context: medical_monitoring_candidate_workflow_principal_gate_20260805

Created: 2026-08-05 23:15:40
Objective: Harden protocol-preparation and rule-template recommendation monitoring routes so production request identity is server-derived and fail-closed, preserving explicit offline test opt-out, then run focused and adjacent verification without starting services or changing runtime state.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_protocol_preparation_router.py`
- `services/api/app/monitoring_rule_template_recommendation_router.py`
- `services/api/app/monitoring_metric_configuration_router.py` (reference fail-closed route pattern)
- `services/api/app/monitoring_runtime_principal.py`
- `services/api/app/monitoring_runtime_route_context.py`
- `services/api/app/monitoring_identity_authorization.py`
- `services/api/app/main.py` production router wiring
- focused router tests under `tests/`
- current runtime gate: `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`

## Scope

- In scope: add injected host-principal resolution and fail-closed authorization to the
  protocol-preparation and rule-template-recommendation routers; derive the service actor
  from the verified principal; keep an explicit `require_server_principal=False` branch
  only for offline tests; wire both production routers through the existing host adapter;
  update focused tests and evidence records.
- Out of scope: starting services or providers, Playwright/browser or real-project runs,
  writes to runtime SQLite, changing B6/C14 or release status, authentication middleware,
  AI prompt/provider behavior, frontend, medical writing, or unrelated router refactors.

## Success Criteria

- Production defaults require a `MonitoringAuthenticatedPrincipal` and return stable
  fail-closed 503/401/403 responses before service access or mutation.
- Candidate decision requests cannot make client `actor` authoritative; accepted/rejected
  service calls receive the server-derived principal ID.
- Explicit offline tests continue to pass only when they opt out of the server-principal
  gate.
- Main production wiring passes `resolve_monitoring_principal_from_request` with the
  default gate enabled for both routers.
- Focused and adjacent monitoring tests, `py_compile`, Ruff, review-gate, and source/hash
  verification pass; no listener is opened and the real-loop gate remains blocked.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 23:15:40: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: selected as the next source-only P10 convergence slice after the metric
  candidate read gate; existing production candidate workflows still lacked the same
  host-principal boundary.
- 2026-08-05: implemented both route gates, wired production host adapter, added
  actor-spoofing/fail-closed tests, and recorded 75 focused plus 142 adjacent passes.
  Real-loop gate remains read-only/blocked and all monitored ports remain empty.
