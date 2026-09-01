# Codex Execution Plan: mm_r7_slice_01_execution_profile_run_binding_20260828

Objective: Implement the frozen R7 slice-01 ExecutionProfile persistence and immutable Monitoring Run binding contract in the isolated R7 POC, with deterministic offline verification and no product/runtime/medical-writing changes.

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | Implement immutable versioned profile-layer persistence and projections in profile_store.py plus package initialization. | `runs/execution/mm_r7_slice_01_execution_profile_run_binding_20260828/worker_01.md` |
| `worker_02` | Implement deterministic effective-profile freeze and immutable Monitoring Run binding/replay rules in run_binding.py. | `runs/execution/mm_r7_slice_01_execution_profile_run_binding_20260828/worker_02.md` |
| `worker_03` | Implement contract-driven tests, nine-cell determinism, adjacent R6 protection, README and evidence receipt. | `runs/execution/mm_r7_slice_01_execution_profile_run_binding_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
