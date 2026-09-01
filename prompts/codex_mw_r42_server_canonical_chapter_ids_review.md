# MODE=CONFERENCE — server-canonical chapter ID acceptance

## Objective

Independently review the server-canonical chapter-ID remediation before any
runtime retry.

## Read these files only

Read these files only:
- `runs/codex_mw_r42_duplicate_chapter_identity_diagnosis.md`
- `runs/codex_mw_r42_server_canonical_chapter_ids_execution.md`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_upper_layer_adapters.py`
- `services/api/app/writing_reference_upper_layer_execution.py`
- `tests/test_chapter_translation_pipeline.py`
- `tests/test_writing_reference_upper_layer_production_wiring.py`
- `tests/test_document_pipeline_round8.py`

## Review questions

1. Are server IDs deterministic, bounded, unique, idempotent, and derived only
   from validated structural order/ranges?
2. Are provider IDs truly advisory without weakening duplicate normalized
   title, boundary, range, coverage, source-span, order, or malformed-object
   gates?
3. Is contract versioning sufficient to prevent stale plan/run reuse?
4. Do production and persisted-restart tests prove no unnecessary correction,
   Pro call, or provider replay?
5. Is any clinical content, title, role, anchor, order, range, or source span
   fabricated or rewritten?

## Hard boundaries

- Read-only except the single report below.
- Do not access r42 runtime/clone, start services, invoke providers, run
  OCR/translation, or retry items.
- Do not modify source/tests/task records or read/write outside the list.

## Output

Write exactly one output file:
`runs/codex_mw_r42_server_canonical_chapter_ids_review.md`

Give READY or NOT READY, findings with evidence, exact tests, boundary
compliance, residual risk, and next action. End with
`ACCEPTANCE_REVIEW_COMPLETE`.
