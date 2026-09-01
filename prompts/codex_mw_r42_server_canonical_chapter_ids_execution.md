# Execution contract: server-canonical document-plan chapter IDs

## Objective

Implement the smallest safe remediation from
`runs/codex_mw_r42_duplicate_chapter_identity_diagnosis.md`: chapter IDs are
server-owned deterministic structural keys derived from validated chapter
order and segment range. Provider IDs must not cause an otherwise valid plan
to fail, while duplicate normalized titles and every range/source gate remain
strictly fail closed.

## Work items

1. In `expand_document_plan_segment_ranges`, validate all existing object,
   title, integer range, required-boundary, continuity, overlap, bounds,
   coverage, order, and source-span invariants, then generate deterministic
   canonical chapter IDs from validated order/start/end.
2. Preserve provider title, anchor/role, ranges, order, expanded source spans,
   source/input hashes, and all clinical text unchanged.
3. Bump the planner/normalizer prompt or contract version so new plan
   fingerprints cannot collide with the provider-ID contract.
4. Update the production output contract accordingly.
5. Keep duplicate normalized titles fail closed. If stable identity codes are
   split, retain the relevant codes in the same-model structural correction
   and Pro-eligibility allowlists.
6. Add focused and persisted regressions described in the diagnosis.

## Read these files only

Read these files only:
- `runs/codex_mw_r42_duplicate_chapter_identity_diagnosis.md`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_upper_layer_adapters.py`
- `services/api/app/writing_reference_upper_layer_execution.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_chapter_translation_pipeline.py`
- `tests/test_writing_reference_upper_layer_execution.py`
- `tests/test_writing_reference_upper_layer_production_wiring.py`
- `tests/test_writing_reference_upper_layer_contracts.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

Allowed writes are limited to the listed product/test files.

## Required invariants

- Canonical IDs are deterministic, bounded, unique, and idempotent for the same
  validated order/ranges.
- Duplicate or missing provider IDs with distinct titles and valid contiguous
  ranges are accepted without Flash correction or Pro.
- Normalized duplicate titles remain rejected.
- Gaps, overlap, out-of-bounds/reversed ranges, missing required boundaries,
  reordered chapters, missing/duplicated/unassigned spans, and malformed
  objects remain rejected with stable codes.
- No title, role, anchor, boundary, order, source span, source hash, or clinical
  content is fabricated, dropped, merged, rewritten, or reordered.
- No raw invalid provider output or prompt body is persisted for diagnostics.
- Existing retry generation, sibling, Pro eligibility, schema v8, OCR,
  Protocol-only, fidelity, and ownership gates remain unchanged.

## Hard boundaries

- Do not access or modify original/clone r42 runtime.
- Do not start services, call providers, run OCR/translation, or retry items.
- Do not edit outside the allowed list except the report below.

## Verification

Run focused new tests and the established six-module offline gate. Report exact
failures; do not weaken unrelated assertions.

## Output

Write exactly one output file:
`runs/codex_mw_r42_server_canonical_chapter_ids_execution.md`

Report behavior, versioning, exact tests/outcomes, boundaries, uncertainty, and
next action. End with `EXECUTION_COMPLETE`.
