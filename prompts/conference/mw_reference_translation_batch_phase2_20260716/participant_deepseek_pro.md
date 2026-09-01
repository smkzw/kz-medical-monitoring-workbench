You are the backend architecture and regulatory-translation-contract participant in a Codex-chaired conference.

First read `/Users/smkzw/.hermes/SOUL.md` fully and state whether you did so.

## Hard boundaries
- Do not edit files, run browsers, call production AI, read secrets, or inspect unrelated project data.
- Work only inside the current workbench workspace except for the required SOUL read.
- Write exactly one output file: `runs/conference/mw_reference_translation_batch_phase2_20260716/participant_deepseek_pro.md`.

Read these files only:
- `AGENTS.md`
- `context/mw_reference_translation_batch_phase2_20260716_conference_context.md`
- `plans/codex_main_venue_mw_reference_translation_batch_phase2_20260716.md`
- `records/active_slices/medical_writing_reference_batch_preparation_20260716/TASK_RECORD.md`
- `services/api/app/writing_reference_preparation_batch.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference.py`
- `services/api/app/main.py`
- `packages/contracts/workbench_contracts/models.py`
- `tests/test_writing_reference_translation_service.py`
- `tests/test_writing_reference_ai_contract.py`
- `tests/test_writing_reference_api.py`
- `tests/test_writing_reference_preparation_batch.py`

Independently design the smallest production-grade persistent batch around the existing single-span translation service. Focus on server-derived scope, source/extraction lineage, double gates, idempotency, concurrency, partial failure, restart recovery, stale-current handling, existing-approved translation reuse, and audit semantics. Do not invent a second translation engine.

Return: boundary check; sources read; proposed typed entities/API/state machine; invariants; failure table; tests; migration/compatibility risks; uncertainty; next step. Cite file paths and symbols. Do not read other participant outputs.
