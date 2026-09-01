Continue the same `mw_durable_jobs_20260722 / complex_manager_grok` execution-
manager session. This is a second integration review, not a conference. Fully
read `/Users/smkzw/.hermes/SOUL.md`, then reread workspace `AGENTS.md`, the
execution context, your first-pass report, the current source, and the final
worker/follow-up reports listed below.

Runner-managed report path:
`runs/execution/mw_durable_jobs_20260722/manager_second_pass.md`. Never write or
edit that report path; return the full report in final text.

Hard boundaries: this pass is read-only for production source and tests. Do not
modify `main.py`, frontend, adapters, shared durable core, contracts or reports.
Codex will route any concrete defect back to the owning worker or W5. You may run
non-destructive tests and inspect any in-workspace source needed for evidence.
Do not substitute Grok output for product AI and do not claim final acceptance.

Initial evidence to read:

- `context/mw_durable_jobs_20260722_execution_context.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/ASYNC_JOB_ARCHITECTURE_DECISION.md`
- `runs/execution/mw_durable_jobs_20260722/manager.md`
- `runs/execution/mw_durable_jobs_20260722/worker_01_followup_lease_01.md`
- `runs/execution/mw_durable_jobs_20260722/worker_02_followup_integrity_03.md`
- `runs/execution/mw_durable_jobs_20260722/worker_03_followup_atomicity_01.md`
- `runs/execution/mw_durable_jobs_20260722/worker_04_followup_integrity_04.md`
- `services/api/app/medical_writing_durable_jobs.py`
- `services/api/app/medical_writing_competitor_triage.py`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py`
- `services/api/app/sqlite_runtime_store.py`
- `services/api/app/writing_reference_translation_batch.py`
- the corresponding durable adapter tests
- `prompts/execution/mw_durable_jobs_20260722/worker_05.md`

Codex has independently accepted W1 shared core, W2 competitor triage and W3
section-candidate/atomic-adoption. Do not rely on that statement alone: verify
the source/report evidence. Proceed only if the W4 report contains
`WORKER_04_TRANSLATION_INTEGRITY_V4_COMPLETE`; otherwise return an explicit gate
failure without inventing completion.

Review the integrated implementation against these cross-adapter invariants:

1. One authoritative `DurableJobStore`/worker contract; adapters do not clone or
   contradict state, lease, heartbeat, cancel, retry, recovery or project-scope
   semantics.
2. Every long product-AI path is reconstructable after process restart from
   persisted payload/configuration and does not rely on request-local provider
   objects. Test-only provider injection cannot leak across project/run or enter
   production.
3. Old-owner isolation is end-to-end: no adapter writes business terminal or
   intermediate artifacts after lost claim; heartbeat/check exceptions fail
   closed; a late result cannot overwrite cancellation or takeover.
4. Retry identities are stable and idempotent, live-running retries conflict,
   durable transition occurs before business reset, and no orphan `running`
   business state remains after failure.
5. Startup recovery does not steal live leases, but can schedule queued,
   retry_wait, expired-running and adapter-specific pending/failed-retryable work.
6. W3 atomic author selection + working-copy application truly occurs in one
   SQLite `BEGIN IMMEDIATE`, including rollback under every fault checkpoint,
   author-freeze/plan/citation/source-DOCX constraints and project isolation.
7. The three adapters expose a coherent, minimal contract that W5 can wire to
   one project-scoped HTTP job API without placing model/OCR/translation work on
   the request thread.
8. W5 prompt is implementation-ready and does not accidentally reintroduce
   generic `待医学批准`, legacy two-request adoption, duplicated job semantics,
   or frontend log overload.

Run a combined deterministic regression across W1-W4 adapter/core tests. Report
findings first, ordered P0/P1/P2 with exact file/line evidence and a precise owner
(W2/W3/W4/W5). If no blocking findings remain, state that W1-W4 are ready for W5
integration, list residual risks, and give W5 a concise integration checklist.

Finish with `MANAGER_SECOND_PASS_READY_FOR_W5` only when no P0/P1 adapter or
cross-contract blocker remains. Otherwise finish with
`MANAGER_SECOND_PASS_BLOCKED` and concrete remediation items.
