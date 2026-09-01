Same-session corrective review, pass 12. Review only the exact v1.10 snapshot and decide ACCEPT or REJECT.

Hard boundaries:
- Read-only inside this workbench. Do not edit files, start services, read real projects, medical-writing paths, product/R5 UI, or security paths.
- The runner owns the report; return the complete handoff and do not write it with tools.

Output file:
Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812.md`

Read these files only:
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md` SHA-256 `51d5047b81521b69a7645768cc201d72fc3765ff91a104a0ae74269efd434183`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json` SHA-256 `2645916a77f97a6537af36d8170e2428037cc7aa2f2a78baa9763c19ca7a0372`, catalog hash `a331501b5dae97b753b6573c815f48d2940f209914fe86a14d3c633c81c68804`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json` SHA-256 `afb3ff67f11941e35dd8e56292e04ba948f9482059e961654fdd35fee122ab59`, registry hash `5f686ebd8333b6ebff21307cac5826661af2646d9b5a881cc397832a3adeef56`
- `tools/generate_d06_challenge_registry.py` SHA-256 `e6600ff9bc51ff50119196ce1e939e254984e315ef1f042448aa47649feb8787`
- `context/medical_monitoring_r4_d06_contract_20260812_context.md` SHA-256 `f305d90a989e8f0873a379011b94eb2f49d932181a5b42b1e04494ba900952bd`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` SHA-256 `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`

Run `python3 tools/generate_d06_challenge_registry.py --check`, independently recheck every catalog/semantic/registry/manifest/fixture/DSL/audience hash and bijection invariant, then rerun the pass-11 counterexamples with local and enclosing hashes/DSL/catalog/manifests/registry resealed:

1. Change an accepted D05 `ActualAssessmentRecord` to withdrawn/superseded, wrong subject/site/run/snapshot/cutoff, wrong object type, unresolved correction, or inconsistent assessment/stable/instrument/time/item/D05 activity/scope-decision identity. It must fail against the canonical four-record accepted inventory and full D06 scope.
2. Replace the full `D06PriorityPolicy` with an arbitrary but internally content-addressed policy; coordinate policy ID/version/hash through resolver, decision, expected outcome, object hashes and all enclosing hashes. It must fail against the exact canonical five-step full policy definition.
3. Add an extra/duplicate/unknown-path assertion clause or unknown operator, reseal DSL and all enclosing hashes. The persisted DSL must remain an exact one-clause-per-expected-leaf bijection with only `equals|is_null`, continuous clause IDs and canonical rule.
4. Change forbidden-language self-reports or add forbidden visible text/keys while coordinating expected audience result, DSL and enclosing hashes. The generator must independently recompute lexicon-ordered phrase hits and visible-key hits from the attempted audience payload or typed audience input, then require suppression.

Also search for one new concrete semantic escape across the complete typed source, full priority policy, exact DSL and independently evaluated audience boundary. A blocker requires a reproducible path/case, effect and minimum correction; generic future-hardening concerns do not block.

If any blocking P0-P4 remains, say `VERDICT: REJECT`. If none remains, say exactly `VERDICT: ACCEPT`. Acceptance is limited to this exact synthetic/offline D06 contract/catalog/registry snapshot and does not accept implementation, R4 overall, R5 UI, real projects, statistical analysis, product, medical writing or security.

Output schema:
1. `# Codex SubAgent Task: medical_monitoring_r4_d06_contract_20260812`
2. `## Boundary Check`
3. `## Work Performed`
4. `## Evidence And Observations`
5. `## Verification And Gaps`
6. `## Findings (P0-P4)`
7. `## Verdict`
8. `## Next Action For Parent Codex`
