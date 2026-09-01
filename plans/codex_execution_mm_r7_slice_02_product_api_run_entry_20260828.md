# Codex Execution Plan: mm_r7_slice_02_product_api_run_entry_20260828

Objective: 按冻结合同实现 R7 Slice-02 隔离产品 API/运行入口：显式 workspace bootstrap、四层 ExecutionProfile、三模式不可变 Run 绑定与稳定中文错误；保持产品主应用、真实项目、端口和医学写作不变

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现 run_entry.py：显式幂等 bootstrap、四层 scope 解析、effective profile 冻结、Run bind/replay/conflict 与公共投影；只改 worker_01 允许路径 | `runs/execution/mm_r7_slice_02_product_api_run_entry_20260828/worker_01.md` |
| `worker_02` | 实现 api.py：最小 FastAPI router、严格 DTO、稳定 code+中文 message、无凭据值泄漏；只改 worker_02 允许路径 | `runs/execution/mm_r7_slice_02_product_api_run_entry_20260828/worker_02.md` |
| `worker_03` | 实现聚焦测试、确定性/重开/失败关闭矩阵、receipt 与 README；只改 worker_03 允许路径 | `runs/execution/mm_r7_slice_02_product_api_run_entry_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
