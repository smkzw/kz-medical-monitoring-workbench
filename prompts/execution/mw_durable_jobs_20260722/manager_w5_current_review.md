Continue the same `mw_durable_jobs_20260722` execution-manager session as a read-only W5 current-source acceptance reviewer. Fully reread and comply with global `/Users/smkzw/.codex/AGENTS.md`, project `AGENTS.md`, the execution context, plan, and current reports. Codex remains final authority.

Hard boundaries:
- Read and test the current workspace only. Do not edit production source, tests, prompts, records, or the runner-managed report.
- Runner-managed report path: `runs/execution/mw_durable_jobs_20260722/manager_w5_current_review.md`; return the complete report in final text.
- Do not claim product-AI E3, browser E4, DOCX E5, launch, or final acceptance.
- Judge current source and real behavior, not worker completion markers or source-string tests.

Read initially:
- `AGENTS.md`
- `context/mw_durable_jobs_20260722_execution_context.md`
- `plans/codex_execution_mw_durable_jobs_20260722.md`
- `runs/execution/mw_durable_jobs_20260722/manager_third_pass.md`
- `runs/execution/mw_durable_jobs_20260722/worker_05.md`
- `runs/execution/mw_durable_jobs_20260722/worker_05_followup_complete_01.md`
- `runs/execution/mw_durable_jobs_20260722/worker_05_followup_complete_02.md`
- `services/api/app/main.py`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_durable_jobs.py`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/useDurableMwJob.js`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- `tests/test_medical_writing_revision_api.py`
- `tests/test_medical_writing_durable_job_integration.py`
- `tests/test_frontend_durable_job_contract.py`

Gate first. Require all exact markers:
- `MANAGER_THIRD_PASS_READY_FOR_W5`
- `WORKER_05_JOB_INTEGRATION_COMPLETE`
If absent, return `MANAGER_W5_CURRENT_REVIEW_BLOCKED`.

Codex has already run the combined W1-W5 matrix: 300 passed in 58.95s. Independently rerun the focused matrix needed to verify any finding, then audit these acceptance requirements:

1. Every long-running start endpoint, including initial section candidate, `request_rewrite`, competitor triage and translation create/retry, returns actual HTTP 202 and only queues/wakes durable work. No HTTP request thread or `BackgroundTasks` path performs long product-AI work.
2. Initial section candidate and rewrite persist a job locator before polling, resume after a browser reload, expose cancel/retry, and reconcile the durable `/result` response before clearing the locator. A fixed in-memory 200-loop poll is not acceptable as the sole control path.
3. Competitor triage and reference translation have the same durable guarantees: project isolation, persisted locator, reload recovery, visible progress/terminal error, cancel, unified retry where applicable, and no locator loss on timeout/network interruption.
4. `useDurableMwJob` is not merely dead code. Its terminal callback receives the reconciled result, and its state machine does not clear persistence before terminal result reconciliation. Confirm any standalone helper has equivalent persistence/recovery or is used only behind a durable owner.
5. Candidate acceptance uses only the atomic accept-and-apply path for production writing, handles CAS/idempotency correctly, and no reachable production UI path can create the old accepted-but-not-applied half-state.
6. Public DTOs and `/result` never expose internal payload, claim token, provider credentials or private stack traces. Cross-project status/cancel/retry/result access fails closed.
7. Dedupe/reuse keys cannot silently return a stale completed AI candidate after the relevant working-copy revision, plan/study definition, evidence selection or corpus snapshot changed. Report the exact current key inputs and severity.
8. Tests must exercise behavior, not only source strings. Identify false-green tests, permissive status assertions, invalid `500` acceptance, and missing reload/cancel/retry/result scenarios. Propose precise tests.
9. Inspect the current frontend at implementation level for race conditions: double submit, project/section switch during polling, unmount, cancellation, timeout, failed retry, and fetching the wrong latest thread when several jobs finish out of order.

Findings must be ordered P0/P1/P2 with exact file:line evidence, concrete user impact, and smallest coherent remediation. Separate confirmed defects from improvement ideas. Return `MANAGER_W5_CURRENT_REVIEW_READY` only if no P0/P1 remains. Otherwise return `MANAGER_W5_CURRENT_REVIEW_BLOCKED` and list the exact blockers. Include a compact loop trace and exact tests run.
