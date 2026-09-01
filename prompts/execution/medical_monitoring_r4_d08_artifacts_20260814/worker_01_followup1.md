# D08 Worker 01 Follow-up 1: Complete Oracle Leaf Audit

Continue the same worker session. The independent Luna verifier rejected the
freeze because the test-side `audit_case` validates core clinical semantics
but not every frozen oracle leaf. Implement a complete independent exact-leaf
audit and close the false-positive mutation harness defect. This is a bounded
write task.

Read these files only:

- `AGENTS.md`
- `reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md`
- `reviews/medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_expected_outcome_oracle_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json`
- `tools/generate_d08_challenge_registry.py`
- `tests/test_d08_artifact_generator.py`
- `runs/review/medical_monitoring_r4_d08_contract_freeze_luna_20260814.md`
- `runs/review/medical_monitoring_r4_d08_contract_freeze_luna_followup1_20260814.md`
- `runs/execution/medical_monitoring_r4_d08_artifacts_20260814/audit_d08_oracle.py`

## Hard boundaries

- You may modify only:
  `tools/generate_d08_challenge_registry.py`,
  `tests/test_d08_artifact_generator.py`, and the generated
  `reviews/medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json`.
- Catalog, oracle and v0.6 contract are immutable; never rewrite them.
- Do not implement or import D08 runtime. Do not start services/8911, read real
  projects, product UI, medical-writing, or security surfaces.
- The generator must remain unable to derive or write oracle leaves.
- Test-side independent reconstruction may derive expected outputs from typed
  input and contract semantics, but must not call generator assembly or reuse
  registry/oracle expected-leaf payload as the source of truth.

Write exactly one output file:

`runs/execution/medical_monitoring_r4_d08_artifacts_20260814/worker_01_followup1.md`

Return the full execution handoff; the runner persists it. Do not write that
runner-owned report yourself.

## Required repair

1. Replace patch-by-patch coverage with an independent test-side reconstruction
   or validation that covers every key/value in `expected_leaf_set`,
   `expected_trace_leaf_set`, and `expected_source_leaf_set` for all 233 cases,
   including integrity, consume-only and cutoff early-return paths.
2. Add a deterministic mutation-sensitivity test: for every oracle case and
   every leaf, make a type-valid unequal mutation and prove the independent
   audit returns at least one discrepancy. The test must report escaping
   case/section/leaf triples exactly.
3. Preserve the existing clinical semantic checks (identity, temporal,
   waiver, propagation, cutoff, visibility, fanout, n-ary, ownership and
   Query/Journey); do not replace them with only a file hash or a digest copied
   from the oracle/registry.
4. Keep the previous fixes: catalog tamper must materialize at the consumed temp
   path and fail specifically with `D08ArtifactError` stale catalog hash;
   unexpected exceptions must not count as fail-closed.
5. Update generator/registry/test hash pins coherently after source changes.
   Catalog/oracle/contract hashes must remain unchanged.
6. Run generator, focused pytest, Ruff, compile, exact hash checks, a direct
   scan for forbidden oracle derivation/write/runtime imports, and verify 8911
   has no listener.

The task is not complete if any oracle leaf mutation still returns
`audit_case == []`, even when the pristine 233-case audit passes. If full
independent reconstruction cannot be justified from the contract and typed
input, return a precise blocker rather than weakening the gate.
