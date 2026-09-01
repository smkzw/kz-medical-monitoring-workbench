You are Kimi Code continuing the same `worker_03` execution session. Read and comply with workspace `AGENTS.md`.

Read these files only:
- `AGENTS.md`
- `context/mw_soa_frontend_execution_20260717_execution_context.md`
- `runs/execution/mw_soa_frontend_execution_20260717/manager_completion.md`
- `runs/execution/mw_soa_frontend_execution_20260717/worker_03_round2.md`
- `runs/execution/mw_soa_frontend_execution_20260717/worker_01_implementation.md`
- `records/active_slices/medical_writing_soa_section_runtime_routing_20260717/TASK_RECORD.md`
- `records/active_slices/medical_writing_soa_builder_20260713/TASK_RECORD.md`
- `records/active_slices/medical_writing_soa_builder_20260713/real_protocol_table_rendering_validation.json`
- `frontend/package.json`
- `frontend/src/App.jsx`
- `frontend/src/features/medical-writing/StructuredTableDesigner.jsx`
- `frontend/tests/medical_writing_section_interaction_isolated_qc.mjs`
- `frontend/tests/medical_writing_authoring_journey_qc.mjs`
- `frontend/tests/medical_writing_imported_pnh_journey_qc.mjs`
- `frontend/tests/medical_writing_table_sync_qc.mjs`
- `services/api/app/main.py`
- `services/api/app/medical_writing_manifest.py`
- `services/api/app/medical_writing_document.py`
- `services/api/app/medical_writing_repository.py`
- `services/api/app/medical_writing_table_templates.py`
- `services/api/app/medical_writing_tables.py`
- `services/api/app/protocol_text_extractor.py`
- `services/api/app/medical_writing_document_exporter.py`
- `tests/test_medical_writing_real_project_flow.py`
- `tests/test_medical_writing_greenfield_runtime.py`
- `tests/test_medical_writing_document_export_api.py`

The two original DOCX paths named in the task context are authorized read-only source inputs. The QC may hash and parse them, but must not modify, copy back to, or write beside them.

Hard boundaries:
- Work only inside the current workspace `.` except temporary isolated runtime/browser directories created under the OS temp directory and read-only access to the two original DOCX inputs.
- Do not edit product code, backend code, contracts, existing tests, package files, stable runtime data, or source DOCX files.
- Write only the new QC script, its bounded evidence directory, and the runner report named below.
- Never write through stable ports 8911/5174. Discover the live 8911 SQLite files from its actual process/environment, hash them before and after, and fail if any stable database/WAL/SHM changes.
- A copied pre-existing document session is not acceptable as proof of from-zero source processing. For D001 and PNH, the isolated test must force the existing production parser/session-building path to read each original DOCX and create or rebuild the test document session from that source. If the current API/service surface cannot do this without modifying product code, stop and report the exact missing route/service contract; do not silently fall back to a pre-deconstructed session.
- Synthetic setup may be used only to guarantee zero/one/multiple candidate branch coverage after the two real-project source-derived flows are established, and must be labelled synthetic.
- Codex owns final browser, screenshot, DOCX, clinical and visual acceptance.

Write exactly one output file: `runs/execution/mw_soa_frontend_execution_20260717/worker_03_implementation.md`.

Implementation objective:
Create `frontend/tests/medical_writing_soa_section_isolated_qc.mjs` and execute it with `QC_ISOLATED_RUNTIME=1`. Implement the accepted worker_03 round-2 matrix, corrected to the actual current UI labels and API contracts.

Required QC behavior:
1. Start isolated API and Vite on free ports with an isolated runtime; prove child environment and stable-hash isolation.
2. Rebuild/import D001 and PNH from the original DOCX through existing production parser/session logic; verify pinned source hashes before and after.
3. Exercise B1/B2/B3 zero/one/multiple candidate paths with exact request logs and no default-first behavior.
4. Exercise all relevant entry, cancel, close, Escape, overlay, explicit selection, create-confirm, gate-disabled, duplicate, edit, save, reload, and designer reopen controls. Record skipped S-items only when an observed real state makes them inapplicable, with evidence; do not mark a test passed because UI is loading or missing.
5. Edit real SoA structure and notes using project-appropriate values, save, reload, and verify by API and DOM.
6. Export draft DOCX through the single production exporter, reopen with python-docx, and verify edited table cell/note, table/notes presence, and absence of raw Markdown/placeholders.
7. Capture 1920x1080 and 1440x900 screenshots after exact project/section/revision assertions and loading completion. Include focused entry, chooser/create, designer, and post-save states as applicable.
8. Fail on console errors, page errors, unexpected HTTP >=400, original source hash changes, stable DB hash changes, or stable service health loss.
9. Always teardown isolated processes and temporary runtime; preserve evidence under `records/active_slices/medical_writing_soa_section_runtime_routing_20260717/browser_qc/`.
10. Run focused pytest and `npm run build` after the E2E, without changing product files.

If the first implementation run exposes a deterministic product defect, do not patch product code in this pass. Capture the minimal reproduction, exact expected/actual state, request/response evidence, and smallest proposed repair for a same-session worker_01 fix.

Report schema:
1. `# Execution Output: mw_soa_frontend_execution_20260717 - worker_03_implementation`
2. `## Boundary And Context Check`
3. `## Work Performed`
4. `## Artifacts And Evidence`
5. `## Commands And Observations`
6. `## Blockers Or Missing Environment`
7. `## Rerun Requests Or Next Step`

Do not claim Codex acceptance.
