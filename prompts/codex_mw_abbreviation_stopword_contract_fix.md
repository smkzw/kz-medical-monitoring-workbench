# MODE=EXECUTION — protocol-heading abbreviation false-positive fix

## Objective

Implement the smallest general fix for the independently confirmed
`source_abbreviation_missing` false positive: ordinary all-caps protocol
heading words `VISIT` and `SCHEDULE` must not be classified as clinical
abbreviations. Preserve fail-closed behavior for real clinical abbreviations
and invalidate downstream persisted reuse under the changed detector/prompt
contract.

## Read these files only

Read these files only:
- `runs/codex_mw_r42_abbreviation_fidelity_diagnosis.md`
- `services/api/app/writing_reference.py`
- `services/api/app/chapter_translation_pipeline.py`
- `services/api/app/writing_reference_translation_batch.py`
- `tests/test_writing_reference.py`
- `tests/test_mw_v11_translation_alignment.py`
- `tests/test_chapter_translation_pipeline.py`
- `tests/test_writing_reference_translation_batch.py`
- `tests/test_document_pipeline_round8.py`

## Required implementation

1. Add only `VISIT` and `SCHEDULE` to the shared general
   `_ABBREVIATION_STOPWORDS`; do not add item-, artifact-, study-, Chinese
   target-, or indication-specific exceptions.
2. Bump `HY_MT2_PROMPT_VERSION` from v0.29 to a clear v0.30 identity reflecting
   protocol-heading abbreviation classification.
3. Bump `TRANSLATION_ALIGNMENT_CONTRACT` from v35 to a clear v36 identity.
   Confirm this changes `TRANSLATION_CONTRACT_FINGERPRINT`,
   `COMPOSITE_TRANSLATION_CONTRACT_HASH`, planner contract identity, chunk
   fingerprint, integration lookup identity, and translation candidate
   idempotency without mutating old rows.
4. Do not change `source_abbreviation_missing`, widen Chinese equivalences, or
   weaken number/unit/negation/comparator/scale/abbreviation fidelity gates.
5. Do not modify planner prompt v3 or server-canonical chapter-ID contracts;
   the change is a downstream translation-contract bump.

## Required regressions

- `VISIT` and `SCHEDULE` in all caps are not detected as clinical
  abbreviations.
- A mixed all-caps protocol label containing a true clinical abbreviation
  such as `ECG` still detects `ECG`.
- A Chinese full heading label with the identical section number passes
  without `source_abbreviation_missing`.
- Removing a real clinical abbreviation and all controlled equivalents still
  produces `source_abbreviation_missing`.
- The version/fingerprint bump prevents old plan/chunk/integration/candidate
  reuse while old immutable rows remain readable and unchanged.

Use synthetic non-clinical fixtures; do not access r42 runtime or provider
output.

## Verification

Run:

1. focused detector/evaluator/contract-identity regressions;
2. complete `tests/test_writing_reference.py` and
   `tests/test_mw_v11_translation_alignment.py`;
3. the six-module planner/translation gate used in r42 acceptance.

Report exact outcomes and warnings.

## Hard boundaries

- Do not access or modify original/clone r42 runtime.
- Do not start services or invoke providers, oMLX, OCR, translation, retry,
  review, or admission.
- Product writes are limited to:
  - `services/api/app/writing_reference.py`
  - `services/api/app/chapter_translation_pipeline.py`
- Test writes are limited to the listed test files.
- Do not modify task context, reviews, metrics, unrelated code, or schemas.

## Output

Write exactly one output file:
`runs/codex_mw_abbreviation_stopword_contract_fix.md`

Report the rule, version identities, files, regression evidence, any failed
paths, boundaries, residual risk, and next safe action. End with
`EXECUTION_COMPLETE`.
