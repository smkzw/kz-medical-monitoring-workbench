# Codex Review: medical_monitoring_canonical_batch_diff_20260806

Date: 2026-08-06
Delegated-agent output: `runs/codex_medical_monitoring_canonical_batch_diff_20260806.md`
Route: Hermes workflow guard direct Codex single-node (`hermes/codex/codex-main:high`); no external worker or conference.

## Verdict

Pass for the bounded canonical read-only P0-03 contract; not a runtime or release
acceptance. The implementation is intentionally blocked from real execution by the
current gate and does not claim the full P0-03 real-project loop is complete.

## Boundary Check

- Codex must confirm the delegated agent stayed inside allowed paths.
- Work stayed within the workbench source, tests and task-record surfaces. No production
  service, browser, provider, runtime database, B6/C14, source-token/CAS or medical-writing
  source was changed.

## Codex Verification

- Source audit: existing `monitoring_batch_diff`/immutable batch repository was reused;
  canonical route now requires server principal, `READ_SOURCE_EVIDENCE`, canonical project
  scope, both batch records belonging to that project, and an injected diff service.
- `9` focused tests passed (4 canonical batch-diff cases plus existing principal-read cases).
- Combined module/batch service/diff regression: **120 passed, 1 existing openpyxl warning**.
- Batch repository regression: **59 passed**.
- Principal host/identity regression: **17 passed**; `py_compile` passed.
- Current gate remains `read_only / blocked`; 8911/5174/8910/4173 are stopped.
- Browser, Playwright, real projects, provider calls and full runtime checks were not run
  because the gate explicitly forbids them.

## Delegated-Agent Output Review

- The route preserves the full deterministic `output_sha256` and only slices the field-change
  presentation; it does not alter source/batch/risk state. Cross-project and missing-dependency
  paths fail closed before diff execution.
- The canonical route is an additional module contract; the legacy endpoint remains for
  compatibility and is not reclassified as production readiness.

## Residual Risk

- Residual P0-03 work remains: real project-neutral intake, source revision/structure drift
  evidence, risk migration and controlled real-project LOOP still require the formal
  B6/source-token/CAS/runtime gate. A persistent supersedes edge and full commercial/UAT
  evidence are also outside this slice.
