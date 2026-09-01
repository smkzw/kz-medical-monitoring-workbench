# Codex Execution Plan: mw-literature-word-link-release-exec

Objective: 在不重做现有文献库、重索引器和OOXML引用书签链的前提下，完成正式终稿引用门禁、用户可处置反馈和Microsoft Word原生引用验收。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 后端：为source_reference_reindex结果建立草稿可提示、approved_final阻断的确定性门禁；输出结构化可处置状态和回归测试。 | `runs/execution/mw-literature-word-link-release-exec/worker_01.md` |
| `worker_02` | 前端：读取导出响应中的文献重索引状态，给出简洁中文处置提示；避免底层日志常驻和额外医学审批；补聚焦测试。 | `runs/execution/mw-literature-word-link-release-exec/worker_02.md` |
| `worker_03` | 验收：使用任务自有真实引用DOCX完成Word更新域、保存关闭重开、引用到参考文献书签的原生跳转和重排保持证据，不碰用户已打开文档。 | `runs/execution/mw-literature-word-link-release-exec/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_grok` | `grok-build` | `grok-4.5` | `runs/execution/mw-literature-word-link-release-exec/manager.md` |

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
