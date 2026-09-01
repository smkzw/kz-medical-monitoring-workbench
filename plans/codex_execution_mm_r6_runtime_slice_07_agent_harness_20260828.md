# Codex Execution Plan: mm_r6_runtime_slice_07_agent_harness_20260828

Objective: 实现并验证 R6 slice-07 ExecutionProfile 与 OMP Agent Harness adapter，默认 MTPLX Qwen3.8 medium，显式支持 DeepSeek V4 Flash max，保持产品服务、医学写作和真实项目不变

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现 profile registry、分层冻结、别名映射和确定性 identity | `runs/execution/mm_r6_runtime_slice_07_agent_harness_20260828/worker_01.md` |
| `worker_02` | 实现 OMP print adapter 的 catalog、preflight、argv、invoke、receipt 与 coverage fail-closed | `runs/execution/mm_r6_runtime_slice_07_agent_harness_20260828/worker_02.md` |
| `worker_03` | 实现离线验收矩阵、两条受控真实模型 smoke 证据和相邻保护检查 | `runs/execution/mm_r6_runtime_slice_07_agent_harness_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
