# MODE=EXECUTION — abbreviation regression evidence correction

## Objective

Close the sole test-evidence gap in
`runs/codex_mw_abbreviation_stopword_contract_acceptance.md` without changing
product code, stopwords, clinical equivalences, or contract versions.

## Read these files only

Read these files only:
- `runs/codex_mw_abbreviation_stopword_contract_acceptance.md`
- `tests/test_mw_v11_translation_alignment.py`

## Required change

Modify only `tests/test_mw_v11_translation_alignment.py`:

1. Make the ECG omission negative fixture contain no competing detected
   all-caps token; assert `detect_clinical_abbreviations(source) == ("ECG",)`
   before evaluating fidelity.
2. Assert the evaluator does not pass and includes
   `source_abbreviation_missing`.
3. Strengthen the Chinese heading positive case to assert `result.passed`,
   empty failure codes, and identical source/target section-number tokens.
4. Keep the mixed-label positive detector assertion that `VISIT` and
   `SCHEDULE` are excluded while `ECG` is retained, but avoid ambiguous
   unasserted tokens.

## Verification

Run the focused tests, the complete two-module detector/alignment suite, and
the six-module planner/translation gate from the acceptance report.

## Hard boundaries

- Do not access r42 runtime or start/call any service/model.
- Do not modify product source, contracts, stopwords, equivalences, context,
  reviews, metrics, or any other test file.

## Output

Write exactly one output file:
`runs/codex_mw_abbreviation_test_evidence_fix.md`

Report the exact fixture change, assertions, tests/outcomes, boundaries, and
next action. End with `EXECUTION_COMPLETE`.
