You are Kimi Code continuing the same `worker_03` session after the external runner terminated the prior pass at its old hard-coded 1800-second limit. The model and four explore agents responded normally; do not describe the prior pass as unresponsive.

Read these files only:
- `AGENTS.md`
- `context/mw_soa_frontend_execution_20260717_execution_context.md`
- `runs/execution/mw_soa_frontend_execution_20260717/manager_completion.md`
- `runs/execution/mw_soa_frontend_execution_20260717/worker_03_round2.md`
- `runs/execution/mw_soa_frontend_execution_20260717/worker_01_implementation.md`
- `records/active_slices/medical_writing_soa_section_runtime_routing_20260717/TASK_RECORD.md`
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

The two original DOCX paths in the retained context remain authorized read-only inputs.

Hard boundaries:
- Preserve all boundaries from the prior implementation prompt: no product/backend/contracts/existing-test/package/stable-runtime/source-DOCX edits.
- Write only `frontend/tests/medical_writing_soa_section_isolated_qc.mjs`, evidence under `records/active_slices/medical_writing_soa_section_runtime_routing_20260717/browser_qc/`, and the runner report below.
- Never write through stable ports 8911/5174; stable DB/source hashes and health must be unchanged.
- Do not launch new explore agents and do not repeat the four completed extraction passes. Their complete reports are retained in this session.
- For imported projects, a fresh isolated API process with an empty isolated runtime is acceptable only when the observed GET document-session path invokes `MedicalWritingDocumentService._load()` and `parse_protocol_docx()` on the original source bytes in that cold process. Record source hash/document id/session evidence proving this. Do not copy pre-existing working-copy/session rows.
- Codex remains final acceptance authority.

Write exactly one output file: `runs/execution/mw_soa_frontend_execution_20260717/worker_03_implementation_resume.md`.

Resume action now:
1. Synthesize the retained extraction results in one short internal plan, then immediately implement `frontend/tests/medical_writing_soa_section_isolated_qc.mjs`.
2. Run `QC_ISOLATED_RUNTIME=1 node frontend/tests/medical_writing_soa_section_isolated_qc.mjs`.
3. Iterate only on deterministic QC-script defects within the authorized new file. Do not patch product code; report any product defect with exact reproduction.
4. Run the two focused pytest files and `npm run build`.
5. Return the complete report with these headings:
   - `# Execution Output: mw_soa_frontend_execution_20260717 - worker_03_implementation_resume`
   - `## Boundary And Context Check`
   - `## Work Performed`
   - `## Artifacts And Evidence`
   - `## Commands And Observations`
   - `## Blockers Or Missing Environment`
   - `## Rerun Requests Or Next Step`

Required evidence remains B1/B2/B3 zero/one/multiple branches; D001 and PNH cold source-derived sessions; cancel/close/Escape/overlay/explicit selection/create gate/duplicate/edit/save/reload/reopen; draft DOCX reopen with edited cell and note; 1920x1080 and 1440x900 exact-state screenshots; console/network/loading guards; stable hash and teardown proof. If one branch needs synthetic setup after both real projects are source-derived, label it synthetic.

Do not claim Codex acceptance.
