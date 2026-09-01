# Execution Context: mm_r8_gate0_contract_draft_20260831

Created: 2026-08-31 10:50:19 CST
Objective: 在不读取任何真实项目文件的前提下，起草医学监查 R8-0 来源准入、防过拟合、独立 harness/LLM 责任、真实本地应用/通知就绪与 System Design 15.4 真实验证总合同；合同接受前禁止真实项目、真实模型和真实浏览器。
Task type: `complex_delivery_conference`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.
Route schedule: `unscheduled`; packet branch recorded at creation in `Asia/Shanghai`. Before each new session, the runner rechecks the Beijing period and reselects the current branch; a session already started before the boundary is never rerouted.
Effective worker chain: `openai-codex/gpt-5.6-luna:max -> codex/gpt-5.6-luna:max`

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor` -> `pi` / `openai-codex` / `gpt-5.6-luna`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §§15.1, 15.4, 19.1, 20.
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R8 and test/evidence strategy.
- `context/medical_monitoring_r7_phase_acceptance_record_20260831.md`.
- `context/medical_monitoring_r7_slice09_overall_and_r7_phase_review_20260831.md`.
- R7 accepted contract shapes may be read only when directly relevant; current filesystem is authoritative.
- The five real project roots named by the user are identifiers only for this contract draft. Workers must not list, stat, hash, open or search any file beneath them.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.
- Read-only contract drafting only. No product/source edits, no real-project byte reads, no external model call, no service/browser, no installation, no deletion and no medical-writing access.
- Do not invent project contents, filenames, disease/drug facts, listing columns, baseline results or gold labels.
- Every proposed field must distinguish `not_provided`, `not_applicable`, `not_evaluable`, `conflict`, `parse_failed` and `blocked` where relevant; absence is never treated as no risk.

## Work Items

1. 起草逐项目只读 source-admission、文件哈希、双快照/报告可用性、项目身份和隔离输出/零写入合同。
2. 起草 anti-overfit 与 harness responsibility 合同：通用 schema、提示框架、原始输出/binding/coverage/source anchor、失败语义和跨项目挑战，不代替模型给出项目医学解构。
3. 起草 real-app/notification/§15.4 readiness 与 R8 测试矩阵合同：真实一键入口、离页信号、备份迁移回滚卸载、两角色两轮 P0-P4 和准入顺序。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
