Same-session corrective contract review, pass 23. Review only the v1.17 validation-artifact erratum prompted by the rejected v1.16 implementation, and decide ACCEPT or REJECT.

Hard boundaries:
- Read-only inside this workbench. Do not edit files, start services, read real projects, medical-writing paths, product/R5 UI, unrelated implementation source/tests, or security paths.
- The runner owns the report; return the complete handoff and do not write it with tools.
- This is not implementation acceptance. Do not excuse a circular oracle/test path merely because the frozen artifacts agree with one another.

Output file:
Write exactly one output file: `runs/codex-subagent_medical_monitoring_r4_d06_contract_20260812_followup20.md`

Read these files only:
- `runs/codex-subagent_medical_monitoring_r4_d06_implementation_review_20260813.md`
  - SHA-256 `26e55fd5abcc43dca16508a51ebf4abf2f6aedd77dcf61a3489a1b9a102f4136`; use only its validation-circularity and 106/191 contradiction findings as the reason for this erratum.
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md` candidate SHA-256 `b40709f3836403b2c26cd089356cd3447fee9930948ef958b03ac678aca89862`
- `tools/generate_d06_challenge_registry.py` SHA-256 `d53c6cf509212a977f663cd5f2635761b7f81784379bcbe32ab18ef282125874`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json` SHA-256 `27dd45d4f17d4655be34711e6ad4d5a6b0c77871f0c01b8f8c53dee8ce19eb76`, catalog version `8.0.1`, catalog hash `c39f41950ae32bfb8c22ec4529a4de640145302d9b129431ee9de2ddb0a21a11`
- `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json` SHA-256 `87dba011bfc484437914e3eb3040284bf195d5b6f60df9b3b26b072ea9b6f245`, oracle hash `fc738b61cd5b4d73a32cb2a9c637b04c3752c27d89932df481add47a6ed762c4`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json` SHA-256 `cb739ffbb0d7a8536fb528f8a7daf21b787d36fd8ce3bc0269884fb617c7d131`, registry hash `c81eee74247ee0578a91ce871040409856162c41d8cff58acc4ec7cd94729158`

Required checks:
1. Recompute every supplied SHA and run `PYTHONDONTWRITEBYTECODE=1 python3 tools/generate_d06_challenge_registry.py --check`.
2. Confirm §1-§14 semantic SHA is exactly `50c631be3636af4076ac004ed308cf653697f712f21eb9ec6c956d0d1c4e9607`, is pinned in the generator, and the complete v1.17 draft bytes/preamble are pinned.
3. Confirm the new semantic rule requires `accepted_report_consistency` to consume complete typed `AcceptedMonitoringReportClaim` and `AcceptedIndividualTrendSource` objects with exact scope/endpoint/timepoint/content hashes and accepted result IDs. Shorthand `{"trend": ...}`, expected text, manifest-required traces, challenge number, fixture ID, test ID, or annotations must not qualify as evidence.
4. Inspect cases 106 and 191. Prove they no longer have identical substantive typed inputs after removing test-only identity/annotation surfaces. Case 106 must remain shorthand/no accepted-artifact provenance; case 191 must contain and bind the complete accepted report/source objects and may require `accepted_artifact -> result` only because runtime can actually consume them.
5. Search all 219 cases for duplicate substantive fixtures after removing challenge number and test-only identities. Explain every remaining duplicate group and verify no duplicate group has contradictory required trace sets or substantive expected outcomes. Expected benign group is 17/173 only; reject if another contradictory group remains.
6. Verify the oracle and DSL for case 191 use the new fixture hash and expected trace, and that catalog, oracle, manifests and registry all bind the new hashes bidirectionally.
7. Run at least these read-only negative checks in an isolated in-memory/temp copy without modifying workspace artifacts: replace case 191 typed report/source by the old shorthand and attempt coordinated local resealing; remove one required accepted-report field; change report/source scope or endpoint/timepoint; alter accepted_result_ids; inject accepted-artifact trace into case 106. Each must be rejected by the canonical snapshot/generator contract or must be shown unable to satisfy the new runtime semantic rule. Do not accept mere self-consistency as proof.
8. Confirm §15 accurately marks v1.16 implementation review rejection, v1.17 as a draft pending corrective review, and does not claim the old dialogue or old implementation was accepted.

Veto criteria:
- Any remaining pair of semantically identical typed inputs with contradictory required runtime traces/outcomes.
- Any route by which expected outcome text, oracle values, manifest-required traces, case/test identity or annotations can be copied into the raw evaluator result.
- Case 191 accepted-artifact trace is not derivable solely from full typed runtime-consumed report/source inputs.
- Hash, registry, scope, or semantic pin mismatch.

If any P0-P4 issue remains, say `VERDICT: REJECT`. Otherwise say exactly `VERDICT: ACCEPT`.

Acceptance is limited to this exact candidate synthetic/offline D06 v1.17 validation-artifact erratum. It authorizes parent Codex only to perform a controlled frozen-metadata transition and request one metadata-only same-session confirmation. It does not accept implementation, R4 overall, R5 UI, real projects, statistical analysis, products, medical writing, security or production.

Output schema:
1. `# Codex SubAgent Task: medical_monitoring_r4_d06_contract_20260812`
2. `## Boundary Check`
3. `## Work Performed`
4. `## Evidence And Observations`
5. `## Verification And Gaps`
6. `## Findings (P0-P4)`
7. `## Verdict`
8. `## Next Action For Parent Codex`
