Continue the same Worker 01 session. Codex rejects the initial implementation;
45 passing tests and 179/179 parity are not acceptance because the runtime is
coupled to synthetic test intent.

Read these files only:

- `prompts/execution/medical_monitoring_r4_d09_runtime_20260815/worker_01.md`
- `runs/execution/medical_monitoring_r4_d09_runtime_20260815/worker_01.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_contracts.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_evaluator.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d09_adapter.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d09_runtime_contract.py`
- `reviews/medical_monitoring_r4_d09_center_pattern_slice_contract_v0_5_20260814.md`
- `reviews/medical_monitoring_r4_d09_typed_fixture_catalog_v1_20260814.json`
- `reviews/medical_monitoring_r4_d09_expected_outcome_oracle_v1_20260814.json`
- `reviews/medical_monitoring_r4_d09_challenge_manifest_registry_v1_20260814.json`
- `tools/generate_d09_challenge_registry.py`
- `tools/generate_d09_expected_oracle.py`
- `tests/test_d09_artifact_generator.py`

## Hard boundaries

- Keep the same four-file runtime write set. Do not edit frozen artifacts,
  generators, artifact tests, existing D01-D08/R1-R3 files, package exports,
  product/UI/services, real projects or medical-writing.
- Do not start TCP 8911 or any service. Synthetic/offline only.
- A failing honest test is preferable to a green overfitted adapter.

## Confirmed blocking defects

The current evaluator branches on `mutation_context.mutation_class` for Query
suppression, not-evaluable states, authority failure, carry-forward,
supersession and method/statistical outcomes. It also treats
`SYN-D09-LOC-MISSING`, the substring `UNKNOWN`, and
`sha256("d09-rev:<revision>")` as runtime domain semantics. These are synthetic
fixture/test conventions, not clinical/runtime facts. The current static test
misses them and the parity result is circular.

## Required correction and diagnostic

1. Runtime semantic modules must not read `mutation_context`,
   `anti_overfit_variant`, `mutation_class`, `base_fixture_id`, fixture/case/
   test identifiers, mutation descriptions, display labels or expected leaves.
   Audit metadata may be carried by a non-semantic envelope only if static
   tests prove evaluator/projection cannot access it.
2. Remove all synthetic sentinel/string/hash conventions from runtime
   semantics. Missing/unresolvable locator, anchor resolution, producer content
   verification, authority validity, method/comparability, Query redundancy/
   fanout, lifecycle prior-state/carry-forward, rule-method supersession and
   visibility decisions must be explicit closed typed facts with validated
   identities/refs, not inferred from identifier spelling or test metadata.
3. Audit every oracle-generator branch that reads `spec["mc"]` or mutation
   class. For each branch, identify the actual v0.5 contract object/field that
   should decide it and whether the current frozen catalog carries that fact.
   Produce a compact machine-readable or tabular gap matrix in the runner
   report: semantic decision, current improper trigger, required explicit
   typed fact, affected case count/IDs (evidence only), and whether existing
   non-mutation fields suffice.
4. Refactor the four owned runtime/test files so semantic code is clean. Do not
   translate mutation classes/sentinels into replacement flags in the test
   adapter; that would preserve the same circularity at another layer. Run the
   exact 179-case audit and report honest parity. If the accepted artifact is
   under-specified, leave exact failing cases/leaves and propose the smallest
   additive catalog schema correction. Do not fake parity.
5. Strengthen static closure tests to reject all listed couplings and generic
   synthetic sentinel decisions. Re-run focused tests, D08 adjacency,
   Ruff/compile and 8911 stopped check.

Write exactly one output file:

`runs/execution/medical_monitoring_r4_d09_runtime_20260815/worker_01_followup1.md`

The runner persists it. Return a complete seven-section report with exact
evidence, remaining failures, SHAs and the next safe action. Do not claim
Worker 01 complete unless semantic code is clean and parity is non-circular.
