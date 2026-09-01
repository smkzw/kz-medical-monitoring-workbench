Continue the same `mw_durable_jobs_20260722` Grok execution-manager session. This is a bounded write-capable remediation after the Hermes worker explicitly returned blockers instead of the required completion marker. You are the execution manager: inspect current source, implement the remaining coherent patch, run decisive tests, and return evidence to Codex. Do not merely restate the previous review.

Read these files only as the initial set; additional in-workspace reads required by the task are allowed and must be recorded:
- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `context/mw_durable_jobs_20260722_execution_context.md`
- `plans/codex_execution_mw_durable_jobs_20260722.md`
- `runs/execution/mw_durable_jobs_20260722/manager_w5_current_review.md`
- `runs/execution/mw_durable_jobs_20260722/worker_05_followup_true_recovery_context_04.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `services/api/app/main.py`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py`
- `services/api/app/medical_writing_plan_consumption.py`
- `services/api/app/medical_writing_company_corpus.py`
- `services/api/app/medical_writing_shared_corpus.py`
- `services/api/app/medical_writing_revision_prompts.py`
- `services/api/app/ai_task_runner.py`
- `services/api/app/ai_execution_policy.py`
- `services/api/app/source_intake.py`
- `packages/contracts/workbench_contracts/models.py`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/useDurableMwJob.js`
- `frontend/src/features/medical-writing/durableJobState.mjs`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- the directly relevant revision/durable/frontend tests

## Hard boundaries

- Codex remains final authority. Do not claim product-AI E3, browser E4, DOCX E5, launch, or final acceptance.
- Write exactly one output file: `runs/execution/mw_durable_jobs_20260722/manager_w5_bounded_remediation_05.md`. It is runner-managed; do not edit that report path. Return the complete report in final text.
- Work only in this workspace except for the explicit global instruction read.
- This is a bounded execution-manager remediation and must run with `permission-mode=bypassPermissions`.

Authorized source write scope:
- `services/api/app/main.py`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py` only for narrowly required generation-lineage/adoption validation
- `packages/contracts/workbench_contracts/models.py` only if a narrow persisted lineage field is required
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/useDurableMwJob.js`
- `frontend/src/features/medical-writing/durableJobState.mjs`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- directly affected tests

Do not change W1 durable-store lease/CAS semantics, product AI or translation algorithms, clinical logic, source DOCX, plan/freeze policy, visual design, or unrelated application structure. Preserve user/other-worker changes.

## Accepted baseline from the latest worker

- Actual rewrite branch HTTP 202 exists.
- Initial/rewrite business key now includes a context fingerprint, so the narrow 409 issue was partially mitigated.
- `App.jsx` now reads revision locators on mount and has partial cancel/retry controls.
- Real writing accept is partially gated away from the old two-request path.

These partial changes are not sufficient. Close every remaining P0/P1 below.

## Backend contract

1. Replace the permissive fingerprint with a canonical versioned descriptor and full 64-hex SHA-256. Required authoritative reads must fail closed; do not use broad `except Exception: pass` to turn missing WC, StudyDefinition, confirmed plan/projection or selected evidence into empty strings.

2. The descriptor/business identity must include:
   - stable real/demo service namespace;
   - operation and normalized semantic request, including intent/instruction/comment/anchor/rewrite parent;
   - authoritative WorkingCopy id/revision/content hash from `authoritative_revision_source_identity()`;
   - authoritative StudyDefinition id/revision/state hash from `authoritative_study_definition_binding()`;
   - confirmed AssemblyPlan id/revision/actual `state_sha256` plus consumed projection names and each `content_sha256`;
   - company corpus snapshot id/version/hash and shared corpus catalog/admitted asset identities used by the candidate;
   - complete selected Evidence Brief identity: status, translation revision, source/document/text/glossary/medical-review identities and approved text hash;
   - current Source Registry entry/span/content-validation identity where consumed;
   - prompt contract version and the provider/model/policy identity from the real AI execution policy resolution. Do not read nonexistent `AiTaskRunner.provider_name/model_name` attributes and silently record empty values.

3. Persist descriptor + digest in durable payload and artifact lineage. Use a versioned v2 business key derived from canonical JSON so identical context reuses and any semantic/context change creates a new job without weakening store conflict semantics.

4. In `SectionAiCandidateExecutor`, rederive and compare the descriptor immediately before product-AI execution and again after AI but before any thread/candidate/audit commit. Drift must fail deterministically and leave no business mutation. Ownership/cancel/heartbeat checks remain mandatory.

5. Persist exact artifact lineage: exact thread id, generated suggestion id(s), post-thread/state hash and generation-context digest. Completed replay must retrieve those exact IDs; remove all first/last suggestion guessing for durable initial/rewrite replay.

6. `accept-and-apply` must revalidate the generation descriptor against current authoritative WC/StudyDefinition/plan/projection/corpus/evidence/source/policy context before the repository transaction. The repository transaction must compare the validated digest with the thread/suggestion lineage. Stale candidates are blocked and write neither author-selection nor body changes. Old production apply helpers must not bypass this gate.

## Frontend contract

7. The tested state machine must be imported and used by production. Remove duplicate inline terminal/cleanup decisions or route them through production-imported `durableJobState.mjs`.

8. For initial, rewrite, triage and translation:
   - persist a versioned locator with exact operation context before polling;
   - resume after reload;
   - terminal status alone is not reconciliation;
   - if `/result` or exact business artifact reconciliation fails, keep locator and expose retry/reconcile;
   - cancel requests cancellation and then reconciles; it does not clear immediately;
   - durable retry persists any returned replacement job id;
   - timeout/network/unmount/project or section switch never means success and cannot mutate the new screen;
   - duplicate submission is blocked per operation context;
   - if initial and rewrite locators coexist, both are recoverable rather than silently `break`ing after one.

9. Exact artifact checks:
   - revision/rewrite require locator/result thread + exact generated suggestion IDs/post-state;
   - triage uses exact run/snapshot;
   - translation uses exact batch/snapshot/scope and persists a new durable id returned by retry.

10. Real-project UI must have no reachable `needs-write-retry`, legacy accept+apply or `applyApprovedRevision` path. Remove the obsolete production button/state rather than merely replacing it with an error badge.

## Decisive tests

Add behavior-level tests that execute the production path:

- identical canonical descriptor reuses the same completed job;
- WC, StudyDefinition, plan/projection, company/shared corpus, evidence status/version/hash, source registry, intent/instruction/comment, rewrite parent, policy/provider/prompt or service namespace change creates a distinct job, not 409;
- invalid/stale selected evidence fails before provider execution;
- pre-AI drift and post-AI/pre-commit drift create no thread/candidate/audit;
- exact initial/rewrite replay remains stable after unrelated suggestions are appended;
- adoption unchanged commits once/idempotently; plan/corpus/evidence/source/policy drift rolls back both selection and body;
- production-imported JS reducer/controller proves persistence-before-poll, reload resume, terminal result fetch failure retention, cancel reconciliation, replacement-job retry, duplicate prevention, exact artifact checks and stale-screen suppression;
- triage failed-run retry uses exact run id; translation retry stores/polls the returned durable id;
- no source-string-only test or `(202,404,409)` permissive assertion is used as the decisive proof.

Run focused tests first, then the complete W1-W5 regression matrix, production-imported Node state tests, frontend contracts and `npm run build`. Report exact commands/counts/warnings and changed files.

Return `MANAGER_W5_BOUNDED_REMEDIATION_COMPLETE` only if current source has no remaining P0/P1 under this contract. Otherwise return `MANAGER_W5_BOUNDED_REMEDIATION_BLOCKED` with the exact recovery boundary and no completion claim.
