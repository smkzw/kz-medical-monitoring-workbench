Continue the same Grok execution-manager session `23209f5d-d713-4c40-ae71-f4f1f6e98b27`. Codex found one final exact-source P0 that the source-identity 07 tests did not execute. Fix only this defect and its tests.

Read these files only as the initial set; additional directly relevant in-workspace reads are allowed and must be recorded:
- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `runs/execution/mw_durable_jobs_20260722/manager_w5_followup_source_identity_07.md`
- `services/api/app/medical_writing.py`
- `services/api/app/source_intake.py`
- `tests/test_medical_writing_generation_context_v2.py`
- `tests/test_medical_writing_registered_sources.py`
- `tests/test_medical_writing_revision_durable.py`

## Hard boundaries

- Codex remains final authority. No E3/E4/E5/browser/DOCX/release/launch claims.
- Work only in this workspace except explicit global instruction reads.
- Write scope: `services/api/app/medical_writing.py` and directly affected tests only.
- Do not alter frontend, durable store lease/CAS, product AI algorithm, clinical logic, translation, source files, runtime data, prompts or records.
- Run with `permission-mode=bypassPermissions`.
- Write exactly one output file: `runs/execution/mw_durable_jobs_20260722/manager_w5_followup_exact_source_binding_08.md`. It is runner-managed; do not edit that report path. Return the complete report in final text.

## Reproduced P0: first-use self-drift and unrelated-source invalidation

Current durable original-protocol flow is internally inconsistent:

1. `submit_revision_durable()` builds generation context before provider execution. On the first AI use of an imported/original protocol, Source Registry may have no medical-writing selection yet, so descriptor entries are empty.
2. `SectionAiCandidateExecutor` pre-AI revalidation is still empty.
3. `_run_revision_ai()` calls `_register_revision_source()` for the selected paragraph/cell, mutating Registry.
4. post-AI/pre-commit revalidation now includes the new entry/span, so the task detects its own expected registration as context drift and rejects every first-use result after provider execution.

Additionally, `_source_registry_descriptor(project_id)` currently includes all medical-writing registrations/spans for the document. Registering an unrelated paragraph later changes every existing candidate’s digest and blocks adoption, despite that unrelated span not being consumed by that candidate.

## Required solution properties

- Generation context must bind the **exact source selection consumed by this operation**, not the whole project/document Registry.
- For initial original-protocol generation, deterministically ensure/register the selected source before the canonical descriptor/business key is finalized, or derive and persist the exact equivalent binding without mutable ambiguity. Registration is allowed only as idempotent source intake; it must not create a revision thread/candidate/audit before provider success.
- Persist exact source binding in the durable payload/context: entry id/content/parser identity plus exact source id/type/locator/preview hash and current validation identity.
- Executor pre-AI and post-AI rederive the same exact binding. `_run_revision_ai()` must consume/check that binding rather than create a new untracked selection.
- Rewrite and adoption must rederive from the parent thread’s persisted exact source entry/source id/locator and fail closed if that exact source changes/disappears.
- A later unrelated registration/span for the same protocol must not change this candidate’s digest or block adoption.
- A change in the exact consumed entry/span/content/validation must change the digest and block stale generation/adoption.
- Table-cell source-locator resolution must remain supported and exact.
- Greenfield behavior from 07 must remain unchanged and registry-free.

Do not solve this by suppressing post-AI drift or excluding Source Registry entirely. Do not pre-register every paragraph. Do not keep all document spans in the candidate descriptor.

## Decisive tests

Add executable behavior tests that prove:

1. Original protocol + initially empty Source Registry + durable submit/executor with an echo provider completes successfully, persists exact entry/source IDs and does not self-drift.
2. No thread/candidate/audit exists if provider fails after source intake; only idempotent source registration may remain.
3. After a successful candidate, register a different paragraph/span for the same file; current candidate generation digest and adoption revalidation remain unchanged.
4. Mutating/removing the exact consumed span, entry content/parser identity or its current validation changes digest/fails closed and adoption writes neither selection nor body.
5. Rewrite exact binding is stable and does not fall back to another span.
6. Greenfield descriptor tests from 07 remain green.

Run focused tests, then generation-context, registered-source, durable revision and durable integration subsets. Return exact commands/counts/warnings and changed files. Return `MANAGER_W5_EXACT_SOURCE_BINDING_COMPLETE` only if the current source passes all tests; otherwise `MANAGER_W5_EXACT_SOURCE_BINDING_BLOCKED` with exact recovery boundary.
