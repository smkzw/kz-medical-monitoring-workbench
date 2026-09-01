You are Kimi Code continuing the same `worker_01` session as the bounded frontend implementation executor. Read and comply with workspace `AGENTS.md`.

Read these files only:
- `AGENTS.md`
- `context/mw_soa_frontend_execution_20260717_execution_context.md`
- `runs/execution/mw_soa_frontend_execution_20260717/manager_completion.md`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/StructuredTableDesigner.jsx`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/package.json`
- `tests/test_frontend_medical_writing_contract.py`
- `tests/test_frontend_structured_table_designer_contract.py`

Hard boundaries:
- Work only inside the current workspace `.`.
- Product write set is exactly `frontend/src/App.jsx`.
- Test write set is exactly `tests/test_frontend_medical_writing_contract.py`.
- Do not modify backend, contracts, StructuredTableDesigner, CSS, package files, stable runtime data, project data, or source DOCX files.
- Do not add dependencies or a second SoA/DOCX/version chain.

Write exactly one output file: `runs/execution/mw_soa_frontend_execution_20260717/worker_01_implementation.md`.

Implement the accepted contract in `manager_completion.md` sections 4-10:
1. Add the exact static failing contracts first and run the focused test command to capture RED.
2. Route `schedule_of_activities_editor` to a dedicated table target; keep analysis-set/sample-size PICOS routing unchanged.
3. Build `sectionSoaTableCandidates` from `workingCopyDisplayBlocks`: class 1 domain/template SoA plus class 2 source-native table blocks in the registered SoA section as pending-human-mapping candidates. Identity is stable `block_id`; document order only; no title regex identity.
4. C=1 direct open through the existing `setInsertedTableBlockId`/`focusTableBlockId` path. C>=2 opens `aria-label="选择要打开的研究流程表"` using native command buttons and no default-first action. C=0 opens `aria-label="创建研究流程表"`; only `创建并打开` rechecks all create gates and invokes existing `insertTableTemplate("schedule_of_activities")`.
5. Keep `selectedSectionConsistencyBlocked` local to the SoA create-confirm branch. Existing generic template insertion behavior must remain unchanged.
6. Pending source candidates show `待人工确认映射` and never auto-write `confirmed_by_user`.
7. Reuse existing dialog classes and duplicate flow. Add minimal self-contained focus handling for initial focus, Tab/Shift+Tab trap, Escape close, and focus return; do not use listbox semantics or add a dependency.
8. Clear chooser/confirm state on section switch. Preserve open-under-dirty/locked as read-only; creation is gated.
9. Run `python3 -m pytest tests/test_frontend_medical_writing_contract.py tests/test_frontend_structured_table_designer_contract.py -x -q` after implementation.
10. Review your own diff against manager checks; remove overbuilt or unrelated changes.

Return the full execution report in your final response, including RED evidence, changed lines/files, GREEN output, unresolved issues, and exact next cross-QC request. Do not use a file-writing tool for the report; the runner persists the final response. Do not claim Codex acceptance.
