# Task Context: medical_monitoring_ai_job_attempts_strict_20260804

Created: 2026-08-04 23:43:59
Objective: Reject boolean retry counts in independent-AI job contracts
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_contracts.py`: immutable AI job-create and job state models.
- `tests/test_monitoring_ai_repository.py`: repository/job contract regressions.
- Existing monitoring-AI evaluation, quality, real-loop, assurance, B6/C14 and release records.

## Scope

- In scope: reject boolean retry/attempt counts in `MonitoringAiJobCreate` and `MonitoringAiJob`; add a direct regression; run offline repository and monitoring-AI checks.
- Out of scope: queue mutation, provider/runtime startup, browser or Playwright login, API login, real projects, medical review, and production writes.

## Success Criteria

- `max_attempts` and persisted `attempt_count` accept strict integers and reject bool values.
- Canonical repository behavior remains covered; changed Python compiles and reserved ports remain empty.

## Risk Boundaries

- Only the AI job contracts, focused repository regression, and task-scoped context/review/metrics/active-slice/ledger records may change.
- No delegated agent, Hermes dispatch, queue/database mutation, service/provider startup, browser/Playwright/API login, real-project import, medical-writing artifact, or production artifact mutation.
- Codex remains final authority; review-gate does not grant provider, medical, or release authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 23:43:59: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 23:44:00: Source inspection found ordinary Pydantic integer fields for job retry/attempt counts, allowing bool coercion.
- 2026-08-04 23:46:00: Switched job retry/attempt fields to `StrictInt` and added a direct bool regression; repository and decisive monitoring-AI suites passed.
