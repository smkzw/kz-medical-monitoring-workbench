# Codex Execution Plan: mm_r7_slice08a_continuity_foundation_20260829

Objective: 按已冻结 Slice-08 v0.1+v0.2 实现 08A synthetic/offline continuity 领域对象、最小 v2→v3 additive migration、计划持久化/校验及确定性/故障矩阵；保持 R2 唯一风险生命周期，复用既有 ResultPublication，不改 UI、不运行真实项目或服务。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现 poc/medical_monitoring_ai_native_r7/src/mm_r7/continuity.py 及聚焦测试：DecisionBaseline、CarryForwardPlan/Item、RiskChangeKind、逐对象处置、规则作用域、缺行不自动关闭、canonical digest；不得改 launch_registry 或 UI。 | `runs/execution/mm_r7_slice08a_continuity_foundation_20260829/worker_01.md` |
| `worker_02` | 实现 launch_registry.py v2→v3 最小 additive migration 与 continuity plan/item 持久化、staging→verified 状态门、事务/故障回滚、close/reopen；补聚焦迁移/存储测试；不得接 UI 或真实模型。 | `runs/execution/mm_r7_slice08a_continuity_foundation_20260829/worker_02.md` |
| `worker_03` | 独立构建/执行 08A 合同验证：三模式基线、对象处置、R2/R7边界、artifact 元数据 fail-closed、9-cell determinism、migration fault/retry、相邻回归；只修复本切缺陷并输出 compact handoff。 | `runs/execution/mm_r7_slice08a_continuity_foundation_20260829/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
