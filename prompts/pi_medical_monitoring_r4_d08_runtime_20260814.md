# D08 Synthetic/Offline Runtime Implementation

You are the bounded finite-code executor. Read the complete workspace
`AGENTS.md` and `/Users/smkzw/.hermes/SOUL.md`; report whether each was read in
full. Implement the accepted D08 runtime, not a plan.

Read these files only:

- `AGENTS.md`
- `context/medical_monitoring_r4_d08_runtime_20260814_context.md`
- `context/medical_monitoring_r4_d08_contract_final_acceptance_20260814.md`
- `reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md`
- `reviews/medical_monitoring_r4_d08_typed_fixture_catalog_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_expected_outcome_oracle_v1_20260814.json`
- `reviews/medical_monitoring_r4_d08_challenge_manifest_registry_v1_20260814.json`
- `tests/test_d08_artifact_generator.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/__init__.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_safety.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_safety_evaluator.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_fixtures.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_query.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_journey.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d07_runtime_contract.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d07_challenge_matrix.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d07_mutation_suite.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d07_query_journey.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_d07_replay.py`

## Hard boundaries

- Modify only new D08 modules under `poc/medical_monitoring_ai_native_r4/src/mm_r4/`, D08 root exports in `src/mm_r4/__init__.py`, and new `poc/medical_monitoring_ai_native_r4/tests/test_d08_*.py` files.
- Frozen contract/catalog/oracle/registry and `tests/test_d08_artifact_generator.py` are immutable. Accepted D01-D07 code/tests are immutable.
- Runtime code must not import or read acceptance artifacts, generator, tests, or identifiers matching case/fixture/oracle/manifest/test IDs. No expected-leaf payload or case-specific branch may appear in runtime.
- Test-only fixture/adaptation code may read frozen artifacts. Runtime receives typed objects only.
- No services, 8911, real projects/data/models/providers, frontend/product, medical-writing, D09/D10, R5 or security work. No dependencies or package installation.
- Use `/Users/smkzw/.local/bin/skim --mode=structure` for initial code reconnaissance, then read exact critical bodies raw. Keep output compact but retain exact evidence.

Write exactly one output file:

`runs/pi_medical_monitoring_r4_d08_runtime_20260814.md`

The runner persists it. Return the complete execution handoff; do not write the
runner-owned report yourself.

## Required implementation

1. Add typed D08 contract/validation definitions, a deterministic evaluator,
   test-only frozen fixture adapter, and renderer-neutral audience projection.
   Prefer the smallest coherent module split; do not mechanically copy D07.
2. Match all 233 frozen oracle expected/trace/source leaves exactly through a
   test-only adapter. Integrity first-failure paths emit no medical/risk/Query/
   Journey payload. Runtime must be semantically driven and invariant to case
   IDs, surface renames and order-insensitive input ordering.
3. Cover explicit-link resolve, reverse cardinality, stable identity and
   duplicate semantics, cutoff precedence, six temporal relations and missing
   precision/timezone, propagation/correction lineage, visibility, n-ary
   relation instances, fanout/routing gates, producer coverage and waiver
   closure.
4. For D08-owned positive outcomes, project affected domains/source jumps,
   risk marker and a natural Chinese three-part Query draft containing
   `依据`/`发现`/`行动项`. Do not label PD; D04 owns PD wording. Negative,
   boundary, not-applicable, not-evaluable, integrity and consume-only paths
   must project exactly as contracted.
5. Add focused contract, 233-case challenge, negative mutation, replay/order/
   anti-overfit and Query/Journey/source-visibility tests. Add AST/static tests
   proving runtime independence from frozen acceptance artifacts and IDs.
6. Export the public D08 API from `mm_r4.__init__` without changing earlier
   exports.
7. Run focused D08 tests, full R4 tests, R1-R3 tests, scoped Ruff/compile, exact
   frozen-input hash checks and 8911 listener check. Do not weaken tests or
   mutate the oracle to make runtime pass.

If the frozen oracle cannot be implemented without ambiguity, stop with the
smallest reproducible case and contract conflict. Otherwise finish the code,
tests and verification in this same session.

Handoff sections: boundary check; files changed; architecture; exact checks and
counts; failed attempts/repairs; residual risks; Codex-owned verification.
