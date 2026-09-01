# Task Context: medical_monitoring_p9_legacy_source_hash_exact_20260805

Created: 2026-08-05 20:40:53
Objective: Fail closed on malformed legacy source content hashes during repository migration
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_batch_repository.py`, especially the legacy
  `_migrate_monitoring_sources` conversion path.
- `tests/test_monitoring_batch_repository.py` legacy migration coverage.
- The active P9/P10 checkpoint, LOOP ledger and real-loop gate; the gate remains
  read-only/blocked.

## Scope

- In scope: require the legacy source row `content_sha256` to already be an
  exact lowercase 64-hex digest before migration writes it into the immutable
  source registry; add a minimal migration regression.
- Out of scope: changing migration schema, legacy text defaults, object store,
  runtime activation, provider/browser/Playwright testing, real projects, or
  unrelated hashes.

## Success Criteria

- Valid legacy source rows still migrate unchanged.
- Uppercase, padded, non-hex, short or numeric legacy content hashes fail closed
  before an invalid modern source row is created.
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

- 2026-08-05 20:40:53: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Source scan found legacy migration copying
  `content_sha256` through `str(...)` into the new immutable source table;
  modern reads reject such rows only after migration has already written them.
- 2026-08-05: Added exact legacy migration validation; 2 boundary and 107
  adjacent tests passed; compileall and Ruff passed; Hermes review-gate with
  `--require-verification` passed. The formal gate remained blocked and all
  reserved ports remained empty.
- Final joint offline regression across nine related P9 modules: **285
  passed** in 10.02s; final changed-module compile and Ruff checks passed.
