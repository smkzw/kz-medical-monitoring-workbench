# R4-D06 implementation correction — same worker follow-up 4

Continue the original implementation worker session `019ff7a9-93f2-7000-8500-c02c1a59c529`. The original independent verifier session has rejected the current immutable snapshot in `runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813_followup2.md`. Correct only the demonstrated D06 blockers; do not restart broad exploration or create a new implementation.

## Hard boundaries

- Work only inside the current workspace.
- Allowed write paths only:
  - `poc/medical_monitoring_ai_native_r4/src/mm_r4/`
  - `poc/medical_monitoring_ai_native_r4/tests/`
  - `poc/medical_monitoring_ai_native_r4/README.md`
- Write exactly one output file: `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup4.md`. It is runner-managed; return the complete report and do not write it through tools.
- Do not edit frozen contract/catalog/oracle/registry/generator, R1-R3 sources, product/frontend/services, medical-writing, prompts/context/review/run files, or security surfaces.
- Do not start port 8911 or any service; do not use real projects/data/providers; do not install packages.

Read these files only:

- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`
- `runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813_followup2.md`
- `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup3.md`
- `poc/medical_monitoring_ai_native_r4/README.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/efficacy.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/efficacy_evaluator.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/efficacy_projection.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/efficacy_fixtures.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_contract.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_slice.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_projection.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_challenge_matrix.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_efficacy_mutations.py`

Adjacent R4/R2/R3 tests may be executed for regression only. Inspect additional D06-local source/tests only when a direct dependency requires it.

## Frozen anchors and starting snapshot

Do not change:

- contract `460aba75857f72527453914b5ea5c205ecf8d5032ec5b83b22c6960ccbc8baeb`
- catalog `d4774a82e3d34dae28d6f25145f672cb62b28c506453d1bcc49ce0d60021a8e9`
- oracle `772bca08198b7e6279915c22077f74e328f97d2563f95a0f49db1f9d4d63e26b`
- registry `a02c4f8b7969e7b86673fc32903929f333adbf2f68fac401551056b23b7e0aba`
- generator `fea1ad5692d81aabb19419709fbd3f5b9c4b9a7efdef9f4280db9668383fc3f2`

Starting runtime hashes: `efficacy.py f4c9661d…`; evaluator `68c904bb…`; projection `48d5fb12…`; fixtures `88d0f9a2…`; root `__init__.py cb05b402…`. The root hash differs from followup3 only because Codex wrapped one long import; preserve this formatting fix.

## Required corrections

Reproduce and close all verifier findings with exact mutation tests:

1. Any typed scope/schema/pre-priority integrity failure must suppress `priority_resolution`, resolver input hash/object, risk/public identity and Journey projection. Preserve frozen oracle behavior for unmutated cases, including case 214; the new mutation must prove invalid typed override fails before priority.
2. Resolve `D06UnitStableCore.stable_source_record_id` against an accepted-current typed source record/inventory in the same scope/cutoff, rather than accepting a synchronously rewritten core/identity/binding. Enforce `domain_id == D06`. A synchronized rehash of core + public identity + risk binding must still fail if source authority or domain is invalid.
3. Make fixture schema validation recursively exact for runtime-consumed nested objects, at least every definition type, assessment/source record, bindings/policies, TTE and enrollment events/registries, risk binding and public identity. Unknown/missing/incompatible nested fields must fail before medical evaluation. Avoid a case-specific validator or duplication of expected outcomes.
4. TTE: bind every precedence/source reference to the typed registry, exact scope/cutoff, event/reference identity, event time/role, lineage/hash and source locators. Rehashed reference or event-time drift must fail closed unless it resolves a valid different typed source with correspondingly derived output.
5. Enrollment: validate decision/source-event reference, exact scope/cutoff, effective/event time, context, rule/version, lineage/hash and locator identity. Rehashed event time or locator drift without valid authority must fail closed.
6. Journey: each marker/source jump must carry actual typed source locator IDs and a payload/source hash; audience serialization must derive its jump data from the constructed projection. Locator mutation/removal must change a content-addressed projection/payload or fail closed—never retain the same generic payload. Preserve Chinese-native renderer-neutral labels and visit axis.
7. Replace or narrow the broad unexpected-exception collapse where practical so typed contract failures retain specific error classes/stages. Add a regression proving expected validation errors are not degraded into an unrelated generic result.

Do not change the frozen artifacts to fit the code and do not branch on case/challenge/test identity. Keep the solution bounded and data-derived.

## Verification

Run and report:

- each new targeted mutation plus full `test_efficacy_mutations.py`;
- D06 focused files and all 219 raw oracle/DSL cases;
- full R4, R2 and R3 tests;
- generator `--check` and frozen hashes;
- fatal Ruff plus `E,F` on every changed D06 file;
- in-memory compilation/import and 706 export/alias checks;
- deterministic replay, 8911 stopped, and zero task-created caches.

Return exact changed files/hashes, commands/counts, demonstrated before/after behavior, unresolved contradictions, and next verifier action. Do not claim acceptance; Codex and the original verifier own acceptance.
