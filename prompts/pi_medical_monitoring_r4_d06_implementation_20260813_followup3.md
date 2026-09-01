Same-session second bounded correction of the still-rejected R4-D06 v1.18 synthetic/offline implementation. Close every P1-P3 in the independent followup1 review; do not claim acceptance.

Hard boundaries:
- Work only in the runner-provided workbench directory.
- Writes are limited to `poc/medical_monitoring_ai_native_r4/src/mm_r4/`, `poc/medical_monitoring_ai_native_r4/tests/`, and `poc/medical_monitoring_ai_native_r4/README.md`.
- Do not change frozen contract/catalog/oracle/registry/generator, context/review/prompt/run files, R1-R3, product/frontend/service, real-project, medical-writing or security surfaces.
- Do not start 8911/services, run real projects/data/providers, install packages, or perform UI/browser work.
- The runner owns `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup3.md`; never write it with tools.
- Preserve unrelated work. Recompute listed hashes before editing; stop on drift.

Output file:
Write exactly one output file: `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup3.md`

Read completely:
- `context/medical_monitoring_r4_d06_implementation_20260813_context.md`
- frozen v1.18 contract SHA `460aba75857f72527453914b5ea5c205ecf8d5032ec5b83b22c6960ccbc8baeb`, semantic SHA `247eb0bc4a4c97428714f069639161ac832bed05cfcb7dfc4c01240a7ef84642`
- catalog/oracle/registry/generator file SHAs `d4774a82e3d34dae28d6f25145f672cb62b28c506453d1bcc49ce0d60021a8e9` / `772bca08198b7e6279915c22077f74e328f97d2563f95a0f49db1f9d4d63e26b` / `a02c4f8b7969e7b86673fc32903929f333adbf2f68fac401551056b23b7e0aba` / `fea1ad5692d81aabb19419709fbd3f5b9c4b9a7efdef9f4280db9668383fc3f2`
- `runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813_followup1.md` SHA `7b0513564e87fc3becf01d4a5ecf045977f7aa58e70c065eff85dd104a6adc85`
- worker followup2 SHA `2dbf38a3195eb0b5a1051c9c80af09b9280ee48958d6a935fd1513badd7e7d48`

Current implementation hashes:
- `efficacy.py` `f4c9661de919018794d4cbe615664eb192bfac16d31a2e960ef9d5425fc69314`
- `efficacy_evaluator.py` `e5abaad8f55f52ffbcf0c02f920f574c98468c9897d1d7d9b2c81f5d2123e7fe`
- `efficacy_projection.py` `0ba7fc9ff0b3e541f10e8b0edfd9c7bb5969b2d5a5dd3c31a025f5ce97487ef6`
- `efficacy_fixtures.py` `88d0f9a28d7eb1b3c58db89febc580574f9d70b5dd3624c4b662c08ea811e849`
- `__init__.py` `ce5731ea096efe2d1fc2c9e0f23a577279d7d97f16f37acd81d9c1bbc7bc985d`
- `README.md` `4bc6694b751b45dc5ca721b917ee761b0391be181d8f721e0752b36c9db5027c`
- tests contract/slice/projection `4c1f4701727a5efec18c48271cb0b564d6402be2a6a2be6afc73249f387026f4` / `1f4a15958ed02a4c3b28f0400c25090dc16d434c7db5dcd516f576839f323c80` / `3b54c5a1698aa00746672ce0c34acd3c448f987b00e6fc9d3a12988dd9cba38b`
- matrix `518c8b258b7625ec3c2f6725cfcc8ffda9c6bef25a17a2cac72da421df28a78f`
- mutations `2845faf7da8761350d57b82229bd7f798fe3a93113fd857f864366f1cc8d85df`

Required corrections:

1. Exact definition boundary.
- Enforce exact v1.18 instrument and endpoint key sets, canonical IDs/versions, exact complete definition scope, exact schemas and valid content hashes at runtime.
- Rehashed unknown field, rehashed version drift, missing field, wrong ID/scope/schema/content must fail closed, not preserve a successful gate.
- Replace all weak `error OR base trace` tests with exact error/stage assertions; add rehashed semantic mutations.

2. No priority before integrity.
- For pre-fixture, scope, schema, definition or registry integrity failure, emit no priority resolution, no resolver input hash/object, no risk/public identity and no clinical projection. Case 214 and wrong-scope mutations must prove this exactly.

3. Bidirectional risk/public identity validation.
- If typed `risk_binding` or `public_r4_risk_identity` is supplied, validate every scope, unit, risk, classifier/subtype, priority decision, stable-core/public identity, lifecycle and locator field against the runtime-derived objects; missing/drifted/extra incompatible content fails closed.
- Do not merely ignore the supplied objects or substitute canonical constants. Add independent mutations that recompute enclosing hashes where applicable.

4. TTE sources without fallback fabrication.
- Derive event/censor interpretation, selected/competing event IDs, precedence binding ID/rule and all source references only from resolved typed TTE registry/bindings/events.
- Missing selected/competing event, missing binding ID, wrong scope/version/rule/reference must fail closed. Remove fixed fallback IDs such as `EV-COMP-001`/`TTE-BIND-001` unless those exact IDs were resolved from input.

5. Enrollment variant source resolution.
- Resolve every source event referenced by active enrollment decisions and all context variants against the typed registry, with exact scope/status/rule/version/linkage. Missing/drifted source must fail closed and suppress Query.
- Chinese Query remains the exact three-part form and derives from resolved decision/rule/source data.

6. Runtime-derived Journey and audience payload.
- Build projection ID, shared visit/time spine, marker IDs/types, risk anchor/identity, priority and source-jump targets from validated typed runtime objects and locators. No page/variant/static fallback identities.
- Serialize the actual constructed projection into audience payload. Remove static `JOURNEY_PAYLOAD` substitution/disconnection. Invalid projection or locator suppresses payload with exact gate/error state.
- Risk marker priority must come from typed `D06PriorityDecision`.

7. Close typed-boundary P3.
- Replace broad `Any` fixture sections with explicit immutable mapping/record protocols or typed dataclasses plus exact recursive schema validation at the adapter/runtime boundary. Deep freeze alone is insufficient. Unknown/missing incompatible nested fields must fail before evaluation.
- Keep compatibility with all 219 frozen cases and avoid duplicating the test oracle in runtime.

8. Preserve every already-closed property: raw pass-through, zero expected/manifest injection, 219 exact outcomes, 106/191 provenance, 17/173 identical semantics, sorted exact traces, derived baseline, wrong-scope actual hash, deep immutability, 706 export identity, fail-closed error handling.

Verification with bytecode/cache disabled:
- all 219 raw outcomes exactly match every oracle/DSL leaf with zero exclusions;
- focused D06 and strengthened mutation tests;
- full R4, R2, R3;
- generator/hash checks; focused Ruff E9/F63/F7/F82; compile/import/export identity/determinism;
- 8911 stopped and only task-created caches removed.

Final handoff schema:
1. `# Implementation Handoff: medical_monitoring_r4_d06_implementation_20260813_followup3`
2. `## Boundary And Initial Hash Check`
3. `## Sources Read`
4. `## Files Changed`
5. `## Corrections By Independent Finding`
6. `## Rehashed Mutation Evidence`
7. `## All-219 And Regression Evidence`
8. `## Failed Paths And Remaining Gaps`
9. `## Exact Final Snapshot Hashes`
10. `## Next Action For Codex`
