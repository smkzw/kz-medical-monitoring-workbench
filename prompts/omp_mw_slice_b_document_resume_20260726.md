MODE=EXECUTION

Hard boundaries:

- Work only inside the current workbench and its configured local runtime.
- Use the real browser product and the product's independent AI.
- Do not replace product AI output with your own output.
- Do not touch accepted PNH triage/corpus code, DOCX export, deployment or
  unrelated UI.
- Production writes are limited to the explicit writable paths in the context.
- Runner-managed output path:
  `runs/omp_mw_slice_b_document_resume_20260726.md`. Never invoke a write/edit
  tool on this report path; return the compact report in your final response.

Read these files only:

- `context/mw_slice_b_document_resume_20260726_context.md`
- `records/handoffs/codex_retake_20260726/NEXT_LAUNCH_EXECUTION_PLAN_20260726.md`
- `records/handoffs/codex_retake_20260726/00_AUDIT_JOURNAL.md`
- `services/api/app/medical_writing_research_pipeline.py`
- `services/api/app/main.py`
- `services/api/app/writing_reference_preparation_batch.py`
- `services/api/app/writing_reference.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/AuthoringCompetitorDrawer.jsx`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`

You may additionally read directly imported tests and styles only after the
browser trace proves they are implicated; record those extra reads in
`DONE.json`.

Read the context first and follow it as the complete assignment contract.

Operate the real desktop product and its independently configured product AI.
You are a tester and bounded implementer, not the system-under-test AI. Do not
substitute your own clinical conclusions, source selection, translations or
writing for product output.

Begin from the live runtime and an isolated new project. Work through the real
page in the order a professional but deliberately low-effort medical writer
would use it. Observe actual states and evidence before editing source. If a
functional defect is reproduced, make the smallest allowed repair, add a
focused regression test, restart only the service that requires the changed
source, and rerun the affected path.

Do not perform a broad audit. Do not review or alter the accepted PNH triage,
the corpus policy, unrelated UI, deployment configuration or DOCX export.
Do not use a corpus override or placeholder document as success evidence.

Keep detailed evidence under
`runs/execution/mw_slice_b_document_resume_20260726/`. Include original
resolution screenshots, browser action trace, HTTP and durable-state snapshots,
artifact counts and hashes, project/pipeline/batch/item IDs, observed product
AI provider/model, changed-file hashes and focused test logs. Reuse this same
session only when a targeted follow-up is needed.

Finish by writing the required `DONE.json`, then return a compact handoff with:
STATUS, CHANGED_FILES, ARTIFACTS, CHECKS, BLOCKERS, RISKS,
EVIDENCE_LOCATORS, NEXT_ACTION, and the OMP session identifier.
