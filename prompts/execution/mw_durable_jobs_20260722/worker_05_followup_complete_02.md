Continue the same W5 Hermes session `20260723_014134_a08d3d`. Your previous continuation correctly withheld `WORKER_05_JOB_INTEGRATION_COMPLETE`; now close only the demonstrated gaps below. Fully reread `/Users/smkzw/.hermes/SOUL.md`, global/project `AGENTS.md`, both W5 reports, this prompt, and current source.

Hard boundaries:
- Same authorized W5 write scope only: `services/api/app/main.py`, narrow medical-writing frontend modules/call sites, and affected API/frontend/integration tests.
- Do not edit accepted W1-W4 durable/business algorithms unless an exact composition incompatibility blocks completion; report instead.
- Product AI remains independently configured. No execution-model content may replace it.
- Runner-managed report path: `runs/execution/mw_durable_jobs_20260722/worker_05_followup_complete_02.md`. Return the report in final text; never write/edit that path.

Read initially:
- `AGENTS.md`
- `runs/execution/mw_durable_jobs_20260722/worker_05.md`
- `runs/execution/mw_durable_jobs_20260722/worker_05_followup_complete_01.md`
- `services/api/app/main.py`
- `services/api/app/medical_writing.py`
- `tests/test_medical_writing_revision_api.py`
- `tests/test_medical_writing_durable_job_integration.py`
- `tests/test_frontend_durable_job_contract.py`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/useDurableMwJob.js`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`

## 1. Fix the three revision failures for the correct reason

Codex reproduced exactly:
- rewrite provider envelope count is 1 instead of 2;
- provider-failure case begins with 6 suggestions instead of 3;
- approved-evidence case times out.

Root cause A: the test class reuses module-level `mw_durable_store`/worker across cases. Deterministic business keys therefore reuse completed jobs and their artifact locators from prior cases, so later providers are not invoked and already-rewritten threads leak across tests. Give each test an isolated temporary `DurableJobStore` + `DurableJobWorker`, register a `SectionAiCandidateExecutor` whose resolver returns the currently patched test service, patch both `main.mw_durable_store` and `main.mw_durable_worker`, and boundedly shut it down in teardown. Do not weaken production dedupe semantics merely to make tests pass.

Root cause B: the approved-evidence test exits `patch(main.medical_writing_revision, service)` immediately after POST, before the asynchronous executor resolves the service. Keep the patch active through terminal polling/result assertions. Add a direct assertion that the provider envelope contains only the approved evidence brief.

For provider failure, require terminal `failed` or `retry_wait` according to the durable retry contract and prove no new suggestions/audit/thread mutation. Do not accept `completed` as a provider-failure result.

Run the 14 revision API tests repeatedly in at least two fresh processes to prove order independence. Then run W1-W5 focused backend tests.

## 2. Use the shared frontend control plane; do not leave dead code

`useDurableMwJob.js` now exists but `App.jsx` does not import/use it and instead has two hand-written 200x1.5s polling loops. Replace those loops with the shared control plane or an equivalently shared controller. Required:
- locator persisted before navigation/reload and resumed after reload;
- terminal callback receives reconciled `/result` data, not only the status body;
- explicit failed/cancelled handling; never fetch/display a “latest thread” after failed/cancelled;
- cancel/retry controls and visible monotonic phase/progress;
- double-click dedupe and project-switch isolation;
- clear locator only after terminal result/business artifact reconciliation.

Initial generation and rewrite must both use it. No 5-minute inline polling loop in event handlers.

## 3. Competitor triage must be actually integrated

The actual UI is `WritingReferencePanel.jsx`, not only `MedicalWritingAuthoringJourneySetup.jsx`. It currently supports manual classification/finalization but has no durable AI triage start/status/result/cancel/retry. Add a restrained AI triage task control there, while preserving manual author review/finalization as the final decision. Persist both `run_id` and `job_id`, use unified job status/result, then reload the business triage run. Surface independent-AI configuration/failure distinctly. Do not auto-finalize AI output.

## 4. Translation must use the unified job control plane

The previous report explicitly left translation on legacy batch polling; that does not satisfy W5. Make create/retry responses expose the durable `job_id` together with backward-compatible batch data. Integrate `ReferenceTranslationBatchPanel.jsx` with unified status/result/cancel/retry and page reload resume. The batch endpoint remains the business artifact view, not the job control plane. Preserve its existing item/chapter progress display and dedupe, but drive lifecycle from the durable job.

## 5. Strengthen deterministic tests

The current `test_frontend_durable_job_contract.py` mostly checks string presence and even documents translation as unchanged. Replace/add assertions that prove the actual three call sites use the shared control plane, App has no manual 200-iteration polling loop, failed/cancelled cannot load a latest thread, atomic adoption is one request for real paragraph and table-cell paths, and triage/translation expose cancel/retry/reload locators. Add backend API tests proving translation start/retry returns a job locator and no long BackgroundTasks path.

Run:
- revision API tests twice in fresh processes;
- W1-W5 focused backend/integration matrix with exact counts;
- all affected frontend contract tests;
- Vite production build.

Finish with exactly `WORKER_05_JOB_INTEGRATION_COMPLETE` only if all checks pass. Browser E4, product-AI E3, DOCX E5 and launch remain Codex-owned.
