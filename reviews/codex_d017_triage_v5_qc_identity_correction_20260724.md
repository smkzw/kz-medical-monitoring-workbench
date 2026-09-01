# Codex Correction: D017 Triage v5 QC Identity

Date: 2026-07-24 CST

## Finding

The first accepted QC-tool revision had a self-referential identity defect:
`REPORT_VERSION` and filenames said v5, while
`EXPECTED_PROMPT_VERSION` still required
`competitor_triage_deepseek_v4_source_truth`. Test fixtures imported the same
constant, so the green suite did not independently prove v5 identity.

## Correction

- The gate now requires
  `competitor_triage_deepseek_v5_source_truth`.
- A dedicated negative test hard-codes v4 at both run and chunk provenance
  levels and requires rejection with both run and chunk mismatch issue codes.

## Verification

```text
101 passed in 0.36s
python3 -m py_compile scripts/qc/d017_competitor_triage_v5_acceptance.py
```

The forthcoming real D017 run must pass this corrected gate. No prior v4 run
can satisfy the v5 identity check.
