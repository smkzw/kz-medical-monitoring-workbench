You are the first-line visual/DOCX execution worker running inside a
Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your output,
include one sentence saying whether you read the full file. Do not claim this unless
you actually read it.

## Hard boundaries

- Work only inside the runner-provided current workspace (`.`).
- Read the production implementation and tests listed below, but do not modify
  production source in this pass.
- You may create scripts and evidence only under
  `records/active_slices/medical_writing_real_scale_word_e5_20260724/`.
- Use Microsoft Word for Mac for the native round-trip. Do not substitute
  LibreOffice, Pages, or a PDF renderer for the Word-native gate.
- Do not use `/tmp` or `/private/tmp` as a Word target. Use the evidence directory.
- Before Word automation, inventory currently open Word documents. Open, update,
  save, export, close, and reopen only the task-owned DOCX. Never close or mutate an
  unrelated user document.
- Tools are available and must not be disabled. Use read/search/terminal/browser/
  visual/desktop tools as required and record the observations.
- Codex remains final visual, DOCX, and production acceptance authority.
- Runner-managed output path:
  `runs/hermes_mw_real_ibdq_word_gate_20260724.md`. Never invoke a write/edit tool on
  this report path; return the complete report in your final response and let the
  runner persist it.

## Read these files only

- `context/mw_real_ibdq_word_gate_20260724_context.md`
- `reviews/codex_subagent_flowchart_image_docx_map_20260724.md`
- `records/active_slices/mw_study_schema_scale_docx_20260720/run_real_docx_acceptance.py`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `services/api/app/medical_writing_document_exporter.py`
- `services/api/app/medical_writing_instrument_appendix.py`
- `services/api/app/medical_writing_figure_exporter.py`
- `tests/test_medical_writing_instrument_appendix.py`
- `tests/test_medical_writing_docx_pagination.py`
- `tests/test_medical_writing_document_exporter.py`

## Task

Execute the complete real-nine-page IBDQ Microsoft Word native publication gate.

1. Create a fresh task evidence directory. Record source file SHA256 values, current
   exporter file SHA256 values, environment, Word version, and the list of open Word
   documents.
2. Adapt or wrap the prior acceptance generator inside the evidence directory so it
   invokes the current production exporter with the real `MY009_IBDQ_scale.pdf`.
   Include a governed study flowchart so the same DOCX proves SVG plus PNG fallback
   survival. Do not copy or alter production modules.
3. Generate a fresh DOCX. Run deterministic tests and OOXML/package checks before
   opening Word.
4. In Microsoft Word for Mac, open only the new DOCX, update all fields, save, close,
   reopen, export to PDF using Word, then close the task document. Preserve unrelated
   user documents.
5. Render the Word-native PDF at 200 DPI or higher. Inspect every page at original
   resolution. Programmatically identify the nine IBDQ pages and verify:
   - exactly nine source pages, in order, with no duplication or omission;
   - title and image on the same page;
   - no isolated heading, image-only overflow, blank separator, clipping, or
     overlapping header/footer;
   - questions, checkboxes, copyright/source text, and page labels are legible.
6. Verify the flowchart is visible and the DOCX package still contains the SVG part,
   SVG relationship, and PNG fallback.
7. Persist the newly generated DOCX, Word round-tripped DOCX, Word-native PDF,
   200-DPI pages, OOXML/media/field checks, page-level QC JSON, screenshots, and a
   concise task record under the allowed evidence directory.
8. If any criterion fails, do not edit production source. Preserve the exact failure,
   localize the cause to code/OOXML/Word behavior, and propose the smallest
   production write set and regression tests for a later authorized remediation.

## Output schema

1. `# Real IBDQ Word Gate Execution: mw_real_ibdq_word_gate_20260724`
2. `## Boundary Check`
3. `## Sources And Environment`
4. `## Rounds Performed`
5. `## Deterministic And OOXML Results`
6. `## Microsoft Word Native Results`
7. `## Page-Level Visual Results`
8. `## Failed Paths And Root Cause`
9. `## Evidence Manifest`
10. `## Codex-Owned Verification`
11. `## Recommended Next Step`

## Quality gates

- Do not claim final visual or production acceptance; Codex owns it.
- Do not report "pass" without machine-readable and page-image evidence.
- Do not treat the older July 20 Word artifact or synthetic r7 sample as current real
  IBDQ acceptance.
- Complete marker:
  `GROK_REAL_IBDQ_WORD_E5_GATE_01_COMPLETE`
