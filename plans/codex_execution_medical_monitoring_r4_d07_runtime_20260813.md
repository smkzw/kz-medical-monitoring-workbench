# Codex Execution Plan: medical_monitoring_r4_d07_runtime_20260813

Objective: 在隔离 R4 POC 中实现冻结 D07 临床安全性、实验室与检查运行时，并通过 144 例独立 oracle、中文 Query/Journey、生命周期与相邻回归验收。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现 D07 闭合 typed runtime、pre-evaluator integrity、确定性医学求值、owner/handoff/priority/lifecycle；仅写 D07 新模块与专属单元测试。 | `runs/execution/medical_monitoring_r4_d07_runtime_20260813/worker_01.md` |
| `worker_02` | 实现 test-only 144 例 catalog/oracle/DSL 运行器、确定性重放与 mutation suite；严禁 runtime 读取 oracle/manifest/registry。 | `runs/execution/medical_monitoring_r4_d07_runtime_20260813/worker_02.md` |
| `worker_03` | 实现 D07 中文三段式 Query、共享访视轴 Journey event/risk marker/source jump/audience validation、最小导出/README 与聚焦/相邻回归。 | `runs/execution/medical_monitoring_r4_d07_runtime_20260813/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_r4_d07_runtime_20260813/manager.md` |

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
