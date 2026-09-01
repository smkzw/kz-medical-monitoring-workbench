Continue the same Kimi Code session for worker_03. Do not restart broad review and
do not open a new session. Read the current files because the shared workspace is
concurrent.

Read these files only as the initial evidence set:

- `AGENTS.md`
- `context/monitoring_p10_rule_release_chain_20260730_execution_context.md`
- `runs/execution/monitoring_p10_rule_release_chain_20260730/worker_03.md`
- `services/api/app/monitoring_shadow_sample_service.py`
- `services/api/app/monitoring_protocol_rule_repository.py`
- `tests/test_monitoring_shadow_sample_service.py`
- `tests/test_monitoring_rule_release_chain_p0_20260730.py`

The initial set does not prohibit reading the exact adjacent implementation needed
for this correction. The runner-managed output file is
`runs/execution/monitoring_p10_rule_release_chain_20260730/worker_03_followup_atomic_commit.md`.
Do not write that file with tools; return the complete report and let the runner
persist it.

Codex reproduced the focused tests and accepts the provisional prevalidation,
effective-capability identity, fresh-load lineage projection, and confirmed-title
fix. One P0 remains and the first report itself records it:

`confirm_samples` currently persists promoted gold/diagnostic cases, then stores
the trusted shadow run in a separate transaction, then stores the medical
confirmation in another transaction. A database/validation/event failure after
promotion can therefore leave a partially trusted state. Prevalidation parity
reduces ordinary evaluation failures but does not make the persistence sequence
failure-atomic.

Required correction:

1. Add the smallest repository transaction that atomically commits the exact
   promoted gold cases, diagnostic cases, trusted shadow run, and
   `ShadowSampleMedicalConfirmation`.
2. Reuse/refactor existing private validation and insert logic. Do not duplicate
   weaker validation and do not use compensating deletes.
3. Preserve independent pre-registered evidence and idempotent replay.
4. A failure injected:
   - after promoted cases are prepared,
   - after the first promoted case insert,
   - during trusted-run insert/validation/event write, and
   - during confirmation insert/event write
   must roll back every newly promoted case, trusted run, confirmation, and event
   from this confirmation attempt, while preserving all pre-existing independent
   evidence.
5. `confirm_samples` must call the atomic repository contract once after its
   no-write prevalidation. The returned trusted run and confirmation must be the
   committed objects. The subsequent lifecycle transition may remain outside this
   evidence transaction and must be idempotently recoverable.
6. Do not weaken the existing strict `store_shadow_run` or
   `store_shadow_sample_confirmation` public paths.

Add focused failure-injection tests for all four boundaries above and an
idempotent replay test. Rerun:

- the new atomic tests;
- `tests/test_monitoring_rule_release_chain_p0_20260730.py`;
- shadow sample, protocol repository/API, resolver, daily-run service/repository/
  router, and rule template focused suites;
- all monitoring backend tests;
- medical-monitoring frontend tests and production build only if frontend files
  change (they should not need to);
- compile/import and Ruff for changed files.

Hard boundaries remain:

- Do not start 8911 or write real runtime databases.
- Do not edit medical-writing business files, `frontend/src/App.jsx`, shared
  styles, `monitoring_ai_router.py`, or `tests/test_monitoring_ai_api.py`.
- Re-read `services/api/app/main.py`; no change should be necessary.
- Return a complete compact execution report. Record exact files, tests, hashes,
  failure-injection proof, residual risk, and the same-session id.

Output schema:

1. `# Execution Follow-up: monitoring_p10_rule_release_chain_20260730 - worker_03_atomic_commit`
2. `## Boundary Check`
3. `## Atomic Commit Design`
4. `## Changes`
5. `## Failure Injection Evidence`
6. `## Regression Evidence`
7. `## Residual Risk And Next Step`
