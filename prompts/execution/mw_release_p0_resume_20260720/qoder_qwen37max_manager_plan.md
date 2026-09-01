You are the read-only execution manager for
`mw_release_p0_resume_20260720`. Use the existing visible QoderVIP/qodercli
session and Qwen3.7-Max. This is a new task unrelated to the previous
cross-project audit, so the caller will send `/new` before this prompt.

Before working, fully read the current global
`/Users/smkzw/.codex/AGENTS.md`, then the workspace `AGENTS.md`.

Hard boundaries:
- Work only in the current medical-writing workbench workspace.
- This first pass is read-only for product source, tests, runtime and user
  originals.
- Do not modify source, tests, databases, stable services, real project data,
  configuration, credentials or user originals.
- You may use terminal, search, web and source inspection. External discovery
  must prefer official docs and qualifying open-source implementations.
- Write exactly one durable artifact:
  `runs/execution/mw_release_p0_resume_20260720/manager_plan.md`.
- Codex remains final source, clinical, browser, Word and release authority.

Read these files first:
- `context/mw_release_p0_resume_20260720_execution_context.md`
- `plans/codex_execution_mw_release_p0_resume_20260720.md`
- `records/active_slices/medical_writing_final_release_e2e_20260720/TASK_RECORD.md`
- `records/active_slices/medical_writing_final_release_e2e_20260720/SOFT_PAUSE_RESUME.md`
- `runs/execution/mw_synopsis_import_latency_p0_20260720/hy3_readonly_audit.md`
- `runs/execution/mw_cross_project_document_contamination_p0_20260720/qoder_qwen37max_readonly_audit.md`
- current source and focused tests directly implementing synopsis import,
  working copies/editor/export and user confirmation/approval semantics.

Task:
Refine these three P0 items into a concrete execution plan.

1. Resumable asynchronous synopsis import:
   - persistent job and stage state;
   - truthful progress from parse through direct DeepSeek v4-pro generation,
     validation and commit;
   - polling or SSE, cancellation, retry/resume and cold-restart recovery;
   - no test Agent in the product path;
   - source-fidelity repair for the reproduced
     `picos.safety_endpoints: expected 1 ordered source item(s), got 0`;
   - real MY009 and MY004 acceptance, latency/error observability and frontend
     lazy-user experience.

2. StudyDefinition-bound working copies:
   - authoritative id/revision/hash fingerprint on create/update/read;
   - fail-closed quarantine for legacy/unbound or stale copies;
   - explicit auditable adopt-authority or migrate-copy action;
   - one content truth across editor, preview and DOCX export;
   - no indication-keyword block and no second medical approval.

3. User selection is confirmation:
   - AI suggestion remains suggestion until selected;
   - user select/adopt/confirm/save atomically creates effective version and
     audit event;
   - subsequent authority/source changes produce `needs_reconfirmation`;
   - remove second `待医学批准/医学批准` workflow while preserving quality,
     evidence, translation and export gates;
   - cover backend contracts, API, frontend labels/actions and migration.

For each item provide:
- first-principles invariants and failure modes;
- exact existing files/services/tests involved;
- exact writable file set for its worker;
- shared-file collision matrix and required serial/parallel order, including
  the currently running competitor-triage Followup 02;
- implementation slices small enough for one worker session;
- deterministic unit/integration/browser/cold-restart/DOCX acceptance;
- migration and rollback;
- external open-source patterns worth adopting, with license and direct link;
- stop conditions and what remains Codex-only acceptance.

Do not merely restate the audits. Inspect current code and catch incorrect
audit assumptions. The final report must make worker prompts directly
derivable without another architecture discussion.
