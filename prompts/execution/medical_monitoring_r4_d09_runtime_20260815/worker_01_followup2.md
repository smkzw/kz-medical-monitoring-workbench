Continue the same Worker 01 session for the second and final corrective pass.
The independent Luna verifier returned `REOPEN_D09_ARTIFACTS`: the prior frozen
artifact set was deterministic but not runtime-ready because 28/179 cases lack
explicit resolved domain facts. Correct the artifact schema and the clean
runtime together, then regenerate and prove non-circular 179/179 parity.

Read these files only:

- `context/medical_monitoring_r4_d09_runtime_worker01_overfit_correction_20260815.md`
- `runs/review/medical_monitoring_r4_d09_artifact_freeze_luna_followup2_20260815.md`
- `runs/execution/medical_monitoring_r4_d09_runtime_20260815/worker_01_followup1.md`
- `reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md`
- `tools/generate_d09_challenge_registry.py`
- `tools/generate_d09_expected_oracle.py`
- `reviews/medical_monitoring_r4_d09_typed_fixture_catalog_v1_20260814.json`
- `reviews/medical_monitoring_r4_d09_partition_quota_manifest_v1_20260814.json`
- `reviews/medical_monitoring_r4_d09_challenge_manifest_registry_v1_20260814.json`
- `reviews/medical_monitoring_r4_d09_expected_outcome_oracle_v1_20260814.json`
- `tests/test_d09_artifact_generator.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_contracts.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_evaluator.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d09_adapter.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d09_runtime_contract.py`

## Hard boundaries

- Synthetic/offline only. Do not start TCP 8911, any service, UI, real project,
  real data, model call, or medical-writing subsystem.
- The v0.5 contract is read-only and its SHA-256 must remain
  `9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40`.
- Do not edit package exports, D01-D08/R1-R3 files, implementation plans,
  context/review records, product/UI/service files, or runner-owned reports.
- Keep all new names clinical/domain-facing. Do not introduce answer flags,
  expected-disposition fields, case-specific switches, or synthetic test
  vocabulary into the typed catalog or runtime.
- A failing honest test is preferable to circular parity.

## Exact allowed write set

Frozen artifact corrective files:

1. `tools/generate_d09_challenge_registry.py`
2. `tools/generate_d09_expected_oracle.py`
3. `reviews/medical_monitoring_r4_d09_typed_fixture_catalog_v1_20260814.json`
4. `reviews/medical_monitoring_r4_d09_partition_quota_manifest_v1_20260814.json`
5. `reviews/medical_monitoring_r4_d09_challenge_manifest_registry_v1_20260814.json`
6. `reviews/medical_monitoring_r4_d09_expected_outcome_oracle_v1_20260814.json`
7. `tests/test_d09_artifact_generator.py`

Clean runtime files:

8. `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_contracts.py`
9. `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_evaluator.py`
10. `poc/medical_monitoring_ai_native_r4/tests/test_d09_adapter.py`
11. `poc/medical_monitoring_ai_native_r4/tests/test_d09_runtime_contract.py`

## Required additive domain facts

Add the smallest closed typed objects/fields that faithfully represent these
already-contracted decisions. Neutral defaults are required for all 179 cases;
only the affected fixtures receive non-default facts.

1. `resolved_authority_decision`
   - resolved `minimum_member_subject_count` (`int` or null)
   - closed authority validity state
   - authority and locator refs
2. `method_comparability_decision`
   - closed method-validity state
   - comparison/comparability state
   - statistical-signal role
   - member-expansion refs/state
   - window-rule-version refs
   - stratum-method-version refs
3. `lineage_context`
   - prior risk-instance ref and prior public identity ref
   - carry-forward state and lineage relation
   - site-identity continuity state
4. full `query_redundancy_decision`
   - closed decision enum
   - resolved maximum fanout
   - unit-member-set hash
   - covered and uncovered member refs
   - member Query refs
   - coverage-proof hash
5. producer source-verification records
   - revision, declared hash, verified hash, closed verification state
6. per-member source-locator resolution state and per-gap anchor-resolution
   state.

Reuse existing L1 completeness and `blind_status + stratum_key`; do not create
duplicate fields for those already-sufficient facts. Preserve subject/site/
study identity boundaries and the v0.5 medical semantics.

## Non-circular derivation requirements

- The oracle generator must not read `spec["mc"]`, mutation class/context,
  anti-overfit metadata, fixture/case/test identifiers, descriptions, display
  labels, expected leaves, synthetic locator/anchor sentinels, or synthetic
  revision-hash recipes for any semantic leaf, disposition, Query decision,
  handoff, supersession, deep link, or producer verification.
- The runtime evaluator must consume only explicit typed domain facts and must
  ignore audit/mutation metadata. The test adapter must not translate mutation
  metadata or sentinel spelling into replacement facts.
- Mutation metadata alone must be behavior-invariant. Mutating each new domain
  fact must either change the appropriate semantic result or fail closed.
- Strengthen artifact/runtime static tests so semantic mutation/sentinel/hash
  coupling fails immediately.
- Do not keep the prior 28-case allowance. Required final parity is exactly
  179/179 cases and 537/537 expected/trace/source leaf dictionaries, with zero
  skips, xfails, exception lists, pinned-gap allowances, or case-ID dispatch.

## Regeneration and verification

- Regenerate catalog, quota, registry and oracle deterministically; update all
  registry artifact hashes and the normalized catalog-generator self-pin.
- Run the updated D09 artifact suite and both generator check modes.
- Run D08 artifact adjacency (54-test baseline or current superset).
- Run D09 Worker01 focused tests, D08 runtime adjacency (186-test baseline or
  current superset), Ruff and `py_compile` on owned Python files.
- Run explicit static scans for all prohibited couplings.
- Verify the contract SHA is unchanged and TCP 8911 is stopped.
- Report final SHA-256 for every allowed-write file, exact parity totals,
  disposition distribution, test counts, and any residual uncertainty.

Write exactly one output file: `runs/execution/medical_monitoring_r4_d09_runtime_20260815/worker_01_followup2.md`

Return the complete seven-section execution report. Do not claim D09 accepted;
only Codex and the independent Luna verifier may re-freeze it. If exact clean
parity cannot be reached without violating these constraints, stop with the
smallest precise blocker and preserve the clean implementation.
