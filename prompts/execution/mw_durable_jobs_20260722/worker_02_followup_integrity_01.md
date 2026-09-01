Continue the same `mw_durable_jobs_20260722 / worker_02` session. Fully reread and comply with `/Users/smkzw/.hermes/SOUL.md` and workspace `AGENTS.md`.

Hard boundaries:
- Work only inside the runner-provided current workspace (`.`).
- Preserve Worker 02 ownership: competitor triage service and focused triage tests only. Do not edit shared core, `main.py`, contracts, frontend or other services.
- Runner-managed report path: `runs/execution/mw_durable_jobs_20260722/worker_02_followup_integrity_01.md`. Never invoke write/edit tools on this report; return it in final text.
- Do not substitute execution-model content for product AI.

Read these files only as the initial set; additional in-workspace reads needed for these defects are allowed and must be recorded:
- `AGENTS.md`
- `runs/execution/mw_durable_jobs_20260722/worker_02.md`
- `services/api/app/medical_writing_competitor_triage.py`
- `tests/test_medical_writing_triage_durable.py`
- `services/api/app/main.py` lines containing `_resolve_triage_provider` (read-only)

Codex independently reran the current triage + durable core suite: 132 tests passed. Source review found production defects not covered by those tests. Fix all and add deterministic regression tests:

0. The interrupted partial patch currently makes API import fail: `CompetitorTriageService.__init__` calls `threading.Lock()` but the module does not import `threading`. Reproduce the collection failure and fix it without weakening the scoped-provider isolation design.

1. Partial persistence currently stores only `updated_chunks`, dropping all unprocessed chunks. After every chunk and on cooperative cancellation, persist the full original ordered chunk list with processed indices replaced; pending tail chunks must survive crash/restart. Test a multi-chunk provider crash/cancel after the first chunk, reconstruct a new service/worker, and prove the remaining NCT chunks are retained and resumed exactly once.
2. After a provider call returns, recheck `cancel_check()`/claim ownership before any business artifact write. A lost lease or cancellation must not persist that chunk result. Make heartbeat progress return ownership status rather than swallowing `False`; stop cleanly when ownership is lost. Test takeover/cancel during a slow provider call and assert old-owner business results are absent.
3. Production `main.py` passes an already `VerifiedTriageProvider`. The durable executor currently wraps it again, which loses the inner base_url/response identity and fails. Reuse an existing `VerifiedTriageProvider` directly; only wrap raw providers. Add a production-shape verified-provider test.
4. Replace mutable global `_last_provider`/lambda state with a restart-safe constructor-level `provider_factory` for production and a project/run-scoped test-only override map if needed. Two concurrent jobs must not consume each other's provider. A newly constructed service after restart with the configured factory must execute queued work without a prior HTTP request. Add both tests. Keep exact DeepSeek v4-pro identity fail-closed.
5. `PARTIAL_FAILED` currently completes the durable job. A retry then calls `store.retry()` on `completed`, which is a no-op after the business run was already changed to RUNNING. For retries of a completed partial job, create/reuse a new retry job keyed by `request.idempotency_key` plus frozen failed-chunk set (or an equivalent stable retry business key). For failed/retry_wait/cancelled jobs, reuse core retry. Perform durable transition successfully before mutating the business run; if it fails/no-ops, leave the run unchanged. Test completed-partial retry, duplicate retry idempotency, live-running retry rejection and no orphan RUNNING run.

Do not weaken basket confirmation, projection or source evidence rules. Rerun existing and new triage tests plus shared durable core. Finish with `WORKER_02_TRIAGE_INTEGRITY_COMPLETE` only if all listed defects are proven closed.
