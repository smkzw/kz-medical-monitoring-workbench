# Task Context: medical_monitoring_ai_router_numeric_strict_20260804

Created: 2026-08-04 23:45:55
Objective: Reject boolean numeric fields at independent-AI API request boundaries
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_router.py`: independent-AI API request models.
- `tests/test_monitoring_ai_api.py`: API/model boundary regressions.
- Existing monitoring-AI service, repository, evaluation, real-loop, assurance, B6/C14 and release records.

## Scope

- In scope: reject boolean chunk sizes, retry counts, and mapping-draft versions at request-model boundaries; add a direct model regression; run offline API/repository/service and decisive monitoring-AI checks.
- Out of scope: API server startup, provider/runtime calls, browser or Playwright login, real projects, medical review, database state, and production writes.

## Success Criteria

- Numeric API request fields accept strict integers and reject bool values before endpoint logic.
- Existing canonical integer requests remain compatible; changed Python compiles and reserved ports remain empty.

## Risk Boundaries

- Only the monitoring-AI router, its API test, and task-scoped context/review/metrics/active-slice/ledger records may change.
- No API server, provider/runtime startup, browser/Playwright/API login, database mutation, real-project import, medical-writing artifact, or production artifact mutation.
- Codex remains final authority; review-gate does not grant API, provider, medical, or release authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 23:45:55: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 23:46:00: Source inspection found ordinary Pydantic integer fields for chunk size, retry counts, and draft version preconditions.
- 2026-08-04 23:48:00: Switched six request fields to `StrictInt`/`Optional[StrictInt]` and added a direct six-case regression; API/repository/service and decisive monitoring-AI checks passed.
