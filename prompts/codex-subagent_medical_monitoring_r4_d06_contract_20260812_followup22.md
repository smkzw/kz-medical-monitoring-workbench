Same-session corrective contract review, pass 25. Review only the v1.18 validation-artifact erratum for the case 17/173 semantic-output collision and decide ACCEPT or REJECT.

Hard boundaries:
- Read-only inside this workbench. Do not edit files, start services, read real projects, medical-writing paths, product/R5 UI, unrelated implementation source/tests, or security paths.
- The runner owns the report; return the complete handoff and do not write it with tools.
- This is not implementation acceptance. The v1.17 implementation correction remains unaccepted.

Output file:
Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812_followup22.md`

Read these files only:
- `runs/pi_medical_monitoring_r4_d06_implementation_20260813_followup1.md`
  - SHA-256 `1943e894536875eaa11d68ef744d8f565029826e466112766c5af4d928bfc9fe`; use only its 17/173 raw-runtime contradiction evidence as the reason for this erratum.
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md` candidate SHA-256 `ff28111a305b87ebf6b6f3d693ddf70c7947944d154a0772f4c2e56b47a1a0a6`
- `tools/generate_d06_challenge_registry.py` SHA-256 `a60268b71440a88d28b3bce25f232e5b8bb3f9e493c76d0d879669b20f2e51a0`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json` SHA-256 `b9aea97f227d35e4a90ecd5af816409f7f11f0c6cedab97ada47b1be99698144`, catalog version `8.0.2`, catalog hash `9b9ac90484bd2b77473b187776f78de4a7ce2d29ac50617f3e398b386ba51fd0`
- `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json` SHA-256 `2ef18279304545b893a5830d4bce9a79d91cfe789d8c5fb6bd258b1d10b6544e`, oracle hash `ed6c1eb3d6571a6171fa375e31917d1ce1a445d15b4c468516fe137431311aa5`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json` SHA-256 `19bb936d369371a302515ddad8a7994584140afeb61a3055a73f08ea1d17ffc3`, registry hash `ab53f39d4ce1dc66d0a1aa6fa65078e45fa89b624573825c5fe8a47c2966f7da`

Required checks:
1. Recompute every supplied SHA and run `PYTHONDONTWRITEBYTECODE=1 python3 tools/generate_d06_challenge_registry.py --check`.
2. Confirm §1–§14 semantic SHA is exactly `abf963754534e9b11bc2f3f9c88d88233b2c44ba58c91b67bdf0a67eaf8fba03`, pinned in the generator, with complete candidate bytes/preamble pinned.
3. Independently compare all 219 fixtures after removing only `fixture.challenge_number`. Enumerate every substantive duplicate group. Confirm the only group is 17/173, both call the same gate entrypoint, have identical required trace edges and identical non-case-bound expected outcomes.
4. For 17/173, confirm the only permitted remaining differences are challenge/test/fixture locator identities plus `domain_assertions.challenge_assertion_code`, `domain_assertions.evaluated_fixture_hash`, and `object_hashes.fixture_hash`. Both must now require exact `clinical_outcome_contract = "definition boundary gate"` in catalog, oracle, DSL and manifest.
5. Inspect the new generator invariant. It must group by canonical full fixture after removing only challenge number and fail closed when a group differs in entrypoint, required trace edges, or any non-case-bound expected outcome leaf. It must not normalize away clinical text, audience, identity, counts, errors, dispositions or traces.
6. Run coordinated in-memory/temp-copy negative mutations that reseal catalog/oracle/manifests/registry pins as needed so the new invariant, not merely the old top-level hash pin, is exercised:
   - restore the old different case-173 clinical text and DSL/oracle value;
   - change case 173 trace;
   - change case 173 entrypoint;
   - change one non-case-bound count/disposition/error/audience/identity leaf while preserving structural validity as far as practical.
   Each must be rejected by the identical-substantive-fixture invariant before acceptance.
7. Confirm case-bound hashes remain independently recomputable and no runtime evaluator is permitted to read challenge number, fixture/test ID, expected text, oracle, manifest or annotations.
8. Confirm §15 states v1.17 implementation remains unaccepted and v1.18 is only a draft corrective artifact candidate; it must not claim recovery of any original conversation or accept any implementation.

Veto criteria:
- Any semantically identical typed fixture pair still has different non-case-bound runtime outcome, trace or entrypoint.
- The invariant can be bypassed by coordinated catalog/oracle/registry resealing.
- The erratum broadens scope or rehabilitates an unaccepted implementation.
- Any hash, semantic, registry or case-bound fixture relation mismatch.

If any P0-P4 issue remains, say `VERDICT: REJECT`. Otherwise say exactly `VERDICT: ACCEPT`.

Acceptance is limited to this exact candidate synthetic/offline D06 v1.18 validation-artifact erratum. It authorizes parent Codex only to perform a controlled frozen-metadata transition and request one metadata-only same-session confirmation. It does not accept implementation, R4 overall, R5 UI, real projects, statistical analysis, products, medical writing, security or production.

Output schema:
1. `# Codex SubAgent Task: medical_monitoring_r4_d06_contract_20260812`
2. `## Boundary Check`
3. `## Work Performed`
4. `## Evidence And Observations`
5. `## Verification And Gaps`
6. `## Findings (P0-P4)`
7. `## Verdict`
8. `## Next Action For Parent Codex`
