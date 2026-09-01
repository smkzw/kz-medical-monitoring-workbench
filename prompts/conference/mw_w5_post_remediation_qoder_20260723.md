# W5 Durable Recovery Post-Remediation Audit — Qoder/Qwen3.8

Use the already-running visible `qodercli` session in `~/Downloads/QoderVIP`. Keep the active model fixed to `qmodel_preview` / `Qwen3.8-Max-Preview`; do not impose artificial tool, turn, context, or output limits, and do not start a substitute or headless Qoder process.

Before entering the workspace, fully read the global Codex instructions at `/Users/smkzw/.codex/AGENTS.md`, the shared workspace overlay at `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`, and fully read and comply with the Qoder/Hermes identity instructions at `/Users/smkzw/.hermes/SOUL.md`. These are instruction authorities, not workspace evidence files.

First `cd ./medical-writing-current`. This is a read-only current-source conference audit after the Grok execution manager finishes W5 remediation. Codex owns final acceptance. Before any audit work, verify that `runs/execution/mw_durable_jobs_20260722/manager_w5_followup_exact_source_binding_08.md` exists and contains the marker `MANAGER_W5_EXACT_SOURCE_BINDING_COMPLETE`; otherwise write only a blocked report identifying the unmet gate and stop without auditing stale source.

## Hard boundaries

- Do not edit production source, tests, runtime databases, stable services, user documents, prompts or records.
- You may run focused read-only tests with bytecode/cache disabled in isolated temporary directories. Do not mutate the normal runtime.
- Runner-managed report path: `runs/conference/mw_w5_post_remediation_qoder_20260723/qoder_qwen38_current_audit.md`.
  In this existing visible Qoder route there is no separate runner, so write exactly this one report with tools and do not create sibling artifacts.
- Do not claim product-AI E3, browser E4, DOCX E5, launch, clinical/regulatory acceptance or final production acceptance.

## Read these files only:

- `AGENTS.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `runs/execution/mw_durable_jobs_20260722/manager_w5_current_review.md`
- `runs/execution/mw_durable_jobs_20260722/worker_05_followup_true_recovery_context_04.md`
- `runs/execution/mw_durable_jobs_20260722/manager_w5_bounded_remediation_05.md`
- `prompts/execution/mw_durable_jobs_20260722/manager_w5_followup_acceptance_06.md`
- `runs/execution/mw_durable_jobs_20260722/manager_w5_followup_acceptance_06.md`
- `runs/execution/mw_durable_jobs_20260722/manager_w5_followup_source_identity_07.md`
- `runs/execution/mw_durable_jobs_20260722/manager_w5_followup_exact_source_binding_08.md`
- `services/api/app/main.py`
- `services/api/app/medical_writing.py`
- `services/api/app/medical_writing_repository.py`
- `services/api/app/medical_writing_plan_consumption.py`
- `services/api/app/ai_task_runner.py`
- `services/api/app/ai_execution_policy.py`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/useDurableMwJob.js`
- `frontend/src/features/medical-writing/durableJobState.mjs`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/features/writing-reference/ReferenceTranslationBatchPanel.jsx`
- `tests/test_medical_writing_durable_jobs.py`
- `tests/test_medical_writing_triage_durable.py`
- `tests/test_medical_writing_revision_durable.py`
- `tests/test_writing_reference_translation_durable_jobs.py`
- `tests/test_medical_writing_durable_job_integration.py`
- `tests/test_medical_writing_generation_context_v2.py`
- `tests/test_frontend_durable_job_contract.py`
- `tests/test_medical_writing_revision_api.py`
- `tests/test_medical_writing_revision_application.py`
- `tests/test_medical_writing_registered_sources.py`
- `frontend/src/features/medical-writing/durableJobState.test.mjs`

This is the initial read set rather than a blanket prohibition. Additional in-workspace current-source reads are allowed when needed to verify a concrete finding; record them.

## Acceptance audit

Audit current source and decisive behavior for:

1. canonical versioned generation descriptor is complete, authoritative, full-hash and fail-closed for required WC, StudyDefinition, confirmed AssemblyPlan/projections, company/shared corpus, Evidence Brief, Source Registry and AI policy resolution; shared corpus must include actual `layer_id`, `asset_version`, `asset_sha256` and admitted-asset identities, while Source Registry must include the entry/span/content/parser/content-validation identities actually consumed rather than booleans or paths;
2. context identity is in the business key and durable payload/lineage, so legitimate context or semantic changes create a new job without 409 while identical requests reuse;
3. executor revalidates before product AI and after AI immediately before any business commit; context drift leaves no thread/candidate/audit mutation;
4. durable `/result` persists exact thread, exact generated suggestion IDs, post-state hash and context hash; v2 reconciliation and replay never infer or fall back to stored/current/first/last/latest items;
5. atomic adoption revalidates generation context and is the only real-project author-selection path;
6. production imports and uses the tested durable state machine for initial, rewrite, triage and translation, or all four route through an equivalent single tested controller;
7. locator is persisted before poll, restored after reload, retained on timeout/network/result-fetch failure, cleared only after exact terminal result and business artifact reconciliation, and not lost on cancel/retry; `cancelled` status alone is never treated as reconciliation and HTTP 200 from `/result` is insufficient until the domain artifact is acknowledged;
8. replacement retry job IDs are persisted; exact run/batch/thread/suggestion/snapshot/scope are reconciled;
9. a stable generation/context guard is rechecked after every awaited boundary so project/section/unmount switch rejects stale completions and cannot mutate the new screen; double submit is blocked per operation; coexisting initial/rewrite locators recover independently without sequential head-of-line blocking or scalar-state overwrite;
10. no reachable real-project `needs-write-retry`, legacy accept+apply or `applyApprovedRevision` path remains;
11. tests are behavior-level and production-imported, not permissive status assertions, source strings, or unused helper tests; require explicit mutation cases for WC, StudyDefinition, plan/projection, company/shared corpus, evidence status/version/hash, Source Registry, intent/instruction/comment, rewrite parent, provider/model/policy/prompt and service namespace, plus cancel-result failure, replacement retry ID, stale screen, exact artifact and dual-locator recovery;
12. triage reconciles exact run/snapshot and translation reconciles exact batch/snapshot/scope/new durable retry ID under the same cleanup, cancel and stale-screen rules.
13. original-protocol candidates register and bind exactly the consumed selection before digest finalization, so an initially empty Registry cannot self-drift after product AI; unrelated later paragraph registration does not invalidate the candidate; rewrite/adoption rebind exact entry/source/locator; greenfield projects remain Registry-free and dynamic imported projects resolve `original_protocol_path()` without hard-coded project IDs.

Run the smallest decisive focused tests needed to prove or disprove each claim. Findings must be P0/P1/P2 with exact file/function/line, reproduction, user impact and smallest coherent remediation. Separate current observation, test evidence, inference, stale historical report and uncertainty.

End with exactly one marker:

- `QODER_W5_CURRENT_AUDIT_READY` only if no P0/P1 remains; or
- `QODER_W5_CURRENT_AUDIT_BLOCKED` with exact blockers.

Include a compact loop trace and all commands/tests run.
