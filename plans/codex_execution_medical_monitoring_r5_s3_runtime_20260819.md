# Codex Execution Plan: medical_monitoring_r5_s3_runtime_20260819

Objective: 实现并验证已接受合同约束下的R5-S3离线项目驾驶舱与中心图谱runtime

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现S3 typed contracts与authority builder，逐叶只读引用R4/S1/S2及具名supplemental authority | `runs/execution/medical_monitoring_r5_s3_runtime_20260819/worker_01.md` |
| `worker_02` | 实现current risk/change/quantity/center map/cockpit renderer-neutral projections及fail-closed invariants | `runs/execution/medical_monitoring_r5_s3_runtime_20260819/worker_02.md` |
| `worker_03` | 实现挑战测试、R4只读SHA证据、focused/full回归与交付证据 | `runs/execution/medical_monitoring_r5_s3_runtime_20260819/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

`ACCEPT_R5_S3`。仅接受 synthetic/offline、renderer-neutral S3；下一阶段为 S4 合同冻结。
