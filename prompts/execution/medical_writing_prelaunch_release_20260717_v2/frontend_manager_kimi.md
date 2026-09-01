# Frontend execution-manager review: current release candidate

First read and comply with the latest `/Users/smkzw/.codex/AGENTS.md`,
workspace `AGENTS.md`, and `frontend/AGENTS.md`. You are Kimi Code/k3 acting
as the visual/frontend execution manager. This is execution management, not a
conference. Codex owns final browser, clinical, Word, and release acceptance.

## Hard boundaries

- Work only inside the current workspace.
- Product source and tests are read-only in this pass.
- Use disposable runtimes and non-stable ports if you need live interaction.
- Do not touch stable ports/databases, credentials, original clinical files,
  or release scripts.
- Do not declare final acceptance.
- Write exactly one output file:
  `runs/execution/medical_writing_prelaunch_release_20260717_v2/frontend_manager_kimi.md`.

Read these files only for initial context:

- `/Users/smkzw/.codex/AGENTS.md`
- `AGENTS.md`
- `frontend/AGENTS.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ACCEPTANCE_CONTRACT.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/TASK_RECORD.md`
- `runs/execution/medical_writing_prelaunch_release_20260717_v2/frontend_remediation.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/browser_final_qc/frontend_remediation_matrix.json`
- `frontend/src/App.jsx`
- `frontend/src/App.css`
- `frontend/src/features/medical-writing/StructuredTableDesigner.jsx`
- `frontend/tests/medical_writing_frontend_remediation_qc.mjs`

The initial list is not a blanket prohibition on tools or evidence. Record
each additional target and why it was needed.

## Objective

Review the current post-remediation desktop writing experience as an execution
manager for a senior Chinese clinical-protocol writer preparing a real project.
Do not merely restate the 42 PASS checks. Inspect whether the checks and
screenshots actually prove the product behavior and whether any test can pass
while the user remains blocked.

## Required review

1. Inspect the greenfield and RUX screenshots at 1440x900, 1920x1080, and
   2560x1440 plus `rux_table_journey_1920_1080.png`.
2. Audit the current interaction matrix and App/StructuredTableDesigner code
   for false positives, missing click paths, weak assertions, stale state,
   focus/caret failures, content loss, and accessibility/desktop ergonomics.
3. Focus on:
   - new project creation and transition into two-stage framing/PICOS;
   - editor Enter, formatting, undo/redo, save/reload/restart;
   - imported-source structure boundaries;
   - document and table fullscreen, real cell editing and format controls;
   - document map and right AI/evidence/literature rails;
   - 1440/1920/2560 clipping, overlap, logo/status bar, editor area hierarchy;
   - visible log/developer text or information overload;
   - HTTP/error handling and whether the expected 409 is isolated.
4. If a live disposable browser check is needed, run it without modifying
   source. Record direct observations separately from inference.
5. Build a defect ledger with severity, exact reproduction, evidence, and the
   precise same-session Grok rerun request for any P0/P1. Do not request broad
   redesigns without a reproducible user impact.
6. State whether the frontend evidence is ready to proceed to the mandatory
   post-fix CMS/Grok/Reasonix full-function retest. This is a manager
   recommendation, not release acceptance.

Use the required execution-report headings:

1. `# Execution Output: medical_writing_prelaunch_release_20260717_v2 - frontend_manager_kimi`
2. `## Boundary And Context Check`
3. `## Work Performed`
4. `## Artifacts And Evidence`
5. `## Commands And Observations`
6. `## Defect Ledger`
7. `## Blockers Or Missing Environment`
8. `## Rerun Requests Or Next Step`
