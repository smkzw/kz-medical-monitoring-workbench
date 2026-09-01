You are continuing the same Hermes MiniMax-M3 execution session as worker_04. Fully comply with `/Users/smkzw/.hermes/SOUL.md` and the workspace `AGENTS.md`.

Hard boundaries:
- Work only inside the current workspace supplied by the runner.
- No production writes and no edits to source, selection, production-run, corpus, application, or test files.
- Do not call write/edit/patch tools in this continuation. Return the full clean report in your final assistant response; the runner will persist it.
- Write exactly one output file: `runs/execution/mw_phase1_translation_exec_20260716/worker_04.md`.

Read these files only:
- `AGENTS.md`
- `context/mw_phase1_translation_exec_20260716_execution_context.md`
- `records/active_slices/medical_writing_phase1_autoimmune_mnc_corpus_20260716/translations/translation_selection.json`
- `records/active_slices/medical_writing_phase1_autoimmune_mnc_corpus_20260716/translations/production_translation_runs.json`
- `runs/execution/mw_phase1_translation_exec_20260716/manager.md`

Execute manager section `Rerun 4 — worker_04` exactly. Start by explicitly rejecting the two superseded RNA ids/hashes and the old global false-positive claim. Re-emit the current nintedanib missed-dose segment and all five current RNA boundary segments as a self-contained clean report. For every segment include full literal and humanizer Chinese candidates, exact id/hash/locator, complete locked-token ledger, seven-axis audit, high-risk source-to-Chinese pairings, and named medical-approval items. Keep each RNA segment separate and mark it `待医学批准 / phase1_2_boundary_exception`. Do not use ellipses, omitted-line markers, diffs, tool logs, or summaries in place of any candidate or ledger.

Output schema:
1. `# Execution Output: mw_phase1_translation_exec_20260716 - worker_04 rerun`
2. `## Boundary And Context Check`
3. `## Work Performed`
4. `## Artifacts And Evidence`
5. `## Commands And Observations`
6. `## Blockers Or Missing Environment`
7. `## Rerun Requests Or Next Step`
