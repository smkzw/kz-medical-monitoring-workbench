Continue the same `mw_durable_jobs_20260722 / worker_01` execution session. Fully reread and comply with `/Users/smkzw/.hermes/SOUL.md`, global/project `AGENTS.md`, the Worker 01 reports, and the current source.

Hard boundaries:
- Work only inside the runner-provided current workspace (`.`).
- Write only `services/api/app/medical_writing_durable_jobs.py` and `tests/test_medical_writing_durable_jobs.py`.
- Do not edit adapters, `main.py`, frontend, contracts, or unrelated tests.
- Runner-managed report path: `runs/execution/mw_durable_jobs_20260722/worker_01_followup_shutdown_release_02.md`. Never write that report with tools; return it in final text.

Read initially:
- `AGENTS.md`
- `runs/execution/mw_durable_jobs_20260722/worker_01.md`
- `runs/execution/mw_durable_jobs_20260722/worker_01_followup_lease_01.md`
- `services/api/app/medical_writing_durable_jobs.py`
- `tests/test_medical_writing_durable_jobs.py`

Codex confirmed a graceful-restart recovery gap: the default lease is 600 seconds. `DurableJobWorker.shutdown()` sets cooperative cancellation and stops heartbeats, but a job whose executor exits on shutdown remains `running` with a nominally live lease. A newly started process correctly refuses to steal it and may therefore wait up to ten minutes. This is correct for an unclean crash but wrong for a known graceful shutdown.

Required correction:
1. Add a precise store CAS operation that releases only the exact current `project_id + job_id + claim_token` owner from `running` back to a recoverable queued state. It must fail closed for token mismatch, expired/lost ownership, terminal/cancelled state, or any replacement owner. It must clear claim/lease and preserve monotonic progress/payload/business identity.
2. A graceful lifecycle release must not consume an additional retry attempt when the next process reclaims the same interrupted work. Design attempt accounting explicitly and test it; do not solve this by raising max attempts or weakening normal failure retry limits.
3. Track active claims in `DurableJobWorker` under a lock. On cooperative shutdown, every still-owned claim is released exactly once, including: executor returns after seeing shutdown, multiple simultaneous jobs, shutdown timeout while a slow executor thread is still alive, and repeated `shutdown()` calls. A late old executor must be unable to complete/fail or overwrite the requeued/new-owner job.
4. Preserve the single overall shutdown deadline; releasing claims must not add unbounded per-thread waits. Do not release claims on ordinary non-shutdown execution, explicit user cancellation, or unclean process crash (which remains lease-expiry recovery).
5. Add deterministic two-worker/restart tests proving a graceful shutdown lets a new worker claim immediately without waiting for the 600-second lease, while a live non-shutdown owner still cannot be stolen. Include token mismatch, late completion, retry-attempt accounting, multiple claims, timeout, and idempotent repeated shutdown.
6. Rerun `tests/test_medical_writing_durable_jobs.py` and any adjacent focused regression required by imports.

Return exact commands/counts and a compact loop trace. Finish with `WORKER_01_GRACEFUL_RELEASE_COMPLETE` only when the deterministic restart tests pass; otherwise report the exact blocker without the marker.
