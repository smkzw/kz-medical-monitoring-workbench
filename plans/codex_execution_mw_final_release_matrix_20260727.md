# Codex Execution Plan: mw_final_release_matrix_20260727

Objective: 医学写作系统最终上线门：仅在隔离运行时中，由四类测试者完成十二个互异非肿瘤适应症、两种用户视角的真实浏览器端到端写作、独立AI、语料、引用与完整DOCX闭环；修复后复测直至通过。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 隔离运行时与独立AI/OCR/Hy-MT2翻译可用性基线，禁止触碰共享真实项目。 | `runs/execution/mw_final_release_matrix_20260727/worker_01.md` |
| `worker_02` | DOCX精确导出门：封面、目录跳转、标题样式、字体、摘要嵌套表、图表量表、引用与Word实际打开。 | `runs/execution/mw_final_release_matrix_20260727/worker_02.md` |
| `worker_03` | Pi Alibaba Qwen3.8 和 Pi CMS 两条真实浏览器三适应症测试通道。 | `runs/execution/mw_final_release_matrix_20260727/worker_03.md` |
| `worker_04` | CodeBuddy Hy3 和 Cursor composer-2.5 两条真实浏览器三适应症测试通道。 | `runs/execution/mw_final_release_matrix_20260727/worker_04.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_grok` | `alibaba` | `qwen3.8-max-preview` | `runs/execution/mw_final_release_matrix_20260727/manager.md` |

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
