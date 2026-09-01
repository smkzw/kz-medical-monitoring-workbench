You are continuing the same `worker_04` execution session for task `medical_monitoring_r4_d02_cm_slice_20260811`. Codex rejected the initial matrix pass because cases 9 and 24 used substitute coverage gaps rather than the exact frozen challenge. Codex has now repaired the engine tri-state/order and updated the two worker-owned files. Review and finish the matrix against the current filesystem.

## Hard boundaries

- Work only inside the runner-provided current workspace root (`.`).
- Modify only `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm_fixtures.py` and `poc/medical_monitoring_ai_native_r4/tests/test_cm_challenge_matrix.py`.
- `cm.py`, `test_cm_slice.py`, projection/shared R4, R1/R2/R3, root exports, product/frontend/backend, medical-writing, real projects, services, providers, dictionaries, port 8911, task records, prompts, runs, logs, reviews, plans, context, and metrics are read-only.
- Runner-managed output file: `runs/execution/medical_monitoring_r4_d02_cm_slice_20260811/worker_04_round2.md`. Return the complete report in the final response; do not write that file with tools.

## Read these source files

- `reviews/medical_monitoring_r4_d02_cm_slice_contract_v1_20260811.md`
- `context/medical_monitoring_r4_d02_cm_slice_20260811_execution_context.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_cm_slice.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm_fixtures.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_cm_challenge_matrix.py`

## Required work

1. Verify case 9 now uses a confirmed treatment role but incomplete stable-treatment evidence and reaches not_evaluable because evidence is incomplete, not because the role or phase is unconfirmed.
2. Verify case 24 now combines an endpoint-inclusivity boundary with an unconfirmed rescue-role condition while study phase is confirmed, and the same restricted rule unit returns not_evaluable because the role coverage gap outranks the boundary.
3. Review all cases 1–30 against the literal frozen §12 item, not merely current engine output. Strengthen any test that only checks a seed/name/count where the numbered item requires an actual identity, lifecycle, Query, projection, cross-domain, L2, or tamper invariant. Do not create substitute scenarios.
4. Preserve and verify the new `stable_treatment_evidence_complete` tri-state semantics in fixture builders: complete+met => negative; incomplete => not_evaluable; complete+unmet => positive.
5. Run focused engine+matrix tests, full R4, Ruff/compile/import, adjacent R2/R3, accepted hash checks for files outside the Codex-authorized engine changes, and port 8911 no-listener. Report any literal §12 item that remains only partially proved; do not call it complete.

Do not claim acceptance; Codex owns Gate 4.
