Continue the same Grok execution-manager session `23209f5d-d713-4c40-ae71-f4f1f6e98b27`. The previous completion marker is rejected by Codex source inspection. This is one targeted same-session acceptance follow-up, not a new broad audit. Inspect the current filesystem, implement the bounded fixes below, run behavioral tests, and return an evidence report. Do not substitute model confidence or source-string assertions for executable behavior.

Read these files only as the initial set; additional in-workspace reads required by reproduced failures are allowed and must be recorded:
- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `context/mw_durable_jobs_20260722_execution_context.md`
- `plans/codex_execution_mw_durable_jobs_20260722.md`
- `runs/execution/mw_durable_jobs_20260722/manager_w5_bounded_remediation_05.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- the current source and directly affected tests listed below

## Hard boundaries

Codex remains final authority. Work only in this workspace except for the explicit global instruction read. Run with `permission-mode=bypassPermissions`. Preserve unrelated changes. Do not change clinical logic, product-AI/translation algorithms, W1 durable-store lease/CAS semantics, source DOCX, visual design, or unrelated application structure.

Authorized source writes:
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py` only if exact lineage/adoption validation requires it
- `packages/contracts/workbench_contracts/models.py` only if a narrow persisted lineage field is required
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/useDurableMwJob.js`
- `frontend/src/features/medical-writing/durableJobState.mjs`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- directly affected tests

Write exactly one output file: `runs/execution/mw_durable_jobs_20260722/manager_w5_followup_acceptance_06.md`. It is runner-managed; do not write that report path with tools. Return the complete report in final text.

## Codex-reproduced acceptance failures to fix

1. **Cancel result-reconciliation violation.** In current `App.jsx`, `cancelRevisionJob` calls `shouldClearLocator(status, resultReconciled || status === "cancelled")`. A cancelled status without a successfully fetched/reconciled result clears the locator. Remove that override. Cancellation must retain the locator and expose reconciliation/retry whenever `/result` or exact business reconciliation fails.

2. **Stale project/section completion.** The revision recovery effect captures `selectedSection` but depends only on `projectId`; active initial/rewrite/retry awaits also have no stable operation-generation guard. Switching project/section while a poll or exact-thread fetch is pending must prevent every message/thread/active-thread/state mutation on the new screen while preserving the old locator. Use a production-imported shared context token/controller or an equivalent explicit generation guard checked after every awaited boundary. Do not rely only on AbortController because polling/results may already resolve.

3. **v2 exact artifact fallback is invalid.** Current recovery and rewrite code uses `extractArtifactThreadId(result) || stored.thread_id` and `extractArtifactThreadId(rwResult) || thread.thread_id`. For `mw_gen_ctx_v2`, missing exact result lineage is reconciliation failure. Remove v2 fallback guessing. Require exact thread ID, exact generated suggestion IDs, and any persisted post-state identity before locator cleanup. Keep any legacy compatibility strictly version-gated and unreachable for a v2 locator/result.

4. **Coexisting initial/rewrite recovery blocks.** Current recovery loops sequentially over two locators, so a long initial poll can block rewrite recovery for minutes and one scalar `revisionJobState` overwrites the other. Make both locators independently recoverable and observable. Start recovery concurrently or introduce a keyed operation-state map/controller. A user must be able to reconcile/cancel/retry the exact initial or rewrite job without silently targeting the other.

5. **Shared hook clears before domain reconciliation.** `useDurableMwJob` removes local storage after transport-level `/result` success, including cached-completed and failed/cancelled paths, before a domain callback proves the exact run/batch/thread/suggestion/snapshot artifact. Refactor the production shared controller so cleanup requires an explicit successful domain-reconciliation acknowledgement. HTTP 200 alone is not enough. Preserve full operation context when retry returns a replacement job ID.

6. **Production state-machine proof is false-green.** The pure helper has 44 basic assertions, but production paths still duplicate polling/cleanup logic. Route terminal classification, locator retention/cleanup, replacement retry, stale-context suppression, exact artifact validation and duplicate prevention through production-imported code. Add executable JS behavior tests against that production controller/adapter. Source-string Python checks are supplemental only.

7. **Backend shared-corpus identity is incomplete.** Current `_corpus_descriptor()` records only admitted segment IDs/hashes and omits the actual `MedicalWritingSharedCorpusCatalog.layer_id`, `asset_version`, and `asset_sha256`, even though the service exposes them. Include these authoritative catalog fields plus deterministic admitted asset identities. Fail closed on partial present catalog identity.

8. **Source Registry identity is not an identity.** Current descriptor records only booleans and a path. Where the generation path consumes registered sources, include deterministic current `SourceRegistryEntry`, relevant span, parser/content hash/version, and content-validation identity/status used by the candidate. Reuse the same authoritative service/store methods the generation path consumes. Missing required identity must fail before provider execution; do not add broad exception suppression. If a source class is genuinely not consumed for the operation, record a precise explicit absent/not-consumed state rather than a fake empty identity.

9. **Canonical descriptor test coverage is materially incomplete.** The previous report claimed broad coverage, but the added tests did not independently prove changes in WC, StudyDefinition, plan/projection, company/shared corpus, evidence status/version/hash, Source Registry, comment, rewrite parent, provider/model/prompt/policy, or service namespace. Add table-driven tests that mutate each authoritative input and prove a distinct v2 job/business identity; identical canonical context must reuse. Verify stale/invalid selected evidence and incomplete required authority fail before product-AI invocation.

10. **Exact lineage and adoption behavioral proof.** Add tests that append unrelated suggestions after completion and prove initial/rewrite replay still returns only the persisted exact suggestion(s). Prove pre-AI and post-AI/pre-commit context drift leaves no thread/candidate/audit mutation. Prove adoption unchanged commits once/idempotently, and drift in plan/corpus/evidence/source/policy rolls back both author decision and body mutation.

11. **Triage and translation parity.** Inspect the current panels for the same result-versus-domain reconciliation, replacement-job ID, stale-screen and locator cleanup errors. Triage must use exact run/snapshot identity; translation exact batch/snapshot/scope/durable ID. Fix only reproduced parity defects and add behavior tests.

## Required verification

Run smallest focused tests while editing, then:
- complete W1-W5 backend regression matrix already defined in the task plan;
- production-imported Node state/controller behavior tests;
- directly affected frontend contract tests;
- `npm run build`.

The report must contain changed files, exact commands, pass counts/warnings, and a requirement-to-test mapping. Explicitly state any still-unverified point. Return `MANAGER_W5_FOLLOWUP_ACCEPTANCE_COMPLETE` only if every P0/P1 above is closed in current source and behavior tests; otherwise return `MANAGER_W5_FOLLOWUP_ACCEPTANCE_BLOCKED` with the exact recovery boundary. Do not claim E3/E4/E5, release, browser acceptance, DOCX acceptance, or launch.
