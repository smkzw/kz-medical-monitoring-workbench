# Task Context: medical_monitoring_ai_output_table_index_strict_20260804

Created: 2026-08-04 23:21:36
Objective: Reject boolean table and row indices in monitoring AI provider-output validation
Task type: `code_scoped_patch_plan`
Risk: `medium`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_service.py`: provider-output protocol structure and claim-anchor validation.
- `tests/test_monitoring_ai_service.py`: protocol output and evidence-binding contracts.
- Existing protocol packet, independent-AI, source-token, approved-input, B6/C14 and release records.

## Scope

- In scope: reject boolean table/row indices at the three provider-output consumers; add direct structure regressions; record offline evidence.
- Out of scope: provider/runtime startup, browser or Playwright login, API login, real projects, medical review, database state, and production writes.

## Success Criteria

- Boolean table coordinates cannot enter provider-output evidence grouping or claim anchors.
- Canonical integer protocol output behavior remains covered.
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

- 2026-08-04 23:21:36: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 23:22:00: Source inspection found three provider-output table-coordinate consumers accepting bool as int; no runtime/provider/browser action was permitted.
- 2026-08-04 23:24:00: Reused the non-boolean integer predicate and added table/row output-validation regressions; monitoring-AI/real-loop suites passed.
