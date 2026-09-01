Same-session metadata-only confirmation, pass 28. Review only the controlled freeze transition from the already accepted v1.18 corrective draft and decide ACCEPT or REJECT.

Hard boundaries:
- Read-only inside this workbench. Do not edit files, start services, read real projects, medical-writing paths, product/R5 UI, implementation source/tests, or security paths.
- The runner owns the report; return the complete handoff and do not write it with tools.
- This is not a new semantic or implementation review. Pass 27 already accepted the exact v1.18 artifact candidate.

Output file:
Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812_followup25.md`

Read these files only:
- `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812_followup24.md` SHA-256 `1d975757a9f0bea48b46dbbba39793cba2264fcf5cf140f6515914f85d64bf7b`
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md` frozen SHA-256 `460aba75857f72527453914b5ea5c205ecf8d5032ec5b83b22c6960ccbc8baeb`
- `tools/generate_d06_challenge_registry.py` SHA-256 `fea1ad5692d81aabb19419709fbd3f5b9c4b9a7efdef9f4280db9668383fc3f2`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json` SHA-256 `d4774a82e3d34dae28d6f25145f672cb62b28c506453d1bcc49ce0d60021a8e9`, catalog hash `44287f1277790ad0bbbd21045565c50049a67d5451c6eefcb30e68f12d64b774`
- `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json` SHA-256 `772bca08198b7e6279915c22077f74e328f97d2563f95a0f49db1f9d4d63e26b`, oracle hash `16b8b9648670adcae14fa16b1fe03c2570a2449e3835671bab00345f6fe9244a`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json` SHA-256 `a02c4f8b7969e7b86673fc32903929f333adbf2f68fac401551056b23b7e0aba`, registry hash `f7a7733b00c1367d95e66d7f8b5e1a12793d51ab0f7585367dcad664922be1b4`

Required checks:
1. Recompute every SHA and run the generator `--check`.
2. Confirm pass 27 says exactly `VERDICT: ACCEPT`, no P0-P4, and authorizes only controlled frozen metadata plus this confirmation.
3. Confirm preamble is exactly title v1.18, status `FROZEN_R4_D06_CONTRACT_V1_18`, scope limited to synthetic/offline bounded R4 POC correction and excluding implementation acceptance, R4 overall, R5 UI, real projects, statistics, products and production.
4. Confirm §15 accurately records v1.17 implementation as unaccepted, pass 27, accepted draft SHA `663ca94a3166fea08080a0611e3831a21396fe3a8783c646a434e2e537b8bef7`, unchanged semantic SHA `247eb0bc4a4c97428714f069639161ac832bed05cfcb7dfc4c01240a7ef84642`, and fixed catalog/oracle/registry anchors. It must state only preamble/§15 metadata changed.
5. Confirm generator pins the exact frozen full file and full preamble. One preamble mutation and one §15/suffix mutation must fail before manifest construction.
6. Confirm catalog/oracle/registry bytes, all 219 cases, the independent definition-boundary resolver, and the 17/173 authoritative result are unchanged from pass 27.

If any metadata mismatch, semantic drift, scope expansion, implementation rehabilitation or broken pin remains, say `VERDICT: REJECT`. Otherwise say exactly `VERDICT: ACCEPT`.

Acceptance is limited to this exact frozen synthetic/offline D06 v1.18 validation-artifact snapshot. It authorizes parent Codex to update acceptance/context records and send a bounded correction request to the existing D06 implementation worker session. It does not accept implementation, R4 overall, R5 UI, real projects, statistical analysis, products, medical writing, security or production.

Output schema:
1. `# Codex SubAgent Task: medical_monitoring_r4_d06_contract_20260812`
2. `## Boundary Check`
3. `## Work Performed`
4. `## Evidence And Observations`
5. `## Verification And Gaps`
6. `## Findings (P0-P4)`
7. `## Verdict`
8. `## Next Action For Parent Codex`
