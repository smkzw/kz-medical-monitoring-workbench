# D08 synthetic/offline runtime final follow-up acceptance

Continue the same independent verifier session. The previous verdict remains authoritative until you independently verify this new immutable snapshot. Do not modify files, start services, use real projects/patient data, or assess R5/UI/medical-writing/security. Work only in the D08 synthetic/offline acceptance scope.

Hard boundaries:

- Work read-only inside the runner-provided workbench.
- Do not modify any source, test, frozen acceptance artifact, product/frontend/service path, or medical-writing path.
- Do not start services, open port 8911, or run real projects/patient data.
- Runner-managed output path: `runs/review/medical_monitoring_r4_d08_runtime_luna_acceptance_followup2_20260814.md`. Do not write it with tools; return the complete report and let the runner persist it.

Read these files only:

- `runs/review/medical_monitoring_r4_d08_runtime_luna_acceptance_followup1_20260814.md`
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

## Current snapshot

- frozen contract: `reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md` — `ff3d3a1bd9844ac8808ca7f9ada1466317763eb883e60d825f15bb3015ac4d64`
- frozen catalog: `reviews/medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json` — `d3cd694bcbe63d977d5ef332be3647fb1274293be6ec364021946ee610ffa82c`
- frozen oracle: `reviews/medical_monitoring_r4_d08_expected_outcome_oracle_v1_20260814.json` — `a40cbb509df2378804fd513a79467cbbc4e208d3b2b5c6f1a2410a63a12b8ac9`
- frozen registry: `reviews/medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json` — `bf0142b36a60524d40d203e641c6fc0ef591c01069dd63caf6fc92da3ec96a9a`
- `src/mm_r4/contracts.py` — `993d6bea9b10842aa13f8226847961ff3881689a34797c8fdb9d68ac1aa6e5c4`
- `src/mm_r4/d08_evaluator.py` — `29f6ea36f8296a094a670a839599fa6c254291c101f6322661b9252057df3af5`
- `src/mm_r4/d08_projection.py` — `56e5ec22134d96b590964eeb3fad6d345d821fadc1ac7ed94a1b588409a92952`
- `src/mm_r4/__init__.py` — `70a7f42c1e8fd268a346d396d86f6f10cb07810852864d2848a42b96413afd3b`
- `tests/test_d08_adapter.py` — `dc546b4dc35ba94d79b104657cf0c3585c8bfdc32bf48b9fdf978b607801a2f4`
- `tests/test_d08_challenge_matrix.py` — `bd61e7ad3a67d83509930c58988480f46d0176f3116af5c55de99f18483dfc78`
- `tests/test_d08_runtime_contract.py` — `21683deeeb4c00eb81a16ab8c9d6189347b647baa025682e1074bbb48e3e2771d`
- `tests/test_d08_verifier_probes.py` — `59325381d10fd2d83962b1259dcf8f257deb57703e24b1b610a62bb8e4479d98`

## Required independent probes

Reproduce every previously failing boundary directly against the runtime, not merely by trusting the new tests:

1. missing required coverage row and `accepted_current=False` must be coverage-gated `not_evaluable`, with no risk/query/journey output;
2. site/project mismatch and shared-spine mismatch must fail closed before medical output;
3. relation authority hash/version mismatch must fail closed;
4. opaque record content hash mismatch must fail closed even when the declared hash state says valid;
5. `right_min=2` with one edge must not be conserved;
6. incomplete n-ary `raw_link_bijection` must not be conserved;
7. raw/materialized rule-window exclusion must be `not_applicable`;
8. hidden source jumps must not be projected to the user-facing journey;
9. a Query draft whose source locators are hidden-only must fail validation.

Also rerun: D08 focused tests, exact all-233 oracle test, full R4, R1-R3 adjacency, frozen generator tests, Ruff/AST compile, and confirm TCP 8911 is stopped. Check start/end hashes for execution-time drift. Treat test-only compatibility reconstruction in `test_d08_adapter.py` as acceptable only if production/runtime projection remains visibility-filtered and the frozen oracle itself is unchanged.

## Current Codex anchors

- D08 focused: `177 passed`.
- exact all-233 oracle: `1 passed, 9 deselected`.
- full R4: `3834 passed`.
- R1-R3: `1264 passed`.
- frozen generator suite: `54 passed`.
- Ruff and Python compile: passed.
- TCP 8911: stopped.

Return a compact evidence report with exact commands/results, start/end hashes, all nine probe outcomes, residual scope, and exactly one terminal verdict: `ACCEPT_D08_RUNTIME` or `REVISE_D08_RUNTIME`. The verifier owns acceptance and must not repair files.
