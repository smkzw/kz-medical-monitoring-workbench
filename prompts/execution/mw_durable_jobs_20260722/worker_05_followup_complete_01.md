# W5 targeted continuation: finish unified durable-job integration

Resume the same Hermes execution-worker session `20260723_014134_a08d3d`. This is a targeted completion pass, not a new design pass. Fully reread `/Users/smkzw/.hermes/SOUL.md`, global/project `AGENTS.md`, the original W5 prompt, your first-pass report, and the current source before editing.

Codex independently reproduced the current source. Do not repeat the first-pass claim that all remaining revision failures are stale tests. The following are real integration defects or missing contracts and must be fixed together.

## Hard boundaries

- Authorized write scope remains: `services/api/app/main.py`; narrow medical-writing frontend call sites/modules; affected frontend/API/integration contract tests. Do not edit the accepted W1-W4 core/adapter algorithms unless a newly demonstrated composition incompatibility makes it unavoidable; if so stop and report the exact blocker.
- Product runtime must continue using its independently configured production AI. Do not replace it with Hermes output.
- No long model/OCR/translation call may run inline or as a FastAPI `BackgroundTasks` fallback. Background tasks may wake the durable worker only.
- Do not weaken plan/freeze/quarantine/source-DOCX contracts or reintroduce generic `待医学批准`.
- Runner-managed report path: `runs/execution/mw_durable_jobs_20260722/worker_05_followup_complete_01.md`. Return the report in final text and never invoke write/edit tools on that path.

Read initially:

- `AGENTS.md`
- `prompts/execution/mw_durable_jobs_20260722/worker_05.md`
- `runs/execution/mw_durable_jobs_20260722/worker_05.md`
- `runs/execution/mw_durable_jobs_20260722/manager_third_pass.md`
- `services/api/app/main.py`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_durable_jobs.py`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- `tests/test_medical_writing_revision_api.py`

## Backend defects to close

1. **Rewrite remains synchronous.** `POST /revision-threads/{thread_id}/actions` still calls synchronous `service.apply_action(... request_rewrite ...)`, while initial generation is durable. Migrate only `request_rewrite` to `service.request_rewrite_durable(...)`, return `202` + `job_id`/status/cached terminal result, and wake the shared worker. Keep short non-AI actions synchronous. Update tests to poll the real durable job and then fetch the resulting thread; do not merely change old `200` assertions.
2. **Atomic adoption request parsing is broken.** The current sync endpoint calls `request.body()` without awaiting it, then passes a coroutine into `json.loads`. Replace raw `Request` parsing with a typed Pydantic request contract in the authorized API layer (or make the route correctly async if an existing contract truly cannot be reused), with stable 422 validation. Add API tests for paragraph and table-cell success, missing/invalid fields, CAS drift, idempotent replay, and all-or-nothing failure.
3. **Translation long-call fallback must disappear.** In create/retry routes, failure to locate/wake a durable job must fail closed or rely on durable recovery; it must never schedule `run_pending`/`run_failed` through `BackgroundTasks`. A wake exception may be recorded as accepted because the sweeper recovers, but no alternate long executor may start.
4. **Unified public DTO/result semantics.** Verify status/result/cancel/retry are project-isolated; no `claim_token`, payload, lease, prompt or unauthorized source content leaks. Terminal result must provide a deterministic artifact locator sufficient for the frontend to fetch triage run/revision thread/translation batch. Add explicit tests.
5. **Lifecycle.** Verify startup recovery runs after all executors/services are registered at app startup and shutdown is bounded. Keep synopsis recovery intact. Do not swallow an initialization/configuration failure that would leave every durable job permanently queued without an observable signal; use the existing logging/health conventions if present.

## Frontend completion

Implement one small reusable durable medical-writing job client/hook if it reduces duplication. Migrate all three user paths:

- competitor triage in `MedicalWritingAuthoringJourneySetup.jsx`;
- initial section candidates and `生成下一轮` in the real authoring surface (`App.jsx` or its current narrow extracted component);
- reference translation in `ReferenceTranslationBatchPanel.jsx`.

Required behavior for each applicable path:

- persist the active `{project_id, job_id, job_type, business locator}` and resume after reload;
- poll unified status with monotonic visible progress/phase text and fetch terminal business artifact;
- disable/dedupe the initiating action while queued/running and on double click;
- cancel and retry through unified APIs with clear state-dependent controls;
- distinguish production-AI/provider/configuration failure from user cancellation and ordinary validation error;
- clear stale locators only after terminal state is reconciled; do not strand completed artifacts;
- no modal/log overload and no extra medical-approval step;
- candidate adoption must use the single `accept-and-apply` endpoint for paragraph and table-cell; remove the frontend two-request accept-then-apply chain.

## Deterministic acceptance

Add or update tests that actually execute the new contracts:

- backend: rewrite 202 -> job poll -> terminal thread; provider failure leaves thread unchanged; initial evidence brief filtering via durable result; project isolation; safe DTO; cancel-late-complete; retry; atomic paragraph/table-cell; translation never invokes background long path;
- frontend: reload resume, terminal rendering, double-click dedupe/disabled action, cancel/retry, independent-AI error, atomic adoption one-request behavior for paragraph and table-cell;
- integration: all three job types coexist without cross-project or cross-type collision.

Run focused W1-W5 backend tests, affected frontend contract tests, and Vite production build. Fix source defects, not only assertions. Finish with exactly `WORKER_05_JOB_INTEGRATION_COMPLETE` only when all deterministic checks pass. Browser E4, product-AI E3, DOCX E5 and launch remain Codex-owned and must not be claimed.

Return a compact report with changed paths, exact commands/counts, remaining uncertainty, and a loop trace.
