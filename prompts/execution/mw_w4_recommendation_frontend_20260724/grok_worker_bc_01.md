# W4-B/C frontend execution: early competitor drawer and real appendix preview

You are Grok Build / grok-4.5 acting as the write-capable visual/frontend
execution worker. Fully read and comply with global and project `AGENTS.md` and
your normal operating instructions. Work only in the runner-provided workbench.
This run uses `permission-mode=bypassPermissions`.

## Read these files only

- `/Users/smkzw/.hermes/SOUL.md`
- `/Users/smkzw/Documents/AI Cache/Codex x Hermes/AGENTS.md`
- `context/mw_w4_recommendation_frontend_20260724_context.md`
- `reviews/codex_subagent_w4_frontend_map_20260724.md`
- `runs/execution/mw_w4_recommendation_frontend_20260724/kimi_manager_plan_01.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/styles.css`
- `frontend/tests/medical_writing_reference_drawer_qc.mjs`
- `frontend/tests/medical_writing_assessment_instruments_isolated_qc.mjs`
- directly imported local frontend components needed to preserve current
  conventions

Write exactly one output file:
`runs/execution/mw_w4_recommendation_frontend_20260724/grok_worker_bc_01.md`.
This is the runner-managed report. Do not write it with tools; return the
complete report in final text and let the runner persist it.

## Hard boundaries

Authorized source/test write set:

- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- new `frontend/src/features/medical-writing/AuthoringCompetitorDrawer.jsx`
- new `frontend/src/features/medical-writing/InstrumentAppendixPreview.jsx`
- `frontend/src/styles.css`
- `frontend/tests/medical_writing_reference_drawer_qc.mjs`
- `frontend/tests/medical_writing_assessment_instruments_isolated_qc.mjs`
- at most one new focused frontend QC file for appendix image interaction

Preserve unrelated user changes. Do not edit backend code, API contracts,
product-AI prompts/providers, `App.jsx`, TipTap, structured table components,
candidate package adoption code, task records, or generated release evidence.
W3 is still unaccepted; do not implement W4-A composite adoption in this pass.
Codex owns final browser, visual, clinical-language, and production acceptance.

## Required implementation

### 1. Early competitor-processing drawer

- Add a restrained desktop right-side drawer that can be opened from the first
  authoring/design step as soon as the project exists. It must reuse the real
  `WritingReferencePanel`; do not copy its fetching, triage, translation,
  review, or selection state machine.
- Extend `WritingReferencePanel` only with optional presentation props such as
  `embedded` and `compact`. Existing callers and default behavior must remain
  unchanged.
- Keep the embedded panel mounted when the drawer is closed so search/triage
  state, selected references, scroll position, and a running job are not lost.
  A project change may use the panel's existing reset behavior.
- Hide or collapse run IDs, hashes, locators, and process logs by default.
  Prioritize candidate studies, source text, translation/review status, and
  actionable processing controls.
- Closing the drawer must not modify or reset unsaved framing/PICOS draft
  values. Support Escape and an explicit close icon button with tooltip and
  accessible label.
- Desktop targets: approximately 560 px on 1920/1600 widths and 480 px at
  1366; no page-level horizontal overflow.

### 2. Real assessment-instrument appendix preview

- Use the existing working-copy `content_blocks` where
  `block_type="appendix_image"` and
  `attachment_kind="assessment_instrument_page"`. Do not add a new backend.
- Render every returned page as a readable thumbnail with page number and
  total. Clicking opens a desktop enlarged review overlay with previous/next
  buttons, page selector/indicator, close button, Escape close, and arrow-key
  navigation.
- For a 9-page 220-DPI instrument, thumbnail images use `loading="lazy"` and
  the enlarged overlay mounts only the current full page image. Do not copy
  base64 payloads into additional state, localStorage, or a second transformed
  image set.
- Keep the source page order deterministic. If `page_count` disagrees with
  actual blocks, show a small content-consistency notice using the actual block
  count; do not block review.
- Zero-page state should preserve the existing upload/replacement workflow.
  Read-only mode must permit review but not upload/delete.
- Use clear clinical-document styling aligned with the existing Kangzhe
  workbench. Avoid nested cards, oversized notices, rounded pill-heavy UI, and
  mobile-driven capability removal.

## Required validation

Update or add deterministic tests that prove:

- the drawer opens from the early authoring step;
- closing/reopening preserves the panel and local framing/PICOS draft state;
- existing non-embedded `WritingReferencePanel` callers retain current output;
- 9 real-shape appendix blocks produce 9 ordered thumbnails;
- enlarged review mounts one current full-page image, supports next/previous,
  page indicator, Escape close, and does not duplicate base64 payloads in state;
- read-only preview remains usable while mutation controls are disabled;
- mismatch and zero-page states are truthful;
- there is no W4-A composite-adopt implementation in this pass.

Run the focused QC files and `npm --prefix frontend run build`. If the current
runtime can safely be used without restarting the backend, exercise the drawer
and appendix preview at 1920x1080, 1600x1000, and 1366x768 and save only
task-scoped temporary screenshots. Do not claim final visual acceptance.

## Completion report

Return a compact loop trace: sources read, files changed, behavior implemented,
exact tests and counts, browser observations if run, failed paths, residual
uncertainty, and recommended next action.

End with exactly:

`GROK_W4_BC_01_COMPLETE`
