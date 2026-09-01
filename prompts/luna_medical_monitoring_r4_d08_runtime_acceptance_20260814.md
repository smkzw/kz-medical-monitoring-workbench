# Independent acceptance review — R4 D08 runtime

You are a fresh-context independent verifier. Read only; do not modify any file, do not start services, do not run real projects, and keep TCP 8911 stopped. The worker and Codex do not own done; you do.

Workspace: `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench`

Review the current immutable snapshot of:

- `reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md`
- `reviews/medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_expected_outcome_oracle_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_evaluator.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_projection.py`
- D08 exports in `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py`
- all `poc/medical_monitoring_ai_native_r4/tests/test_d08_*.py`
- worker reports `runs/pi_medical_monitoring_r4_d08_runtime_20260814.md` and `runs/pi_medical_monitoring_r4_d08_runtime_followup1_20260814.md` only as claims to verify, never as authority.

Current source hashes to pin at start and end:

- d08_contracts.py `b1d4c1a42bb77c3358165300a471ea4fbce96ac3eb4553c2b633896028ea816d`
- d08_evaluator.py `131074f93fc63808625a4ddc209007c481d0455a02962607781ac85244ddc3dc`
- d08_projection.py `5af0bb5af7ba12331c7d2f4ade96a239a4b0a4ee5a289227efa8e4f10d59785d`
- mm_r4/__init__.py `aac7713673ec274a47fa69698ae8e03cac42282cff91a9eaa5d8998650be8b11`
- test adapter `8384978cf0bdf6069dc0b100b27b456870e492771e2ab88e9325069671961c74`
- challenge `bd61e7ad3a67d83509930c58988480f46d0176f3116af5c55de99f18483dfc78`
- collection `4dfd3b61b363ed320801a5b6c9e64ad05cc12aadf9352bbccd6539b382c74f23`
- mutations `17ccb37a0078939986e7ad9fbdac38eebac5c5f713d3926ecae6c1686071f3ec`
- query/journey `53221a4ac9dfc512e78bc3da9123775ddf4ab5612fa2c8f4f1109becf3c49e8f`
- replay `ab699a5fc939598f358f73b22a6f888b8900b96e88ecb50bfa6da2d09fa1cdfe`
- runtime contract `c89a780e9f580ab01e2b68de8ea0d06811d6e38454ac9ef81f881682b71f209c`

Frozen hashes must remain:
contract `ff3d3a1b...d64`; catalog `d3cd694b...2a9a`; oracle `a40cbb50...ac9`; registry `bf0142b3...a9a`; generator `63d610e8...f100`; generator test `0b4e7c1d...f906`.

Acceptance criteria:

1. Runtime is stdlib-only, deterministic, typed, offline/synthetic, and never reads/imports the frozen acceptance artifacts, generator, or tests.
2. No runtime branch on case/fixture/oracle/manifest/test IDs, `mutation_description`, free-text reason prose, English substring hints, or expected leaves. Test-only frozen-artifact compatibility mappings must remain outside `mm_r4` runtime and cannot leak identifiers into decisions.
3. Closed structured facts cover propagation (including producer-not-evaluable / ambiguous-chain), relation wrong-subject/site, identity/duplicate decisions, explicit links, reverse cardinality, stable identity, cutoff, six temporal relations, propagation/correction, visibility, n-ary RELID, fanout/routing, coverage/waiver. Check whether the modeled propagation fields faithfully satisfy v0.6 rather than merely fitting examples.
4. Pre-evaluator integrity fails at the first contract stage and emits no medical/risk/Query/Journey payload.
5. All 233 cases exactly match all expected/trace/source leaves through the test-only adapter; replay, order, semantic mutations, mutation-description invariance, and anti-overfit tests are meaningful rather than tautological.
6. D08-owned positives produce risk identity plus natural Chinese three-part Query (依据/发现/行动项), no PD wording; audience visibility and source jumps do not leak hidden/forbidden records. Journey marker semantics remain renderer-neutral and usable downstream.
7. Tests collect and pass from workbench root; run focused D08, full R4, R1-R3 adjacency, Ruff/compile, frozen hashes, and confirm 8911 stopped. You may reduce duplicate commands only if decisive equivalent evidence is already reproduced.
8. Identify any P0-P4 defect. Any material contract mismatch, fixture-text coupling in production runtime, false-positive/false-negative logic, audience data leak, non-root-runnable test, or source drift is REVISE.

Return a compact evidence report with exact commands/results, start/end hashes, findings by severity, residual scope, and exactly one verdict token on its own line:

`ACCEPT_D08_RUNTIME`

or

`REVISE_D08_RUNTIME`

Do not accept R4 overall, real endpoints, R5/UI, production readiness, or medical-writing scope.
