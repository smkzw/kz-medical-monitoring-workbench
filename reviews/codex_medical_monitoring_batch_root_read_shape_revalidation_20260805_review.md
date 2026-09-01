# Codex Review: medical_monitoring_batch_root_read_shape_revalidation_20260805

Date: 2026-08-05 (Asia/Shanghai)
Delegated-agent output: not dispatched; Codex performed the bounded source-only slice directly.

## Verdict

Pass for the declared source-only batch-root shape and state-integrity slice.
This does not change the blocked real-loop or commercial-release status.

## Boundary Check

- Hermes was initialized for the tracked workflow, but no Hermes execution
  session, delegated agent, or external provider was dispatched. Codex changed
  only the declared batch repository/test and evidence surfaces.
- No production path, runtime database, service, port, browser/Playwright
  session, API login, real project, medical judgment, or B6/C14 authority
  artifact was touched.

## Codex Verification

- Source review confirmed `_batch_from_row()` rejects malformed/non-canonical
  domain JSON, non-object proof JSON, invalid versions, invalid timestamps, and
  frozen-state timestamp conflicts while preserving valid draft and frozen
  round-trips.
- Focused: 46 passed. Adjacent batch/diff/rule-runner/field-profiler,
  daily-run/AI, gold-case, mapping-lifecycle and API group: 131 passed.
  `compileall` and Ruff passed; reserved ports 8911/5174/8910/4173 were free.
- No browser/PPT/PDF/live authority check was run because this slice is
  explicitly source-only and the real-loop/release gates remain blocked.

## Delegated-Agent Output Review

- Evidence records the exact commands, counts, hashes, existing warnings, and
  residual limits. The regressions mutate persisted root fields through the
  repository's SQLite database and assert fail-closed reads.
- The change does not introduce a new batch identity scheme, alter lifecycle
  transitions, or claim medical correctness.

## Residual Risk

Residual risk: root shape checks do not independently validate all referenced
source, mapping, rule, or proof semantics and do not prove live provider output,
clinical accuracy, UI/a11y quality, Playwright acceptance, or release readiness.
Formal B6 outcomes, source-token/CAS revalidation, host/runtime identity,
real-project/mode runs, and the commercial release dossier remain
unproven/blocked.
