# MODE=CONFERENCE — abbreviation test-evidence rereview

## Objective

Determine whether the sole test-confounding gap from
`runs/codex_mw_abbreviation_stopword_contract_acceptance.md` is closed.

## Read these files only

Read these files only:
- `runs/codex_mw_abbreviation_stopword_contract_acceptance.md`
- `runs/codex_mw_abbreviation_test_evidence_fix.md`
- `tests/test_mw_v11_translation_alignment.py`

## Review questions

1. Is `ECG` the exact and only detected token in the omission negative case?
2. Does that case explicitly fail and retain `source_abbreviation_missing`?
3. Does the positive Chinese heading case assert complete pass, empty failures,
   and identical section-number tokens?
4. Were only test fixtures/assertions changed?

Run the focused three tests, the complete two-module suite, and the six-module
gate reported by the remediation.

## Hard boundaries

- Read-only except the report.
- No r42 runtime, service, provider, oMLX, OCR, translation, or retry access.
- Do not modify product source, contracts, tests, context, reviews, or metrics.

## Output

Write exactly one output file:
`runs/codex_mw_abbreviation_test_evidence_rereview.md`

Give READY or NOT READY, evidence, exact tests, boundaries, residual risk, and
the next resume action. End with `ACCEPTANCE_REVIEW_COMPLETE`.
