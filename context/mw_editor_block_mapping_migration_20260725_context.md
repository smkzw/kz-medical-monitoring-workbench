# Task Context: mw_editor_block_mapping_migration_20260725

Created: 2026-07-25 04:53:06
Objective: 修复医学写作TipTap回车/格式持久化块映射，并评审旧导入项目StudyDefinition迁移链路
Task type: `code_scoped_patch_plan`
Risk: `high`
Selected agent route: `codex` / `codex-main` / `high`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Project: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`
- Frontend editor implementation:
  - `frontend/src/App.jsx`
  - `frontend/src/features/medical-writing/editorSourceMapping.js`
  - `frontend/tests/editor_source_mapping_qc.mjs`
  - `frontend/tests/medical_writing_editor_formatting_qc.mjs`
- Backend consistency/import implementation:
  - `services/api/app/medical_writing_study_consistency.py`
  - `services/api/app/main.py`
  - relevant repository, synopsis-import, StudyDefinition, and authoring-journey services/tests
- Durable project record:
  - `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- Runtime truth: frontend `http://127.0.0.1:5174`, backend `http://127.0.0.1:8911`.
- Direct browser reproduction on `test01` showed that Enter at a heading boundary
  persisted the new body sentence inside the heading source block. A subsequent
  reload returned heading text containing both the heading and the inserted body
  sentence. Bold markup was not observed after the attempted toolbar action.
- The validation sentence was removed through the formal working-copy API and the
  section was restored at revision 2; no test sentence may remain in project data.

## Scope

- In scope:
  - preserve stable source block identity across Enter, inline marks, save, and reload;
  - prevent a body paragraph created after a heading from contaminating the heading
    block or silently changing its semantic type;
  - add deterministic and browser-facing regressions for Enter, bold, save, reload,
    undo/redo, and structure-error behavior;
  - implement or formally stage a source-preserving migration path that converts a
    legacy imported protocol/synopsis into a versioned StudyDefinition plus authoring
    journey before full editing;
  - preserve imported source files and source registry entries as read-only evidence.
- Out of scope:
  - security/backdoor scanning;
  - unrelated medical-monitoring or enrollment-review work;
  - rewriting current real project content;
  - changing the independent production-AI provider or prompt suite.

## Success Criteria

- Heading text remains heading-only after Enter, typing, save, and reload.
- New body text is attached to a valid paragraph/body source block while paragraph
  boundaries and allowed TipTap marks survive backend validation.
- Existing table and figure identities, citation marks, undo/redo, and source order
  remain intact.
- Focused frontend mapping tests, browser editor tests, Python contract tests, and
  Vite build pass.
- A legacy imported project can enter a formal, auditable migration/bootstrap flow
  that derives and confirms a StudyDefinition; no fake binding and no overwrite of
  the imported source is allowed.
- Codex repeats the real browser workflow and verifies persisted API payloads before
  accepting the patch.

## Risk Boundaries

- Worktree is shared and dirty; preserve unrelated user/agent changes and avoid broad
  formatting or refactors.
- Test edits must use a disposable or explicitly restored working copy. Never leave
  validation text in an existing project.
- Do not restart both services until focused tests and build pass; then perform one
  controlled restart and verify health/version state.
- Until 2026-07-25 08:30 Asia/Shanghai, any new role that would resolve to
  `Hermes/aishuo/cms-model` is routed to the existing QoderVIP `qodercli` session
  with model `qwen3.8-max-preview`; after that boundary, return new roles to Hermes.
- Do not start a substitute Qoder process. Observe the existing `qodercli` lineage.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Allowed Write Sets

- Frontend editor worker:
  - `frontend/src/App.jsx`
  - `frontend/src/features/medical-writing/editorSourceMapping.js`
  - `frontend/tests/editor_source_mapping_qc.mjs`
  - focused editor/browser tests only
- Legacy migration worker:
  - `services/api/app/medical_writing_legacy_authoring_migration.py` if needed
  - narrowly required API/contracts/repository files
  - focused backend tests only
- Codex:
  - integration fixes, task context, and durable task record

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-25 04:53:06: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-25 05:03: Direct runtime reproduction confirmed semantic source-block
  contamination at a heading boundary. The test project was restored through the
  versioned API before implementation work began.
- 2026-07-25 05:27: Frontend patch completed and independently reviewed. Heading
  overflow is routed into the immediately following paragraph source block; marks
  survive that routing; invalid targets fail closed. The same-revision reload defect
  now forces a fresh TipTap hydration only after both server reads succeed. Focused
  results: frontend contract 100 passed, mapping QC 9 scenarios passed, Vite build
  passed with 1888 transformed modules.
- Pending at this checkpoint: legacy-import backend state machine, Qoder manager
  review, controlled service restart, and real-browser/API persistence acceptance.
- 2026-07-25 05:51: Legacy-import backend state machine completed. Focused test
  result was 5 passed; the combined adjacent authoring/synopsis/consistency/frontend
  regression was 168 passed. Source bytes remain unchanged, confirmation is atomic
  and idempotent, and the existing consistency service reports binding_required.
- 2026-07-25 06:04: The preflighted Qoder manager contract was submitted to the
  existing QoderVIP qodercli session through its visible Terminal tab. Transcript
  evidence recorded model qmodel_preview and a new request. No substitute process
  was started. Await the designated report/marker without status prompts.
- 2026-07-25 06:47: Stateful desktop acceptance passed against the stable
  `5174/8911` runtime. At the heading boundary, Enter created a paragraph in the
  immediately following paragraph source block; the heading block remained
  heading-only. A bold marker persisted through UI save, API read, and same-revision
  UI reload. The unsaved-discard path did not mutate the server copy. The script
  then restored the section through the formal versioned API to revision 4 and
  verified that no `[QC-` marker remained. Evidence:
  `records/active_slices/medical_writing_production_rebaseline_20260722/evidence/editor_heading_boundary_20260725/heading_boundary_persistence_qc.json`
  and `saved_heading_body_bold_roundtrip.png`.
- 2026-07-25 06:49: Post-acceptance regressions passed: source mapping 9 scenarios,
  frontend medical-writing contract 100 tests, and Vite production build with 1888
  transformed modules. The focused editor block-mapping loop is accepted. The next
  safe action is the legacy import bootstrap frontend and medical-role override
  acceptance; do not reopen this loop unless a real user workflow reproduces a
  regression.
