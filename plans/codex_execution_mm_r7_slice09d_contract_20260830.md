# Codex Execution Plan: mm_r7_slice09d_contract_20260830

Objective: 冻结 R7 Slice-09D synthetic/offline 性能、容量与长任务恢复基线合同；建立分级通用语料、可复现测量方法、恢复/资源边界和中文用户投影，并把跨研究/药物/疾病/listing 结构反过拟合约束与独立 harness/LLM 责任边界写入合同。不得运行真实项目/模型/浏览器，不启动 8911/5174/8984，不修改医学写作或安全专项。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 审阅既有 Slice-08/09、R5-S6/S7 性能证据与当前代码，提出 09D 分级 synthetic corpus、指标、采样、冷暖运行、容量台阶和停止条件；不得把单机历史数值直接变成普适 SLO。 | `runs/execution/mm_r7_slice09d_contract_20260830/worker_01.md` |
| `worker_02` | 审阅长任务、恢复、备份/迁移/审计链与技术日志实现，提出进程中断、重启、资源压力、幂等、恢复时间和数据完整性的故障/恢复矩阵及中文用户结果，保持 stdlib-first 与离线边界。 | `runs/execution/mm_r7_slice09d_contract_20260830/worker_02.md` |
| `worker_03` | 从反过拟合与 harness 责任边界审阅 09D/R8 连接：真实方案/IB/listing 只作为只读泛化挑战；禁止疾病/药物/量表/风险/列名/布局硬编码；listing 解构和药物/疾病提取必须由子系统独立 harness/LLM 完成，Codex 只打磨提示/schema/校验/挑战矩阵。输出合同条款与验收矩阵建议。 | `runs/execution/mm_r7_slice09d_contract_20260830/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
