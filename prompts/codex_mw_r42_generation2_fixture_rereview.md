# MODE=CONFERENCE — exact generation-2 supersession evidence rereview

## Objective

Independently determine whether the sole P1 evidence gap from the prior
v2-to-v3 planner contract supersession acceptance review is closed.

## Read these files only

Read these files only:
- `runs/codex_mw_r42_contract_supersession_acceptance_review.md`
- `runs/codex_mw_r42_generation2_fixture_remediation.md`
- `tests/test_document_pipeline_round8.py`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/writing_reference_upper_layer_execution.py`
- `services/api/app/writing_reference_translation_batch.py`

## Review questions

1. Does the mixed persisted regression now create a real immutable v2 initial
   Flash root followed by a valid failed v2 generation-2 ordinary retry whose
   parent is that root?
2. Does the generation-3 v3 target clear ordinary retry lineage and retain a
   distinct supersession edge to the exact generation-2 source and execution
   fingerprint?
3. Are source generation/parent and target generation/empty ordinary parent
   explicitly asserted after persistence and restart?
4. Are the existing derived-sibling, three accepted-plan migrations, zero
   migration planner calls, no stale downstream reuse, duplicate retry/worker,
   restart, and invalid no-mutation assertions preserved?
5. Did the remediation avoid product-code changes and expose any product
   failure?

## Required verification

Run the focused seven transition tests and the six-module planner/translation
gate from the prior acceptance report. Report exact outcomes.

## Hard boundaries

- Read-only except the single report below.
- Do not access r42 original/clone runtime, start services, invoke providers,
  acquire oMLX leases, run OCR/translation, or retry items.
- Do not modify product source, tests, context, reviews, or metrics.

## Output

Write exactly one output file:
`runs/codex_mw_r42_generation2_fixture_rereview.md`

Give READY or NOT READY, prioritized findings with exact evidence, test
outcomes, boundary compliance, residual risk, and next safe action. End with
`ACCEPTANCE_REVIEW_COMPLETE`.
