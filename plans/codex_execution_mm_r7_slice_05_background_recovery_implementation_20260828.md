# Codex Execution Plan: mm_r7_slice_05_background_recovery_implementation_20260828

Objective: 按冻结合同 FROZEN_R7_SLICE_05_BACKGROUND_RECOVERY_V0_2 实施 synthetic/offline 后台执行与中断恢复：单一 SQLite 进度事实源、R7 run-level 控制租约、依赖感知调度、停止/继续、consistent snapshot 和产品中文 overlay；不得改 R1/R6、前端、医学写作，不启动服务/模型/真实项目。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现 R7 background recovery/control adapter：控制表、状态机、原子 claim/CAS heartbeat、依赖感知 synthetic worker、停止/继续和一致快照；仅新增 R7 模块并最小接 runtime_progress。 | `runs/execution/mm_r7_slice_05_background_recovery_implementation_20260828/worker_01.md` |
| `worker_02` | 在项目级 product router 最小挂载 start/resume/cancel 与 progress overlay，保持 canonical 项目、权限、catch-all、每请求关闭和中文泄漏阻断。 | `runs/execution/mm_r7_slice_05_background_recovery_implementation_20260828/worker_02.md` |
| `worker_03` | 新增 Slice-05 聚焦离线测试、失败注入、双连接并发、依赖阻断、边界回归、README 与 receipt 草案；不得启动 8911/5174、模型或真实项目。 | `runs/execution/mm_r7_slice_05_background_recovery_implementation_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
