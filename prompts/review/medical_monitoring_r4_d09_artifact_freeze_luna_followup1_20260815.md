# D09 immutable artifact freeze review follow-up 1

Continue the same independent Luna/max verifier session. The prior verdict was
`REVISE_D09_ARTIFACTS`. Re-review the repaired immutable snapshot read-only;
do not accept worker or parent assertions without reproducing decisive checks.

Read these files only:

- `AGENTS.md`
- `runs/review/medical_monitoring_r4_d09_artifact_freeze_luna_20260815.md`
- `reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md`
- `reviews/medical_monitoring_r4_d09_typed_fixture_catalog_v1_20260814.json`
- `reviews/medical_monitoring_r4_d09_partition_quota_manifest_v1_20260814.json`
- `reviews/medical_monitoring_r4_d09_challenge_manifest_registry_v1_20260814.json`
- `reviews/medical_monitoring_r4_d09_expected_outcome_oracle_v1_20260814.json`
- `tools/generate_d09_challenge_registry.py`
- `tools/generate_d09_expected_oracle.py`
- `tests/test_d09_artifact_generator.py`
- `tests/test_d08_artifact_generator.py`
- `reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md`
- `reviews/medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_expected_outcome_oracle_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json`
- `tools/generate_d08_challenge_registry.py`

## Hard boundaries

- Read-only; do not modify any source, test, artifact, configuration or state.
- Do not start services or access real projects, real data, models, product UI,
  security scope, or the medical-writing subsystem.
- Do not read files outside the exact list above.
- TCP 8911 must remain stopped.

Write exactly one output file:

`runs/review/medical_monitoring_r4_d09_artifact_freeze_luna_followup1_20260815.md`

The parent persists it. Return the complete report only in your final answer;
do not write it through file tools.

## Repaired immutable snapshot

- D09 contract: `9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40`
- D09 catalog: `4c0ad3b8e5e63d2f9e03162d6f36fe19be024cb2ab1df87f8f279f36db1ee239`
- D09 quota: `e6fd75b512222fe0ee79845c0b1bb5248ef7f91b8197a3b1d99d3fee88bc7785`
- D09 registry: `23ae043f607aeb4de936fdf49f6afa4988055cee5083743484447f337948f9e6`
- D09 oracle: `b5c937739493613d00abd92cbef24fddfd1c88ff230cb7150bde784bbcee53e4`
- D09 catalog generator: `b5be914d1c0dd7740c586fcd04567c004f786c201ec2cfd2147568d70f11baeb`
- D09 oracle generator: `ff6096de5b054e877f4076543bcab20a084136f8ed428221e03336099d6a8407`
- D09 tests: `bdaf3d2e0842842003e28658a9b0776a02a9cc1156168fb5cca0ff0cbee1ad8a`

If any hash differs at start or end, return `REVISE_D09_ARTIFACTS`.

## Required re-review

1. Confirm CASE-047 now admits both D01 and D08 member risk kinds, preserves
   contract-authorized D08 membership and verified same-origin deduplication
   2/2/2, and contains no production case-ID branch.
2. Confirm the invariant is general across all 179 cases and the generator's
   real `validate_catalog` / `validate_typed_input` path rejects an unlisted
   member risk kind after a consistent catalog reseal. A test-only helper is
   not sufficient.
3. Re-run the complete D09 suite (expected 96), D08 adjacency suite (expected
   54), both D09 generator checks, compile checks and 8911 stopped check. The
   expanded read set now includes every D08 dependency needed by the suite.
4. Reconfirm the original nine acceptance questions: 179-case bijection and
   quota floors; oracle isolation; 179/179 disposition/count reconstruction
   without hidden tags, skips, case IDs, free text or catalog disposition;
   named edge-case semantics; fail-closed stage-A/stage-B hashes and deltas;
   canonical/hash/determinism/invariance/mutation gates; and no product,
   runtime, UI, real-project, model, service or medical-writing changes.
5. Record start/end hashes and explicitly state whether the snapshot stayed
   byte-stable.

Return exactly one of these first lines:

- `ACCEPT_D09_ARTIFACTS`
- `REVISE_D09_ARTIFACTS`

Then provide concise evidence and any residual boundary. Do not repair files.
