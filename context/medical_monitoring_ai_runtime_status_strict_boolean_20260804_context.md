# Task Context: medical_monitoring_ai_runtime_status_strict_boolean_20260804

Created: 2026-08-04 23:02:45
Objective: Require literal boolean semantic-AI and configured flags in monitoring AI runtime resolution and transport validation
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_service.py`: runtime resolver and transport validation.
- `tests/test_monitoring_ai_service.py`: runtime and provider-boundary regression contracts.
- Existing P10/B6/C14/approved-input/host-identity and release records.

## Scope

- In scope: require literal boolean `configured` and `semantic_ai_tasks_enabled` at the two monitoring-AI runtime consumers; add focused string-status regressions; record offline evidence.
- Out of scope: provider/runtime startup, browser or Playwright login, API login, database state, real projects, medical approval, medical-writing artifacts, and release promotion.

## Success Criteria

- String-valued configured or semantic-AI flags cannot make runtime resolution available or transport validation pass.
- Canonical boolean runnable profiles remain covered by the existing tests.
- Monitoring AI and adjacent real-loop/assurance tests pass, changed Python compiles, and reserved ports remain empty.

## Risk Boundaries

- Only the monitoring-AI service, focused test, and task-scoped evidence/review/metrics/ledger records may change.
- No delegated agent, Hermes dispatch, provider call, service startup, browser/Playwright/API login, database mutation, real-project import, or production artifact mutation.
- Codex remains final authority; review-gate does not grant runtime or medical approval.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 23:02:45: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 23:03:00: Source scan found two monitoring-AI consumers using truthiness for gateway flags; no runtime/provider/browser action was permitted.
- 2026-08-04 23:05:00: Changed both consumers to literal-boolean checks and added resolver/transport regressions; focused and full offline suites passed.
