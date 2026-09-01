# Task Context: mw_flowchart_label_clip_20260724

Created: 2026-07-24 23:06:19
Objective: 修复医学写作研究流程图条件标签裁切，增加渲染级回归并重跑真实 Word 流程图门禁，不改其他导出逻辑
Task type: `visual_report_structure`
Risk: `high`
Selected agent route: `mixed` / `conference:visual-no-chair-grok45+kimi-code-k3` / `mixed:Codex-led visual panel; Grok Build then qwen then mimo replacement order`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- `services/api/app/medical_writing_study_schema.py`
- `tests/test_medical_writing_study_schema.py`
- `records/active_slices/medical_writing_real_scale_word_e5_20260724/scripts/run_real_ibdq_docx_gate.py`
- `records/active_slices/medical_writing_real_scale_word_e5_20260724/rendered_200dpi/page_03.png`
- `runs/execution/mw_real_ibdq_word_gate_20260724/kimi_manager_review_01.md`
- Direct source observation: the affected conditional edge label is centered at
  `x=1266`; the source node spans `x=1060..1228` and target node spans
  `x=1304..1472`. The label is wider than the 76 px inter-node corridor and is
  drawn before nodes, so the source node covers its left prefix.

## Scope

- In scope: generic edge-label layout in the production study-schema SVG/PNG
  renderer; deterministic tests proving labels never sit under node rectangles;
  regenerate the real MY009/IBDQ fixture and provide 200 DPI page evidence.
- Out of scope: project-specific string branches, changes to Word pagination or
  instrument appendices, frontend work, clinical-content changes, and broad
  exporter refactors.

## Success Criteria

- The full label `240 mg BID安全性不佳` is readable in the regenerated page 3.
- Edge labels remain legible for horizontal, vertical and conditional edges and
  do not overlap source/target node rectangles.
- Existing study-schema tests and focused DOCX/OOXML tests pass.
- No regression to the accepted 9-page IBDQ pagination or Word-native media
  preservation evidence.

## Risk Boundaries

- Authorized write set:
  `services/api/app/medical_writing_study_schema.py`,
  `tests/test_medical_writing_study_schema.py`, and task-scoped regenerated
  evidence under
  `records/active_slices/medical_writing_real_scale_word_e5_20260724/`.
- Do not write any other production source.
- Do not hard-code MY009, dose text, node IDs, project IDs, or a single fixture's
  coordinates in the production renderer.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-24 23:06:19: Task initialized by `tools/hermes_workflow_guard.py init-task`.
- 2026-07-24 23:10: Codex and Kimi independently accepted
  IBDQ_PAGINATION_GATE and WORD_NATIVE_ROUNDTRIP_GATE, and rejected
  FLOWCHART_VISUAL_GATE because the lower conditional label renders as
  `ng BID安全性不佳`.
- 2026-07-25 00:38: After two bounded renderer revisions, the regenerated
  task DOCX completed a native Microsoft Word update/save/close/reopen/PDF
  cycle without touching the user's open MG-K10 document. Post-Word OOXML
  retained SVG, PNG fallback, `svgBlip`, TOC and nine unique IBDQ pages.
- 2026-07-25 00:42: All 13 Word-native PDF pages were rendered at 200 DPI.
  Codex and an independent visual reviewer confirmed the full
  `240 mg BID安全性不佳` edge label and every flowchart node/arrow are
  readable without overlap or clipping; IBDQ 1/9 through 9/9 are consecutive
  and complete. The calibrated deterministic page-level visual gate passed.
  This bounded task is accepted; complete production protocol layout remains
  a separate release gate.
