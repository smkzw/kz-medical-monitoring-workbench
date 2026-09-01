# Task Context: medical_monitoring_p9_source_register_prior_hash_exact_20260805

Created: 2026-08-05 20:33:34
Objective: Fail closed on non-canonical persisted source lineage hashes during source registration
Task type: `code_open_audit`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/monitoring_batch_repository.py`, especially the existing
  source-lineage branch in `register_source`.
- `tests/test_monitoring_batch_repository.py` source binding persistence and
  tamper tests.
- The active P9/P10 checkpoint, LOOP ledger and real-loop gate; the gate remains
  read-only/blocked.

## Scope

- In scope: validate persisted prior source `binding_sha256` and
  `content_sha256` with the exact helper before lineage reuse/revision
  comparison; add an offline tamper regression.
- Out of scope: changing source revision semantics, migration behavior, object
  storage, runtime activation, provider/browser/Playwright testing, real
  projects, or unrelated repository fields.

## Success Criteria

- A malformed prior source digest fails closed during `register_source` rather
  than being string-coerced into a lineage comparison.
- Existing source registration/revision, derived verification, batch loading and
  adjacent AI/source consumers remain green.
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

- 2026-08-05 20:33:34: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-08-05: Source scan found the prior-lineage branch comparing persisted
  binding/content hashes with `str(...)`; source read paths are strict, but
  re-registration could otherwise continue after a tampered prior digest.
- 2026-08-05: Added exact prior-lineage validation; 2 boundary and 105
  adjacent tests passed; compileall and Ruff passed; Hermes review-gate with
  `--require-verification` passed. The formal gate remained blocked and all
  reserved ports remained empty.
