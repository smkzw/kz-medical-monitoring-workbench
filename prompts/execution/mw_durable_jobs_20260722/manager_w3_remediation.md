Continue the same native Grok Build `mw_durable_jobs_20260722` execution-manager session. This is a bounded write-capable remediation after the primary W3 worker twice emitted unsupported completion markers and Kimi fallback failed health preflight without a session. Fully reread `/Users/smkzw/.hermes/SOUL.md` as the workflow operating record, global/project `AGENTS.md`, your manager second-pass report, current W3 reports/source/tests, then implement and verify the missing W3 integrity evidence. Codex remains final authority.

## Hard boundaries
- Work only inside the runner-provided current workspace (`.`) using `permission-mode=bypassPermissions`.
- Write only `services/api/app/medical_writing.py`, `services/api/app/medical_writing_repository.py`, `tests/test_medical_writing_revision_durable.py`, `tests/test_medical_writing_revision_application.py`, plus minimal `services/api/app/sqlite_runtime_store.py` only if a proven table transaction defect requires it.
- Do not edit `main.py`, frontend, shared durable core, triage, translation, exporter, contracts, records, or unrelated tests.
- Product AI remains independently configured; do not substitute Grok output for product-AI behavior.
- Runner-managed output file: `runs/execution/mw_durable_jobs_20260722/manager_w3_remediation.md`. Never write it with tools; return the complete report in final text.

Read initially:
- `AGENTS.md`
- `runs/execution/mw_durable_jobs_20260722/manager_second_pass.md`
- `runs/execution/mw_durable_jobs_20260722/worker_03_followup_integration_02.md`
- `runs/execution/mw_durable_jobs_20260722/worker_03_followup_concurrency_tests_03.md`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py`
- relevant atomic methods in `services/api/app/sqlite_runtime_store.py`
- `tests/test_medical_writing_revision_durable.py`
- `tests/test_medical_writing_revision_application.py`

Do not trust the W3 V3 marker. Codex independently confirmed its tests do not exercise the claimed paths:

1. `test_cancel_after_ai_prevents_commit` passes `lambda: True`, so execution exits at the first pre-AI check. Build sequenced/barrier tests proving initial preparation or rewrite AI completed before cancel/claim loss. Cover initial and rewrite separately for cancel true/exception, heartbeat false/exception, takeover, clean retry once, and late old owner after new-owner success. Assert real repository thread/audit/turn/status state, not only fake commit counters. Make ownership exceptions fail closed without business write.
2. Concurrency and service-routing tests intentionally use `ai_task_runner=None` and expected failure, so they prove only resolver invocation and unchanged object identity. Use successful deterministic fake product-AI runners, two real repositories/projects and concurrent executor calls through one resolver. Assert each repo gets exactly its own candidate/audit/provider/model; one job ownership loss cannot suppress/capture the other. Exercise successful concurrent rewrite too.
3. Audit the new thread-local `_effective_repo` implementation for remaining direct `self.repo` reads, nested-context restoration, exception cleanup and rewrite mutation. Rewrite preparation must operate on a deep copy so an in-memory repository cannot mutate before commit. Prefer explicit repo flow if thread-local state remains fragile; preserve one canonical prompt/evidence path.
4. Table-cell atomic success test does not assert target cell text/rich text. Add exact target update, non-target preservation, rich/plain consistency, table version/CAS, source immutability; wrong block/table/row/column/cell, block hash/table version/selected-text drift; idempotent result equality; multiple injected transaction-boundary rollbacks with unchanged thread/suggestions/working copy/cell/audit/snapshot/idempotency and clean retry exactly once.
5. Run revision durable/API/application and shared durable-core tests. Inspect final diff for unrelated churn.

Return exact commands/counts, source locations, failed iterations, residual uncertainty and a compact loop trace. Emit `MANAGER_W3_REMEDIATION_COMPLETE` only when the missing success/concurrency/rewrite/table evidence passes; otherwise return the blocker without a marker.
