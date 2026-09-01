# Execution contract: restore interrupted planner-parent retry compatibility

## Objective

Close the sole P1 finding in
`runs/codex_mw_r42_legacy_source_inference_review.md`: a parentless Flash
document-planning run with status `interrupted` is a legitimate failed retry
parent and must not be rejected when modern explicit lineage identifies it.

## Work items

1. Add `interrupted` to the exact retry-parent status contract and repository
   lookup without changing any other owner/model/parent/generation checks.
2. Add a modern explicit-lineage regression: one failed item explicitly
   references a parentless Flash `interrupted` run and receives exactly one
   next retry generation.
3. Preserve fail-closed behavior for successful, Pro-child, mismatched-model,
   zero-candidate, and multiple-candidate parents.

## Read these files only

Read these files only:
- `runs/codex_mw_r42_legacy_source_inference_review.md`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

Allowed product/test writes:

- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

## Hard boundaries

- Do not access any r42 runtime or isolated clone.
- Do not start services, call providers, or run OCR/translation/items.
- Do not alter schema v8, route ownership, privacy/audit fields, or unrelated
  status behavior.
- Do not edit outside the allowed list except the report below.

## Verification

Run the new focused regression and the established six-module offline gate.

## Output

Write exactly one output file:
`runs/codex_mw_r42_interrupted_parent_fix.md`

Report exact changes, tests/outcomes, boundary compliance, and next action.
End with `EXECUTION_COMPLETE`.
