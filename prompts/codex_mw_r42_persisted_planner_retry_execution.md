# Execution contract: close r42 persisted planner retry findings

## Objective

Implement P1 and P2 exactly as bounded by:

- `runs/codex_mw_r42_persisted_planner_retry_independent_review.md`
- `runs/codex_mw_r42_persisted_planner_retry_remediation.md`

The result must provide a durable batch-retry generation and retry-parent
lineage, protect derived siblings from fabricated planner calls, and prevent
ineligible document-planning errors from invoking Pro.

## Work items

1. Add backward-compatible retry-generation/parent/source-item contracts,
   repository lookup/audit, and internal upper-layer request/result lineage.
2. Allocate one retry generation per failed artifact inside the existing batch
   retry transaction, run only the canonical source item, and let siblings
   reuse the recovered immutable plan.
3. Enforce document-planning Pro eligibility and terminal input/manifest
   classification; add the persisted-path and negative regressions described
   in the remediation proposal.

## Read and modify only these product/test files

Read these files only:
- `context/mw_r42_persisted_planner_retry_context.md`
- `runs/codex_mw_r42_persisted_planner_retry_independent_review.md`
- `runs/codex_mw_r42_persisted_planner_retry_remediation.md`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
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

Allowed product/test writes are limited to the same contract, service, and
test paths listed above. The task context is read-only for the worker.

## Hard boundaries

- Do not modify frontend, medical-monitoring files, shared runtime, r42
  runtime, configuration, roles, providers, credentials, or clinical source
  artifacts.
- Do not start a service or live provider.
- Do not run download, OCR, triage, translation, or the five r42 failed items.
- Do not weaken Protocol-only, effective-OCR, source-lineage, anchor,
  fidelity, ownership, lease, or cancellation gates.
- Keep schema version 8; additive payload fields only.
- Persist bounded lineage metadata only; no raw provider output, clinical
  text, prompt body, secret, or credential.
- Do not edit any file outside the allowed list except the report below.

## Verification

Run focused tests while implementing, then:

```text
python3 -m pytest -q \
  tests/test_writing_reference_upper_layer_execution.py \
  tests/test_writing_reference_upper_layer_production_wiring.py \
  tests/test_writing_reference_upper_layer_contracts.py \
  tests/test_chapter_translation_pipeline.py \
  tests/test_writing_reference_translation_batch.py \
  tests/test_document_pipeline_round8.py
```

Report exact failures and changes. Do not hide or weaken a failing assertion.

## Output

Write exactly one output file: `runs/codex_mw_r42_persisted_planner_retry_execution.md`

The report must contain sources read, files changed, behavior implemented,
tests and exact outcomes, failed paths, uncertainty, and next recommended
action. End with `EXECUTION_COMPLETE`.
