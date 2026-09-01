Same-session corrective review, pass 17. Review only the exact v1.15 snapshot and decide ACCEPT or REJECT.

Hard boundaries:
- Read-only inside this workbench. Do not edit files, start services, read real projects, medical-writing paths, product/R5 UI, or security paths.
- The runner owns the report; return the complete handoff and do not write it with tools.

Output file:
Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812.md`

Read these files only:
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md` SHA-256 `1fbfc1c4fe9126dd585869c7bcfded66a380e7a8bff870393ac92c3b1bb6837b`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json` SHA-256 `e12584660af3d0605e80a3aa9336f8a12372d0ff17e68f477871b1a396c7c832`, catalog hash `7e77cff83635b34a75b2a0835f6280ac660fe3ce13d5b361a0d1618cdc6cbb1b`
- `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json` SHA-256 `64ff4976b586c6c26dd5c663178e1e8a643d78ac3f66bf200eecfa5df4abe77f`, oracle hash `fb7c14090c675377401733d9b53df939d5a141b264778c0d4d591e3a30207860`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json` SHA-256 `847c58f61848b169708811dcf1922a3745cb5f2c9e56f837e213e4a5e973ffd8`, registry hash `1fe06307d6277eba5e4964fdc9cc5a64455fc5a2051f2873d0fe33be0157e6ab`
- `tools/generate_d06_challenge_registry.py` SHA-256 `bc70b43c7af5bed68c38931ce73686f839ee38251772027caf50de2e9a6f51af`
- `context/medical_monitoring_r4_d06_contract_20260812_context.md` SHA-256 `c30bd06ddcca7aaad4840c5a158dd51e5d5b3fc570c4bde6aa06a8d3731e8269`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` SHA-256 `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`

Run `python3 tools/generate_d06_challenge_registry.py --check`, independently recheck the complete v1.15 snapshot, and rerun the pass-16 catalog identity mutation while resealing catalog/manifests/registry: change, remove, or mismatch catalog ID/version. Exact `medical-monitoring-r4-d06-typed-fixtures/8.0.0` must be required, and both values must be present in every manifest and registry.

Also search for one new concrete semantic escape across the complete contract/catalog/oracle/registry. A blocker requires a reproducible path/case, effect and minimum correction; generic future-hardening concerns do not block.

If any blocking P0-P4 remains, say `VERDICT: REJECT`. If none remains, say exactly `VERDICT: ACCEPT`. Acceptance is limited to this exact synthetic/offline D06 contract/catalog/oracle/registry snapshot and does not accept implementation, R4 overall, R5 UI, real projects, statistical analysis, product, medical writing or security.

Output schema:
1. `# Codex SubAgent Task: medical_monitoring_r4_d06_contract_20260812`
2. `## Boundary Check`
3. `## Work Performed`
4. `## Evidence And Observations`
5. `## Verification And Gaps`
6. `## Findings (P0-P4)`
7. `## Verdict`
8. `## Next Action For Parent Codex`
