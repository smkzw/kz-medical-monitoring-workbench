# R4-D07 contract v0.3 targeted independent follow-up

Resume the same independent verifier session `019ffae1-ee77-7070-8043-0bb7c22c5fe2`. Review only the v0.3 correction of the six residual findings from follow-up 1. Do not rely on or expose the author's private reasoning.

## Hard boundaries

- Work read-only inside the current workbench.
- Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813_followup2.md`. It is runner-managed; return it, do not write it through tools.
- Do not run runtime implementation/tests, generate the 144 artifacts, use real projects/models/providers/browser/R5/product/services/medical-writing, or start port 8911.
- Semantic acceptance does not mean executable artifact or runtime acceptance.

Read these files only:

- `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md`
- `runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813_followup1.md`
- `context/medical_monitoring_r4_d07_contract_20260813_context.md`
- `reviews/medical_monitoring_r4_d05_visit_schedule_slice_contract_v1_20260812.md`
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`

## Snapshot

- v0.3 contract SHA-256: `2ab4203bb40e0d905ee4e8aa315104b8196f18f459fe59a9443326ae114c6912`
- task context SHA-256: `9bc9ba68b2336500ff3068c4752c6b25dabf56c9e3806785c8cb377ccc6f17cd`
- follow-up 1 report SHA-256: `34b81fc19538af70d6c6d201ab561477f636902171d0f664ffaf589ec91587a4`

## Required checks

Determine whether v0.3 closes each prior item without introducing a contradiction:

1. P1-01: full subject/site/domain/scope/snapshot/cutoff tuple propagation, record scope decision, timezone/cutoff rules, stable source-event identity and unit algorithm version;
2. P1-02: exact missing/unexpected/duplicate reconciliation formula, deterministic domain-complete predicate, typed applicability evidence, and D05 gate-to-unit behavior with a non-L1 control-plane object;
3. P1-03: exact artifact top-level/core key sets, canonical/semantic hash range, five-way registry bijection, closed DSL/operators/clauses, expected raw/trace/source leaves, ordered integrity stages/error classes, and oracle/generator/runtime independence;
4. P2-01: closed conditional schemas for range, conversion, grade comparator, predicate, baseline, trend, organ-pattern components and examination requirements;
5. P2-02: content-addressed action-obligation definition/binding, stable obligation identity, merge/split and duplicate prevention;
6. P2-03: full shared-spine scope equality, typed PD permission, audience lexicon and validation result, source-jump target/cardinality/reverse/temporal validation, and conditional payload rules.

Report only remaining actionable P0-P4 with exact section/schema and deterministic failure mode. Do not demand project-specific clinical thresholds in the generic kernel. If these six findings are closed and no new P0-P4 exists, return `VERDICT: ACCEPT_SEMANTIC_CONTRACT_V0_3`, explicitly reserving generation and independent verification of the 144 executable artifacts before full contract freeze and runtime implementation.

Required report sections: boundary/sources/hashes; resolved findings; residual P0-P4; uncertainty; next action; verdict.
