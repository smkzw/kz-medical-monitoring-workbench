# W4 read-only execution-manager plan

You are Kimi Code / k3 with high reasoning acting as the visual/frontend
execution manager. Fully read global and project `AGENTS.md` and your normal
instructions. Work only in the runner-provided workbench.

## Read these files only

- `context/mw_w4_recommendation_frontend_20260724_context.md`
- `reviews/codex_subagent_w4_frontend_map_20260724.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/main.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- the existing frontend QC files explicitly named in the W4 map

Write exactly one output file:
`runs/execution/mw_w4_recommendation_frontend_20260724/kimi_manager_plan_01.md`.
The runner owns that report. Do not write it with tools; return the complete
report in final text.

## Hard boundaries

- Read-only planning pass. Do not edit any production source, test, evidence,
  prompt or record.
- W3 composite-adopt is still in progress. Identify the exact final API/type
  facts the implementation worker must reread after W3 acceptance.
- Do not introduce a parallel frontend state machine, remount TipTap, rewrite
  the structured table editor, move product-AI responsibilities into the UI, or
  use "待医学批准" for a medical-manager selection.
- Desktop is primary. Do not remove desktop capability for mobile.
- Codex owns final browser, clinical-language and production acceptance.

## Manager work

Produce an implementation-ready plan with at most four non-overlapping workers
or coherent slices. Include:

1. Exact current component/state/API map and proposed minimal file write sets.
2. A package-card interaction contract for recommended/alternative/pending
   candidates, path overrides, tradeoffs, evidence gaps, source text first, and
   one-request composite adoption with truthful receipt feedback.
3. An early competitor drawer that reuses `WritingReferencePanel`, including
   the minimal `variant/embedded/compact` contract and state-preservation rules.
4. A real assessment-instrument appendix preview using `appendix_image` blocks
   already returned in the working copy: thumbnails, page count, page selection,
   enlarged review, long 9-page behavior, and base64 memory/performance
   constraints. Do not invent a new backend unless current response truly
   cannot support it.
5. Desktop information architecture for 1920x1080, 1600x1000 and 1366x768.
   Keep recommendations primary and manual fields under advanced refinement.
6. Exact deterministic tests, browser interaction checks and screenshot matrix.
   Include return-key/editor/table/fullscreen regressions and no horizontal
   overflow.
7. Sequencing, rollback boundaries, likely edge cases, and the evidence Codex
   must verify directly.

Return a compact loop trace and end with:
`KIMI_W4_MANAGER_PLAN_01_COMPLETE`
