# MODE=CONFERENCE — r42 persisted planner retry acceptance review

You are an independent Codex acceptance reviewer. Review the completed bounded
implementation for the r42 persisted document-planner retry defect. Do not edit
product source, tests, configuration, runtime data, or task records.

## Read these files only

Read these files only:

- `context/mw_r42_persisted_planner_retry_context.md`
- `runs/codex_mw_r42_persisted_planner_retry_independent_review.md`
- `runs/codex_mw_r42_persisted_planner_retry_remediation.md`
- `runs/codex_mw_r42_persisted_planner_retry_execution.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/writing_reference_upper_layer_execution.py`
- `services/api/app/writing_reference_upper_layer_adapters.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_writing_reference_upper_layer_execution.py`
- `tests/test_writing_reference_upper_layer_production_wiring.py`
- `tests/test_writing_reference_upper_layer_contracts.py`
- `tests/test_chapter_translation_pipeline.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

The current filesystem is authoritative. The deleted original parent JSONL is
not recoverable and must not be described as recovered.

## Review questions

1. Is P1 closed on the real persisted path: one accepted batch retry allocates
   one durable retry generation and one canonical planner source per failed
   artifact, with ordinary replay/restart reusing the same new stage run?
2. Is P2 closed: document-planning Pro escalation requires a completed eligible
   second Flash correction, while immutable input/manifest defects and an
   ineligible final code never invoke Pro?
3. Are retry ancestry and Flash-to-Pro ancestry distinct and internally
   consistent, including Pro children of retry generations?
4. Does sibling reuse prevent duplicate planner/provider calls and fail closed
   when the canonical source has not recovered a plan?
5. Is compatibility preserved for old JSON payloads and repository schema v8?
6. Are gates, privacy, audit boundedness, and route ownership unchanged?
7. Did the execution stay within its file allowlist?

## Hard boundaries

- Read-only review except for the single report below.
- Run only focused offline tests or read-only inspection if needed.
- Do not start a service, call a live provider, touch the r42 runtime/SQLite,
  run OCR or translation, or retry the five failed items.
- Do not modify product source, tests, configuration, runtime data, task
  context, or prior reports.
- Do not read or write any file outside the explicit lists in this prompt.

## Output

Write exactly one output file:
`runs/codex_mw_r42_persisted_planner_retry_acceptance_review.md`

Use this structure:

- verdict: READY or NOT READY;
- findings ordered P0/P1/P2, with exact file/line evidence;
- explicit P1/P2 closure assessment;
- tests or inspections performed and exact outcomes;
- allowlist/privacy/runtime-boundary compliance;
- residual risks and the next safe action.

If there are no findings, say so explicitly. A READY verdict authorizes only
the parent Codex agent to prepare the isolated five-item replay; it does not
authorize this reviewer to run it.
