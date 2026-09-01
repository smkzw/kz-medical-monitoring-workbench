# Task Context: medical_monitoring_p9_batch_source_binding_hash_exact_20260805

Created: 2026-08-05 20:29:41
Objective: Reject non-canonical source hashes when loading a profile-ready frozen batch
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_batch_repository.py`, especially
  `load_profile_ready_batch` and source binding assembly.
- `tests/test_monitoring_batch_repository.py` plus adjacent daily-run AI and
  field-profiler source-binding tests.
- The active P9/P10 checkpoint, LOOP ledger and real-loop gate; the gate remains
  read-only/blocked.

## Scope

- In scope: validate each persisted source content hash with the repository's
  strict exact SHA-256 helper when loading a profile-ready frozen batch, and add
  SQLite tamper regressions for malformed raw values.
- Out of scope: source registration/migration semantics, row parsing, runtime
  activation, provider/browser/Playwright testing, real projects, or unrelated
  batch fields.

## Success Criteria

- Profile-ready batch source bindings reject numeric, uppercase, padded and
  non-hex content hashes rather than returning them as `DiffReadyBatch` source
  identities.
- Existing batch loading, field profiling, daily AI source binding and adjacent
  repository tests remain green.
- Compile, Ruff, review-gate `--require-verification`, gate and reserved-port
  checks pass.

## Risk Boundaries

- Do not write to production paths until Codex review gate passes and writable paths are explicit.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-08-05 20:29:41: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Source scan found `load_profile_ready_batch()` copying
  `content_sha256` with `str(...)` without the strict source hash helper, even
  though source registration and other profile identity paths validate raw
  canonical bytes.
- 2026-08-05: Added exact source-hash validation; the four-case boundary,
  54-test batch repository suite, and 64-test adjacent suite passed; compileall
  and Ruff passed; Hermes review-gate with `--require-verification` passed. The
  formal gate remained blocked and all reserved ports remained empty.
