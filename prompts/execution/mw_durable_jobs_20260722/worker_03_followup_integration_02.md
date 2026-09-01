Continue the same `mw_durable_jobs_20260722 / worker_03` execution session. Fully reread and comply with `/Users/smkzw/.hermes/SOUL.md`, global/project `AGENTS.md`, the original Worker 03 report, the atomicity follow-up report, and the manager second-pass report.

Hard boundaries:
- Work only inside the runner-provided current workspace (`.`).
- Preserve Worker 03 ownership: `services/api/app/medical_writing.py`, `services/api/app/medical_writing_repository.py`, `tests/test_medical_writing_revision_durable.py`, `tests/test_medical_writing_revision_application.py`; a minimal targeted change in `services/api/app/sqlite_runtime_store.py` is authorized only if required to preserve the existing single SQLite transaction for table-cell adoption. Do not edit `main.py`, frontend, shared durable-job core, triage, translation, exporter, or unrelated services.
- Runner-managed report path: `runs/execution/mw_durable_jobs_20260722/worker_03_followup_integration_02.md`. Never invoke write/edit tools on this report; return the report in final text.
- Product AI remains the independently configured service. Do not substitute execution-model output for product AI.

Read initially:
- `AGENTS.md`
- `runs/execution/mw_durable_jobs_20260722/worker_03.md`
- `runs/execution/mw_durable_jobs_20260722/worker_03_followup_atomicity_01.md`
- `runs/execution/mw_durable_jobs_20260722/manager_second_pass.md`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py`
- relevant medical-writing methods in `services/api/app/sqlite_runtime_store.py`
- `services/api/app/main.py` lines around `_medical_writing_services` for read-only integration context
- `tests/test_medical_writing_revision_durable.py`
- `tests/test_medical_writing_revision_application.py`

Codex independently confirmed four integration defects. Fix them as one coherent W3 integrity slice rather than preserving compatibility workarounds.

## P0-1: old-owner business writes during long product-AI execution

`SectionAiCandidateExecutor.execute` currently calls full `submit_revision` / rewrite `apply_action`, which commits the revision thread before the executor proves it still owns the durable claim. A cancel, heartbeat failure, lease expiry, or takeover during product-AI generation can therefore leave business state written by an old owner even though durable completion is rejected.

Required correction:
1. Split product-AI generation/preparation from business persistence for both initial submission and rewrite. Reuse the existing request validation, confirmed-plan projection, 3-5 candidate/citation/provider audit logic, and repository commit APIs; do not fork a lower-quality second prompt path.
2. Immediately before every revision-thread business commit, prove ownership with exception-safe fail-closed `cancel_check()` and a positive heartbeat/claim refresh. Any exception, false result, cancellation, expiry, or takeover means no revision thread, rewrite append, audit event, working-copy mutation, or other business artifact is written by that owner.
3. The durable payload must remain sufficient after process restart and must not depend on request-local objects.
4. Add deterministic barriers/fakes that flip cancellation, heartbeat failure/exception, or ownership after AI returns but before commit. Assert no new thread/audit for initial submission and no rewrite turn/audit mutation for rewrite. Then prove a clean retry succeeds exactly once.

## P0-2: one executor must route to the correct per-project service

`main._medical_writing_services(project_id)` dynamically chooses demo versus real service/repository, while `DurableJobWorker` registers exactly one executor per job type and the current executor binds one service instance.

Required correction:
1. Make `SectionAiCandidateExecutor` accept a restart-stable service resolver callable (or an equivalently narrow resolver abstraction) keyed by `project_id`, while retaining backward compatibility for existing direct service construction if tests need it.
2. Resolve the service inside `execute` for every job. Never persist a request-local service object in the durable payload.
3. Add a deterministic test with two project IDs routed to distinct fake services/repositories and prove one registered executor sends each job to the correct service without cross-project writes.
4. Do not edit `main.py`; expose an implementation-ready constructor/API for W5 composition-root wiring.

## P0-3: atomic candidate adoption must support table-cell anchors

The frontend already offers AI revision on `table_cell`, but `accept_and_apply_candidate` explicitly raises and tells callers to use the unsafe two-step path. W5 must remove the two-request accept-then-apply workflow for all editable targets, not silently retain it for tables.

Required correction:
1. Extend the existing single-transaction `accept_and_apply_candidate` path to table-cell anchors using the canonical table/cell validation and rich-text replacement behavior already implemented by `apply_approved_revision_to_working_copy`.
2. Preserve block/table/row/column/cell identity checks, selected-text uniqueness, rich-text/plain-text agreement, citations if supported by the existing table path, expected working-copy revision CAS, frozen/quarantined guards, source DOCX immutability, audit/idempotency effects, and all-or-nothing rollback.
3. Add success, stale revision, anchor drift/wrong cell, rich-text preservation, idempotent replay, and injected pre-commit failure tests. After failure, suggestion/thread/working copy/audit/idempotency must remain pre-action; clean retry succeeds once.
4. Do not disable table-cell AI or retain a two-step production escape hatch.

## P1-4: invalid section consistency check

`if thread.section_id != thread.section_id` is a tautology. Replace it with a meaningful document/section/working-copy consistency validation using existing canonical project/document/section state, or remove it if the surrounding authoritative lookup already proves the invariant. Add a negative test for a genuinely mismatched/missing section so the guard is observable.

## Regression and completion gate

Run at minimum:
- `tests/test_medical_writing_revision_durable.py`
- `tests/test_medical_writing_revision_api.py`
- `tests/test_medical_writing_revision_application.py`
- `tests/test_medical_writing_durable_jobs.py`

Also run any additional focused tests you add. Inspect the final diff for unrelated churn. Report exact commands, counts, source locations, remaining uncertainty, and a compact loop trace.

Finish with `WORKER_03_REVISION_INTEGRATION_V2_COMPLETE` only when all four defects are closed by deterministic tests. Otherwise return the exact remaining blocker without the marker.
