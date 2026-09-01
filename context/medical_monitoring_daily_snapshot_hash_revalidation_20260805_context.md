# Task Context: medical_monitoring_daily_snapshot_hash_revalidation_20260805

Created: 2026-08-05 01:26:33
Objective: Revalidate persisted daily diff and rule snapshot content and row identity hashes on restart reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_daily_run_repository.py`
- `tests/test_monitoring_daily_run_repository.py`
- adjacent daily-run service, analysis, router and module-contract tests
- current P10 completion matrix and release gate audit

## Scope

- In scope: preserve existing snapshot payload/field semantics, then verify
  persisted diff and rule snapshot row identity and canonical output hashes on
  restart reads; add semantically-valid tamper regressions.
- Out of scope: medical inference, runtime startup, provider/browser/Playwright,
  real projects, B6/C14, migrations, UI or medical-writing files.

## Success Criteria

- A persisted diff or rule snapshot with a semantically valid but tampered
  payload cannot be read as a valid snapshot or feed downstream processing.
- Existing snapshot replay/migration and malformed-field contracts remain
  precise; repository and adjacent tests, compile and Ruff pass.
- No authority or activation flag changes.

## Risk Boundaries

- Do not start or connect to 8911, 5174, 8910 or 4173; do not touch runtime
  databases or real projects.
- No external model dispatch; Codex remains final authority.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 01:26:33: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 01:26: source audit confirmed `_diff` and `_rule_snapshot`
  deserialized persisted JSON without recomputing `output_sha256` or binding
  deterministic snapshot/row identity; runtime gates remain closed.
- 2026-08-05 01:27-01:36: added fail-closed payload/hash/identity checks and
  tamper regressions; focused 20 and adjacent 261 tests passed, compileall and
  Ruff passed, and reserved ports were empty. Review-gate returned `ok=true`;
  runtime, provider, browser and real-project gates remain closed.
