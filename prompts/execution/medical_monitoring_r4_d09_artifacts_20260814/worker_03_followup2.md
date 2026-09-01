Continue the same Worker 03 session. The fresh Luna/max freeze verifier returned
`REVISE_D09_ARTIFACTS` on the post-followup snapshot. Repair only the confirmed
CASE-047 whitelist defect and its missing invariant test; do not broaden scope.

Read these files only:

- `prompts/execution/medical_monitoring_r4_d09_artifacts_20260814/worker_03.md`
- `prompts/execution/medical_monitoring_r4_d09_artifacts_20260814/worker_03_followup1.md`
- `runs/execution/medical_monitoring_r4_d09_artifacts_20260814/worker_03_followup1.md`
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

## Hard boundaries

- The only write set is the six D09 generator/artifact files and
  `tests/test_d09_artifact_generator.py` already authorized in the original
  assignment.
- Do not touch D08 files, runtime, UI, medical-writing, real projects, models,
  services, security scope, or TCP 8911.
- Keep the frozen contract SHA unchanged. Do not weaken schemas, oracle
  isolation, hash pins, mutation gates, zero-skip reconstruction, or the
  fail-closed stage-A/stage-B registry contract.
- Preserve the corrected `verify_resolved_registry` documentation: the
  generator hash must equal the frozen stage-A generator pin.

## Required correction and proof

1. Correct `D09-CASE-047` so every `subject_risk` member's `risk_kind`,
   including the two D08 `d08_cross_domain_relation` members, belongs to that
   case's `pattern_definition.accepted_member_risk_kinds`. The encoding must
   remain contract-authorized and keep the intended verified same-origin
   deduplication result 2/2/2.
2. Add a general invariant test across all 179 cases: every typed
   `subject_risk` member risk kind is accepted by its case definition. Include
   a focused CASE-047 assertion and a mutation that proves an unlisted member
   risk kind is rejected by the verifier or test oracle. Do not special-case
   the case ID in production generation logic.
3. Regenerate only derived D09 artifacts and all affected pins. Confirm that
   catalog/oracle/registry remain bijective and that every disposition and
   decisive count is still independently reconstructed from typed input with
   zero skip tables.
4. Run the complete D09 artifact tests, D08 adjacency tests, both D09 generator
   checks, compile checks, exact SHA/canonical checks, and the TCP 8911 stopped
   check. Record exact counts and the final immutable SHA set.

Write exactly one output file:

`runs/execution/medical_monitoring_r4_d09_artifacts_20260814/worker_03_followup2.md`

The runner persists it. Return a compact complete report with sources read,
changes, commands/results, final SHAs, uncertainty, and next action.
