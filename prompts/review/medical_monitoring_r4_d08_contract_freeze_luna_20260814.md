# R4-D08 Independent Contract Freeze Verification

You are the independent verifier for the medical-monitoring R4-D08 contract
freeze. Work in a fresh context. This is a read-only adversarial review: do not
write or modify any file. The only valid final verdict is
`ACCEPT_D08_CONTRACT` or `REVISE_D08_CONTRACT`, followed by concise exact
evidence and any reproducible blockers.

Read the complete workspace `AGENTS.md`. If its older routing text conflicts
with this assignment, keep this assignment's explicit Luna/max read-only
boundary. Never start a service or port 8911. Never access real projects,
patient data, medical-writing files, product UI, D08 runtime, or system-security
surfaces. Do not install anything.

Read these files only:

- `AGENTS.md`
- `reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md`
- `context/medical_monitoring_r4_d08_draft_artifact_build_acceptance_record_20260814.md`
- `reviews/medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_expected_outcome_oracle_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json`
- `tools/generate_d08_challenge_registry.py`
- `tests/test_d08_artifact_generator.py`
- `runs/execution/medical_monitoring_r4_d08_artifacts_20260814/worker_01.md`
- `context/medical_monitoring_r4_d07_oracle_erratum_decision_20260814.md`
- `tests/test_d07_artifact_generator.py`

## Hard boundaries

- Read-only. Do not modify any file.
- Do not start any service or listener, including port 8911.
- Do not read any file outside the exact list above.
- Do not access real projects, patient data, medical-writing files, product UI,
  D08 runtime, or system-security surfaces.
- Worker and parent reports are evidence to challenge, never authority.
- If a required conclusion cannot be established from this closed read set,
  return `REVISE_D08_CONTRACT` or state the exact residual uncertainty; do not
  broaden the read scope.

Write exactly one output file:

`runs/review/medical_monitoring_r4_d08_contract_freeze_luna_20260814.md`

The runner persists that file. Return the complete report only in your final
answer and do not write it yourself.

## Immutable review set

1. `reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md`
   expected file and full-NFC-LF semantic SHA-256
   `ff3d3a1bd9844ac8808ca7f9ada1466317763eb883e60d825f15bb3015ac4d64`.
2. `context/medical_monitoring_r4_d08_draft_artifact_build_acceptance_record_20260814.md`.
   This is artifact-build authorization only, not contract acceptance.
3. `reviews/medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json`
   expected file SHA `d3cd694bcbe63d977d5ef332be3647fb1274293be6ec364021946ee610ffa82c`,
   233 cases, internal hash
   `c9da16767f7441c105db4158a103606396d96c23ec29c44b652a46ce90bf0ac5`.
4. `reviews/medical_monitoring_r4_d08_expected_outcome_oracle_v1_20260814.json`
   expected file SHA `a40cbb509df2378804fd513a79467cbbc4e208d3b2b5c6f1a2410a63a12b8ac9`,
   content hash `724b95cb0964a4bdb992ba08655a4aff30983cb8d7454038fdbe269588f0b3d1`.
5. `reviews/medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json`
   expected file SHA `7c53cc2d694c0e0ca10d859f7fb27df95b5492a3c9229d8d34aef3840de2d915`,
   content hash `6e1ab6655712693ca93d000c7230c6f2aa038c85eddf0d9b09361b1ea16e3d12`,
   DSL hash `a99647c2f345ed4bc99624c6645fea5de5aebfbb9b1544d37b6043fe535b3acc`.
6. `tools/generate_d08_challenge_registry.py`, expected SHA
   `39f23fbdd5109523b2f7611d4bb5c55888aa3957e1aeab50e30d0553acaed3c5`.
7. `tests/test_d08_artifact_generator.py`, expected SHA
   `f6a0bef4ad7acfcdb4778c6c9066e4ac8e9fc61e837cad88f88f63b30deb33af`.
8. `runs/execution/medical_monitoring_r4_d08_artifacts_20260814/worker_01.md`
   as non-authoritative handoff evidence only.
9. `context/medical_monitoring_r4_d07_oracle_erratum_decision_20260814.md`.
   The current accepted D07 oracle file/content hashes are `c2c2c469...` and
   `e0e244d0...`; the obsolete assertion at
   `tests/test_d07_artifact_generator.py:945` must not redefine D07 state.

## Mandatory independent checks

- Compute all exact hashes before and after the review and reject any drift.
- Run `python3 tools/generate_d08_challenge_registry.py` and
  `python3 -m pytest -q -p no:cacheprovider tests/test_d08_artifact_generator.py`.
  Ruff and compile checks may also be run. These checks must not start a
  service.
- Prove the generator contains no path that derives expected leaves from
  `typed_input`, disposition, case specs or runtime; no oracle write path; no
  D08 runtime import. Confirm replay manifest is non-self-referential.
- Audit exact 16-key catalog cases, five-column bijection, family floors,
  owned versus consume-only boundaries, duplicate substantive-input
  consistency, anti-overfit, and all negative mutations.
- Manually inspect cases 179 and 198 plus representative cutoff, temporal
  direction, waiver covered-zero versus uncovered, correction/propagation,
  visibility, fanout, n-ary, owner-routing and Query/Journey audience
  projection cases.
- Decide whether the semantic verifier in the test file is genuinely
  independent of the generator rather than shared-logic self-certification.
- Confirm no listener on 8911.

Parent observations (D08 generator 233 cases and byte-identical replay; 14
mutations fail closed; D08 51 tests; D07 authoritative check; R1/R2/R3/R4
327/598/339/3657 tests) are evidence to challenge, not conclusions to copy.

Accept only if contract, catalog, oracle, registry, generator and tests are
self-consistent on one immutable snapshot, oracle independence and
anti-overfit are credible, and no reproducible contract-level ambiguity
remains. Otherwise return `REVISE_D08_CONTRACT` with the smallest reproducible
blocking defect.
