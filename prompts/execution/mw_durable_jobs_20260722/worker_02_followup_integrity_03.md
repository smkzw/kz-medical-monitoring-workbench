Continue the same `mw_durable_jobs_20260722 / worker_02` session. Fully reread
`/Users/smkzw/.hermes/SOUL.md`, workspace `AGENTS.md`, your prior v2 report, and
the current source. Do not redo accepted work.

Allowed writes are limited to:

- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_medical_writing_triage_durable.py`

Do not edit the shared durable core, main.py, frontend, contracts, other medical
writing adapters, or runner-managed report files. Do not substitute your model
for product AI.

Runner-managed report path:
`runs/execution/mw_durable_jobs_20260722/worker_02_followup_integrity_03.md`.
Return the report in final text; never write that path yourself.

Codex independently reproduced 146 passing focused tests and accepted the exact
project/run provider lookup, live-running retry conflict, and the already tested
cancel/false-heartbeat branches. One remaining source-level P0 is not covered:

`CompetitorTriageExecutor._heartbeat_progress()` catches every exception and
returns `True`. A heartbeat exception means ownership could not be proven. The
old owner must fail closed, stop execution, and perform no later business write
or finalization. It must never convert an unknown lease state into success.

Make the smallest coherent correction and add deterministic adapter-level tests
that prove all of the following:

1. A heartbeat exception immediately before a normal chunk business commit
   leaves the persisted chunk and run unchanged and returns a retryable error.
2. A heartbeat exception in the no-candidate and input-drift branches cannot
   reach `_finalize_run_status()` or persist their locally modified chunk list.
3. Immediately before final status persistence, ownership is checked through
   `cancel_check()` and/or a fail-closed heartbeat; a lease loss or heartbeat
   error there cannot persist REVIEW_READY/PARTIAL_FAILED/FAILED.
4. Existing false-heartbeat, cancel, exact routing, retry, legacy triage and
   shared durable-core tests remain green.

Do not weaken tests with timing allowances. Use deterministic fakes and explicit
write spies/state comparisons. Rerun:

- `tests/test_medical_writing_competitor_triage.py`
- `tests/test_medical_writing_triage_durable.py`
- `tests/test_medical_writing_durable_jobs.py`

Finish with `WORKER_02_TRIAGE_INTEGRITY_V3_COMPLETE` only when the fail-closed
ownership contract is implemented and proven.
