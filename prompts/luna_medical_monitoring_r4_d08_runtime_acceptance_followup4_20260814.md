# Same-session D08 runtime acceptance follow-up 4

Continue the same independent verifier session. Follow-up 3 remains REVISE until this immutable snapshot passes. Read-only review; do not repair files.

Hard boundaries:
- Work only inside the runner-provided workbench and only on D08 synthetic/offline runtime acceptance.
- Do not modify files, start services, use real projects/patient data, or assess R5/UI/security/medical-writing.
- Runner-managed output path: `runs/review/medical_monitoring_r4_d08_runtime_luna_acceptance_followup4_20260814.md`. Return the report; do not write this path with tools.

Read these files only:
- `runs/review/medical_monitoring_r4_d08_runtime_luna_acceptance_followup3_20260814.md`
- `reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md`
- `reviews/medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_expected_outcome_oracle_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json`
- `tools/generate_d08_challenge_registry.py`
- `tests/test_d08_artifact_generator.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/`
- `poc/medical_monitoring_ai_native_r4/tests/`
- `poc/medical_monitoring_ai_native_r1/tests/`
- `poc/medical_monitoring_ai_native_r2/tests/`
- `poc/medical_monitoring_ai_native_r3/tests/`

Current hashes:
- d08_contracts `8d8fb6727a878642b361b444edb110b7283ef11b41adc1cb3c561152699225ad`
- d08_evaluator `0d584064143263409a3e282a087c4931a4cfb4a1d832556836bc9a71ad23e43b`
- d08_projection `2764c737e906ad1f947b8785d66c03c2989c0c455eb6bd37bfb3a9f502098c9b`
- package init `70a7f42c1e8fd268a346d396d86f6f10cb07810852864d2848a42b96413afd3b`
- adapter `b8e3b63290bcf4a4ce7ab8d8ca978f9e237fac8deb462966feb3ba48e6d66347`
- challenge matrix `bd61e7ad3a67d83509930c58988480f46d0176f3116af5c55de99f18483dfc78`
- runtime contract test `21683deeb4c00eb81a16ab8c9d6189347b647baa025682e1074bbb48e3e2771d`
- verifier probes `5d4ed184fe561a54702cc9e165a39fa6342bff6d5d910836314614de33313a25`

Independently reproduce all four follow-up 3 defects:

1. For `integrity_matrix`, global integrity must precede rule-window applicability: bad node hash plus excluded window must fail closed on the node hash with zero units/payload.
2. Duplicate stable identities must not be resolved by set/hash iteration order. Across multiple `PYTHONHASHSEED` values and record order permutations, audience relation-edge projection must be identical and fail closed unless each endpoint maps uniquely.
3. Propagation intersection must be recomputed from `changed_fields` and `DerivedObject.declared_consumed_fields`; changing only caller-supplied `consumed_field_intersection` must not change the outcome. The frozen adapter may materialize the legacy declaration only at its test boundary.
4. A present raw link without any closed resolve decision must be `not_evaluable/resolve_decision_missing`, never conserved negative.

Recheck all earlier accepted probes, exact 233 oracle, D08 focused, full R4, R1-R3, generator, Ruff/compile, hash stability, and TCP 8911 stopped. Current Codex anchors: targeted 4 passed; D08 186 passed; full R4 3843 passed; R1-R3 1264 passed; generator 54 passed; Ruff/compile pass; 8911 stopped.

Return exact evidence, residual scope, start/end hashes, and exactly one terminal verdict: `ACCEPT_D08_RUNTIME` or `REVISE_D08_RUNTIME`.
