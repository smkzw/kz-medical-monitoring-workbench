# Codex Execution Plan: medical_monitoring_r5_s1_20260818

Objective: 实现并独立验收 R5 S1：exact typed contracts/canonical hash、只读 R4 authority adapter/receipt、真实 S1 challenge tests 与 immutable R4 SHA gate；仅写 poc/medical_monitoring_ai_native_r5 和本任务记录，不启动 8911

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | W1_exact_typed_contracts_and_canonical_hash | `runs/execution/medical_monitoring_r5_s1_20260818/worker_01.md` |
| `worker_02` | W2_r4_authority_adapter_and_receipt | `runs/execution/medical_monitoring_r5_s1_20260818/worker_02.md` |
| `worker_03` | W3_real_s1_challenge_tests_and_r4_sha_gate | `runs/execution/medical_monitoring_r5_s1_20260818/worker_03.md` |
| `worker_04` | W4_independent_acceptance_evidence | `runs/execution/medical_monitoring_r5_s1_20260818/worker_04.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

- W1 and W2 use disjoint implementation/test files and may run concurrently.
- W3 starts only after W1/W2 terminal outputs and Codex integration review.
- W4 is read-only and starts only after the implementation/test snapshot is frozen.
- Codex verifies exact object/enum coverage, canonical hash recipes, R4 read-only SHA gate, all 16 S1 challenge locators, focused/full R5 tests, selected R4 adjacent tests, compile/static forbidden-branch scan and 8911 stopped.
- Fresh isolated stage reviewer must return `ACCEPT_R5_S1` before S2 is unlocked.
