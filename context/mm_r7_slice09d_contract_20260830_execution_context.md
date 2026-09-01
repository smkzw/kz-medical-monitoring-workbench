# Execution Context: mm_r7_slice09d_contract_20260830

Created: 2026-08-30 23:22:39 CST
Objective: 冻结 R7 Slice-09D synthetic/offline 性能、容量与长任务恢复基线合同；建立分级通用语料、可复现测量方法、恢复/资源边界和中文用户投影，并把跨研究/药物/疾病/listing 结构反过拟合约束与独立 harness/LLM 责任边界写入合同。不得运行真实项目/模型/浏览器，不启动 8911/5174/8984，不修改医学写作或安全专项。
Task type: `long_horizon_code`
Risk: `medium`
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

- TODO: Codex must add authoritative source files, screenshots, datasets, or URLs before dispatch.
- Do not add production paths without explicit Codex authorization.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 审阅既有 Slice-08/09、R5-S6/S7 性能证据与当前代码，提出 09D 分级 synthetic corpus、指标、采样、冷暖运行、容量台阶和停止条件；不得把单机历史数值直接变成普适 SLO。
2. 审阅长任务、恢复、备份/迁移/审计链与技术日志实现，提出进程中断、重启、资源压力、幂等、恢复时间和数据完整性的故障/恢复矩阵及中文用户结果，保持 stdlib-first 与离线边界。
3. 从反过拟合与 harness 责任边界审阅 09D/R8 连接：真实方案/IB/listing 只作为只读泛化挑战；禁止疾病/药物/量表/风险/列名/布局硬编码；listing 解构和药物/疾病提取必须由子系统独立 harness/LLM 完成，Codex 只打磨提示/schema/校验/挑战矩阵。输出合同条款与验收矩阵建议。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
