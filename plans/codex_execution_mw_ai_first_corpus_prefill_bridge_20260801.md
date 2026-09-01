# Codex Execution Plan: mw_ai_first_corpus_prefill_bridge_20260801

Objective: 把已持久化且来源绑定的第一轮Protocol语料分析接入authoring prefill，生成可审阅设计候选并保持精确事实fail-closed

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 设计并实现exact round1 analysis identity/hash到prefill evidence catalog的只读桥接 | `runs/execution/mw_ai_first_corpus_prefill_bridge_20260801/worker_01.md` |
| `worker_02` | 实现模块到target path的保守兼容及生成/采用目录同源重建 | `runs/execution/mw_ai_first_corpus_prefill_bridge_20260801/worker_02.md` |
| `worker_03` | 补齐确定性测试并验证不放宽剂量终点等精确事实门 | `runs/execution/mw_ai_first_corpus_prefill_bridge_20260801/worker_03.md` |

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `finite_code_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/mw_ai_first_corpus_prefill_bridge_20260801/manager.md` |

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
