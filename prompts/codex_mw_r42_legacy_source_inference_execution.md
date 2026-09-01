# Execution contract: infer canonical source for legacy r42 retry payloads

## Objective

Close the isolated-r42 preflight compatibility gap without touching any
runtime: old failed batch-item JSON can lack
`document_plan_failure_is_derived` and
`document_plan_failure_source_stage_run_id`. When one artifact has multiple
failed items, infer the canonical source only when exactly one item owns an
exact failed parentless Flash document-planning stage run. Preserve the
fail-closed behavior for zero or multiple candidates.

## Work items

1. Extend the existing retry-lineage allocator to inspect exact historical
   failed parentless Flash runs for each legacy group member when new lineage
   fields cannot identify one canonical source.
2. Add a persisted regression matching the observed r42 shape: two failed
   items for one artifact, both old payloads defaulting to non-derived/empty
   source fields, but only one item owns the failed Flash source run.
3. Prove one canonical generation/parent/source tuple is allocated and the
   sibling does not invoke the planner; retain missing/multiple-parent
   fail-closed tests.

## Read these files only

Read these files only:
- `context/mw_r42_persisted_planner_retry_context.md`
- `runs/codex_mw_r42_persisted_planner_retry_execution.md`
- `runs/codex_mw_r42_persisted_planner_retry_acceptance_review.md`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

Allowed product/test writes:

- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

## Observed bounded evidence

In the isolated clone only, batch
`wref_translation_batch_ad27f97d2f06c106b0c2a158` has two failed items for
artifact `wref_doc_037466e78db6f0a5cbcd`. Both old payloads parse with empty
source lineage and `document_plan_failure_is_derived == false`. Exactly one
item, `wref_translation_item_a9a602e1274b457aa0713048`, owns a failed
parentless Flash document-planning run; the sibling owns none. Do not read the
clone or reproduce these IDs in product logic.

## Hard boundaries

- Do not modify or read the original r42 runtime or the isolated replay clone.
- Do not start a service or call a live provider.
- Do not run download, OCR, triage, translation, or the five failed items.
- Do not weaken exact project/owner/artifact/extraction/stage/model/status and
  parentless lineage checks.
- Do not guess from item ordering. Infer only from exact persisted stage-run
  ownership, with exactly one candidate; otherwise use
  `document_plan_retry_parent_missing_or_ambiguous`.
- Keep schema version 8 and additive payload compatibility.
- Do not edit any file outside the allowed list except the report below.

## Verification

Run the focused new/adjacent tests, then the same six-module gate:

```text
python3 -m pytest -q \
  tests/test_writing_reference_upper_layer_execution.py \
  tests/test_writing_reference_upper_layer_production_wiring.py \
  tests/test_writing_reference_upper_layer_contracts.py \
  tests/test_chapter_translation_pipeline.py \
  tests/test_writing_reference_translation_batch.py \
  tests/test_document_pipeline_round8.py
```

## Output

Write exactly one output file:
`runs/codex_mw_r42_legacy_source_inference_execution.md`

Report files changed, inference rule, exact fail-closed behavior, tests and
outcomes, boundary compliance, and next action. End with
`EXECUTION_COMPLETE`.
