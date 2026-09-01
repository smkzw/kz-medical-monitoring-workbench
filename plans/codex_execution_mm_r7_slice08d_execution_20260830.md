# Codex Execution Plan: mm_r7_slice08d_execution_20260830

Objective: 按冻结08D v0.1+v0.2合同完成三模式synthetic综合回归、独立oracle、15格确定性、故障恢复及相邻边界证据；不启动服务、不运行真实项目/模型、不触碰医学写作或08C视觉

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现冻结20格三模式synthetic矩阵与输入侧独立oracle，必要时仅修复被测试证明的最小连续性/桥接缺陷 | `runs/execution/mm_r7_slice08d_execution_20260830/worker_01.md` |
| `worker_02` | 实现5种hash seed乘3种优化级别确定性、真实PRAGMA busy_timeout、全故障钩子、CAS/重放/迟到回调恢复覆盖 | `runs/execution/mm_r7_slice08d_execution_20260830/worker_02.md` |
| `worker_03` | 执行固定相邻回归、公开中文边界、compileall、路径中性、医学写作保护和8911/5174停止证据，形成机器可读清单 | `runs/execution/mm_r7_slice08d_execution_20260830/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Pending worker completion. Codex will reopen all changed files, verify the 20 case keys and independent oracle, enumerate source fault hooks, run the combined deterministic/adjacent suite, inspect the machine-readable evidence, confirm 8911/5174 remain stopped and medical-writing unchanged, then request an independent 08D acceptance conference. No rendered/browser surface is required because 08D explicitly preserves rather than reopens accepted 08C visual work.
