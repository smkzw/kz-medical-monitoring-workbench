You are continuing the same `worker_04` execution session for task `medical_monitoring_r4_d02_cm_slice_20260811`. This is the second and final recovery pass. Codex rejects the claim that all 30 literal challenges are fully proved. Perform an evidence-honest gap audit and strengthen only what your two-file write boundary can genuinely prove.

## Hard boundaries

- Work only inside the runner-provided current workspace root (`.`).
- Modify only `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm_fixtures.py` and `poc/medical_monitoring_ai_native_r4/tests/test_cm_challenge_matrix.py`.
- Engine/projection/shared R4, R1/R2/R3, root exports, product/frontend/backend, medical-writing, real projects, services, providers, dictionaries, port 8911, task records, prompts, runs, logs, reviews, plans, context, and metrics are read-only.
- Runner-managed output file: `runs/execution/medical_monitoring_r4_d02_cm_slice_20260811/worker_04_round3.md`. Return the complete report in the final response; do not write that file with tools.

## Read these source files

- `reviews/medical_monitoring_r4_d02_cm_slice_contract_v1_20260811.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm_fixtures.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_cm_challenge_matrix.py`
- Relevant public lifecycle/cross-domain contracts read-only.

## Required audit and proof

1. Case 9 literal item contains two branches: two versioned evidence-supported stable/new-start interpretations => boundary; missing stable evidence => not_evaluable. Prove both, or explicitly report the missing engine input/model.
2. Case 14 must establish an old risk and then evaluate a different medication and/or rule for the same subject, proving it neither maintains nor closes that old risk. Mere different identity ids and a candidate-free negative are insufficient.
3. Cases 17/26 must start from two actual versioned competing identity bindings for the same source/stable risk core. Directly calling `mark_identity_ambiguous` on a single-binding risk is only a lifecycle guard test, not proof that competing bindings are detected. If the current public engine cannot represent competing alternatives, report the exact missing contract instead of claiming coverage.
4. Case 25 must change ordinary snapshot/revision/full locator or non-identity data while holding stable event/core and lineage fixed, then prove identity continuity. Same-input replay alone is insufficient.
5. Case 27 must exercise active-mapping plus D02-handoff dual-path dedup by the frozen tuple `(table_semantic, record_id, evidence_role, content_hash)`, including unchanged claim dedup and changed claim new record. Hash equality alone is necessary but insufficient. If the consumer/dedup adapter does not exist, report it as partial.
6. Recheck cases 15/16/18/30 for literal history immutability, supersede-not-resolve, complete Query/projection joins, and D01 224 + neutral/tamper contract; strengthen where possible.
7. Return a table for all 1–30 with status `FULL`, `PARTIAL`, or `BLOCKED_BY_ENGINE_CONTRACT`, evidence test names, and exact gap. Do not state no gaps unless every literal branch is executable.

Run focused matrix+engine, full R4, Ruff/compile/import, adjacent R2/R3 and port check. Do not claim Gate 4 acceptance; Codex owns acceptance.
