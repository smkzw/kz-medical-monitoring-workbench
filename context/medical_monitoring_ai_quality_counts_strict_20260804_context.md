# Task Context: medical_monitoring_ai_quality_counts_strict_20260804

Created: 2026-08-04 23:48:42
Objective: Reject boolean counts in independent-AI quality and citation evidence contracts
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_quality.py`: immutable quality observations and coverage summaries.
- `services/api/app/monitoring_ai_release_gate.py`: citation-review evidence counts.
- `tests/test_monitoring_ai_quality.py` and `tests/test_monitoring_ai_release_gate.py`: quality/release boundary regressions.

## Scope

- In scope: reject boolean attempt/resource/coverage/citation counts; reject bool attempt numbers before explicit conversion; add direct regressions; run offline AI quality/release checks.
- Out of scope: provider/runtime startup, browser or Playwright login, API login, real projects, medical review, database state, and production writes.

## Success Criteria

- Quality and citation evidence counters accept strict non-negative integers and reject bool values before derived summaries or release evidence are evaluated.
- Canonical integer evidence remains compatible; changed Python compiles and reserved ports remain empty.

## Risk Boundaries

- Only quality/release evidence contracts, their focused tests, and task-scoped context/review/metrics/active-slice/ledger records may change.
- No delegated agent, Hermes dispatch, service/provider startup, browser/Playwright/API login, database mutation, real-project import, medical-writing artifact, or production artifact mutation.
- Codex remains final authority; review-gate does not grant provider, medical, or release authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 23:48:42: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 23:49:00: Source inspection found ordinary Pydantic counters and an explicit `int()` conversion for attempt numbers in quality evidence.
- 2026-08-04 23:51:00: Switched quality/release counters to strict integer types, added raw attempt-number rejection, and added parametrized regressions; decisive offline checks passed.
