You are Grok Build/grok-4.5 recovering the durable visual and interaction
report from your already-run medical-writing workbench test. This is not a new
broad test. First fully read `/Users/smkzw/.codex/AGENTS.md` and
`/Users/smkzw/.hermes/SOUL.md`.

Hard boundaries:

- Do not edit product source, stable runtime or clinical source documents.
- Do not expose credentials, protected prompts or full clinical source text.
- Do not use a terminal or execute any command in this pass.
- Use read-only file tools for evidence and a file-edit/write tool only for
  the single required report.
- Write exactly one output file:
  `runs/execution/mw_final_release_full_function_20260718/grok_visual_final.md`.

Read:
- `context/mw_final_release_full_function_20260718_context.md`
- `logs/execution/mw_final_release_full_function_20260718/grok_visual_final_stdout.txt`
- `logs/execution/mw_final_release_full_function_20260718/grok_visual_final_resume_stdout.txt`
- `frontend/output/medical-writing-table-sync-final-20260718/medical_writing_table_sync_qc.json`
- `records/active_slices/medical_writing_authoring_journey_20260715/browser_qc/new_project_isolated/medical_writing_new_project_isolated_qc.json`
- `records/active_slices/medical_writing_authoring_journey_20260715/browser_qc/stable_readonly_audit/medical_writing_stable_readonly_audit.json`

The prior run used the wrong completion/report schema and its file was rolled
back. Recover only observed evidence; do not invent interactions or claim final
visual acceptance. The initial list is a starting context. Record any extra
file read if narrowly necessary.

Use these exact headings, all required:

# Execution Output:
## Boundary And Context Check
## Work Performed
## Artifacts And Evidence
## Commands And Observations
## Blockers Or Missing Environment
## Rerun Requests Or Next Step

Include desktop writer usability, project switch/new-project visibility,
editor/document-map/table-designer/AI-rail interactions, overflow/overlap,
error/blank-screen observations, exact evidence paths, and prior session ID
`b1bd56b4-f875-4baf-b2e5-903a2077a36a`. State that no command was run in this
recovery pass. Use PASS/FAIL/PARTIAL/UNVERIFIED. After writing the report,
return the same complete report as the final response without planning
narration.
