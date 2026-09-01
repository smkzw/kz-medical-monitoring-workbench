# Execution context: R7 slice-01 ExecutionProfile persistence and Run binding

Task ID: `mm_r7_slice_01_execution_profile_run_binding_20260828`

Implement only the frozen contract in `context/medical_monitoring_r7_slice_01_execution_profile_run_binding_contract_20260828.md`.

## Hard boundaries

- Create files only under `poc/medical_monitoring_ai_native_r7/` plus runner-owned execution reports.
- Do not modify product services/frontend, runtime databases, medical-writing, real projects, R1-R6 source/tests/receipts, ports or processes.
- Do not invoke a real model/provider/harness, browser or OCR.
- Stdlib only; deterministic and fail closed.
- Do not claim final acceptance; Codex owns integration and acceptance.

## Work ownership

1. Worker 01 owns `src/mm_r7/profile_store.py` and `src/mm_r7/__init__.py`: immutable versioned profile-layer persistence and public/audit projections.
2. Worker 02 owns `src/mm_r7/run_binding.py`: deterministic effective-profile freeze and immutable Run binding/replay rules.
3. Worker 03 owns `tests/`, `README.md`, and `evidence/r7_execution_profile_run_binding_receipt.json`: contract-driven tests, nine-cell determinism, adjacent R6 checks and evidence.

Workers must coordinate through the frozen contract rather than editing each other's files. Runner reports must include exact commands, test counts, hashes, boundary evidence and unresolved defects.
