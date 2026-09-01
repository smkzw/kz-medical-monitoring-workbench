# Task Context: medical_monitoring_assurance_proof_hash_revalidation_20260805

Created: 2026-08-05 01:19 (Asia/Shanghai)
Objective: Revalidate persisted full-recompute proof content and row identity
hashes on restart reads
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes workflow guard because it
touches P8 persisted full-recompute evidence and restart/recovery integrity.

## Source Of Truth

- `services/api/app/monitoring_assurance_repository.py`
- `tests/test_monitoring_assurance.py`
- adjacent assurance router/service/repository and module-contract tests
- current P10 completion matrix and release gate audit

## Scope

- In scope: preserve existing typed field validation, then verify full-recompute
  proof payload/SQLite row identity and canonical content hash on read; add a
  valid-field tamper regression.
- Out of scope: medical inference, runtime startup, provider/browser/Playwright,
  real projects, B6/C14, migrations, UI or medical-writing files.

## Success Criteria

- A persisted proof with a semantically valid but tampered field cannot be read
  as a valid proof or permit completion.
- Existing malformed field diagnostics remain precise; assurance tests,
  compile, Ruff and reserved-port checks pass.
- No authority or activation flag changes.

## Risk Boundaries

- Do not start or connect to 8911, 5174, 8910 or 4173; do not touch runtime
  databases or real projects.
- No external model dispatch; Codex remains final authority.

## Loop Log

- 2026-08-05 01:19: source audit found `_proof_from_row` parsed fields but did
  not compare proof payload/SQLite content hashes or row identity.
- 2026-08-05 01:20-01:22: preserved typed-field diagnostics, added proof row
  identity/canonical hash revalidation, added a semantically-valid tamper
  regression, and completed focused/adjacent offline assurance checks.
- 2026-08-05 01:23: created task records, review and metrics; review-gate
  returned `ok=true` with no warnings or errors. LOOP 5.182 recorded. Runtime,
  provider, browser and real-project gates remain closed.

Created: 2026-08-05 01:19:17
Objective: Revalidate persisted full-recompute proof content and row identity hashes on restart reads
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

- 2026-08-05 01:19:17: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05 01:20-01:23: Codex completed the bounded proof read-side hash and
  row-identity hardening; focused 29 and adjacent 177 tests passed, compileall
  and Ruff passed, and review-gate returned `ok=true`. Runtime, provider,
  browser and real-project gates remain closed.
