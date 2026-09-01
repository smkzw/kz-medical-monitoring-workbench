# Task Context: medical_monitoring_metric_api_20260805

Created: 2026-08-05 22:30:31
Objective: Expose the project-neutral medical monitoring metric-candidate contract through a read-only, project/batch/protocol-bound API service and route; retain candidate-only and medical-confirmation boundaries with no provider/runtime activation.
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_metric_configuration.py` (LOOP 5.318
  candidate-only contract)
- `services/api/app/monitoring_protocol_rule_repository.py` (`protocol_version`
  and `facts_for_version` source-bound reads)
- `services/api/app/monitoring_batch_repository.py` (`get_batch` and frozen
  batch readiness)
- `services/api/app/monitoring_ai_field_profiler.py` (complete frozen listing
  profile)
- `services/api/app/main.py` (workbench route wiring)
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
  (runtime gate remains blocked/read-only)

## Scope

- In scope: a read-only `MonitoringMetricConfigurationService`, a GET router
  bound to project/protocol-version/batch identity, deterministic service/router
  tests, and minimal main-app wiring. The route returns the existing candidate
  bundle plus explicit review metadata; it never confirms, stores, publishes,
  activates, or calls a provider.
- Out of scope: UI changes, provider/runtime activation, metric inference,
  medical confirmation endpoints, rule-pack changes, real project/browser
  execution, or medical-writing surfaces.

## Success Criteria

- Wrong or missing project/protocol/batch ownership fails closed with stable
  HTTP errors; only a frozen batch may be profiled.
- The service passes all protocol facts (including unconfirmed facts) to the
  existing builder so unsupported/unconfirmed declarations remain visible as
  issue rows rather than disappearing.
- The API response preserves `candidate_only`,
  `pending_medical_confirmation`, `medically_confirmed=false`, source/profile
  digests and explicit issue rows.
- Focused service/router tests and adjacent monitoring regressions pass;
  import/build validation passes.
- No service, browser, provider, API login or real project is started while the
  authoritative gate is blocked.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.
- The GET route must remain read-only in product semantics. Derived profiling may
  use the existing deterministic cache contract but must not mutate protocol,
  batch, fact, metric or confirmation state.
- Never infer a metric from project names, labels, trend arrays or field names;
  delegate to the strict builder only.
- Keep 8911, 5174, 8910 and 4173 stopped while the gate is blocked.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 22:30:31: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 22:30:31: Chosen bounded route: service reads protocol version,
  all facts and a complete frozen batch profile, then calls the existing
  candidate builder; router exposes only GET and returns candidate/review
  metadata. No AI/provider or write path is added.
- 2026-08-05 22:31–22:34: Added the service, router, main-app wiring and four
  API/service tests. Focused metric contract/API plus protocol-preparation,
  AI API, field-profiler and startup-recovery tests passed **113**; py_compile
  and main-app route discovery passed. Final full monitoring sweep passed
  **2540** with **25 warnings** in 1084.41 seconds.
- 2026-08-05 22:49: Runtime gate remains read-only/blocked; the route was not
  served and no browser/provider/API-login/real-project execution occurred.
