# Task Context: medical_monitoring_ai_candidate_binding_revalidation_20260805

Created: 2026-08-05 01:40:38
Objective: Revalidate persisted monitoring AI candidate binding to its parent job on reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_ai_contracts.py`
- `tests/test_monitoring_ai_repository.py`
- adjacent AI service/router, risk bridge and module-contract tests
- current P10 completion matrix and release gate audit

## Scope

- In scope: validate persisted candidate JSON and bind candidate job/project/
  task/input-revision/prompt/evidence source pairs to the strict parent job on
  candidate reads; add tamper regressions.
- Out of scope: provider calls, runtime startup, browser/Playwright, real
  projects, B6/C14, schema migrations, UI or medical-writing files.

## Success Criteria

- A candidate with semantically valid but cross-bound parent/job/source metadata
  cannot be returned for review or disposition.
- Existing terminal candidate status and task-specific output contracts remain
  precise; focused/adjacent tests, compile and Ruff pass.
- No authority or activation flag changes.

## Risk Boundaries

- Do not start or connect to 8911, 5174, 8910 or 4173; do not touch runtime
  databases or real projects.
- No provider or external model dispatch; Codex remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 01:40:38: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 01:41: source audit found `candidates()` parsed candidate JSON
  without binding it to the strict parent job or source/hash graph; runtime and
  provider gates remain closed.
- 2026-08-05 01:42-02:02: added strict parent, row, task, revision, prompt and
  evidence-source binding checks with a tamper regression. Focused 48 and
  adjacent 715 tests passed, compileall/Ruff passed, review-gate returned
  `ok=true`, and provider/runtime/browser gates remain closed.
