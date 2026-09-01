# Codex Execution Plan: mw_indexes_sidecar_20260716

Objective: 为医学写作Word目录与交叉引用闭环提供三个独立、可落地的实现侧车，由Codex保留主线合成与最终验收

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 审计并实现源DOCX题注后嵌入图片对象的确定性保真导入方案，重点覆盖RUX表8 PNG丢失；限定写入隔离补丁/测试报告，不改稳定运行时数据。 | `runs/execution/mw_indexes_sidecar_20260716/worker_01.md` |
| `worker_02` | 审计文档索引目录、SEQ书签与REF交叉引用的后端契约、失败关闭边界和API端点，提交可应用补丁或精确变更清单。 | `runs/execution/mw_indexes_sidecar_20260716/worker_02.md` |
| `worker_03` | 审计医学写作编辑器交叉引用选择器的桌面端交互、TipTap/ProseMirror mark持久化与浏览器验收路径，提交可应用补丁或精确变更清单。 | `runs/execution/mw_indexes_sidecar_20260716/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_grok` | `grok-build` | `grok-4.5` | `runs/execution/mw_indexes_sidecar_20260716/manager.md` |

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
