# Task Context: mw_w4_recommendation_frontend_20260724

Created: 2026-07-24 23:13:02
Objective: 在W3最终API合同冻结后实现医学写作推荐优先桌面端前端、竞品抽屉、量表逐页预览与原子组合采用
Task type: `visual_report_structure`
Risk: `high`
Selected agent route: `mixed` / `conference:visual-no-chair-grok45+kimi-code-k3` / `mixed:Codex-led visual panel; Grok Build then qwen then mimo replacement order`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `reviews/codex_subagent_w4_frontend_map_20260724.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/main.py`
- `packages/contracts/workbench_contracts/models.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- Existing medical-writing frontend QC scripts named in the W4 map.

## Scope

- In scope: a read-only execution-manager plan first; after Codex accepts W3,
  recommendation-first framing/PICOS package UI, one-request composite adoption,
  pending override UX, early competitor drawer, original-source-first evidence,
  real per-page assessment-instrument preview, desktop visual hierarchy, and
  focused browser/build regression.
- Out of scope: changing product-AI prompts/providers, TipTap remount, table
  editor rewrite, flowchart renderer, DOCX exporter, or a second frontend state
  machine.

## Success Criteria

- Minimum project facts trigger visible AI preparation without repeated inputs.
- One recommended package plus alternatives can be compared, edited and adopted
  in one W3 composite request; partial pending paths require explicit override.
- Competitor research/processing can open from the first design step without
  becoming a permanent writing-workbench panel.
- Evidence cards show source text first; locators/hashes/run IDs remain
  secondary provenance details.
- Every appendix page already present in working-copy `appendix_image` blocks is
  visually reviewable as an image thumbnail and enlarged page before export.
- No "待医学批准" state is introduced after the medical-manager user selects.
- Desktop layouts at 1920x1080, 1600x1000 and 1366x768 remain usable.

## Risk Boundaries

- This first manager pass is read-only. Do not edit production source or tests.
- W3 is still in progress; derive the implementation plan from current source
  but require the worker to reread the final W3 model/API before writing.
- Do not treat browser string assertions as visual acceptance.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-24 23:13:02: Task initialized by `tools/hermes_workflow_guard.py init-task`.
