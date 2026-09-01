# MODE=CONFERENCE — protocol-heading abbreviation fix acceptance

## Objective

Independently accept or reject the general `VISIT`/`SCHEDULE` abbreviation
false-positive fix and downstream translation-contract bump before the task is
paused. This review does not authorize any runtime retry.

## Read these files only

Read these files only:
- `runs/codex_mw_r42_abbreviation_fidelity_diagnosis.md`
- `runs/codex_mw_abbreviation_stopword_contract_fix.md`
- `services/api/app/writing_reference.py`
- `services/api/app/chapter_translation_pipeline.py`
- `tests/test_writing_reference.py`
- `tests/test_mw_v11_translation_alignment.py`
- `tests/test_chapter_translation_pipeline.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

## Review questions

1. Is the rule limited to the two ordinary protocol-heading words and free of
   item/study/indication/Chinese-target exceptions?
2. Do true clinical abbreviations, including mixed labels with `ECG`, remain
   detected and fail closed when omitted without a controlled equivalent?
3. Does the Chinese heading case pass for the right reason while preserving
   section number and all other fidelity gates?
4. Are Hy prompt and alignment versions truthfully bumped, and do their new
   identities propagate through downstream fingerprint, planner identity,
   chunks, integrations, composite candidate identity, and immutable old-row
   non-reuse?
5. Were planner v3, server-canonical chapter IDs, schemas, and unrelated
   clinical equivalences unchanged?
6. Do tests cover positive, negative, identity, and immutable compatibility
   paths without relying on r42 clinical text?

## Required verification

Run the complete two-module detector/alignment suite and the six-module
planner/translation gate. Report exact outcomes.

## Hard boundaries

- Read-only except the single report below.
- Do not access original/clone r42 runtime.
- Do not start services or invoke providers, oMLX, OCR, translation, retry,
  review, or admission.
- Do not modify product source, tests, context, reviews, or metrics.

## Output

Write exactly one output file:
`runs/codex_mw_abbreviation_stopword_contract_acceptance.md`

Give READY or NOT READY, prioritized findings with exact evidence, tests,
boundary compliance, residual risk, and the next safe resume action. End with
`ACCEPTANCE_REVIEW_COMPLETE`.
