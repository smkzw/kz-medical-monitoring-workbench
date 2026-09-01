# R4-D07 contract v0.4 final targeted semantic follow-up

Resume independent verifier session `019ffae1-ee77-7070-8043-0bb7c22c5fe2`. Review only the v0.4 correction of the three residual findings in follow-up 2.

## Hard boundaries

- Work read-only inside the current workbench.
- Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813_followup3.md`. It is runner-managed; return it, do not write it through tools.
- Do not run or edit runtime/tests, generate 144 validation artifacts, use real projects/providers/browser/R5/product/services/medical-writing, or start port 8911.
- Semantic acceptance does not accept artifacts or runtime.

Read these files only:

- `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md`
- `runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813_followup2.md`
- `context/medical_monitoring_r4_d07_contract_20260813_context.md`
- `reviews/medical_monitoring_r4_d05_visit_schedule_slice_contract_v1_20260812.md`
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`

## Snapshot

- v0.4 contract SHA-256: `0b1f42c108ab6d4f5caa11a879cd2233328518e061772f74668cf1afd520fe84`
- task context SHA-256: `28b263a940e3c31c2e074a825a8cf3a35dec7a5a000a958b115933f5b35c938a`
- follow-up 2 report SHA-256: `46426a85bc0f839dce37c3309e6cb313e333aad99d597ca1ea2594b4ed45f815`

## Required checks

1. Verify source_revision and complete parent scope propagation through record decision, unit, result and organ-pattern assessment, plus the D05-bound cutoff policy/hash and exact inclusive interval/partial-date/timezone truth table.
2. Verify closed comparator, operand, temporal-relation, missing-point and trend-kind semantics are deterministic without hard-coded clinical thresholds.
3. Verify shared-spine episode/source revision and typed field-by-field equality decision, and single versus ordered-many source-jump target refs, hashes, cardinality and reverse bindings are internally consistent.

Report only actionable remaining P0-P4 with exact location and deterministic failure. If the three findings are closed and no new P0-P4 exists, end `VERDICT: ACCEPT_SEMANTIC_CONTRACT_V0_4`, reserving separate generation and independent verification of the 144 artifacts before full freeze/runtime.

Required report sections: boundary/sources/hashes; resolved findings; residual findings; uncertainty; next action; verdict.
