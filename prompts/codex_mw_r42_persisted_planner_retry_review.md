# Read-only review contract: r42 persisted planner structural retry

## Objective

Independently review the current medical-writing persisted document-planning
implementation. Determine whether it safely performs exactly one same-model
structural-correction call before Pro escalation, preserves immutable lineage,
and emits stable planner validation codes without weakening existing gates.

## Source files

Read these files only:

- `context/mw_r42_persisted_planner_retry_context.md`
- `services/api/app/writing_reference_upper_layer_execution.py`
- `services/api/app/writing_reference_upper_layer_adapters.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/writing_reference_repository.py`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `tests/test_writing_reference_upper_layer_execution.py`
- `tests/test_writing_reference_upper_layer_production_wiring.py`
- `tests/test_writing_reference_upper_layer_contracts.py`
- `tests/test_chapter_translation_pipeline.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

## Checks

1. Production persisted path makes two Flash calls at most for deterministic
   planner-structure failure and does not accidentally combine with the legacy
   outer retry.
2. Both Flash calls retain the same stage-run ID, source/input hash, prompt
   version, artifact/extraction owner, and bounded audit lineage.
3. Pro is invoked only after the corrective Flash call remains eligible for
   structural escalation; transport failures do not silently upgrade.
4. Specific codes for missing chapters/role, gap, overlap, out-of-bounds,
   missing required boundary, duplicate identity, and unstructured output
   survive adapter, persisted executor, batch failure, and derived-sibling
   propagation.
5. Old stage-run payloads remain readable, and no database migration is
   required merely for additive payload metadata.
6. Protocol-only, effective-OCR, fidelity, source-lineage, and anchor-readiness
   gates are not bypassed.
7. No raw provider response, sensitive clinical text, credential, or hidden
   prompt is newly persisted in the bounded attempt metadata.

## Hard boundaries

- Product code and runtime are read-only.
- Do not start services or run live providers.
- Do not mutate SQLite databases.
- Do not rerun download, OCR, triage, translation, or the five r42 failed items.
- Report only actionable findings with file and line locators. If there are no
  findings, state the checked scope and residual risks.
- The only allowed write is the runner-owned report file below.

## Output file

Write exactly one output file: `runs/codex_mw_r42_persisted_planner_retry_independent_review.md`

## Required handoff

Return:

- sources read;
- findings ordered by severity;
- evidence locators;
- checks with no issue found;
- residual risk;
- recommended next action.

End with `REVIEW_COMPLETE`.
