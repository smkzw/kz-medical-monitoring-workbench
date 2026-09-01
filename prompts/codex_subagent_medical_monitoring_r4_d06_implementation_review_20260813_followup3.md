# R4-D06 implementation independent review — same-session follow-up 3

Continue the original independent verifier session `019ff7e2-f2ef-71a0-9c84-fa5e303cad24`. The original worker corrected every finding from your followup2 report. Verify the current immutable snapshot read-only; do not repair it.

## Hard boundaries

- Work only inside the current workspace and remain read-only.
- Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813_followup3.md`. This is runner-managed; return the complete report and do not write it through tools.
- Do not start services/8911, real projects/data/providers, product UI, medical-writing, security work, or package installation.
- Do not edit source, tests, frozen artifacts, context, prompts or reports.

Read these files only:

- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json`
- `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json`
- `runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813_followup2.md`
- `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup4.md`
- `tools/generate_d06_challenge_registry.py`
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

Adjacent R1/R2/R3/R4 test directories may be executed only through regression commands; inspect unrelated source only if a failure demonstrates a direct propagation path.

## Frozen anchors and current snapshot

Frozen artifacts must still hash to contract `460aba75857f...`, catalog `d4774a82e3d3...`, oracle `772bca08198b...`, registry `a02c4f8b7969...`, generator `fea1ad5692d8...`.

Current changed hashes:

- evaluator `0c6b797806069763391d975d65cf774ffefa853821ad092bc26db2aff7879da6`
- projection `13e3fb3b627ed5c3f0b9a8ea6298834de0885357b46fc3d64702fd7ffc88d30c`
- mutation tests `9bbad530a400f8d6a8c4060aaf2bd006dd7b0745f9b756005fb69df310346b08`
- README `d5703aaa5560cc9fb1bd3165f5c2d01a10dd03d8860113fcc114ab62803c12ca`
- unchanged efficacy `f4c9661d...`, fixtures `88d0f9a2...`, root `cb05b402...`, contract/slice/projection/matrix tests as previously frozen.

Codex independently reproduced mutation `93 passed`; R4/R2/R3/R1 `2213/598/339/327 passed`; generator check; fatal Ruff and changed-file E,F; in-memory compilation; 706 unique/resolvable exports and R2 alias.

## Required challenge

Re-run the exact escapes you found in followup2, not merely the new tests:

1. typed scope override must error with no priority/resolver/identity/projection;
2. synchronized fake stable-source identity/core/public identity/risk binding and `domain_id=D07` must fail accepted-source/domain authority;
3. unknown/missing nested fields across definitions, assessments and other consumed typed objects must fail at adapter/runtime boundary;
4. rehashed TTE source-reference/event-time/locator/scope/lineage mutations must fail or derive from a valid different typed authority;
5. rehashed enrollment time/locator/reference/rule mutations must fail and suppress Query;
6. Journey marker locators and payload hashes must come from actual typed sources; locator mutation must change content address, locator removal must fail/suppress, and serialized audience payload must not remain a generic provenance-free constant;
7. error-class/stage specificity must remain adequate;
8. raw 219 oracle/DSL, determinism, R4/R2/R3/R1, generator, Ruff, compile/export, port/cache and hashes must all hold.

Also challenge whether the 37-object structural schema table is complete for every runtime-consumed object without becoming an oracle/case lookup, and whether source-authority validation actually checks accepted-current scope/cutoff/lineage rather than only matching an ID string.

Classify every remaining P0-P4. End with exactly `VERDICT: ACCEPT` only if none remain, otherwise `VERDICT: REJECT` and the minimal concrete correction. Case 214 priority adjudication from followup2 remains settled unless new evidence contradicts it.
