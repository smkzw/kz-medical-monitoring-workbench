# Codex Execution Plan: mw_durable_jobs_20260722

Objective: 将竞品分诊、章节AI候选和参考资料翻译迁移到统一SQLite持久作业合同，保持独立生产AI、冷恢复、取消、租约和项目隔离，并完成前后端集成与回归

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 统一DurableMedicalWritingJob合同、SQLite存储、worker生命周期与恢复语义 | `runs/execution/mw_durable_jobs_20260722/worker_01.md` |
| `worker_02` | 竞品分诊适配统一持久任务并移除HTTP同步长调用 | `runs/execution/mw_durable_jobs_20260722/worker_02.md` |
| `worker_03` | 章节AI候选适配统一持久任务并实现候选采纳原子写入 | `runs/execution/mw_durable_jobs_20260722/worker_03.md` |
| `worker_04` | 翻译批次适配统一持久任务及重启恢复 | `runs/execution/mw_durable_jobs_20260722/worker_04.md` |
| `worker_05` | 统一作业API、前端进度交互、取消重试和集成回归 | `runs/execution/mw_durable_jobs_20260722/worker_05.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_grok` | `grok-build` | `grok-4.5` | `runs/execution/mw_durable_jobs_20260722/manager.md` |

## Codex Acceptance

User-requested soft pause at 2026-07-22 18:20. Shared durable core accepted after 108
Codex-run tests. Worker 02 follow-up and Worker 04 were interrupted with code preserved;
Worker 03 report exists but true atomicity is not accepted. Resume from
`records/active_slices/medical_writing_production_rebaseline_20260722/SOFT_PAUSE_RESUME.md`.
Worker 05 has not started. Final acceptance remains pending.
