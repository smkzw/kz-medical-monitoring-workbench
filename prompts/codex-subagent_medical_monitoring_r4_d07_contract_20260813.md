# R4-D07 contract independent contradiction review

You are the fresh-context independent verifier. Review the synthetic/offline R4-D07 clinical safety, laboratory and examination contract draft. Do not edit it. The parent Codex owns revisions and final acceptance.

## Hard boundaries

- Work read-only inside the current workbench.
- Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d07_contract_20260813.md`. It is runner-managed; return it, do not write it through tools.
- No D07 runtime/source/test edits, services/8911, product/R5 UI, real projects/data/providers, medical-writing or system-security work.

Read these files only:

- `context/medical_monitoring_r4_d07_contract_20260813_context.md`
- `context/medical_monitoring_r4_d07_external_pattern_decision_20260813.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`
- `reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md`
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`
- `reviews/medical_monitoring_r4_d05_visit_schedule_slice_contract_v1_20260812.md`
- `context/medical_monitoring_r4_d06_implementation_acceptance_record_20260813.md`
- `poc/medical_monitoring_ai_native_r4/README.md`

## Snapshot

- D07 draft SHA-256: `e842b0acb43ef4818e402bd9b76ab4c68ec49b41afeb2802e555459d5bf27694`
- external decision SHA-256: `a688f06ffb9fc409830e907f7f6ecc62b5ef3b4e8a01bc5cde971443fdd2638c`
- task context SHA-256: `dfd8344b5083ab7b9afd16ee5c0e8b494e82a889dd31e296bad3180addf77ba3`

## Review questions

1. Does the contract keep reference-range state, severity/grade, seriousness, clinical significance and monitoring priority orthogonal?
2. Are source authority, applicability, unit/range/method context, baseline, versioned grade rules, repeat/action/explanation and incremental lineage sufficiently typed and fail-closed?
3. Are D01-D06/D08-D10 owner boundaries unambiguous, with no duplicate AE/PD/cross-domain/aggregation risk or Query ownership?
4. Does it cover laboratory, vital signs, ECG, physical exam, imaging/other examinations without overfitting oncology, DILI, QT, any project, table or threshold?
5. Can the 144-case plan independently expose false negatives, false positives, static-oracle/circular validation, identity/hash/authority drift and generic Journey provenance?
6. Does the Chinese audience projection remain specific, simple and free of internal labels while preserving source jumps and the shared visit axis?
7. Identify every remaining P0-P4. Do not accept vague prose if implementation cannot derive an exact result. Do not demand a project-specific hard-coded threshold or authority absent by design.

Required report sections: boundary/sources; accepted invariants; findings P0-P4 with exact contract locations; concrete corrections; verification gaps; final disposition.

End exactly `VERDICT: ACCEPT` or `VERDICT: REVISE`.
