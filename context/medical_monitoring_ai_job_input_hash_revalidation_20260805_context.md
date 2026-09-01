# Task Context: medical_monitoring_ai_job_input_hash_revalidation_20260805

Created: 2026-08-05 01:35:35
Objective: Revalidate persisted monitoring AI job input revision and payload hashes on restart reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_ai_repository.py`
- `services/api/app/monitoring_ai_contracts.py`
- `tests/test_monitoring_ai_repository.py`
- adjacent AI service/router, mapping and module-contract tests
- current P10 completion matrix and release gate audit

## Scope

- In scope: verify persisted AI input revision/payload hashes and stable job ID
  on job and payload reads; add semantically-valid input tamper regressions.
- Out of scope: provider calls, runtime startup, browser/Playwright, real
  projects, B6/C14, migrations, UI or medical-writing files.

## Success Criteria

- A persisted job with a semantically valid but stale input revision or payload
  cannot be read or submitted to downstream AI execution.
- Existing typed job/retry/candidate contracts remain precise; focused/adjacent
  tests, compile and Ruff pass.
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

- 2026-08-05 01:35:35: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 01:36: source audit found `input_payload()` and `_job()` trusted
  persisted JSON despite stored revision/payload hashes; runtime and provider
  gates remain closed.
- 2026-08-05 01:37-01:58: added strict execution-read hash/stable-ID checks,
  preserved stale-list filtering, and added payload/revision/identity tamper
  regressions. Focused 48 and adjacent 645 tests passed, compileall/Ruff
  passed, review-gate returned `ok=true`, and all runtime/provider/browser
  gates remain closed.
