Same-session corrective review, pass 13. Review only the exact v1.11 snapshot and decide ACCEPT or REJECT.

Hard boundaries:
- Read-only inside this workbench. Do not edit files, start services, read real projects, medical-writing paths, product/R5 UI, or security paths.
- The runner owns the report; return the complete handoff and do not write it with tools.

Output file:
Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812.md`

Read these files only:
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md` SHA-256 `317f4fa2c308c9ce99e99b3fde246fea4a4e01032d7fc132b4adeffbb4f0297a`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json` SHA-256 `64cfae59d4285b6cf9bab0e120725e4600517843dae52610ab96b1d3d1b1bb69`, catalog hash `49c5f549a4f6d04c2a0543c7e71a8032e858b4e983bada604aee3b5cca04f63d`
- `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json` SHA-256 `64ff4976b586c6c26dd5c663178e1e8a643d78ac3f66bf200eecfa5df4abe77f`, oracle hash `fb7c14090c675377401733d9b53df939d5a141b264778c0d4d591e3a30207860`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json` SHA-256 `3063f874c03f042a109882c31417c1b6d92b841d5d551e2a5b4bf777f32b3930`, registry hash `56f1f0f3cc5ea00134a85b510844e4162c4ecb104474825f6316349933bee848`
- `tools/generate_d06_challenge_registry.py` SHA-256 `5484a6b2d27c8ca567a484d5bb6dbfa112c8f17e9d0e236521e8120e2e04f355`
- `context/medical_monitoring_r4_d06_contract_20260812_context.md` SHA-256 `ac643c49550a20d91e0459e7b89bf2d0221fb7a65624ae874c299fd890e7d419`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` SHA-256 `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`

Run `python3 tools/generate_d06_challenge_registry.py --check`, independently recheck every catalog/oracle/semantic/registry/manifest/fixture/DSL/audience hash and bijection invariant, then rerun the pass-12 counterexamples with local and enclosing hashes resealed:

1. Migrate all fixture scopes and consumed objects together to another subject/site/run/snapshot/cutoff. The exact canonical synthetic scope must reject the snapshot.
2. Replace an assessment item ID with a nonexistent ID, remove assessment/item source locators, change item parent/order/status/correction/content, or coordinate item value drift through evaluator inputs. Typed `AssessmentItemRecord` membership and the immutable fixture oracle must fail closed.
3. Mutate Journey/Query payload required fields, Chinese text, schema versions, unknown visible keys, nested/top-level suppression, validator/lexicon identity, validation state or visible-only paths. Independent schema, suppression and visible-path evaluation must reject coordinated self-reports.
4. Mutate case 1 coverage, L1/L2/L3, counts or clinical outcome contract and reseal catalog/DSL/manifests/registry. The separately persisted immutable expected-outcome oracle must reject. Then mutate and reseal the oracle itself; its generator-pinned hash must reject. Confirm the oracle hash is also bound into every manifest and the registry.

Also search for one new concrete semantic escape across these four repaired boundaries. A blocker requires a reproducible path/case, effect and minimum correction; generic future-hardening concerns do not block.

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
