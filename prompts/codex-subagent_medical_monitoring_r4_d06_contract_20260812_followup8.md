Same-session corrective review, pass 11. Review only the exact v1.9 snapshot and decide ACCEPT or REJECT.

Hard boundaries:
- Read-only inside this workbench. Do not edit files, start services, read real projects, medical-writing paths, product/R5 UI, or security paths.
- The runner owns the report; return the complete handoff and do not write it with tools.

Output file:
Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812.md`

Read these files only:
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md` SHA-256 `a87d9e23005010bb4c7151b7e93adfb46dddf3ea46d4b6e69dcb6400acb55047`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json` SHA-256 `650ee11a029fc08f998dae7227a0d7c492f75fbd0d176f76a7d0d90bd66240d3`, catalog hash `c628341ff4bf06643769602d5da38f0d8ded5fb8c777a5687defc61d5869acf5`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json` SHA-256 `d56ff96417d9513190f5246d8903444ab697ba619723bd8ce2242457a77bed83`, registry hash `0cb32f39497ff87046e3519b08a86cfb8a29eed1cbfa7c7b35daebe80baa7a2a`
- `tools/generate_d06_challenge_registry.py` SHA-256 `655609b9d5011eb51758df64803b26ff98f9cbc988cc6ffadbe361bf0cacfbe2`
- `context/medical_monitoring_r4_d06_contract_20260812_context.md`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` SHA-256 `8ad9d6ddd1df4da8a8c54877339cb30b9513c5c68e9b55ba5bc7ac2168ecfc03`

Run `python3 tools/generate_d06_challenge_registry.py --check`, independently recheck every hash/manifest/DSL/audience invariant, then rerun the pass-10 counterexamples with all local and enclosing hashes/DSL/catalog/manifests/registry resealed:

1. D05 fake unit/planned/actual activity must fail against `AcceptedD05AssessmentInventoryItem`, even if ref and FK are changed together. Also challenge source record type and the canonical four-record accepted set.
2. Maturity consumer drift must fail against the single typed `D06MaturityConsumerBinding`, including bidirectional decision ID, endpoint, timepoint, scope and spine.
3. Priority timepoint or reason-code drift must fail even when expected outcome is changed too. Exact outcome includes endpoint definition, stable endpoint/timepoint and reasons, and the resolver resolves frozen definitions plus precedence-step reason mapping.
4. Wrong object types for resolver, decision, risk binding, public identity and TTE binding must fail.
5. Public source/concept/temporal/rule drift must fail against `D06UnitStableCore`; the core itself must resolve accepted `ASM-W4-A`, endpoint/instrument/timepoint definitions, primary-subtype-to-unit-kind mapping and algorithm lineage.
6. Risk unit/risk drift must fail exact equality across priority decision, risk binding, public identity and stable core.
7. TTE target/competing event drift must fail against canonical typed event sources and the frozen rule, including coordinated record/registry/interpretation mutation.
8. Enrollment rule/version drift must fail against the independent canonical `EnrollmentDecisionRule` and exact active/variant outcome assertions.

Reproduce the earlier accepted mutations, not just the parent’s test shapes, and search for a new concrete semantic escape. A blocker requires a reproducible path/case, effect and minimum correction; generic future-hardening concerns do not block.

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
