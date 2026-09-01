# Worker 02 final same-session correction — R4-D02 CM engine

Resume the existing Worker 02 session. This is the second and final recovery pass.

## Hard boundaries

Work only inside the runner-provided workspace root. Modify only:

- `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_cm_slice.py`

Do not touch shared R4 contracts, D01, R1/R2/R3, product/frontend/backend, medical-writing, real projects, providers, dictionaries, services, or port 8911.
- Runner-managed output file: `runs/execution/medical_monitoring_r4_d02_cm_slice_20260811/worker_02_round3.md`. Return the report in the final response and do not write that file with tools.

## Read these source files

- `reviews/medical_monitoring_r4_d02_cm_slice_contract_v1_20260811.md`
- `context/medical_monitoring_r4_d02_cm_slice_20260811_execution_context.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_cm_slice.py`
- Shared R4 files only to verify their accepted hashes; do not modify them.

The round-2 implementation is not yet accepted. Make these bounded corrections:

1. Rule-unit phase gate must fail closed for every inconsistent or unconfirmed phase state. Only `study_phase_confirmed is True` plus a non-empty phase may proceed. Both `(confirmed=False, phase non-empty)` and `(confirmed=True, phase empty)` must be `not_evaluable`, not evaluation. Preserve confirmed phase outside `applicable_phases` as `not_applicable`.
2. Indication-check units must apply the same required-phase gate before they can become positive or negative. A missing, blank, or unconfirmed research phase is `not_evaluable`; do not create candidate, Query, or cross-domain ref. This follows frozen D02 §5.1/§5.2/§5.4: stage is a required, verifiable input.
3. Remove backend/internal token leakage from the user-facing unresolved-ingredient reason. The reason must be natural Chinese and must not include `ingredient_resolution`, `RiskCandidate`, `L1`, `formal fact` translations, `正式事实`, `候选信号`, `只读`, or `未知风险`. Internal structured fields may retain canonical identifiers.
4. Add deterministic tests for both inconsistent phase combinations on rule units, missing/unconfirmed phase on indication units, zero candidate/Query/ref for those indication gaps, and unresolved-ingredient user-language scanning.

Preserve all accepted round-2 corrections. Run focused `test_cm_slice.py`, full R4 tests, Ruff, compile/import, adjacent R2/R3 regressions, and verify shared accepted hashes remain unchanged. Return exact counts, hashes, commands, scope confirmation, and residual uncertainty. Do not claim Gate 2 acceptance; Codex owns acceptance.
