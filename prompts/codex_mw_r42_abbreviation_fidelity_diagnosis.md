# MODE=CONFERENCE — r42 abbreviation fidelity-block diagnosis

## Objective

Read-only diagnose the sole attempt-3 fidelity block
`unit_1:source_abbreviation_missing` for
`wref_translation_item_4dae08490b884310d35a6198`. Determine whether it is:

- a true Hy-MT2 omission that should remain blocked;
- an accepted Chinese/full-term or singular/plural equivalent missing from the
  deterministic equivalence contract;
- a false-positive source abbreviation detection;
- a source/chunk/unit alignment or normalization defect; or
- another precisely evidenced cause.

Do not retry, admit, edit, or regenerate the item.

## Read these files only

Read these files only:
- `runs/mw_r42_attempt3_controlled_recovery_20260731.md`
- `services/api/app/writing_reference.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_translation_batch.py`
- `services/api/app/writing_reference_repository.py`
- `tests/test_writing_reference.py`
- `tests/test_mw_v11_translation_alignment.py`
- `runs/execution/mw_r42_planner_retry_20260731/runtime/writing_reference.sqlite3`

## Required analysis

1. Resolve the blocked item's exact artifact, v3 plan, chapter, chunk,
   translation revision, integration, source spans, and fidelity record using
   read-only SQLite.
2. Inspect only the minimum authorized source and translated unit required to
   identify the detected source abbreviation and its observed target form.
   Do not reproduce clinical prose in the report.
3. Re-run the deterministic abbreviation detector/fidelity evaluator in
   memory on that exact unit and report only bounded hashes, token(s), stable
   codes, and boolean/equivalence results.
4. Trace the exact code branch and existing tests. Determine whether the
   current block is semantically correct or a product false positive.
5. If a code change is justified, propose the smallest general rule and
   regression cases. It must not be r42-item-specific, must not silently admit
   arbitrary missing abbreviations, and must preserve clinical fidelity.
6. Distinguish observed evidence from inference. If source authority is
   insufficient, leave the item blocked.

## Hard boundaries

- Clone and original runtime are read-only. No service startup.
- Do not invoke any provider, oMLX, OCR, translation, retry, medical review,
  corpus admission, or state mutation.
- Do not modify product source/tests/context/reviews/metrics.
- Do not expose full source text, translated text, prompts, provider output,
  credentials, or secrets. Use bounded tokens, locators, counts, and hashes.
- Do not inspect any other clinical item unless required to disprove a shared
  code path; prefer existing tests instead.

## Output

Write exactly one output file:
`runs/codex_mw_r42_abbreviation_fidelity_diagnosis.md`

Give a verdict, exact evidence locators/code lines, bounded observed token
mapping, whether the block should remain, the smallest safe remediation if
needed, tests to add, residual uncertainty, and next action. End with
`CONFERENCE_COMPLETE`.
