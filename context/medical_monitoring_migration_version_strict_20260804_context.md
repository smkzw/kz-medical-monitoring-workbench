# Task Context: medical_monitoring_migration_version_strict_20260804

Created: 2026-08-04 23:30:43
Objective: Reject boolean schema versions in read-only monitoring migration contracts
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_migration_contract.py`: read-only migration ledger, observation, and store-version validation.
- `tests/test_monitoring_migration_contract.py`: migration contract regressions.
- Existing B6/C14, approved-input, CAS, real-loop, release, and clinical-contract records.

## Scope

- In scope: reject boolean schema versions in migration specs, observations, and store snapshots; add direct regressions; run offline monitoring regressions and record evidence.
- Out of scope: database migration execution, provider/runtime startup, browser or Playwright login, API login, real projects, medical review, and production writes.

## Success Criteria

- Boolean values cannot enter migration schema-version or store-version contracts as integers.
- Canonical integer migration plans and read-only reconciliation behavior remain covered; changed Python compiles and reserved ports remain empty.

## Risk Boundaries

- Only the migration contract, its focused test, and task-scoped context/review/metrics/active-slice/ledger records may change.
- No migration executor, database mutation, service/provider startup, browser/Playwright/API login, real-project import, medical-writing artifact, or production artifact mutation.
- Codex remains final authority; review-gate does not grant migration, provider, medical, or release authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 23:30:43: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 23:31:00: Source scan found boolean-as-int gaps in migration spec, observation, and store-version checks; migration execution remained out of scope.
- 2026-08-04 23:33:00: Added explicit bool rejection and direct regressions; focused migration/clinical contract suites passed under `.venv`.
- 2026-08-04 23:58:00: Re-ran the decisive monitoring-AI/real-loop/assurance group after adjacent changes: 871 passed with 17 warnings; migration py_compile and reserved-port checks passed. Two earlier broad all-monitoring runs exited without a retained terminal summary and are not used as acceptance evidence.
