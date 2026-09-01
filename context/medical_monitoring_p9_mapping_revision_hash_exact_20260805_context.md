# Task Context: medical_monitoring_p9_mapping_revision_hash_exact_20260805

Created: 2026-08-05 20:48:00
Objective: Reject malformed persisted batch mapping revision hashes before reuse comparison without changing mapping semantics
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_batch_repository.py`, especially
  `_validation_evidence_mutation()` and its persisted
  `monitoring_mapping_revisions.mapping_sha256` reuse check.
- `tests/test_monitoring_batch_repository.py` plus the adjacent batch,
  field-profiler, daily-run AI and analysis tests.
- `records/active_slices/medical_monitoring_real_loop_gate_audit_20260804/CURRENT_REAL_LOOP_GATE_AUDIT.json`
  and the P9 source-only checkpoint/LOOP ledger. The authoritative gate is
  `read_only / blocked`; no runtime or real-project work is permitted.

## Scope

- In scope: validate a persisted mapping revision hash as an exact lowercase
  64-hex SHA-256 value before comparing it with the canonical mapping payload;
  add isolated tamper regressions for uppercase, padded, non-hex, short and
  non-string values; preserve current mapping idempotency and lifecycle
  semantics.
- Out of scope: rule meaning, mapping content, database migration, runtime
  activation, provider/model calls, services, browser/Playwright/API login,
  real projects, B6/C14, source-token/CAS replay, and unrelated modules.

## Success Criteria

- A malformed persisted `mapping_sha256` fails closed through the explicit
  integrity boundary rather than an ordinary content-conflict comparison.
- Valid mapping revision replay and existing lifecycle behavior remain green.
- Focused and adjacent tests, changed-module compileall, Ruff (if available),
  review-gate with `--require-verification`, gate assertions and reserved-port
  checks pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 20:48:00: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Candidate selected from the remaining monitoring hash comparison
  scan. This is a bounded source-only integrity repair under the blocked gate.
- 2026-08-05: `_validation_evidence_mutation()` now validates an existing
  persisted mapping hash with `_require_exact_sha256()` before comparing it to
  the current canonical mapping payload. Added five isolated SQLite tamper
  subcases; focused 1 passed, batch repository 58 passed, adjacency 108
  passed, and the nine-module joint regression 286 passed.
- 2026-08-05: Changed-module compileall and Ruff passed. Gate assertions still
  report `read_only / blocked`; 8911/5174/8910/4173 remain empty. No provider,
  runtime, browser, API login or real project action occurred.
