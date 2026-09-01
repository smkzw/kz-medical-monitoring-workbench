Continue the same `mw_durable_jobs_20260722 / worker_01` session. Fully reread `/Users/smkzw/.hermes/SOUL.md`, workspace `AGENTS.md`, the V3 report, manager third-pass P2-W1-01, and current source/tests.

## Hard boundaries
- Work only in the current workspace.
- Write only `services/api/app/medical_writing_durable_jobs.py` and `tests/test_medical_writing_durable_jobs.py`.
- Runner-managed output file: `runs/execution/mw_durable_jobs_20260722/worker_01_followup_claim_origin_05.md`; never write it with tools.

Confirmed defect:
- `claim()` increments `attempt_count` only when origin status is `retry_wait`; claims from `queued` or expired `running` preserve it.
- `release_claim()` always decrements (floor 1). After an expired-running takeover at attempt >1, recovery first changes/claims the row without a new increment; a later graceful release incorrectly decrements and refunds a prior genuine failed attempt.

Required correction:
1. Persist enough internal claim-origin metadata in SQLite to know whether the current claim incremented `attempt_count`. A private column such as `claim_origin_status` or `claim_incremented_attempt` is acceptable. It must be restart-stable and must not be exposed through the public `DurableJobRecord`.
2. Add a backward-compatible schema migration for existing durable DBs, not only fresh CREATE TABLE. Never drop/recreate or lose queued/running/terminal jobs.
3. On claim, record origin atomically with token/lease. On graceful release, decrement only when this exact claim originated from `retry_wait` and therefore incremented; queued/expired-running origin preserves count. Clear origin metadata on release, complete, fail, cancel, retry/requeue and other terminal/ownership-clearing transitions as appropriate.
4. Exact-token/live-lease CAS, progress, finalization race, max-attempt and project isolation must remain unchanged.
5. Deterministic tests:
   - retry_wait claim increments then graceful release restores previous count;
   - first queued claim/release/reclaim preserves count;
   - expired-running takeover at attempt >1 then graceful release preserves the prior count (does not decrement);
   - multiple graceful restarts from queued do not drift;
   - old-schema DB migration preserves rows and permits correct claim/release;
   - token mismatch/late owner cannot alter origin/count.
6. Run durable core plus synopsis regression.

Emit `WORKER_01_GRACEFUL_RELEASE_V4_COMPLETE` only after migration and all origin/attempt tests pass.
