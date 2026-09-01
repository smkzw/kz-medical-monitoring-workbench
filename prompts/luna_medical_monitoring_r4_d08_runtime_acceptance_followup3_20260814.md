# Same-session D08 runtime final acceptance follow-up 3

Continue the same independent verifier session. Your follow-up 2 `REVISE_D08_RUNTIME` remains authoritative until this snapshot passes independent probes. Do not repair files.

Hard boundaries:
- Work read-only inside the runner-provided workbench.
- Assess only D08 synthetic/offline runtime and its frozen acceptance surface.
- Do not start services, use real projects/patient data, assess R5/UI/security/medical-writing, or modify files.
- Runner-managed output path: `runs/review/medical_monitoring_r4_d08_runtime_luna_acceptance_followup3_20260814.md`. Do not write it with tools; return the complete report for the runner.

Read these files only:
- `runs/review/medical_monitoring_r4_d08_runtime_luna_acceptance_followup2_20260814.md`
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

Current snapshot hashes:
- d08_contracts `02522430eb5064979c9c048f91229c6c80c3a01f41161ad664255ae6f87af67e`
- d08_evaluator `9ae603029482febb828aa0687df21ec4b9c2183c7f695d1d5901c047168b83e8`
- d08_projection `56e5ec22134d96b590964eeb3fad6d345d821fadc1ac7ed94a1b588409a92952`
- package init `70a7f42c1e8fd268a346d396d86f6f10cb07810852864d2848a42b96413afd3b`
- adapter `17e60071af378c67970c2243a4ec164f3eded99bfa103090914daba91b555648`
- challenge matrix `bd61e7ad3a67d83509930c58988480f46d0176f3116af5c55de99f18483dfc78`
- runtime contract test `21683deeb4c00eb81a16ab8c9d6189347b647baa025682e1074bbb48e3e2771d`
- verifier probes `e218ac43d50686d8ebcbda124a4d6a21b9e513e9c83d512fc936e0dab5b217c7`

Independently reproduce every follow-up 2 finding:

1. An over-limit per-anchor cardinality with `positive_forbidden_edge` must be positive, while separate valid anchors must not be globally collapsed into a false overmatch.
2. A simultaneous stage-3 required-producer coverage gap and later bad authority hash must stop at the coverage unit (`not_evaluable`) with no risk/query/journey; stages 1-2 must still outrank coverage.
3. Mixed data plus rule/mapping change must produce exactly one data propagation unit and exactly one lineage supersede handoff, including when rule version is not `1`.
4. Every RMB outcome, including anomaly branches, must retain the actual typed rule identity in production runtime; no synthetic rule fallback may remain in evaluator source.
5. `authority_hash_mismatch` must belong to the closed integrity error enum.
6. Test-only frozen-oracle compatibility in `test_d08_adapter.py` may translate legacy resolve anomaly leaf identity to `SYN-RULE-001`, but production runtime must not do so and the translation must be structured-semantic, not case-ID/prose coupled.

Also rerun the nine probes accepted in follow-up 2, exact all-233 oracle, D08 focused, full R4, R1-R3 adjacency, generator, Ruff/compile, and TCP 8911 stopped. Pin start/end hashes and check drift.

Codex anchors:
- new targeted probes: `5 passed, 37 deselected`;
- D08 focused: `182 passed`;
- exact all-233 oracle: `1 passed, 9 deselected`;
- full R4: `3839 passed`;
- R1-R3: `1264 passed`;
- frozen generator: `54 passed`;
- Ruff/compile passed; TCP 8911 stopped.

Return exact evidence, all reproduced outcomes, residual scope, start/end hashes, and exactly one terminal verdict: `ACCEPT_D08_RUNTIME` or `REVISE_D08_RUNTIME`.
