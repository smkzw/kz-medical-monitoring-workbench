You are the implementation worker inside a Codex-controlled workflow.

First, fully read and comply with `/Users/smkzw/.hermes/SOUL.md`. In your final handoff, state whether you read the full file; do not claim this unless true.

Hard boundaries:
- Work only inside the runner-provided workbench working directory.
- This is an authorized edit round, but writes are limited to `poc/medical_monitoring_ai_native_r4/src/mm_r4/`, `poc/medical_monitoring_ai_native_r4/tests/`, and `poc/medical_monitoring_ai_native_r4/README.md`.
- Do not change the frozen D06 contract, catalog, oracle, registry, generator, R1-R3 packages, any product/frontend/service surface, any real-project path, medical-writing path, or security implementation/test.
- Do not start 8911 or any service, run real projects/data/providers, install packages, or perform browser/UI work.
- The runner owns `runs/pi_medical_monitoring_r4_d06_implementation_20260813.md`; never write it with tools. Return a complete compact handoff and let the runner persist it.
- Preserve all unrelated current changes. There is no git root at the workbench; use explicit before/after paths and hashes instead of git claims.

Output file:
Write exactly one output file: `runs/pi_medical_monitoring_r4_d06_implementation_20260813.md`

Read these authoritative files completely before editing:
- `context/medical_monitoring_r4_d06_implementation_20260813_context.md`
- `reviews/medical_monitoring_r4_d06_efficacy_slice_contract_v1_20260812.md`
- `context/medical_monitoring_r4_d06_contract_acceptance_record_20260813.md`
- `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json`
- `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json`
- `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json`
- `tools/generate_d06_challenge_registry.py`
- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md`
- `poc/medical_monitoring_ai_native_r4/README.md`
- Existing D05 architecture and shared contracts in `poc/medical_monitoring_ai_native_r4/src/mm_r4/` and their focused tests. Read only files needed to follow their public-contract, hashing, coverage, Query, lifecycle and projection patterns.

Task:
Implement the frozen synthetic/offline R4-D06 efficacy endpoint, scale, baseline, timepoint, individual-trend, Query and renderer-neutral Patient Journey slice. Choose the smallest coherent module split consistent with D05, expected to include D06 domain/evaluator/projection/fixture modules, focused tests, root exports and README documentation.

Non-negotiable implementation semantics:
1. Runtime code derives every result from typed input plus frozen rules. Runtime/evaluator/projection code must not import/load the catalog, oracle, registry or challenge metadata, and must never branch on `challenge_number`, `fixture_id`, `test_id`, expected text or expected outcome. No lookup table from case identity to answer.
2. Define immutable typed objects and deterministic content identities for canonical scope, versioned endpoint/scale/component definitions, assessment/item records, baseline/timepoint/ICE/TTE bindings, D05 temporal spine/assessment producer refs, evaluation stable core, priority decision, risk binding/public identity, and trace edges. Enforce exact project/run/subject/site/episode/cutoff/version identity and fail closed on unresolved or conflicting authority.
3. Implement applicability and gate handling before medical expected-set formation; five exclusive L1 dispositions; deterministic score/component/baseline/change/response/composite/repeat/rater-mode/trend/reported-result checks; TTE event/censor ambiguity; no invented values, imputation, favorable interpretation, group comparison or statistical inference.
4. Implement the frozen first-match priority policy and typed decision linkage. Positive units may create one D06 risk/Query according to contract; negative/not-applicable/not-evaluable accounting must remain independent. `not_evaluable` creates a coverage notice, never a Query. Do not duplicate D05 occurrence/timing, D07 safety, D08 cross-domain or D10 aggregation ownership.
5. Generate native Chinese three-part Query drafts with exactly `依据：` / `发现：` / `行动项：`. PD-assessment wording is permitted only for the accepted enrolled/post-enrollment typed context. Do not send or track Query replies.
6. Provide renderer-neutral efficacy Patient Journey projection with an explicit visit axis, distinct efficacy/scale/response/trend lanes, typed event and risk markers, source jump targets, risk anchors, and separate pending/out-of-cutoff areas. Never collapse into “已记录事项” or expose internal terms such as “正式事实”“候选信号”“只读”“positive”“candidate” to the user.
7. Implement audience payload schemas/validation from the contract. Invalid schema, forbidden wording, missing Chinese text, invalid source jump, or failed validation must suppress the payload.
8. Make all 219 frozen catalog rows executable through real D06 entrypoints (`efficacy_evaluator`, `gate_evaluator`, `contract_schema_validator`, `audience_projection_validator`, `challenge_registry_validator`) and compare actual outputs with the independently persisted oracle/DSL on the test side. Each row needs a named, non-tautological assertion; reject static/literal/no-op callbacks, unconsumed assertions, trace/hash drift and altered immutable inputs.
9. Public exports must be object-identical, unique and non-breaking. Existing D01-D05 behavior and frozen R2/R3 behavior must remain unchanged.

Verification to run with `PYTHONDONTWRITEBYTECODE=1` and pytest cache disabled:
- New D06 focused tests, including all 219 challenge rows and deterministic replay.
- Full `poc/medical_monitoring_ai_native_r4/tests`.
- Frozen R2 and R3 suites using their existing local commands/conftest conventions; do not edit them.
- Focused Ruff E/F if an existing Ruff executable is available; do not install one.
- `compileall` without leaving bytecode, import/root-export identity and uniqueness checks.
- `python3 tools/generate_d06_challenge_registry.py --check` to prove frozen inputs did not change.
- Confirm port 8911 is not listening and remove only task-created `__pycache__`, `.pyc`, `.pytest_cache`, `.ruff_cache` under R4.

Stop and report rather than weakening the contract if the immutable catalog/oracle cannot be implemented without contradiction. Do not claim acceptance; Codex and a fresh-context verifier own acceptance.

Final handoff schema:
1. `# Implementation Handoff: medical_monitoring_r4_d06_implementation_20260813`
2. `## Boundary Check`
3. `## Sources Read`
4. `## Files Changed`
5. `## Implementation Summary`
6. `## Verification Evidence`
7. `## Failed Paths And Remaining Gaps`
8. `## Exact Snapshot Hashes`
9. `## Next Action For Codex`
