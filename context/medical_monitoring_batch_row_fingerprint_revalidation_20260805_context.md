# Task Context: medical_monitoring_batch_row_fingerprint_revalidation_20260805

Created: 2026-08-05 01:57:37
Objective: Revalidate persisted monitoring batch normalized-row fingerprints and field-profile row-set identity on reads
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

- 2026-08-05 01:57:37: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: source audit found `list_rows()` hydrated persisted normalized
  row data and trusted `row_fingerprint`; field-profile cache identity also
  returned the replace-rows `row_set_sha256` without recomputing the current
  normalized row set. Runtime/provider gates remain closed.
- 2026-08-05: patch in progress adds canonical fingerprint validation and
  replace-rows evidence comparison before normalized rows are returned.
- 2026-08-05: focused repository 40 and adjacent batch/diff/rule/field-profile/
  daily-run/AI/gold-case/API 131 tests passed; compileall, Ruff and
  reserved-port checks passed. No provider/runtime/browser/real-project/B6/C14
  action occurred. Continue with a bounded source-only P7/P8/P9 gap.

## Scope

- In scope: read-side canonical row fingerprint and row-set hash checks in the
  monitoring batch repository; focused persisted-row tamper regressions.
- Out of scope: medical inference, source-object changes, schema migration,
  provider/browser/runtime startup, API login, real projects, B6/C14 and UI.

## Success criteria

- A semantically valid persisted row payload or fingerprint mutation fails
  closed before diff, field profiling, AI or risk consumers receive it.
- Existing batch lifecycle, row-order and cache-identity contracts remain
  precise; focused/adjacent tests, compileall and Ruff pass.
