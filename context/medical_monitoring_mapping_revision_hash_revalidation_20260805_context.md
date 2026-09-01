# Task Context: medical_monitoring_mapping_revision_hash_revalidation_20260805

Created: 2026-08-05 01:43:54
Objective: Revalidate persisted monitoring mapping revision identity and semantic quality hash on reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_mapping_draft_repository.py`
- `tests/test_monitoring_mapping_draft_repository.py`
- adjacent AI repository, record-rule-resolver, daily-run and module-contract
  tests
- current P10 completion matrix and release gate audit

## Scope

- In scope: recompute confirmed mapping revision identity from persisted fields,
  field sources and source hashes; verify semantic quality report hash when the
  revision carries one; add a valid-field tamper regression.
- Out of scope: provider calls, runtime startup, browser/Playwright, real
  projects, B6/C14, schema migrations, UI or medical-writing files.

## Success Criteria

- A semantically valid edit to a persisted confirmed mapping revision cannot be
  read or used as the original deterministic revision.
- Existing immutable-trigger, migration and mapping assembly/confirmation
  contracts remain precise; focused/adjacent tests, compile and Ruff pass.
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

- 2026-08-05 01:43:54: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 01:44: source audit found `_revision_from_row` did not recompute
  the deterministic revision ID or semantic-report hash; runtime/provider gates
  remain closed.
- 2026-08-05 01:45-02:12: added semantic-report hash and deterministic
  `monmaprev_…` identity revalidation plus a persisted field tamper regression.
  Focused 45 and adjacent 697 tests passed, compileall/Ruff passed,
  review-gate returned `ok=true`, and runtime/provider/browser gates remain
  closed.
