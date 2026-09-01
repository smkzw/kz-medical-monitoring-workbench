# Execution Context: mm_r7_slice09a_execution_20260830

Created: 2026-08-30 10:31:37 CST
Objective: 实现冻结的 R7 Slice-09A synthetic/offline 项目备份、导出、预检、恢复、进度和原子回滚能力，并完成独立验证与相邻回归。
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

- `context/mm_r7_slice09a_execution_contract_20260830.md`
- `plans/mm_r7_slice09a_execution_assignments_20260830.md`
- `reviews/medical_monitoring_r7_slice09a_project_backup_restore_contract_v0_1_20260830.md`
- `reviews/medical_monitoring_r7_slice09a_project_backup_restore_contract_v0_2_20260830.md`
- `reviews/medical_monitoring_r7_slice09a_project_backup_restore_contract_v0_3_20260830.md`
- Current R7/R1/product source and tests in this workspace; current filesystem is final truth.

## Risk Boundaries

- Only the source/test files explicitly allowed by the execution contract may be changed.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.
- Do not start services/models/browsers, access real projects, modify medical-writing or touch frontend/UI.

## Work Items

1. 实现 stdlib-only maintenance gate、deterministic mmbackup、operation ledger、preflight、restore/rollback core 与聚焦测试。
2. 把 09A core 最小接入 R7 产品路由和实际产品/后台写边界，完成五个中文 DTO 路由及聚焦测试。
3. 建立独立 oracle 与 adversarial matrix，覆盖确定性、闭包、损坏、身份、重放、writer race、切换/回滚和 reopen 对账，并运行相邻回归。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
