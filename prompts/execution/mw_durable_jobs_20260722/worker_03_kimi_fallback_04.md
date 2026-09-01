You are Kimi Code k3/high acting as the bounded fallback execution worker for `mw_durable_jobs_20260722 / worker_03` after the primary worker produced two completion markers unsupported by its tests. Read and comply with global/project `AGENTS.md` and your normal Kimi Code operating instructions. Work from current source; do not revert accepted W2/W4/W1 changes.

## Hard boundaries
- Work only inside the runner-provided current workspace (`.`).
- Write only `services/api/app/medical_writing.py`, `services/api/app/medical_writing_repository.py`, `tests/test_medical_writing_revision_durable.py`, `tests/test_medical_writing_revision_application.py`, plus minimal `services/api/app/sqlite_runtime_store.py` only if a proven table transaction defect requires it.
- Do not edit `main.py`, frontend, shared durable core, triage, translation, exporter, contracts, records, or unrelated tests.
- Product AI remains the independently configured service. Do not substitute your own model output for product-AI behavior.
- Runner-managed output file: `runs/execution/mw_durable_jobs_20260722/worker_03_kimi_fallback_04.md`. Never write/edit it with tools; return the complete report in final text.

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

Current implementation direction is useful but the claimed evidence is invalid/incomplete. Independently audit and close the following without trusting prior markers.

### A. Prove post-AI ownership loss, not entry cancellation
- Current `test_cancel_after_ai_prevents_commit` passes `lambda: True`, so the executor exits at its first pre-AI check. Replace with sequenced/barrier fakes proving `prepare_revision_submission` or `prepare_rewrite_action` completed before ownership loss.
- Cover initial submission and rewrite separately for: cancel flips true, cancel raises, heartbeat false, heartbeat raises, lease/takeover false, clean retry exactly once, and late old-owner response after new-owner success.
- Assert real repository business state: no new initial thread/audit; no rewrite suggestion/turn/status/audit mutation. A mock commit counter alone is insufficient.
- Make cancel-check exceptions fail closed as a normal durable error result rather than relying on outer worker exception handling when practical.

### B. Prove successful concurrent routing and no shared-state contamination
- Existing concurrency/routing tests intentionally fail before AI because `ai_task_runner=None`; they prove only resolver invocation and unchanged `self.repo` identity.
- Use deterministic successful fake product-AI runners and two distinct real repositories/projects. Execute two jobs concurrently through one resolver-backed executor. Assert each repo receives exactly its own thread/audit/candidate, no cross-project artifact, correct provider/model metadata, and one job's ownership loss cannot suppress/capture the other.
- Exercise concurrent rewrite preparation/commit on the shared service path as well.
- Inspect the new thread-local `_effective_repo` refactor for nested contexts, exception cleanup, and any remaining direct `self.repo` reads inside the canonical AI path that could bypass the selected repo. Simplify to explicit repo parameters if thread-local indirection remains fragile; do not reintroduce shared mutation or duplicate prompt logic.
- Ensure rewrite preparation operates on a deep copy and cannot mutate an in-memory repository before commit.

### C. Complete table-cell atomic acceptance evidence
- Existing success test only checks working-copy revision/thread status. Assert the exact target cell plain text changed to proposal, non-target cells unchanged, rich-text representation preserved and consistent, table version/CAS advanced correctly, and source DOCX state immutable.
- Add wrong block/table/row/column/cell, stale table version/block hash, selected-text drift, rich-text mismatch, idempotent replay result equality, and multiple injected transaction-boundary failures. For every failure prove thread/suggestions, working copy, table/cell content, audit/snapshots/idempotency are unchanged; clean retry succeeds once.
- Keep one SQLite `BEGIN IMMEDIATE` transaction and all existing plan/freeze/quarantine/source/citation guards.

### D. Regression
- Run revision durable/API/application plus shared durable-core tests and any focused tests added.
- Report exact commands/counts, source locations, failed iterations and remaining uncertainty. Inspect the final diff for unrelated churn.

Emit `WORKER_03_KIMI_FALLBACK_COMPLETE` only when A/B/C are directly exercised by passing deterministic tests. Otherwise report the exact blocker without a completion marker.
