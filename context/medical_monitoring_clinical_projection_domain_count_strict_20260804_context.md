# Task Context: medical_monitoring_clinical_projection_domain_count_strict_20260804

Created: 2026-08-04 23:27:59
Objective: Reject boolean domain counts in clinical monitoring projections
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_clinical_projection_contract.py`: subject-profile and rollup projection contracts.
- `tests/test_monitoring_clinical_projection_contract.py`: projection contract regressions.
- Existing clinical-event, consumer-handoff, monitoring-AI, real-loop, assurance, B6/C14 and release records.

## Scope

- In scope: reject boolean subject-profile `domain_counts` values; add a direct regression; run adjacent offline regressions and record evidence.
- Out of scope: provider/runtime startup, browser or Playwright login, API login, real projects, medical review, database state, and production writes.

## Success Criteria

- Subject-profile domain counts accept non-negative integers but reject Python bool values.
- Existing clinical projection behavior remains covered; changed Python compiles and reserved ports remain empty.

## Risk Boundaries

- Only the clinical projection contract, its focused test, and task-scoped context/review/metrics/active-slice/ledger records may change.
- No delegated agent, Hermes dispatch, service/provider startup, browser/Playwright/API login, database mutation, real-project import, medical-writing artifact, or production artifact mutation.
- Codex remains final authority; review-gate does not grant provider, medical, or release authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 23:27:59: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 23:29:00: Source inspection found subject-profile domain counts using a plain integer check while rollup counts already rejected bool-as-int.
- 2026-08-04 23:31:00: Added the explicit non-boolean guard and direct regression; project virtual-environment tests passed.
