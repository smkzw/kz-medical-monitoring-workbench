# R5-S5 public semantic-authority delta v0.1

## Disposition

`IMPLEMENTED_FOR_INDEPENDENT_REVIEW` — not ACCEPTED. This delta is append-only and synthetic/non-clinical.

## Root-cause repair

The previous candidate let a receipt repeat `accepted` and a package hash, which made a fully resealed changed package capable of authorizing itself. Raw token evidence had the same defect: it could change token/owner and recompute its own hash. Nested exact schemas and global coverage were incomplete, the S4 join exceeded eight fields, and SAE/AESI paths were invented on `RiskCandidate`.

This revision pins a frozen synthetic acceptance registry (`71dc168b99dd1ea2d768284fe69e0c0cdd013b9fa261e85132f0b334cf20e075`) and a frozen typed-source registry (`28d536579be39b80bdb3dc1033845cae0eea27d362eef1375ac66eb3a34c5939`). Receipts and evidence are projections that must independently resolve to those roots. Both registries are `synthetic_test_only`, `non_clinical=true`; clinical acceptance remains outside this delta.

## Contract changes

- all nested schemas deny additional properties, including `ExactRuleComponent` and `SourceRevisionContentPair`;
- exact UTF-8 matching only; severity enum and risk-code regex/content hash are closed;
- global validation enforces 13 exact + 3 compound event rules, the full 16→8 relation, exact-one match, complete taxonomy/lexicon and all legacy severity mappings;
- S4 join has exactly eight fields;
- SAE/AESI non-promotion resolves from `mm_r2.risk.RiskInstance.clinical_risk_flags`;
- 66 active cases include fully resealed MH→ae, forged Chinese label, catastrophic, receipt extra field, missing legacy, fuzzy, cross-owner raw token and accepted-record mismatch attacks.

## Verification contract

Run the independent verifier normally, under `python3 -O`, with multiple `PYTHONHASHSEED` values, and Ruff. It also verifies parent pins, the 542-file inventory aggregate, negative-only rejected snapshot pins, allow/deny scope, producer absence, port 8911 stopped, deterministic regeneration and stable raw SHA-256. The worker does not produce an acceptance record.
