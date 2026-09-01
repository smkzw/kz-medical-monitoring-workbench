Continue the same `mw_durable_jobs_20260722 / worker_03` session. Fully reread and comply with `/Users/smkzw/.hermes/SOUL.md` and workspace `AGENTS.md`.

Hard boundaries:
- Work only inside the runner-provided current workspace (`.`).
- Preserve Worker 03 ownership: `services/api/app/medical_writing.py`, `services/api/app/medical_writing_repository.py`, `tests/test_medical_writing_revision_durable.py`; a minimal targeted change in `services/api/app/sqlite_runtime_store.py` is now explicitly authorized only to implement the required single SQLite transaction and its fault injection. Do not edit `main.py`, frontend, contracts, shared durable-job core, exporter, author-freeze APIs outside the atomic path, or unrelated services.
- Runner-managed report path: `runs/execution/mw_durable_jobs_20260722/worker_03_followup_atomicity_01.md`. Never invoke write/edit tools on this report; return it in final text.
- Do not substitute execution-model content for product AI.

Read initially:
- `AGENTS.md`
- `runs/execution/mw_durable_jobs_20260722/worker_03.md`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py`
- the medical-writing revision/working-copy methods in `services/api/app/sqlite_runtime_store.py`
- `tests/test_medical_writing_revision_durable.py`
- `tests/test_medical_writing_revision_application.py`

Codex rejects the current atomicity claim. The report itself confirms two sequential committed CAS transactions: thread/suggestion becomes `author_selected` first, then working-copy application commits separately. An exception between them leaves a durable half-state. Retryability is not atomicity.

Required correction:
1. Implement true both-or-neither persistence for candidate acceptance plus working-copy update in one SQLite `BEGIN IMMEDIATE` transaction. Reuse existing validation/idempotency/audit behavior; do not duplicate broad repository logic or weaken stale/frozen/quarantined/project/source-DOCX protections.
2. The operation must atomically persist all relevant effects: selected suggestion accepted, siblings not selected, thread author-selected, working-copy revision/content update, idempotency outcome and required audit events. Any validation or injected exception before COMMIT must roll back all of them.
3. Add deterministic fault injection at multiple internal boundaries, at minimum after revision-decision writes and before working-copy write/commit. After each injected failure prove: thread remains pre-action, all suggestions remain pending, working copy is byte/semantic equivalent to pre-action, no success idempotency record remains, and a clean retry succeeds exactly once.
4. Preserve idempotent replay after success and stale expected-revision rejection. Keep source DOCX immutable.
5. Review `SectionAiCandidateExecutor`: check claim/cancel before and after the real synchronous AI path and before business writes; prove queued payload is sufficient after process restart and does not depend on request-local objects.
6. Rerun focused revision durable/API/application tests and shared durable core. If another worker's incomplete triage import prevents collection, run the W3-owned tests that do not import `main.py`, record that external blocker precisely, and do not modify triage code.

Finish with `WORKER_03_REVISION_ATOMICITY_COMPLETE` only when fault-injection tests prove true rollback atomicity. Otherwise return the exact remaining boundary without the marker.
