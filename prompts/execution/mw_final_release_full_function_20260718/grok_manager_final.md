You are the Grok Build/grok-4.5 execution manager for the final
medical-writing release evidence consolidation. First fully read
`/Users/smkzw/.codex/AGENTS.md` and `/Users/smkzw/.hermes/SOUL.md`.

This is a bounded consolidation pass.

Hard boundaries:

- Do not test the product again or use a terminal.
- Do not edit product source, stable runtime, clinical source documents,
  worker reports or test evidence.
- Use read-only file tools for evidence and a file-edit/write tool only for the
  required report.
- Write exactly one output file:
  `runs/execution/mw_final_release_full_function_20260718/grok_manager_final.md`.

Read these files only:
- `context/mw_final_release_full_function_20260718_context.md`
- `plans/codex_execution_mw_final_release_full_function_20260718.md`
- `runs/execution/mw_final_release_full_function_20260718/cms_full_final.md`
- `runs/execution/mw_final_release_full_function_20260718/grok_visual_final.md`
- `runs/execution/mw_final_release_full_function_20260718/reasonix_ai_final.md`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/multi_model_final_qc/codex_final_browser_report.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/word_engine_poc/reports/openxml_release_gate_production_v1.json`
- `records/active_slices/medical_writing_editor_references_20260715/legacy_reindex_real_projects_qc/report.json`
- `records/active_slices/medical_writing_prelaunch_acceptance_20260717/ai_final_qc/ai_apply_gate_results_v2.json`

Reconcile contradictions and false positives explicitly. In particular:

- Do not infer that empty managed `/literature` state means imported source
  references were not re-indexed. Export-time legacy re-index and the managed
  interactive library are separate surfaces.
- Do not classify a testing-agent cancellation, report-schema rejection or
  test-fixture cleanup failure as a product defect.
- Do not claim that every acceptance-contract function was freshly re-run when
  a role relied on current durable evidence.
- Distinguish release-blocking P0/P1 from P2/product-backlog gaps. A P0/P1 must
  have a reproduced user-visible failure on the current candidate.
- Enforce the no-paid-engine boundary: production is python-docx plus
  controlled OOXML, MIT Open XML SDK validation, LibreOffice render-only and
  Microsoft Word desktop final acceptance.

Use these exact headings:

# Execution Output:
## Boundary And Context Check
## Work Performed
## Artifacts And Evidence
## Commands And Observations
## Blockers Or Missing Environment
## Rerun Requests Or Next Step

Include a compact acceptance matrix for browser/editor, new project entry,
tables, AI, references, persistence, DOCX/OpenXML and commercial-engine policy.
List every remaining P0/P1, or state "none reproduced" with evidence. List P2
items separately with impact and disposition. State that no command was run in
this consolidation pass. Codex remains final release authority. After writing
the report, return the same complete report as the final response.
