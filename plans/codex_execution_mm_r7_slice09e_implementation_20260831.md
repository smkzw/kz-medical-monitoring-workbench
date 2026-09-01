# Codex Execution Plan: mm_r7_slice09e_implementation_20260831

Objective: 按冻结合同v0.2实现医学监查Slice-09E本地分发与数据处置synthetic/offline闭环，保持医学写作与真实项目不变。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现deploy/medical_monitoring_local中文管理入口、preflight、端口归属与退出码合同。 | `runs/execution/mm_r7_slice09e_implementation_20260831/worker_01.md` |
| `worker_02` | 实现发布清单、prepare-upgrade受控synthetic演练与preview-only uninstall plan，复用09A/09B语义。 | `runs/execution/mm_r7_slice09e_implementation_20260831/worker_02.md` |
| `worker_03` | 实现聚焦测试、normal/-O/-OO与三个hash seed确定性、边界和相邻R7验证证据。 | `runs/execution/mm_r7_slice09e_implementation_20260831/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Codex will inspect all changes, run focused tests plus normal/-O/-OO × three hash seeds, run the accepted R7/R1 adjacent suites proportionate to impact, verify port and medical-writing boundaries, and obtain an independent implementation conference before accepting 09E.
