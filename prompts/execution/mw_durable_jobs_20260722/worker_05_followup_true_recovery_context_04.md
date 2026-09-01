Continue the same `mw_durable_jobs_20260722` Worker 05 Hermes session. This is a targeted fourth remediation pass. The previous report marker is rejected after Codex inspected the current source. Do not repeat broad refactoring or claim completion from test counts. Fix the exact production defects below and prove them with behavior-level tests.

Read these files only as the initial set; additional in-workspace reads required to implement or test the contract are allowed and must be listed in the loop trace:
- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `context/mw_durable_jobs_20260722_execution_context.md`
- `plans/codex_execution_mw_durable_jobs_20260722.md`
- `runs/execution/mw_durable_jobs_20260722/manager_w5_current_review.md`
- `runs/execution/mw_durable_jobs_20260722/worker_05_followup_production_acceptance_03.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `services/api/app/main.py`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py`
- `services/api/app/medical_writing_plan_consumption.py`
- `services/api/app/models.py`
- `services/api/app/durable_jobs.py`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/useDurableMwJob.js`
- `frontend/src/features/medical-writing/durableJobState.mjs`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- `tests/test_medical_writing_revision_durable.py`
- `tests/test_medical_writing_revision_api.py`
- `tests/test_medical_writing_durable_job_integration.py`
- `tests/test_frontend_durable_job_contract.py`
- `frontend/src/features/medical-writing/durableJobState.test.mjs`

## Hard boundaries

- Codex remains final authority. Do not claim product-AI E3, browser E4, DOCX E5, launch, or final acceptance.
- Write exactly one output file: `runs/execution/mw_durable_jobs_20260722/worker_05_followup_true_recovery_context_04.md`. This is runner-managed output.
- Do not edit that report path. Return the complete report in final text; the runner owns report persistence.
- Work only in this workspace except for the two global instruction reads.

Authorized write scope:
- `services/api/app/main.py`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py` only if an existing authoritative generation-lineage/adoption revalidation boundary must be extended
- `services/api/app/models.py` only for a narrowly required response/payload contract
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/useDurableMwJob.js`
- `frontend/src/features/medical-writing/durableJobState.mjs`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- directly affected backend/frontend tests

Do not change W1 durable-store lease/CAS semantics, product AI algorithms, clinical logic, source DOCX, plan/freeze policy, broad visual design, or unrelated application structure.

## Current-source defects that must all close

### 1. Revision recovery is still not implemented in production

Current `App.jsx` writes `mw_revision_job_${projectId}` and `mw_rewrite_job_${projectId}`, but never reads either key. It still owns initial and rewrite through standalone `pollDurableMwJob` fixed-loop polling. Implement real production recovery:

- Route initial candidates and rewrites through the shared durable controller/hook (or one equivalent production-imported state machine), not dead helper code.
- On mount/project re-entry, read persisted locators and resume the exact job. Persist operation context sufficient to distinguish initial/rewrite and section/thread/suggestion identity.
- Timeout, process interruption, reload, unmount, project switch or section switch are not success. Keep the locator unless a terminal status plus terminal `/result` were both reconciled, or the user explicitly dismisses a reconciled terminal failure.
- Show actionable retry/cancel controls. Cancellation must be requested and then reconciled; do not erase the locator immediately.
- Reject stale completion callbacks after project/section context changes.
- Never choose `threadsResp[last]`, `suggestions[0]` or `suggestions[-1]` to infer the completed artifact.

### 2. The shared hook/state machine is dead and clears too early

Current `durableJobState.mjs` is only imported by its test. `useDurableMwJob` is not used in production. It also clears localStorage after a terminal status even if `/result` fails.

- Production code must import and execute the tested state/reconciliation logic.
- Locator cleanup requires successful result reconciliation for `completed`, `failed`, or `cancelled` terminal outcomes. A failed result request retains the locator and exposes retry/reconcile.
- The terminal callback receives a normalized object containing both terminal status and reconciled result.
- Cached-completed start and resumed-completed start must run through the same reconciliation path.
- One active locator per operation context disables duplicate submission.

### 3. Canonical generation context must be authoritative, complete and fail-closed

Replace the current permissive `_derive_context_fingerprint` implementation. Required authoritative reads must not be wrapped in broad `except Exception: pass` blocks.

Build a canonical versioned descriptor and full 64-hex SHA-256 over at least:

- stable service route namespace distinguishing real and demo repositories/services;
- project/document/section/anchor and semantic request fields, including intent, instruction, user comment, rewrite source thread and source suggestion;
- current authoritative working-copy id, revision and content/state hash;
- authoritative StudyDefinition binding id, revision and hash;
- confirmed ProtocolAssemblyPlan id, revision and actual `state_sha256`;
- every relevant confirmed plan-consumption projection manifest identity and `content_sha256` used by this candidate path;
- protocol corpus snapshot identity and relevant company/shared corpus snapshot identity;
- each selected Evidence Brief id, current status, version/revision, full source/document/translation/glossary/medical-review hashes or equivalent current identity;
- source-registry/current source identity where the writing path consumes it;
- product provider, model, prompt-contract version and policy version.

Use existing authoritative repository/helper methods. Missing or stale required working-copy, StudyDefinition, confirmed plan, required projections or selected evidence must fail before reuse/AI execution. Do not silently replace missing fields with empty strings. Optional surfaces may be represented explicitly as `null` only when the existing business path genuinely treats them as optional.

Persist the descriptor and full fingerprint in the durable payload/audit lineage.

### 4. Legitimate context changes must create new jobs, not 409

The store is uniquely keyed by `(project_id, job_type, business_key)`. Therefore adding a fingerprint only to `request_hash` is insufficient and currently converts valid context changes into `DurableJobRequestConflict`.

- Define versioned `v2` business identities that include the full canonical semantic request plus context fingerprint.
- Repeating an identical request in identical context reuses the same job.
- Changing working-copy, StudyDefinition, plan/projection, corpus, evidence, intent, instruction, comment, rewrite source state, provider/prompt/policy or service namespace creates a distinct job without conflict.
- Do not weaken the store conflict behavior for truly inconsistent payloads under the same key.

### 5. Revalidate before and after AI, and immediately before commit

- Executors must rederive the authoritative descriptor/fingerprint immediately before product-AI execution and again immediately before any revision-thread/audit/business write.
- If context drifted, fail the durable job with a deterministic stale-context error and write no revision thread, candidate, working-copy change or business audit claiming candidate generation.
- Retain existing claim/cancel/heartbeat ownership checks. Context validity is an additional gate, not a substitute.

### 6. Exact artifact lineage and replay

- Initial and rewrite executor results must persist exact `thread_id`, exact generated suggestion id(s), post-generation thread/state hash and the generation context fingerprint.
- Completed replay must retrieve and return those exact artifacts. Never infer from first/last/current list position.
- A later suggestion appended to the same thread must not change an old job's `/result`.
- Adoption must revalidate that the generation context still matches current authoritative plan/corpus/evidence/source state. Stale generated candidates must be blocked with a clear regeneration action before `accept-and-apply`.

### 7. Triage and translation must use the same recovery semantics

- Persisted locator is retained on timeout/network failure/unmount.
- Resume on remount; cancel then reconcile; durable failure/cancellation exposes real retry/reconcile.
- Domain-level translation retry for partial failed items may remain, but must not strand the unified durable job.
- Remove stale locator only after successful terminal result reconciliation or explicit dismissal of a reconciled failure.

### 8. Retire reachable production half-state adoption

Current source still contains `needs-write-retry` and `applyApprovedRevision`. Remove or make unreachable for real writing projects. Real author selection must use only `accept-and-apply`; no production UI may leave `author_selected` without the working-copy body write or offer a legacy retry-write path.

### 9. Replace false-green tests with decisive behavior tests

Add/repair tests that prove the production path, not merely source strings or an unused pure helper:

- actual durable submission: identical context reuses; each relevant context/semantic field change creates a new job rather than 409;
- invalidated/stale selected evidence fails before reuse/AI;
- context drift after AI but before commit produces no revision thread/business write;
- exact rewrite suggestion replay remains stable after later suggestions are appended;
- actual HTTP rewrite branch is 202 and exact atomic missing-thread contract is a specific 4xx;
- production-imported frontend state/controller: persistence before polling, reload resume, timeout/network locator retention, terminal result reconciliation, result-fetch failure retention, cancel reconciliation, retry, duplicate prevention and stale-screen suppression;
- `App.jsx` mounts and reads both revision locators and exposes cancel/retry through the actual production path;
- triage and translation share the tested recovery contract;
- no reachable real-project `needs-write-retry`/legacy accept+apply path.

Tests that merely accept several status codes, search for source strings, call `_derive_context_fingerprint` without a durable submit, or test code not imported by production do not satisfy this pass.

## Verification and completion marker

Run focused revision/API/durable/frontend behavior tests, the full W1-W5 matrix (updated count is acceptable), Node tests for production-imported state logic, frontend contract tests and `npm run build`. Report exact commands, counts, warnings and files changed.

End with `WORKER_05_TRUE_RECOVERY_CONTEXT_COMPLETE` only if every requirement above is implemented in current source and proven by decisive tests. Otherwise return a precise blocker and recovery boundary with no completion marker.
