Same-session corrective review, pass 27. Review only closure of pass-26 F-02/F-03 for the candidate v1.18 artifact and decide ACCEPT or REJECT.

Hard boundaries:
- Read-only inside this workbench. Do not edit files, start services, read real projects, medical-writing paths, product/R5 UI, implementation source/tests, or security paths.
- The runner owns the report; return the complete handoff and do not write it with tools.
- This is not implementation acceptance.

Output file:
Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812_followup24.md`

Read these files only:
- `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812_followup23.md` SHA-256 `8515b224019e31f306413eb0af4b59155726d51e2f8961c25721070078a2e77b`
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md` candidate SHA-256 `663ca94a3166fea08080a0611e3831a21396fe3a8783c646a434e2e537b8bef7`
- `tools/generate_d06_challenge_registry.py` SHA-256 `f1da595a925b4af66c18ac1384bf9b383bcebd046c73a8c8049ec86286ae317c`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json` SHA-256 `d4774a82e3d34dae28d6f25145f672cb62b28c506453d1bcc49ce0d60021a8e9`, catalog version `8.0.3`, catalog hash `44287f1277790ad0bbbd21045565c50049a67d5451c6eefcb30e68f12d64b774`
- `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json` SHA-256 `772bca08198b7e6279915c22077f74e328f97d2563f95a0f49db1f9d4d63e26b`, oracle hash `16b8b9648670adcae14fa16b1fe03c2570a2449e3835671bab00345f6fe9244a`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json` SHA-256 `a02c4f8b7969e7b86673fc32903929f333adbf2f68fac401551056b23b7e0aba`, registry hash `f7a7733b00c1367d95e66d7f8b5e1a12793d51ab0f7585367dcad664922be1b4`

Required checks:
1. Recompute all supplied SHA values and run the generator `--check`. Confirm semantic SHA `247eb0bc4a4c97428714f069639161ac832bed05cfcb7dfc4c01240a7ef84642`, all complete byte/preamble pins, 219 mappings and artifact hashes.
2. Confirm cases 17/173 remain the only substantive duplicate group and have identical non-case-bound outcomes/trace/entrypoint plus authoritative text `definition boundary gate`.
3. Confirm endpoint exact identity now includes version `1.0`; instrument and endpoint exact key sets match the contract and reject unknown or missing fields.
4. Confirm both definition scopes have the exact ten-key set project/run/mode/subject/site/episode/source revision/accepted snapshot/scope binding/cutoff and every value equals the fixture scope.
5. Independently recompute instrument and endpoint content hashes from the complete definition excluding only `content_hash`; confirm exact equality and that the resolver repeats this check.
6. Fully coordinate and reseal the pass-26 endpoint-version, wrong-subject scope and unexpected-field mutations so each reaches the new resolver. Also test missing/extra scope fields, site/episode drift, missing endpoint version, and content changes with both stale and recomputed content hashes. Every variant must stop before manifest construction.
7. Re-run the pass-25 synchronized wrong-text mutation and confirm the independent resolver remains the rejecting layer with zero manifests.
8. Confirm updated fixture hashes for 17/173 are bound in expected outcomes, DSL, oracle, manifests and registry without orphan mappings; no one-time upgrader remains.
9. Confirm §15 keeps v1.17 implementation unaccepted and v1.18 draft-only.

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
