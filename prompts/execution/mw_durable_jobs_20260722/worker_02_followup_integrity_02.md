Continue the same `mw_durable_jobs_20260722 / worker_02` session. Fully reread `/Users/smkzw/.hermes/SOUL.md`, workspace `AGENTS.md`, prior follow-up report, and current source. Do not redo accepted fixes.

Hard boundaries remain the same: write only `services/api/app/medical_writing_competitor_triage.py` and `tests/test_medical_writing_triage_durable.py`. Do not edit shared durable core, `main.py`, contracts, frontend or other services. Do not substitute execution-model output for product AI.

Runner-managed report path: `runs/execution/mw_durable_jobs_20260722/worker_02_followup_integrity_02.md`. Never write/edit that report path; return the complete report in final text.

Codex independently reproduced 142 passing focused tests, but source review found three P0 defects hidden by the tests:

1. `_build_provider_for_durable_run()` does not receive `project_id/run_id` and returns the first arbitrary value from `_test_provider_overrides`. This directly contradicts the claimed project/run isolation. Change the resolver and executor call to use the exact persisted `(project_id, run_id)` key. Prefer the constructor production factory in production; test overrides must be explicit test-only injection and exact-key only. Add a truly concurrent two-project/two-run test whose providers emit distinguishable classifications and synchronize so both overrides coexist before either resolves; prove each run uses only its own provider. Also prove a missing exact key fails closed instead of taking another run's provider.
2. Business persistence precedes final ownership proof. At lines around the chunk loop, the adapter stores `run_partial` before heartbeat; if heartbeat returns `False`, the stale owner has already committed the chunk. Reorder so the claim-renewing heartbeat/ownership check succeeds immediately before each chunk business write. If `cancel_check()` or heartbeat says ownership is lost, return without any repository write at all. The old owner must not even persist the unchanged full run because that can overwrite a new owner's progress. Add a takeover test where owner B commits progress after A's provider returns but before A attempts its write; A must not overwrite B.
3. The no-candidate/input-drift branches currently call heartbeat but ignore its `False` return and can continue/finalize. Apply the same fail-closed ownership behavior to every branch and immediately before `_finalize_run_status`. No business finalization after lost claim.

Also change live-running retry from a silent `reused=True` success to the existing explicit conflict/error semantics without mutating business state, as the original contract required. Preserve the completed-partial stable retry job behavior.

Rerun legacy triage, durable triage adapter and shared durable core tests. Finish with `WORKER_02_TRIAGE_INTEGRITY_V2_COMPLETE` only when exact provider routing and old-owner business-write isolation are proven.
