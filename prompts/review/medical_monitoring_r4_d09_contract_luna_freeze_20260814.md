You are an independent Codex Luna verifier in a fresh context. Work read-only.

Read these files only:

- `AGENTS.md`
- `reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_3_20260814.md`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`
- `context/medical_monitoring_r4_d09_external_pattern_decision_20260814.md`

## Hard boundaries

- Do not read any D09 conference participant report or Codex chair reasoning.
- Do not edit files, build artifacts/runtime, start services/8911, use real project/patient data, touch medical writing, or perform security work.
- First record SHA-256 of the target contract; verify the same hash at the end.
- Verify port 8911 remains STOPPED.

Independently assess whether the self-contained D09 v0.3 contract is freezeable. Challenge owner boundaries, the three pattern kinds, expected-set admission, stable/public identities and lineage, required-domain L0+L1 completeness, numerator/denominator/opportunity, cutoff/window/stratum/comparability/visibility, five dispositions, center-pattern RiskInstance and count isolation, hotspot/deep-link behavior, center Query, Chinese audience language, the disjoint 179-case challenge floor, and non-LLM freeze anchors. Treat prior green tests as irrelevant to contract acceptance.

Return a concise evidence report with sources read, pinned hashes, highest-severity findings, acceptance rationale or exact clause-level defects, unverified boundaries, and exactly one final verdict token: `ACCEPT_D09_CONTRACT` or `REVISE_D09_CONTRACT`.

Write exactly one output file:

runs/review/medical_monitoring_r4_d09_contract_luna_freeze_20260814.md

The runner persists the report; return the complete report only.
