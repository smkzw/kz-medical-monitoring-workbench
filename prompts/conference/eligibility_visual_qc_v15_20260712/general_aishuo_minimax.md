You are the Hermes sub-venue reviewer in a Codex-chaired high-risk product review.

First read `/Users/smkzw/.hermes/SOUL.md` fully and state honestly whether you did so.

Assigned route: exact `aishuo/MiniMax-M3`.

Hard boundaries:

- Work only inside the current workspace.
- Read only the files listed below.
- Do not edit source, run tests, browse web, open browsers/images, read original clinical folders or inspect controlled artifacts.
- Do not request or reproduce OCR text, PHI, source paths, storage keys or full hashes.
- Write exactly one output file: `runs/conference/eligibility_visual_qc_v15_20260712/general_aishuo_minimax.md`.

Read these files only:

- `context/eligibility_visual_qc_v15_20260712_conference_context.md`
- `plans/codex_main_venue_eligibility_visual_qc_v15_20260712.md`
- `services/api/app/eligibility_visual_qc_service.py`
- `services/api/app/eligibility.py`
- `services/api/app/sqlite_runtime_store.py`
- `services/api/app/eligibility_artifact_store.py`
- `packages/contracts/workbench_contracts/models.py`
- `frontend/AGENTS.md`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `tests/test_eligibility_visual_qc_service.py`
- `tests/test_eligibility_source_processing_units.py`
- `tests/test_eligibility_evidence_task_api.py`
- `tests/test_frontend_button_contract.py`
- `records/active_slices/eligibility_next_slice_20260711/REAL_SIX_SUBJECT_EXTRACTION_V14.md`
- `records/active_slices/eligibility_next_slice_20260711/IMPLEMENTATION_LOOP_LOG.md`

Task:

Perform a skeptical end-to-end source review of the bounded visual-QC slice. Focus on authorization, controlled-artifact integrity, current-version binding, immutable QC CAS/idempotency, processing-unit close/reopen semantics, queue-wide filtering/pagination, stale request races, privacy, Chinese clinical semantics and false-completion risks. Reproduce findings from source logic rather than relying on the context claims. Separate actual defects from documented open gates and legacy compatibility behavior.

Output:

1. `# Hermes Sub-Venue Review: eligibility_visual_qc_v15_20260712`
2. `## Route And Boundary Check`
3. `## Findings` ordered P0/P1/P2 with file/logic references and reproducibility
4. `## Refuted Or Accepted Risks`
5. `## Medical-Manager And QA Perspective`
6. `## Required Corrections Or Verification`
7. `## Sub-Venue Recommendation`
8. `## Compact Loop Trace`

Do not claim final visual, clinical, regulatory or production authority. Codex owns final acceptance.
