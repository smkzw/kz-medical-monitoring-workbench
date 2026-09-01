# Task Context: medical_monitoring_p9_batch_idempotency_hash_exact_20260805

Created: 2026-08-05 20:37:13
Objective: Reject non-canonical persisted batch idempotency request hashes during replay
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_batch_repository.py`, especially
  `_idempotent_replay` and the persisted idempotency row contract.
- `tests/test_monitoring_batch_repository.py` idempotency/replay tests and
  adjacent batch/source consumers.
- The active P9/P10 checkpoint, LOOP ledger and real-loop gate; the gate remains
  read-only/blocked.

## Scope

- In scope: validate persisted `monitoring_idempotency.request_sha256` as a raw
  canonical SHA-256 before replay comparison and add malformed-hash coverage.
- Out of scope: changing idempotency semantics, response reconstruction, runtime
  activation, provider/browser/Playwright testing, real projects, or unrelated
  repository hashes.

## Success Criteria

- Numeric, uppercase, padded or invalid persisted request hashes fail closed with
  a repository integrity error before replay/conflict comparison.
- Existing idempotent replay, conflict, mutation and adjacent source/AI tests
  remain green.
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

- 2026-08-05 20:37:13: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Source scan found `_idempotent_replay()` comparing persisted
  `request_sha256` with `str(...)`; the path failed closed as a conflict but did
  not preserve the canonical persisted-hash contract.
- 2026-08-05: Added exact replay-hash validation; 2 boundary and 106 adjacent
  tests passed; compileall and Ruff passed; Hermes review-gate with
  `--require-verification` passed. The formal gate remained blocked and all
  reserved ports remained empty.
