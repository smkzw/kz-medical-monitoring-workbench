Continue the same `mw_durable_jobs_20260722 / worker_01` session. The prior `WORKER_01_GRACEFUL_RELEASE_COMPLETE` marker is rejected because source and tests contradict the stated attempt/ownership contract. Reread `/Users/smkzw/.hermes/SOUL.md`, workspace `AGENTS.md`, the prior prompt/report and current source.

## Hard boundaries
- Work only in the current workspace.
- Write only `services/api/app/medical_writing_durable_jobs.py` and `tests/test_medical_writing_durable_jobs.py`.
- Runner-managed output file: `runs/execution/mw_durable_jobs_20260722/worker_01_followup_attempt_semantics_03.md`; never write it with tools.

Read initially:
- `AGENTS.md`
- `runs/execution/mw_durable_jobs_20260722/worker_01_followup_shutdown_release_02.md`
- `services/api/app/medical_writing_durable_jobs.py`
- `tests/test_medical_writing_durable_jobs.py`

Codex-confirmed defects:

1. `release_claim` uses `max(1, current_attempt - 1)`. First claim sets attempt_count=1; release leaves 1; next claim increments to 2. The graceful interruption therefore does consume an attempt despite the report claiming otherwise. Existing tests only assert the intermediate wrong value and never assert post-reclaim equality.
2. The method documentation and task contract say expired/lost ownership must fail closed, but source explicitly does not validate lease liveness. An old token can mutate an expired running row before the sweeper/replacement acts.

Required correction:
- Restore `attempt_count` exactly to its value before the interrupted claim, including first claim 1 -> release 0 -> next claim 1. Preserve non-negative validation and existing max-attempt behavior. Do not change normal failure accounting.
- Require `running`, exact token, and a still-live valid lease at the transactional read/CAS boundary. Expired/malformed/empty lease returns false without changing row/progress/attempt count. Replacement owner and terminal rows remain untouched.
- Add direct tests that record count immediately before first/second claim, release, then reclaim and assert the reclaimed count equals the interrupted claim count, including repeated graceful restart cycles near max_attempts. Add expired-token, malformed/empty lease, replacement-owner and late old-owner cases.
- Recheck the shutdown race around active-claim removal versus completion. If shutdown can begin after the claim is removed from `_active_claims` but before complete/fail, make the boundary deterministic so either the already-finished result completes before shutdown ownership release or the claim is released; it must not remain live for 600 seconds. Add a barrier test for that exact interleaving.
- Run durable core plus synopsis regression.

Return exact evidence. Emit `WORKER_01_GRACEFUL_RELEASE_V2_COMPLETE` only when post-reclaim attempt accounting, live-lease ownership and shutdown interleaving tests pass. Otherwise return the blocker without a marker.
