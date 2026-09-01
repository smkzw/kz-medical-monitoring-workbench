Continue the same independent D06 contract-review session. Do not edit files. This is pass 7 and a veto review, not implementation.

Hard boundaries:
- Read-only review inside the current workbench.
- Do not modify files, start services, use real projects, or inspect medical-writing paths.
- Runner-managed output path: `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812.md`. Do not write it with tools; return the complete report and let the runner persist it.

Read these files only:
- `context/medical_monitoring_r4_d06_contract_20260812_context.md`
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json`
- `tools/generate_d06_challenge_registry.py`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`

First verify the exact current artifacts and run `python3 tools/generate_d06_challenge_registry.py --check`:
- contract file SHA-256 `88fb2e12b71fb9541e0a9b8cb2c286718738f78296819f58a4d4bf3a29acc37e`
- contract semantic hash `ee2463a97fd76d39365e96379afd32ff6d5fa6910df6fd767418658bf8e7c647`
- typed catalog hash `c7eb9e3d28926e502efade0075c78d5d4f4850d7f4ceb4d1c0f929f9aff4fdbe`
- typed catalog file SHA-256 `53158873c15c52228edd9f00dce837ee6c60ee66f5ea344e0904b10960003a9d`
- registry hash `9798016c4ae0997814087c2b898264a8366d595400109ed7a54a6c02a9140ad9`
- registry file SHA-256 `43e765d74e76156b26d22893d7126c54dbbb7f98e02f89b2416b1a3e90b22a19`
- R4 matrix SHA-256 `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`

Re-test pass-6 F-01 through F-05 and detect any new P0-P4 defect. In particular:
- confirm the exact byte anchor now matches;
- determine whether the separate catalog contains concrete typed synthetic scope, definitions, records, bindings, policies and per-case values for all 218 cases, with no generator inference from Markdown prose;
- verify catalog/registry/row/test bijection and immutable hashes;
- inspect samples 1, 4, 35, 59, 69, 108-110, 141-146, 163, 176, 183, 195-196, 204, 214-218 for field-level exact expectations;
- verify TTE precedence binding, TTE boundary interpretations, ICE/estimator scope, enrollment Query scope, and audience exact lexicon hits plus payload suppression;
- reject any outcome-dependent callback, generic assertion-code-only acceptance, optional-field loophole, or wrong-scope join.

For every remaining finding give exact section/line or catalog/manifest number, a concrete counterexample, impact, and minimum correction. If no blocking P0-P4 remains, say exactly `VERDICT: ACCEPT`; otherwise `VERDICT: REJECT`. Acceptance remains limited to this synthetic/offline D06 contract, typed catalog and registry. It does not accept implementation, R4 overall, R5 UI, real projects, statistical analysis, product, or medical writing.

Return the same compact report schema and preserve the current session identity.
