# Task Context: medical_monitoring_ai_evaluation_counts_strict_20260804

Created: 2026-08-04 23:39:03
Objective: Reject boolean evidence counts in the independent-AI evaluation matrix
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_evaluation_matrix.py`: independent-AI evidence matrix pair counts.
- `tests/test_monitoring_ai_evaluation_matrix.py`: matrix construction and completeness regressions.
- Existing monitoring-AI contracts, quality/release gates, real-loop, assurance, B6/C14 and release records.

## Scope

- In scope: reject boolean evidence counts in `MonitoringAiEvaluationPair`; add direct regressions; run offline matrix/quality/release checks and record evidence.
- Out of scope: provider/runtime startup, browser or Playwright login, API login, real projects, medical review, database state, and production writes.

## Success Criteria

- All six matrix evidence-count fields accept strict non-negative integers and reject bool values.
- Canonical matrix construction and release-gate consumers remain covered; changed Python compiles and reserved ports remain empty.

## Risk Boundaries

- Only the evaluation matrix, its focused test, and task-scoped context/review/metrics/active-slice/ledger records may change.
- No delegated agent, Hermes dispatch, service/provider startup, browser/Playwright/API login, database mutation, real-project import, medical-writing artifact, or production artifact mutation.
- Codex remains final authority; review-gate does not grant provider, medical, or release authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-04 23:39:03: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-04 23:40:00: Source inspection found Pydantic `int` fields in evaluation-pair counts could coerce bool values to 1.
- 2026-08-04 23:41:00: Switched six pair count fields to `StrictInt` and added parametrized bool regressions; matrix/quality/release checks passed under `.venv`.
