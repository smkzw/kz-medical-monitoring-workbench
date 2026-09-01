# Task Context: medical_monitoring_approved_input_manifest_bytes_strict_20260804

Created: 2026-08-04 23:10:28
Objective: Reject boolean source-manifest byte counts in approved-input replay
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_approved_input_dry_run.py`: source-manifest replay validator.
- `tests/test_monitoring_approved_input_dry_run.py`: manifest and approved-input regression contracts.
- Existing B6/C14/approved-input/host-identity and release records.

## Scope

- In scope: reject boolean source-manifest byte counts, add a direct regression, and record offline evidence.
- Out of scope: reviewer decisions, medical approval, source-token mutation, CAS replay, provider/runtime startup, browser or Playwright login, API login, real projects, and production writes.

## Success Criteria

- A boolean `bytes` value cannot be accepted as a source-manifest integer.
- Canonical integer byte counts and existing approved-input behavior remain covered.
- Approved-input/CAS/release/real-loop assurance tests pass, changed Python compiles, and reserved ports remain empty.

## Risk Boundaries

- Only the approved-input dry-run, its focused test, and task-scoped evidence/review/metrics/ledger records may change.
- No delegated agent, Hermes dispatch, service/provider startup, browser/Playwright/API login, database mutation, reviewer disposition, CAS replay, real-project import, or production artifact mutation.
- Codex remains final authority; review-gate does not grant approved-input or medical authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 23:10:28: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 23:11:00: Source inspection found Python bool accepted as an integer source-manifest byte count; no runtime or reviewer action was permitted.
- 2026-08-04 23:13:00: Rejected boolean byte counts and added a direct manifest regression; approved-input/CAS/release/real-loop offline suites passed.
