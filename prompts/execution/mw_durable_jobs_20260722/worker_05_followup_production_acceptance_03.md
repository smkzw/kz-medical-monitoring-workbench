Continue the same `mw_durable_jobs_20260722` Worker 05 Hermes session. This is one combined, bounded production-acceptance remediation pass based on Codex current-source review and the Grok execution-manager report `runs/execution/mw_durable_jobs_20260722/manager_w5_current_review.md`.

Read these files only as the initial set; additional in-workspace reads required by the task are allowed and must be recorded:
- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `context/mw_durable_jobs_20260722_execution_context.md`
- `plans/codex_execution_mw_durable_jobs_20260722.md`
- `prompts/execution/mw_durable_jobs_20260722/worker_05.md`
- `runs/execution/mw_durable_jobs_20260722/worker_05_followup_complete_01.md`
- `runs/execution/mw_durable_jobs_20260722/worker_05_followup_complete_02.md`
- `runs/execution/mw_durable_jobs_20260722/manager_w5_current_review.md`
- `services/api/app/main.py`
- `services/api/app/medical_writing.py`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/useDurableMwJob.js`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- `tests/test_medical_writing_revision_api.py`
- `tests/test_medical_writing_durable_job_integration.py`
- `tests/test_frontend_durable_job_contract.py`

## Hard boundaries

- Codex remains final authority. Do not claim product-AI E3, browser E4, DOCX E5, launch, or final acceptance.
- Runner-managed output file: `runs/execution/mw_durable_jobs_20260722/worker_05_followup_production_acceptance_03.md`.
- Do not use write/edit tools on that runner-managed output file. Return the complete report in final text and let the runner persist exactly that one report.
- Work only inside the current workspace except for reading the two explicit global instruction files above.

Authorized write scope for this pass only:
- `services/api/app/main.py`
- `services/api/app/medical_writing.py` only for server-derived durable context fingerprint / stale-completed reuse prevention
- `frontend/src/App.jsx` narrow revision job and atomic-adoption call sites only
- `frontend/src/features/medical-writing/useDurableMwJob.js` and at most one small adjacent pure state-machine/helper module
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx` narrow triage durable controls only
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx` narrow translation durable controls only
- affected backend/frontend/integration tests

Do not change durable-store semantics, business AI/translation algorithms, source DOCX, plan/freeze contracts, clinical logic, visual design, or broad App structure.

The current W5 completion marker is rejected. Close every P0/P1 below in current source and prove behavior:

1. **Strict terminal semantics and exact result association**
   - A fixed polling loop reaching its loop limit/network interruption is not success. Only `status === "completed"` may trigger completed UI behavior.
   - Initial section candidate and rewrite must reconcile unified `/result` first and use its exact `artifact.thread_id`; never use the last item of `/revision-threads`.
   - Concurrent/out-of-order jobs for different sections must not cross-activate the wrong thread.

2. **Persisted revision control plane**
   - Use the reusable durable job hook/state machine in production, not dead code plus standalone in-memory polling.
   - Persist `{project_id, job_id, job_type, operation_context}` before polling; operation context must distinguish initial vs rewrite and retain section/thread identity needed to reconcile the exact result.
   - Resume automatically after reload/project remount, show monotonic phase/progress and terminal errors, and expose cancel and unified retry controls without modal/log overload.
   - Keep the locator on timeout/network interruption. Clear only after a terminal status and a successfully reconciled terminal `/result`, except explicit user dismissal of a terminal failure.
   - Prevent double submit while the same active job exists; project or section switch/unmount must not mutate the new screen from the old job.
   - Fix the hook so `onTerminal` receives the reconciled result plus status, not only the pre-result status body.

3. **Triage and translation parity**
   - Move both onto the same durable ownership semantics or a genuinely equivalent shared controller.
   - Do not clear persisted locators after max-loop timeout/network interruption.
   - Cancel must request cancellation, then reconcile terminal status/result before locator cleanup; do not delete locator immediately.
   - Failed/cancelled jobs must have a real unified retry path where the job contract permits retry. Translation's domain-level “retry failed items” may remain for partial business batches, but the durable job failure itself must not be stranded.
   - Preserve current project isolation, translation batch progress and business semantics.

4. **HTTP 202**
   - Initial candidate, competitor triage, translation create/retry already use 202 and must stay so.
   - `request_rewrite` must return actual HTTP 202 while accept/reject remain short synchronous 200. Since the route mixes actions, return an explicit 202 response for the durable branch without changing synchronous branches.

5. **Atomic adoption as the only production accept path**
   - For real writing sessions, an author selection must call only `accept-and-apply`. If the working copy is frozen, dirty, quarantined, non-authoritative or stale, block with a clear actionable message; never fall through to legacy `/actions` accept and never leave `author_selected` without the body write.
   - Demo-only behavior may remain isolated, but no reachable production “重试写入” may use the old two-request apply helper.
   - The atomic response currently contains `thread_id`, not `thread`. Reconcile the exact thread by `thread_id` and refresh/update the UI deterministically; do not branch on a nonexistent `payload.thread`.

6. **Server-derived context fingerprint for durable dedupe**
   - Before `create_or_reuse`, derive a stable context fingerprint from authoritative backend state, not frontend claims. It must invalidate completed candidate reuse when any relevant source changes: current working-copy id/revision/content hash, StudyDefinition id/revision/hash, confirmed ProtocolAssemblyPlan id/revision/hash, protocol/company corpus snapshot identity, and the current versions/hashes of selected evidence briefs where available.
   - Include this fingerprint in both business identity/request hash and the durable payload or audit lineage needed to prove what context generated the candidate.
   - Keep repeated identical requests idempotent. Fail closed if a required authoritative binding that the existing writing path requires is missing/stale; do not invent facts or weaken plan/freeze guards.
   - Rewrite identity must likewise prevent stale replay when its source thread/current context has changed.

7. **Replace false-green tests with behavioral evidence**
   - Add backend tests that assert rewrite actual HTTP status `202`, not `(200, 202)`.
   - Remove acceptance of HTTP `500` for nonexistent atomic thread; assert the correct 4xx contract and fix the route if needed.
   - Add deterministic tests for context-fingerprint reuse/invalidation across working-copy, StudyDefinition, plan, corpus and evidence-version changes.
   - Add frontend behavior/state-machine tests, not only source-string checks, for: persistence before poll; reload resume; timeout/network interruption retains locator; only completed is success; `/result.artifact.thread_id` exact selection; concurrent jobs cannot pick list tail; cancel reconciliation; unified retry; terminal callback includes result; project/section switch ignores stale completion; duplicate start disabled.
   - Use existing frontend tooling where available. A small pure `.mjs` state-machine module with executable Node tests is acceptable if it is the actual production code path. Source-string tests may remain as supplementary guards only.

8. **Regression and report**
   - Run focused backend/API/frontend behavioral tests, the full W1-W5 300-test matrix (or the updated exact count), and `npm run build`.
   - Report exact counts, files changed, known warnings and remaining E3/E4/E5 work.
   - End with `WORKER_05_PRODUCTION_ACCEPTANCE_REMEDIATION_COMPLETE` only if all P0/P1 above are closed in source and deterministic tests. Otherwise provide the exact blocker and recovery boundary without a completion marker.
