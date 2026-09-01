# Task Context: medical_monitoring_phase_c13_activation_projection_contract_20260802

Created: 2026-08-02 02:18:16
Objective: Define a read-only blocked activation-to-standard-event-to-Timeline/Profile projection contract over C8-C12 evidence; do not create events or activate mappings
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- C8 review-only coverage matrix, C11 cross-surface conservation report and C12
  inactive fallback/retirement policy matrix
- C4 `MonitoringClinicalEvent`/`MonitoringClinicalObservation`, C5
  `MonitoringClinicalReadModel` and C6 `ClinicalConsumerHandoff` contracts
- Current filesystem is authoritative; no real listing/protocol, browser, service, runtime
  database, adapter invocation or real-project data is in scope.

## Scope

- In scope: a blocked, read-only activation route that records how a future medically approved
  mapping would enter the shared C4 event/observation layer and C5/C6 Timeline/Profile/consumer
  projections. It must preserve C8/C11/C12 identity and explicitly report blockers.
- Out of scope: mapping activation, event/projection creation, source parsing, clinical values,
  API/React/UI changes, runtime persistence, adapter invocation, browser checks and real-project
  runs.

## Success Criteria

- Every C8 mapping is represented once or explicitly missing; identity and C8/C11/C12 hashes
  are conserved, and all 46 current rows are `blocked_pending_approval`.
- The route names the shared event and projection contracts, preserves consumer surface keys,
  requires five explicit blockers, and keeps event creation/projection/activation false.
- A deterministic blocked report plus focused/full tests pass without creating a clinical event.

## Risk Boundaries

- Generated artifacts are limited to this task's execution evidence path; no production,
  registry, runtime or database writes are allowed.
- The route must not infer a source value, baseline, CTCAE, severity, normality, treatment
  identity, risk or clinical readiness from C8-C12 structural evidence.
- Codex is the implementation, review and acceptance authority; no delegated agent, Hermes
  route or conference is used.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-02 02:18:16: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-02 02:19: direct task contract filled; current C8-C12 inputs remain review-only,
  schema-only and inactive; C13 will describe a blocked future route only.
- 2026-08-02 02:20: added activation projection contract, tests and deterministic blocked
  report builder. 46/46 rows are blocked pending approval; no event or projection was created.
