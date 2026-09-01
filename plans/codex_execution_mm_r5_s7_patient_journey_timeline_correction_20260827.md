# Codex Execution Plan: mm_r5_s7_patient_journey_timeline_correction_20260827

Objective: 将医学监查受试者 Patient Journey 从卡片墙纠偏为共享横向时间轴：实际日期/访视节点、八域泳道、按日期定位的事件点与区间、风险锚点、缺失日期隔离、点击详情，并保持高密度可用性与中文医学语义。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 审阅当前前端数据适配与时间语义，提出最小可实现的横向时间坐标、事件碰撞和高密度聚合契约；只写执行报告，不改文件。 | `runs/execution/mm_r5_s7_patient_journey_timeline_correction_20260827/worker_01.md` |
| `worker_02` | 在限定的 R5 Patient Journey 前端 JSX/CSS 与对应测试内实现共享横向时间轴、访视节点、八域泳道、按日期定位的点/区间、风险标记、缺失日期区与点击详情；不得改医学写作子系统或其他模块。 | `runs/execution/mm_r5_s7_patient_journey_timeline_correction_20260827/worker_02.md` |
| `worker_03` | 在实现完成后独立运行聚焦测试与静态审阅，核对事件时间定位、访视轴、八域、点击详情、缩放/密度和中文标签；只写执行报告，不改产品文件。 | `runs/execution/mm_r5_s7_patient_journey_timeline_correction_20260827/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
