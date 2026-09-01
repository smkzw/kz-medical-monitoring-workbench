# Task Context: mw_real_ibdq_word_gate_20260724

Created: 2026-07-24 22:22:19
Objective: Use the current medical-writing DOCX exporter and the real nine-page MY009 IBDQ PDF to complete a Microsoft Word native publication gate: regenerate, update fields, save, close/reopen, export PDF, render at 200 DPI, and prove every attachment title and image share one page with no extra blanks.
Task type: `visual_report_structure`
Risk: `high`
Selected agent route: `mixed` / `conference:visual-no-chair-grok45+kimi-code-k3` / `mixed:Codex-led visual panel; Grok Build then qwen then mimo replacement order`

## Trigger Reason

This task was initialized through the Codex x Hermes complex-task entrypoint because it is expected to involve more than three execution steps, research/writing/report/code/report-visual work, or source-grounded verification.

## Source Of Truth

- Current exporter and attachment implementation:
  - `services/api/app/medical_writing_document_exporter.py`
  - `services/api/app/medical_writing_instrument_appendix.py`
  - `services/api/app/medical_writing_figure_exporter.py`
- Current regression coverage:
  - `tests/test_medical_writing_instrument_appendix.py`
  - `tests/test_medical_writing_docx_pagination.py`
  - `tests/test_medical_writing_document_exporter.py`
- Current audit:
  - `reviews/codex_subagent_flowchart_image_docx_map_20260724.md`
- Current r7 synthetic evidence:
  - `records/active_slices/medical_writing_production_rebaseline_20260722/docx_layout_qc/`
  - `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- Real nine-page IBDQ input:
  - `records/active_slices/mw_study_schema_scale_docx_20260720/reference_inputs/MY009_IBDQ_scale.pdf`
- Existing real acceptance generator and older evidence, which may be reused only as
  inputs and implementation reference:
  - `records/active_slices/mw_study_schema_scale_docx_20260720/run_real_docx_acceptance.py`
  - `records/active_slices/mw_study_schema_scale_docx_20260720/acceptance_outputs/`
- The older Word output is not acceptance evidence for current r7. Its page 22 title
  and page 23 image are split.

## Scope

- In scope:
  - Generate a new DOCX from current source using the real nine-page IBDQ PDF.
  - Preserve the current study flowchart SVG plus PNG fallback path in the fixture.
  - Open only the task-owned DOCX in Microsoft Word for Mac.
  - Update all fields, save, close/reopen, export a Word-native PDF, then close the
    task-owned file.
  - Render the Word-native PDF at 200 DPI or higher and perform page-level visual and
    programmatic checks.
  - Write all new evidence under
    `records/active_slices/medical_writing_real_scale_word_e5_20260724/`.
  - Return a compact loop trace and exact acceptance result.
- Out of scope:
  - No production source edits in this first pass.
  - Do not alter or close any user-owned Word document.
  - Do not use LibreOffice output as a substitute for the Word-native PDF.
  - Do not reuse the older July 20 DOCX/PDF as current-code proof.
  - Do not claim the whole medical-writing subsystem is released.

## Success Criteria

1. A newly generated DOCX is traceable to the current exporter source and the real
   IBDQ PDF SHA256.
2. Microsoft Word updates fields, saves, closes, reopens, and exports the task DOCX
   without a blocking repair dialog.
3. All nine IBDQ source pages appear exactly once on nine consecutive Word pages.
4. Each attachment page title and its page image are on the same Word page.
5. No isolated title page, image-only overflow page, separator blank page, clipped
   content, missing page, or duplicated page is present.
6. IBDQ questions, checkboxes, source/copyright text, page labels, headers, and
   footers remain legible at 200 DPI.
7. The flowchart remains visible and the DOCX still contains an SVG relationship plus
   PNG fallback.
8. OOXML validation, media counts, field/bookmark checks, page-level visual QC, and
   the final result are persisted in machine-readable evidence.

## Risk Boundaries

- The only writable path for this first pass is
  `records/active_slices/medical_writing_real_scale_word_e5_20260724/`.
- Do not edit production source. If current code fails, stop after producing a precise
  reproducer, page evidence, root-cause analysis, and a minimal proposed write set.
- Do not overwrite any existing acceptance artifact.
- Do not use `/tmp` or `/private/tmp` as a Word sandbox target; write directly to the
  task evidence directory.
- Do not close, save, or modify unrelated Word documents. Record all Word documents
  open before and after the task.
- The delegated agent is not final authority; Codex owns verification and acceptance.

## Timeout Policy

- Do not mark the delegated agent failed for slow response alone.
- For complex or artifact-heavy work, wait and poll generously; use conference mode when multiple independent model perspectives are needed.
- Failure requires terminal error, provider exhaustion/rate limit after controlled retry, empty/truncated retry output, or no progress after hard wait plus one retry.

## Loop Log

- 2026-07-24 22:22:19: Task initialized by `tools/hermes_workflow_guard.py init-task`.
