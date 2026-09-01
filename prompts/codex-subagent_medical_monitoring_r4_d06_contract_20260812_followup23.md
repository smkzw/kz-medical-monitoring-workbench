Same-session corrective review, pass 26. Review only the closure of pass-25 F-01 for the candidate v1.18 validation-artifact erratum and decide ACCEPT or REJECT.

Hard boundaries:
- Read-only inside this workbench. Do not edit files, start services, read real projects, medical-writing paths, product/R5 UI, implementation source/tests, or security paths.
- The runner owns the report; return the complete handoff and do not write it with tools.
- This is not implementation acceptance.

Output file:
Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812_followup23.md`

Read these files only:
- `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812_followup22.md`
  - This is pass 25 REJECT and F-01 authority.
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md` candidate SHA-256 `f9fb8115c9abef0b30add9c29d580dc0d28036a7d8c870f263b975e9e1ea3242`
- `tools/generate_d06_challenge_registry.py` SHA-256 `31689fef6f43fb0d587093a2d422549eb0ec737faca752ea9d6fcdad8c55bd88`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json` SHA-256 `b9aea97f227d35e4a90ecd5af816409f7f11f0c6cedab97ada47b1be99698144`, catalog hash `9b9ac90484bd2b77473b187776f78de4a7ce2d29ac50617f3e398b386ba51fd0`
- `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json` SHA-256 `2ef18279304545b893a5830d4bce9a79d91cfe789d8c5fb6bd258b1d10b6544e`, oracle hash `ed6c1eb3d6571a6171fa375e31917d1ce1a445d15b4c468516fe137431311aa5`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json` SHA-256 `1d45e691e0f6181415fd1dc936e56658b702969eadfe1ad493d9b23c86fd18bb`, registry hash `7bcf1050efaf618c5d1e85a2977cbed0017d2717801d9d127d0ca2ca071d38aa`

Required checks:
1. Recompute all supplied SHA values; run `PYTHONDONTWRITEBYTECODE=1 python3 tools/generate_d06_challenge_registry.py --check`.
2. Confirm semantic SHA is exactly `b66ae7a883e4f32c891bc7a36ee8f693b6b48de6ac51301a286e578c6149fe64`, with candidate full bytes/preamble and semantic hash all pinned.
3. Inspect `resolve_definition_boundary_clinical_contract`. It must derive the exact value `definition boundary gate` without consulting expected outcome, oracle, DSL, manifest, implementation table, challenge number, fixture/test ID or annotations.
4. Confirm resolver input is genuinely typed and narrow: exact gate entrypoint; exact sole typed parameter `applicable_instrument_ids=[INST-001,INST-002]`; exact instrument and endpoint object type/ID/stable key/version/content-hash identities; nonempty source locators; definition scope fields and cutoff equal the fixture scope. Missing, reordered, duplicated, renamed, unknown or wrong-scope inputs must fail closed.
5. Confirm every substantive duplicate group is first checked for identical entrypoint/trace/non-case-bound outcome, then every member must independently resolve the same authoritative contract text, and its expected leaf must equal that derived text.
6. Reproduce pass-25 coordinated reseal counterexample: change both 17 and 173 to the same wrong text, matching DSL and oracle, and locally reseal all adjustable hashes/pins. It must now fail specifically at the typed semantic resolver comparison before manifest construction.
7. Also test at least exact candidate-set reorder/duplicate, instrument identity/hash drift, endpoint identity/hash drift, missing source locator and definition-scope/cutoff drift in a fully coordinated in-memory/temp copy. Adjust fixture-bound hashes/oracle/DSL/catalog pins as needed so each test actually reaches the resolver. All must fail before manifest construction.
8. Confirm catalog, oracle, DSL and generated manifests all contain the authoritative value; case-bound fixture hashes and bidirectional registry mappings remain valid for all 219 cases.
9. Confirm §15 still says v1.17 implementation remains unaccepted and v1.18 is only a draft corrective artifact candidate.

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
