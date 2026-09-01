# Task Context: medical_monitoring_approved_input_cas_strict_boolean_20260804

Created: 2026-08-04 23:05:02
Objective: Require literal boolean CAS completion flags in the approved-input dry-run
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_approved_input_dry_run.py`: approved-input/CAS readiness evaluator.
- `tests/test_monitoring_approved_input_dry_run.py`: package and readiness regression contracts.
- Existing B6/C14/approved-input/host-identity and release records.

## Scope

- In scope: require literal boolean `metadata_chain_complete` and `cas_replay_complete` in aggregate-case readiness; add a direct string-status regression; record offline evidence.
- Out of scope: reviewer decisions, medical approval, source-token mutation, CAS replay, provider/runtime startup, browser or Playwright login, API login, real projects, and production writes.

## Success Criteria

- String-valued CAS completion flags cannot produce an approved-input-ready report.
- Canonical boolean diagnostic-ready package behavior remains covered.
- Approved-input/CAS/release/real-loop assurance tests pass, changed Python compiles, and reserved ports remain empty.

## Risk Boundaries

- Only the approved-input dry-run, its focused test, and task-scoped evidence/review/metrics/ledger records may change.
- No delegated agent, Hermes dispatch, service/provider startup, browser/Playwright/API login, database mutation, reviewer disposition, real-project import, or production artifact mutation.
- Codex remains final authority; review-gate does not grant approved-input or medical authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 23:05:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 23:06:00: Source inspection found CAS completion flags consumed with truthiness; no runtime or reviewer action was permitted.
- 2026-08-04 23:08:00: Changed both CAS completion checks to literal booleans and added a string-status regression; focused and adjacent offline suites passed.
