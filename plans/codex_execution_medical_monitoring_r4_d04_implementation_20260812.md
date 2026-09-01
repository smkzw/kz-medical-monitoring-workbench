# Codex Execution Plan: medical_monitoring_r4_d04_implementation_20260812

Objective: 依据已冻结D04合同实现入排、方案要求与潜在方案偏离的合成离线纵切，并完成隔离回归

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现R4共享候选关键性读取与生命周期高风险持久化钩子，单一所有者修改共享文件 | `runs/execution/medical_monitoring_r4_d04_implementation_20260812/worker_01.md` |
| `worker_02` | 实现D04 protocol领域模型、组合表达式、适用性门、证据评估、中文Query与覆盖缺口通知 | `runs/execution/medical_monitoring_r4_d04_implementation_20260812/worker_02.md` |
| `worker_03` | 实现Journey投影、合成fixtures、公开导出与83项挑战测试，并完成D01-D03/R2/R3相邻回归 | `runs/execution/medical_monitoring_r4_d04_implementation_20260812/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_r4_d04_implementation_20260812/manager.md` |

## Codex Acceptance

Codex will verify the frozen input hash, allowed-path ownership, focused and adjacent regressions, full R4/R2/R3 suites, Ruff/compileall, public object identity, deterministic payload/hash and port 8911 stopped. This is a renderer-neutral R4 slice; no R5 visual acceptance is claimed.
