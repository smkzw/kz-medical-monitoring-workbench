# Task Context: medical_monitoring_ai_field_profile_int_strict_20260804

Created: 2026-08-04 23:16:03
Objective: Reject boolean numeric fields in monitoring AI listing field-profile validation
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_service.py`: listing field-profile input validation.
- `tests/test_monitoring_ai_service.py`: field-profile and chunk-contract tests.
- Existing independent-AI, source-token, approved-input, B6/C14 and release records.

## Scope

- In scope: reject boolean numeric values in row counts, relationship aggregate counts, and complete-profile chunk counts; add focused regressions; record offline evidence.
- Out of scope: provider/runtime startup, browser or Playwright login, API login, real projects, medical review, database state, and production writes.

## Success Criteria

- Boolean numeric values cannot pass listing field-profile validation as 0/1.
- Canonical integer profile, relationship, and chunk behavior remains covered.
- Monitoring-AI and real-loop/assurance tests pass, changed Python compiles, and reserved ports remain empty.

## Risk Boundaries

- Only the monitoring-AI service, focused test, and task-scoped evidence/review/metrics/ledger records may change.
- No delegated agent, Hermes dispatch, service/provider startup, browser/Playwright/API login, database mutation, real-project import, medical-writing artifact, or production artifact mutation.
- Codex remains final authority; review-gate does not grant provider, medical, or release authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 23:16:03: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 23:17:00: Source inspection found three field-profile numeric validation sites accepting bool as int; no runtime/provider/browser action was permitted.
- 2026-08-04 23:19:00: Added a shared non-boolean integer predicate and row/relationship/chunk regressions; monitoring-AI and real-loop offline suites passed.
