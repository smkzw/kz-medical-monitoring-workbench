# Codex Execution Plan: mm_r7_slice09a_execution_20260830

Objective: 实现冻结的 R7 Slice-09A synthetic/offline 项目备份、导出、预检、恢复、进度和原子回滚能力，并完成独立验证与相邻回归。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现 stdlib-only maintenance gate、deterministic mmbackup、operation ledger、preflight、restore/rollback core 与聚焦测试。 | `runs/execution/mm_r7_slice09a_execution_20260830/worker_01.md` |
| `worker_02` | 把 09A core 最小接入 R7 产品路由和实际产品/后台写边界，完成五个中文 DTO 路由及聚焦测试。 | `runs/execution/mm_r7_slice09a_execution_20260830/worker_02.md` |
| `worker_03` | 建立独立 oracle 与 adversarial matrix，覆盖确定性、闭包、损坏、身份、重放、writer race、切换/回滚和 reopen 对账，并运行相邻回归。 | `runs/execution/mm_r7_slice09a_execution_20260830/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
