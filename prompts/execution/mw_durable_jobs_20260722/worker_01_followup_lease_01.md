Continue the same `mw_durable_jobs_20260722 / worker_01` session. Fully reread and comply with `/Users/smkzw/.hermes/SOUL.md` and the workspace `AGENTS.md`.

Hard boundaries:
- Work only inside the runner-provided current workspace (`.`).
- Preserve original Worker 01 sole file ownership; do not edit business adapters, `main.py`, frontend or synopsis service.
- Runner-managed report path: `runs/execution/mw_durable_jobs_20260722/worker_01_followup_lease_01.md`. Do not write this report path with tools; return the report in final text.
- Do not install packages or substitute any external model for product AI.

Read these files only as the initial set; additional in-workspace reads required to fix the listed defects are allowed and must be recorded:
- `AGENTS.md`
- `runs/execution/mw_durable_jobs_20260722/worker_01.md`
- `services/api/app/medical_writing_durable_jobs.py`
- `tests/test_medical_writing_durable_jobs.py`

Codex independently reran the focused suite with Python 3.12: 81 combined durable-job + synopsis tests passed, but source review found untested correctness gaps. Fix all gaps below within your original file ownership, add deterministic regression tests, and rerun both test files.

1. Lease expiry must itself invalidate an owner. `heartbeat`, `complete`, and `fail` currently accept the matching token even after `lease_expires_at <= now` when no replacement owner has claimed yet. They must return false and make no state/progress/artifact mutation after expiry. Put the lease condition in the transactional read/CAS logic and test heartbeat, complete and fail after expiry before takeover.
2. Add a claim-aware ownership check used by worker `cancel_check`: it must return cancellation/lost ownership when status is not running, token differs, or lease expired. The old executor must observe lost ownership even if a new owner is running. Test takeover while old executor is still active.
3. `retry()` is documented for failed/retry_wait/cancelled but currently requeues queued and live-running jobs. Reject/no-op queued, running and completed; do not create duplicate execution or steal a live claim. Add tests.
4. `shutdown(timeout)` must apply one overall deadline, not `timeout` per thread. The cooperative cancel check must also become true on shutdown so well-behaved executors exit. A running job left by shutdown must remain recoverable and must not be completed by that worker. Add a multi-thread bounded-time test without flaky long sleeps.
5. A service that restarts while a prior process's lease is still nominally live must not leave that job stuck forever. Keep multi-node lease safety: do not immediately steal a live lease. Add a periodic/delayed recovery sweep owned by the local worker (or an equivalent bounded mechanism) that requeues/wakes the job after expiry. Prove with a short-lease restart test. Ensure shutdown stops the sweeper.
6. Remove the unused `_build_complete_params` helper and the no-op executor lock block in `wake`; keep the implementation compact and explain any intentionally retained private-store scan.

Do not alter business adapters, `main.py`, frontend or synopsis service. Finish with `WORKER_01_DURABLE_CORE_RECOVERY_COMPLETE` only if all original and new focused tests pass. Return the complete report in final text; the runner persists it.
