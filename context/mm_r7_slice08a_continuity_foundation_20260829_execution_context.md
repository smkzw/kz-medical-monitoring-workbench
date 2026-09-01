# Execution Context: mm_r7_slice08a_continuity_foundation_20260829

Created: 2026-08-29 12:58:42 CST
Objective: 按已冻结 Slice-08 v0.1+v0.2 实现 08A synthetic/offline continuity 领域对象、最小 v2→v3 additive migration、计划持久化/校验及确定性/故障矩阵；保持 R2 唯一风险生命周期，复用既有 ResultPublication，不改 UI、不运行真实项目或服务。
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.
Route schedule: `unscheduled`; packet branch recorded at creation in `Asia/Shanghai`. Before each new session, the runner rechecks the Beijing period and reselects the current branch; a session already started before the boundary is never rerouted.
Effective worker chain: `openai-codex/gpt-5.6-luna:max -> openai-codex/gpt-5.6-terra:high -> codex/gpt-5.6-luna:max`

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

1. 实现 poc/medical_monitoring_ai_native_r7/src/mm_r7/continuity.py 及聚焦测试：DecisionBaseline、CarryForwardPlan/Item、RiskChangeKind、逐对象处置、规则作用域、缺行不自动关闭、canonical digest；不得改 launch_registry 或 UI。
2. 实现 launch_registry.py v2→v3 最小 additive migration 与 continuity plan/item 持久化、staging→verified 状态门、事务/故障回滚、close/reopen；补聚焦迁移/存储测试；不得接 UI 或真实模型。
3. 独立构建/执行 08A 合同验证：三模式基线、对象处置、R2/R7边界、artifact 元数据 fail-closed、9-cell determinism、migration fault/retry、相邻回归；只修复本切缺陷并输出 compact handoff。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
