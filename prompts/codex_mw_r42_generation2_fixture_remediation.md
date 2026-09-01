# MODE=EXECUTION — exact generation-2 supersession fixture remediation

## Objective

Close the single evidence gap in
`runs/codex_mw_r42_contract_supersession_acceptance_review.md` without
changing product code: make the mixed persisted regression reproduce a real
v2 generation-1 root followed by a failed v2 generation-2 ordinary retry,
then a generation-3 v3 contract supersession.

## Read these files only

Read these files only:
- `runs/codex_mw_r42_contract_supersession_acceptance_review.md`
- `tests/test_document_pipeline_round8.py`
- `tests/test_writing_reference_upper_layer_execution.py`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/writing_reference_upper_layer_execution.py`

## Required change

- Change only test fixtures/assertions.
- In the mixed persisted regression, seed an immutable failed generation-1 v2
  Flash root for the canonical source item.
- Seed the existing failed generation-2 v2 Flash source as a valid ordinary
  retry of that generation-1 root, with its ordinary retry parent ID,
  source execution fingerprint, prompt version/text, model, input hash,
  deployment profile, owner/batch/item/artifact/extraction identity, and
  statuses satisfying the real persisted contract.
- Keep the v3 target as generation-3 contract supersession with ordinary retry
  fields empty and the distinct supersession edge pointing to generation 2.
- Add explicit assertions that the source is generation 2, has the exact
  generation-1 ordinary retry parent, and that the fresh v3 target has no
  ordinary retry parent.
- Preserve the existing two-item derived sibling, three migrated accepted v2
  plans, zero planner calls for migration, duplicate retry/worker behavior,
  restart reconstruction, no stale downstream reuse, and invalid-transition
  no-mutation assertions.
- If the corrected fixture exposes a product failure, stop and report the
  exact failure; do not modify product code in this task.

## Verification

Run the focused transition command from the acceptance report and the same
six-module planner/translation gate. Report exact outcomes.

## Hard boundaries

- Do not access or modify original/clone r42 runtime.
- Do not start services, invoke providers, acquire oMLX leases, run
  OCR/translation, or retry items.
- Do not modify product source, contracts, task context, reviews, or metrics.
- The only test write allowed is `tests/test_document_pipeline_round8.py`.

## Output

Write exactly one output file:
`runs/codex_mw_r42_generation2_fixture_remediation.md`

Describe the exact lineage constructed, assertions, tests/outcomes, any
exposed product failure, boundary compliance, and next action. End with
`EXECUTION_COMPLETE`.
