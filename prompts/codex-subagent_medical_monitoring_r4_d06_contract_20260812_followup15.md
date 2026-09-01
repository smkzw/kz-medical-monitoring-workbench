Same-session corrective review, pass 18. Review only the exact v1.16 snapshot and decide ACCEPT or REJECT.

Hard boundaries:
- Read-only inside this workbench. Do not edit files, start services, read real projects, medical-writing paths, product/R5 UI, or security paths.
- The runner owns the report; return the complete handoff and do not write it with tools.

Output file:
Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812.md`

Read these files only:
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md` SHA-256 `d94e2cfded96c89a3f5cd701a16b5008a5ae7637ef2a5247541ac8a881b12afb`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json` SHA-256 `e12584660af3d0605e80a3aa9336f8a12372d0ff17e68f477871b1a396c7c832`, catalog hash `7e77cff83635b34a75b2a0835f6280ac660fe3ce13d5b361a0d1618cdc6cbb1b`
- `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json` SHA-256 `64ff4976b586c6c26dd5c663178e1e8a643d78ac3f66bf200eecfa5df4abe77f`, oracle hash `fb7c14090c675377401733d9b53df939d5a141b264778c0d4d591e3a30207860`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json` SHA-256 `561f01a3cc14170165fd904b73f9aef57e0fb687319331851303ebd0ee6f4f98`, registry hash `df0b13d1e412294b409eaf1b9e628558e7f56d120985f7a16b811e20dd962c80`
- `tools/generate_d06_challenge_registry.py` SHA-256 `74dc55fac2ea2c5a8ffca5fc066dc08c6f3ae768c869d8312701e0e89bc390a6`
- `context/medical_monitoring_r4_d06_contract_20260812_context.md` SHA-256 `e99fce2f03777c1fefc2ae96944cc650e2754e5c2f14654b2daa8030774f3676`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` SHA-256 `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`

Run `python3 tools/generate_d06_challenge_registry.py --check`, independently recheck the complete v1.16 snapshot, and rerun pass-17 mutations with full enclosing reseal: unknown/missing top-level catalog field, unknown/missing case field, plus arbitrary content modification. The exact catalog/case key sets and generator-pinned entire catalog hash must reject all variants.

Also search for one new concrete semantic escape across the complete contract/catalog/oracle/registry. Because the complete catalog and oracle hashes are now generator-pinned, a blocker must show an accepted mutation without changing generator source. Generic future-hardening concerns do not block.

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
