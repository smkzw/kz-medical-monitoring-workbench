# MODE=CONFERENCE — r42 duplicate chapter identity diagnosis

## Objective

Read-only diagnose the one isolated generation-2 artifact that failed Flash
attempt 1, same-model structural correction attempt 2, and Pro with
`planner_duplicate_chapter_identity`. Determine whether the defect is provider
output, normalization, validation, prompt contract, or source-segment identity,
and propose the smallest structure-only fix without fabricating clinical
content.

## Read these files only

Read these files only:
- `runs/mw_r42_planner_retry_controlled_replay_20260731.md`
- `services/api/app/writing_reference_upper_layer_execution.py`
- `services/api/app/writing_reference_upper_layer_adapters.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `runs/execution/mw_r42_planner_retry_20260731/runtime/writing_reference.sqlite3`
- `tests/test_writing_reference_upper_layer_execution.py`
- `tests/test_writing_reference_upper_layer_production_wiring.py`
- `tests/test_document_pipeline_round8.py`

Use bounded read-only SQL/Python inspection of only the failed artifact's
generation-2 stage runs and planner plan/input metadata. You may parse
structured persisted input/output locally, but the report must contain only
counts, hashes, stable codes, duplicate identity values, ranges, and structural
field names. Do not reproduce clinical text, prompt bodies, or provider prose.

## Questions

1. Which identity is duplicated, in which Flash/Pro attempts, and are ranges or
   chapter semantic roles otherwise distinct?
2. Did the corrective instruction address the exact duplicate, and did the
   second response structurally change?
3. Does validation require provider-generated `chapter_id` uniqueness even
   when deterministic range/role information could safely generate IDs?
4. Would deterministic canonical IDs be safe and idempotent without altering
   chapter boundaries, order, roles, titles, source hashes, or clinical text?
5. What exact code/test surface should change, and what cases must remain
   fail-closed?

## Hard boundaries

- Read-only diagnosis except the single report below.
- Do not modify source/tests/runtime, start services, call providers, or retry
  items.
- Do not expose raw clinical text, prompt text, provider output, secrets, or
  credentials.
- Do not propose silently dropping/merging/reordering chapters or changing
  source ranges to force validity.
- Do not read/write outside the explicit list.

## Output

Write exactly one output file:
`runs/codex_mw_r42_duplicate_chapter_identity_diagnosis.md`

Give root cause with exact structural evidence, safe/rejected remediation
options, required tests, uncertainty, and next action. End with
`DIAGNOSIS_COMPLETE`.
