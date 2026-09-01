# MODE=CONFERENCE — legacy canonical-source inference review

## Objective

Independently determine whether the bounded legacy-source inference patch is
safe for the isolated r42 five-item replay.

## Read these files only

Read these files only:
- `prompts/codex_mw_r42_legacy_source_inference_execution.md`
- `runs/codex_mw_r42_legacy_source_inference_execution.md`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

## Review questions

1. Does legacy inference activate only when explicit source lineage is absent
   and all group members have the legacy non-derived default?
2. Does it require exactly one exact failed parentless Flash planning owner,
   without item-order guessing?
3. Do zero/multiple candidates and mismatched lineage fail before batch/item
   mutation with `document_plan_retry_parent_missing_or_ambiguous`?
4. Does the sibling still avoid planner/provider invocation before source
   recovery?
5. Are schema v8, route ownership, privacy, and the original modern-payload
   behavior preserved?

## Hard boundaries

- Read-only except for the single report below.
- Do not access the original r42 runtime or isolated replay clone.
- Do not start a service, call a provider, run OCR/translation, or retry items.
- Do not edit product source, tests, prior reports, or task context.
- Do not read or write files outside the explicit lists.

## Verification

Focused offline tests are permitted. Report exact selectors and outcomes.

## Output

Write exactly one output file:
`runs/codex_mw_r42_legacy_source_inference_review.md`

Give READY or NOT READY, findings with file/line evidence, boundary compliance,
residual risk, and next safe action. End with `ACCEPTANCE_REVIEW_COMPLETE`.
