# Codex Execution Plan: mm_r7_slice09b_contract_20260830

Objective: 在不修改产品源码的前提下，梳理并冻结 R7 Slice-09B schema 迁移、升级、失败回滚和旧项目兼容契约；仅使用 synthetic/offline 工作区，保持 8911/5174 停止并保护医学写作子系统。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 清点 R1 与 R7 所有持久化数据库、当前 schema/version 识别方式、既有 additive migration 与缺口，输出逐库证据和最小迁移边界。 | `runs/execution/mm_r7_slice09b_contract_20260830/worker_01.md` |
| `worker_02` | 设计升级前备份、维护门、逐步迁移、版本最后推进、故障注入、失败回滚和重试的状态机与验收矩阵，指出与 Slice-09A 的复用边界。 | `runs/execution/mm_r7_slice09b_contract_20260830/worker_02.md` |
| `worker_03` | 从中文资深医学监察员产品视角设计旧项目打开、只读兼容、升级提示/进度/结果 DTO 与错误语言，列出不得暴露的工程化字段及测试矩阵。 | `runs/execution/mm_r7_slice09b_contract_20260830/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
