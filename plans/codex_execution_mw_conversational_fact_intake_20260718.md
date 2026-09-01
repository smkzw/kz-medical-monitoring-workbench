# Codex Execution Plan: mw_conversational_fact_intake_20260718

Objective: 在医学写作子系统中实现IB可选的最小产品事实包与通用对话式事实采集：DeepSeek-v4-pro拆解用户自然语言，用户确认后写入版本化事实，缺少IB不阻断调研和写作，仅局部阻断依赖缺失事实的确定性条款。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 后端合同、独立AI提示词、持久化会话和幂等API | `runs/execution/mw_conversational_fact_intake_20260718/worker_01.md` |
| `worker_02` | 桌面端无IB最小输入与对话式确认交互，移除重复必填 | `runs/execution/mw_conversational_fact_intake_20260718/worker_02.md` |
| `worker_03` | 多项目单元/API/浏览器测试与待医学批准语义审计 | `runs/execution/mw_conversational_fact_intake_20260718/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `complex_manager_grok` | `grok-build` | `grok-4.5` | `runs/execution/mw_conversational_fact_intake_20260718/manager.md` |

## Codex Acceptance

1. Inspect every worker diff and reject unrelated edits or fake/providerless AI.
2. Run focused Python and frontend tests in an isolated runtime.
3. Exercise a real DeepSeek V4 Pro fact-decomposition turn without stable
   runtime mutation.
4. Rebuild and visually inspect the desktop flow at 1920x1080.
5. Verify clean-project no-IB and optional-IB paths plus user adoption semantics.
6. Start Worker 03 after implementation, then Grok manager after all worker
   evidence exists. Codex retains final clinical, browser and production
   acceptance.
