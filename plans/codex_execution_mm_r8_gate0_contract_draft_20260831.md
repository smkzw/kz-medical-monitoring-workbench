# Codex Execution Plan: mm_r8_gate0_contract_draft_20260831

Objective: 在不读取任何真实项目文件的前提下，起草医学监查 R8-0 来源准入、防过拟合、独立 harness/LLM 责任、真实本地应用/通知就绪与 System Design 15.4 真实验证总合同；合同接受前禁止真实项目、真实模型和真实浏览器。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 起草逐项目只读 source-admission、文件哈希、双快照/报告可用性、项目身份和隔离输出/零写入合同。 | `runs/execution/mm_r8_gate0_contract_draft_20260831/worker_01.md` |
| `worker_02` | 起草 anti-overfit 与 harness responsibility 合同：通用 schema、提示框架、原始输出/binding/coverage/source anchor、失败语义和跨项目挑战，不代替模型给出项目医学解构。 | `runs/execution/mm_r8_gate0_contract_draft_20260831/worker_02.md` |
| `worker_03` | 起草 real-app/notification/§15.4 readiness 与 R8 测试矩阵合同：真实一键入口、离页信号、备份迁移回滚卸载、两角色两轮 P0-P4 和准入顺序。 | `runs/execution/mm_r8_gate0_contract_draft_20260831/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Codex will merge the three reports into one versioned contract, verify that no real-project path was touched, hash/freeze the draft, then run an independent contract conference. Worker reports cannot accept R8-0.
