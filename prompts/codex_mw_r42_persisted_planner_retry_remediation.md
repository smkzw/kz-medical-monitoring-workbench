# Bounded remediation proposal: persisted planner retry generation and Pro gate

## Objective

Produce an implementation-ready patch proposal for the two findings in
`runs/codex_mw_r42_persisted_planner_retry_independent_review.md`:

1. a failed persisted document plan must receive one genuinely fresh,
   server-owned retry generation while ordinary replay stays idempotent;
2. document-planning Pro escalation must require a completed same-model
   structural-correction attempt and an eligible final structural code.

Do not edit product source. Codex will review and integrate the proposal.

## Work items

1. Design the smallest backward-compatible retry-generation lineage that
   reaches the upper-layer fingerprint/idempotency material from a translation
   batch retry. It must create one new immutable source stage-run, parent it to
   the failed source run, and let same-artifact siblings reuse the recovered
   plan without fabricated provider calls.
2. Define and place a document-planning Pro-eligibility predicate. Immutable
   input/manifest defects must be terminal or otherwise ineligible; Pro must
   not run unless the Flash stage shows planner attempt 2 and an eligible final
   structural failure code.
3. Specify exact tests for persisted batch retry, ordinary replay, derived
   sibling recovery, ineligible input/manifest failures, and an eligible first
   failure followed by an ineligible second failure.

## Source files

Read these files only:
- `context/mw_r42_persisted_planner_retry_context.md`
- `runs/codex_mw_r42_persisted_planner_retry_independent_review.md`
- `services/api/app/writing_reference_upper_layer_execution.py`
- `services/api/app/writing_reference_upper_layer_adapters.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/writing_reference_repository.py`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `tests/test_writing_reference_upper_layer_execution.py`
- `tests/test_writing_reference_upper_layer_production_wiring.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

## Hard boundaries

- Do not edit product source, tests, databases, configuration, or runtime.
- Do not start services or providers.
- Do not run OCR, download, triage, translation, or the five r42 failed items.
- Do not weaken Protocol-only, effective-OCR, source-lineage, anchor, or
  fidelity gates.
- Do not store raw provider output, clinical text, secrets, or credentials.
- The only allowed write is the runner-owned proposal below.

## Output

Write exactly one output file: `runs/codex_mw_r42_persisted_planner_retry_remediation.md`

The proposal must contain:

- root-cause confirmation or correction;
- precise data/lineage contract;
- file-by-file patch hunks or pseudodiff detailed enough to implement;
- exact tests and expected observations;
- compatibility and migration analysis;
- rejected alternatives;
- residual risks.

End with `REMEDIATION_PROPOSAL_COMPLETE`.
