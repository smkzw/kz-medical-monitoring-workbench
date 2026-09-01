# R4-D07 contract v0.2 targeted independent follow-up

Resume the same independent verifier session `019ffae1-ee77-7070-8043-0bb7c22c5fe2`. Review the revised immutable snapshot only; do not rely on or expose the author's private reasoning.

## Hard boundaries

- Work read-only inside the current workbench.
- Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813_followup1.md`. It is runner-managed; return it, do not write it through tools.
- Do not run runtime implementation or tests, real projects, models/providers, browser/R5, product/services, medical-writing or port 8911.
- This pass may accept the semantic contract snapshot, but must not claim that the 144 validation artifacts or D07 runtime already exist.

Read these files only:

- `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md`
- `runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813.md`
- `context/medical_monitoring_r4_d07_contract_20260813_context.md`
- `context/medical_monitoring_r4_d07_external_pattern_decision_20260813.md`
- `reviews/medical_monitoring_r4_d05_visit_schedule_slice_contract_v1_20260812.md`
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`

## Sources and anchors

- Contract: `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md`
  - expected SHA-256: `d952550ce88f431ad0d41805484a9ff3d04c4f418053d86b406f3b535ee59efc`
- Initial verifier report: `runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813.md`
  - SHA-256: `2db6442ae567391d9f968e6a0d092a4c3b2f79223fbbbb8ae2c8f1c152c1a6e0`
- Task context: `context/medical_monitoring_r4_d07_contract_20260813_context.md`
  - expected SHA-256: `3345a1ae424fa2fa8deebd4aee47fc977131616a9dda1530b37a99d831473383`
- External decision record: `context/medical_monitoring_r4_d07_external_pattern_decision_20260813.md`
  - SHA-256: `a688f06ffb9fc409830e907f7f6ecc62b5ef3b4e8a01bc5cde971443fdd2638c`
- Use the previously read D05/D06/R4 common contracts only for adjacency comparison.

## Scope

Perform a targeted semantic contradiction review of v0.2 against every P1/P2 item in the initial report. In particular verify:

1. typed owner/query/handoff routing and producer-consumer bindings prevent duplicate D01-D04/D08 risks and Queries;
2. per-record scope/cutoff/time/authority/correction/current-record/canonical-hash and stable identity fail closed;
3. materialized L0 coverage, expected-set reconciliation, D05 open gates and strict `not_applicable` semantics are sufficient;
4. the validation-artifact and anti-self-proof contract is sufficient to support later 144-case executable freezing without allowing oracle/runtime coupling;
5. reference range, reported/recomputed grade, CS/NCS, seriousness clue and monitoring priority remain orthogonal through result, handoff, Query and Journey projection;
6. R2 lifecycle/carry-forward/supersession/ambiguity/close/reopen/machine-close restrictions are exact enough;
7. unit/range/grade/baseline/trend/follow-up, organ-pattern and ECG/VS/PE/imaging contexts are closed typed schemas rather than prose-only rules;
8. observation, follow-up obligation and organ-pattern split/merge rules preserve distinct clinical actions;
9. typed Journey/shared-spine/source-jump/payload hash/join reason/Chinese validator and D04-gated PD wording are adequate.

## Review disposition

- Report only actionable residual P0-P4 findings. A finding must name the exact contract section/schema and why it blocks deterministic implementation or independent validation.
- If no residual P0-P4 exists, return `VERDICT: ACCEPT_SEMANTIC_CONTRACT_V0_2`, explicitly stating that executable freeze still requires the separately generated and independently verified validation artifacts.
- Include sources read, hashes checked, observations, uncertainty, and next recommended action.
