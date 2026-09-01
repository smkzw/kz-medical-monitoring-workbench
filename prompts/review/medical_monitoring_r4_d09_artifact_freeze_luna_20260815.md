# D09 immutable artifact freeze review

You are an independent verifier in a fresh context. Review only; do not edit any file, start any service, run real projects, or access the medical-writing subsystem. The worker's reasoning and self-assessment are not acceptance evidence.

Workspace: current workbench directory.

Read these files only:

- `AGENTS.md`
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

- Read-only. Do not modify source, tests, artifacts, configuration, or state.
- Do not start services or access real projects, real data, models, product UI,
  security scope, or the medical-writing subsystem.
- Do not read files outside the exact list above.
- TCP 8911 must remain stopped.

Write exactly one output file:

`runs/review/medical_monitoring_r4_d09_artifact_freeze_luna_20260815.md`

The runner/parent persists it. Return the complete report only in your final
answer; do not write the report through file tools.

## Immutable snapshot

- Contract: `reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md`
  - SHA-256 `9d20b99487260c286e5105ba1d1de6fb4e4d5af3f9a3faaee5df2e67f0907e40`
- Typed fixture catalog: `reviews/medical_monitoring_r4_d09_typed_fixture_catalog_v1_20260814.json`
  - SHA-256 `3ac9e4157ed8682ed85ca1f54a93ba6589ffc0741878bb2f701db2d7753b3e48`
- Partition quota manifest: `reviews/medical_monitoring_r4_d09_partition_quota_manifest_v1_20260814.json`
  - SHA-256 `57e3a8ff735bd5f82c2ba82ce9745e5d5d99786cddafbcf61cb5ba883dff3786`
- Resolved challenge registry: `reviews/medical_monitoring_r4_d09_challenge_manifest_registry_v1_20260814.json`
  - SHA-256 `c4d2b1452ea23823c066fa8ff7fc9f8c29b9e4f9ebe1da2238b1243c3ba6851c`
- Expected-outcome oracle: `reviews/medical_monitoring_r4_d09_expected_outcome_oracle_v1_20260814.json`
  - SHA-256 `b5c937739493613d00abd92cbef24fddfd1c88ff230cb7150bde784bbcee53e4`
- Catalog/registry generator: `tools/generate_d09_challenge_registry.py`
  - SHA-256 `0c21104158f732ded33afc1a3531c7992704d2dbc429c67b00491addd2345ec5`
- Oracle generator: `tools/generate_d09_expected_oracle.py`
  - SHA-256 `ff6096de5b054e877f4076543bcab20a084136f8ed428221e03336099d6a8407`
- Freeze tests: `tests/test_d09_artifact_generator.py`
  - SHA-256 `b4e63b295f89f24eeb51d2775c3e07c3681c7aeb5ada0bed97a1f4940b776af5`

If any SHA differs at start or end, return `REVISE_D09_ARTIFACTS` and report snapshot drift.

## Acceptance questions

Independently inspect the contract, generators, tests, and representative/edge artifact rows. Run deterministic checks as needed. Decide whether all of the following are true:

1. Exactly 179 challenge cases form a complete, unique, bijective catalog/registry/oracle chain and satisfy every frozen partition minimum.
2. Expected leaves remain absent from catalog input and confined to the independent oracle; runtime/generator import-read closure does not leak oracle answers into catalog generation.
3. Every case disposition and every decisive count can be reconstructed from contract-authorized typed input with zero semantic skip tables, hidden oracle-side semantic tags, case-ID branching, free-text interpretation, or catalog disposition leakage.
4. The previously problematic cases 023, 024, 026, 028, 038, 047, 063, 067, 078, 085, 163, and 168 are encoded by explicit typed facts and produce contract-consistent outcomes.
5. Counterevidence, same-origin deduplication, integrity blocks, boundary/abstention, query suppression, mixed cutoff, unlistable-member, and design-clause-closed-zero semantics follow the frozen contract rather than ad-hoc oracle metadata.
6. Stage-A/stage-B registry resolution is fail-closed. `generator_hash` equals the frozen normalized generator pin and cannot be altered even when `content_hash` is consistently resealed. Only the declared stage-B delta is accepted.
7. Canonical JSON, NFC, finite-number, content/file hashes, deterministic double generation, input-order/display-name invariance, and mutation gates are real and sufficiently independent to detect drift.
8. D09 tests, D08 adjacency tests, both generator checks, and compile checks pass; TCP 8911 remains stopped.
9. No product runtime/UI/real-project/model/service or medical-writing scope was changed by this artifact-freeze slice.

## Required output

Return one of these exact first lines:

- `ACCEPT_D09_ARTIFACTS`
- `REVISE_D09_ARTIFACTS`

Then give concise, evidence-based findings: checks run, decisive observations, any defect with file/line/case locator, uncertainty, and whether the snapshot remained byte-stable. Do not repair files.
