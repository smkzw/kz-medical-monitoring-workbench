# Execution Context: mm_r7_slice09b_contract_20260830

Created: 2026-08-30 13:33:04 CST
Objective: 在不修改产品源码的前提下，梳理并冻结 R7 Slice-09B schema 迁移、升级、失败回滚和旧项目兼容契约；仅使用 synthetic/offline 工作区，保持 8911/5174 停止并保护医学写作子系统。
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

1. 清点 R1 与 R7 所有持久化数据库、当前 schema/version 识别方式、既有 additive migration 与缺口，输出逐库证据和最小迁移边界。
2. 设计升级前备份、维护门、逐步迁移、版本最后推进、故障注入、失败回滚和重试的状态机与验收矩阵，指出与 Slice-09A 的复用边界。
3. 从中文资深医学监察员产品视角设计旧项目打开、只读兼容、升级提示/进度/结果 DTO 与错误语言，列出不得暴露的工程化字段及测试矩阵。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
