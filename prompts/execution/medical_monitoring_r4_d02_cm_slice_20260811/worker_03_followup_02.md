You are continuing the same `worker_03` execution session for task `medical_monitoring_r4_d02_cm_slice_20260811`. This is the second and final recovery pass. Gate 3 remains unaccepted because independent review found two remaining temporal-anchor defects. Repair only these defects.

## Hard boundaries

- Work only inside the runner-provided current workspace root (`.`).
- Modify only `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm_projection.py` and `poc/medical_monitoring_ai_native_r4/tests/test_cm_projection.py`.
- Shared R4 files, `cm.py`, R1/R2/R3, root exports, product/frontend/backend, medical-writing, real projects, services, providers, dictionaries, port 8911, task records, prompts, runs, logs, reviews, plans, context, and metrics are read-only or out of scope.
- Runner-managed output file: `runs/execution/medical_monitoring_r4_d02_cm_slice_20260811/worker_03_round3.md`. Return the complete report in the final response; do not write that file with tools.

## Read these source files

- `reviews/medical_monitoring_r4_d02_cm_slice_contract_v1_20260811.md`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm.py`
- `poc/medical_monitoring_ai_native_r4/src/mm_r4/cm_projection.py`
- `poc/medical_monitoring_ai_native_r4/tests/test_cm_projection.py`

## Required corrections

1. `_is_full_day` / `_to_date` must accept only an exact canonical `YYYY-MM-DD` string. Do not slice the first ten characters: values such as `2026-01-03junk`, timestamp suffixes, whitespace inside the value, or other trailing content are not full-day endpoints and must take the fail-closed fallback. Leading/trailing outer whitespace may be stripped. Add adversarial tests.
2. For `ongoing=True` with a valid explicit `cutoff`, compute the real overlap using the cutoff as the effective CM end. The risk marker's overlap anchor must be the deterministic date intersection with the rule window (for example CM start before rule start, cutoff after rule end => rule start through rule end), not always `持续中`. Only ongoing without a valid cutoff remains fail-closed/non-fabricated and may use `持续中`. Add exact tests for both valid-cutoff and missing-cutoff paths.
3. Preserve every accepted round-2 correction and keep focused/full/Ruff/compile/import/adjacent regression green.

Run focused projection tests, CM engine tests, full R4, `python3 -m ruff`, compile/import, adjacent R2/R3, shared hash checks, and port 8911 no-listener check. Return exact counts, hashes, scope confirmation, and residual uncertainty. Do not claim Gate 3 acceptance; Codex owns acceptance.
