You are the product and clinical-workflow participant in a Codex-chaired conference.

First read `/Users/smkzw/.hermes/SOUL.md` fully and state whether you did so.

## Hard boundaries
- Do not edit files, run browsers, call production AI, read secrets, or inspect unrelated project data.
- Work only inside the current workbench workspace except for the required SOUL read.
- Write exactly one output file: `runs/conference/mw_reference_translation_batch_phase2_20260716/participant_minimax.md`.

Read these files only:
- `AGENTS.md`
- `context/mw_reference_translation_batch_phase2_20260716_conference_context.md`
- `plans/codex_main_venue_mw_reference_translation_batch_phase2_20260716.md`
- `records/active_slices/medical_writing_reference_batch_preparation_20260716/TASK_RECORD.md`
- `services/api/app/writing_reference_preparation_batch.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference.py`
- `packages/contracts/workbench_contracts/models.py`
- `frontend/src/features/writing-reference/ReferencePreparationBatchPanel.jsx`
- `frontend/src/features/writing-reference/WritingReferencePanel.jsx`
- `tests/test_writing_reference_translation_service.py`
- `tests/test_writing_reference_preparation_batch.py`
- `tests/test_frontend_medical_writing_contract.py`

Independently assess the phase-2 batch regulatory-Chinese-candidate capability from a senior Chinese clinical medical writer's perspective. Focus on the shortest understandable user flow, medical authority boundaries, useful batch summary and exception handling, and whether the proposed backend states match actual reviewer work.

Return: boundary check; sources read; independent design; evidence versus inference; failure modes; concrete API/state/UX/test recommendations; uncertainty; next step. Cite file paths and symbols. Do not read other participant outputs.
