Same-session corrective review, pass 14. Review only the exact v1.12 snapshot and decide ACCEPT or REJECT.

Hard boundaries:
- Read-only inside this workbench. Do not edit files, start services, read real projects, medical-writing paths, product/R5 UI, or security paths.
- The runner owns the report; return the complete handoff and do not write it with tools.

Output file:
Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812.md`

Read these files only:
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md` SHA-256 `89ac62a397e95414a093d5a8e444bdc7b443e2021e4268c9003d02423b378a12`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json` SHA-256 `e12584660af3d0605e80a3aa9336f8a12372d0ff17e68f477871b1a396c7c832`, catalog hash `7e77cff83635b34a75b2a0835f6280ac660fe3ce13d5b361a0d1618cdc6cbb1b`
- `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json` SHA-256 `64ff4976b586c6c26dd5c663178e1e8a643d78ac3f66bf200eecfa5df4abe77f`, oracle hash `fb7c14090c675377401733d9b53df939d5a141b264778c0d4d591e3a30207860`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json` SHA-256 `a72af6c302a2653b8177c882a299f5e0316d906d8092ee56b29417b09c4bf280`, registry hash `dbac848a15eda228f358c0b58a01fbb1301b3d11cb98097067245da153f66b9a`
- `tools/generate_d06_challenge_registry.py` SHA-256 `e90e0f90e264f10ea2313b4889ab9c84811ef1410e39fc222ce87d1b49e54144`
- `context/medical_monitoring_r4_d06_contract_20260812_context.md` SHA-256 `7ed37283d359c4683279ab0bfac58c180c5df3c0b2cb0a5fd5859bee25a4ddb5`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` SHA-256 `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`

Run `python3 tools/generate_d06_challenge_registry.py --check`, independently recheck the complete v1.12 snapshot, and rerun the pass-13 bypass by clearing, truncating, reordering and extending `required_audience_checks` in case 31 while resealing catalog/manifests/registry. Every audience entrypoint must require the exact ordered ten-item canonical set; every non-audience entrypoint must require none. Confirm the independent audience checks then actually execute and remain bound to the immutable fixture/outcome oracle.

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
