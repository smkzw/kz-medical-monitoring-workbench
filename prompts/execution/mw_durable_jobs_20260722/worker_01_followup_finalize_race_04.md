Continue the same `mw_durable_jobs_20260722 / worker_01` session. Fully reread `/Users/smkzw/.hermes/SOUL.md` and workspace `AGENTS.md`. The V2 marker is not yet accepted because the exact shutdown/finalize race requested in the prior prompt is still untested and remains in source.

## Hard boundaries
- Work only in the current workspace.
- Write only `services/api/app/medical_writing_durable_jobs.py` and `tests/test_medical_writing_durable_jobs.py`.
- Runner-managed output file: `runs/execution/mw_durable_jobs_20260722/worker_01_followup_finalize_race_04.md`; never write it with tools.

Read initially: `AGENTS.md`, the V2 report, current durable core and its tests.

Confirmed race:
- `_run` decides `should_complete=True` and removes `claim_key` from `_active_claims` before `check_ownership` and complete/fail CAS.
- `shutdown()` can begin after that removal, find no active claim, hit its bounded timeout while finalization is delayed, and return while the row is still `running` with a 600-second lease.
- `test_shutdown_after_active_claim_removal_still_completes` starts shutdown only after the row is already completed, so it does not exercise the named window.

Required correction:
1. Keep the claim visible in `_active_claims` until complete/fail CAS has either committed or lost ownership; discard it in a final cleanup after CAS. Do not hold `_active_claims_lock` across potentially blocking SQLite/provider work and do not make shutdown's deadline unbounded.
2. Let graceful `release_claim` and complete/fail race through their existing SQLite CAS: exactly one wins. If shutdown release wins, old finalize returns false; if completion wins, release returns false on terminal state. In neither order may a live orphan remain.
3. Add a deterministic test that blocks immediately before complete/fail CAS after executor return, starts `shutdown(timeout=<short>)`, and proves shutdown returns bounded with row queued or terminal, never running/live. Then release the barrier and prove the late finalize cannot overwrite a re-claim/new owner. Cover both success-complete and retryable-fail finalization.
4. Preserve the now-correct live-lease guard and attempt accounting tests. Run durable core + synopsis.

Emit `WORKER_01_GRACEFUL_RELEASE_V3_COMPLETE` only after the exact race tests pass.
