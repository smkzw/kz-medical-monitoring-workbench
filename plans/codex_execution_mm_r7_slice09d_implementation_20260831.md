# Codex Execution Plan: mm_r7_slice09d_implementation_20260831

Objective: 按冻结合同 v0.2 实施 R7 Slice-09D synthetic/offline 性能、容量与长任务恢复基线：冻结通用 corpus/generator/input-side oracle/measurement schema/fault matrix，完成最小 stdlib-first runner、确定性/恢复/资源裁决和证据输出。严禁真实项目/模型/浏览器、8911/5174/8984、医学写作、安全专项；不得硬编码疾病/药物/量表/风险/listing 列名或布局。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现版本化 15-profile synthetic corpus manifest、通用 generator、input-side oracle 与反过拟合静态/mutation guards；只使用 opaque identity，不触碰真实资料，提供 focused tests 与固定 artifacts。 | `runs/execution/mm_r7_slice09d_implementation_20260831/worker_01.md` |
| `worker_02` | 实现 stdlib-first measurement runner/schema：7 workload 基准包、process-cold/warm、calibration、watchdog、资源 guard、raw JSONL/stat summary/capacity statement 与独立 15-cell determinism；不得运行 24 小时全量基准，本执行先完成可验证 T0/T1 bounded proof。 | `runs/execution/mm_r7_slice09d_implementation_20260831/worker_02.md` |
| `worker_03` | 实现 fault/recovery matrix 与中文 DTO 投影验证：中断/cancel/lease/generation/迟到回调/backup/restore/migration/audit/log/resource 边界；复用现有 09A-09C seam，最小改动并完成 R1/R7 相邻回归。 | `runs/execution/mm_r7_slice09d_implementation_20260831/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
