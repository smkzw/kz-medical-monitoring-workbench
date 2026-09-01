# Task Context: medical_monitoring_assurance_rollup_hash_revalidation_20260805

Created: 2026-08-05 01:16 (Asia/Shanghai)
Objective: Revalidate persisted assurance rollup content and row identity
hashes on restart reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes workflow guard because it
touches P8 persisted assurance evidence and restart/recovery integrity.

## Source Of Truth

- `services/api/app/monitoring_assurance_repository.py`
- `tests/test_monitoring_assurance.py`
- adjacent assurance router/service/repository and module-contract tests
- current P10 completion matrix and release gate audit

## Scope

- In scope: on rollup reads, verify payload `content_sha256`, SQLite row hash,
  and canonical payload hash with the content field blanked; fail closed with
  `AssuranceDriftError`; update the tamper regression.
- Out of scope: medical inference, risk-fact copying, runtime startup,
  provider/browser/Playwright, real projects, B6/C14, migrations, UI or
  medical-writing files.

## Success Criteria

- A tampered persisted rollup cannot be read as a valid `RollupSummary` even if
  later count checks would otherwise pass.
- Existing assurance repository/service/router behavior remains green;
  compile, Ruff and reserved-port checks pass.
- No authority or activation flag changes.

## Risk Boundaries

- Do not start or connect to 8911, 5174, 8910 or 4173; do not touch runtime
  databases or real projects.
- No external model dispatch; Codex remains final authority.

## Loop Log

- 2026-08-05 01:16: source audit found rollup writes a content hash but
  `_rollup_from_row` trusted both JSON and column values without re-computing
  the canonical content hash.
- 2026-08-05 01:17-01:19: added row identity and canonical content-hash
  revalidation, updated the persisted-tamper regression, and completed
  focused/adjacent offline assurance checks.

Created: 2026-08-05 01:16:43
Objective: Revalidate persisted assurance rollup content and row identity hashes on restart reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- TODO: Add authoritative local files, extracts, datasets, screenshots, URLs, or user-provided materials.
- Do not add production paths unless the user has explicitly authorized reading them for this task.

## Scope

- In scope: TODO
- Out of scope: TODO

## Success Criteria

- TODO

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 01:16:43: Task initialized by `tools/hermes_workflow_guard.py init-task`.
