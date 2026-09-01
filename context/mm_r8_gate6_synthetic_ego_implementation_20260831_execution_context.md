# Execution Context: mm_r8_gate6_synthetic_ego_implementation_20260831

Created: 2026-08-31 14:11:43 CST
Objective: 按已独立接受的 G6 合同实现 actual local app + synthetic fixture + mock/recorded adapter + synthetic binding 的受众验收基础；保持真实项目、真实模型/harness、外网与医学写作关闭，浏览器视觉另建独立 packet
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

- `reviews/medical_monitoring_r8_gate6_synthetic_ego_audience_acceptance_contract_v0_1_20260831.md`
- `context/medical_monitoring_r8_gate6_contract_acceptance_record_20260831.md`
- `context/medical_monitoring_r8_gate5_pre_real_independent_acceptance_record_20260831.md`
- `reviews/medical_monitoring_r8_gate0_source_admission_anti_overfit_contract_v0_1_20260831.md`
- Current source under `deploy/medical_monitoring_local`, `services/api/app`, `frontend/src`, and current tests.
- Existing R7 07C4/08C4 source and records are reusable structure references only; their acceptance is not inherited.

Authorized write scope is limited to current-workspace medical-monitoring G6 implementation files under
`deploy/medical_monitoring_local`, `services/api/app`, `frontend/src`, focused tests, and this task's
`context/reviews/plans/metrics/runs/logs` evidence surfaces. Workers must not write
`deploy/medical_writing_local`, medical-writing source/assets/tests, real project roots, or any path outside
this workbench. Do not start services, browsers, models, or external network in this implementation packet;
actual ego(lite) visual execution is a later separate governed packet.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 实现 entry_manifest、execution_boundary_manifest、viewport_layout_manifest 与用户可双击 actual app 冷启动/生命周期 fail-closed 基础及聚焦测试
2. 实现跨领域 synthetic fixture、synthetic binding/mock-recorded adapter、九终态四能力通知矩阵和十三项应用内用户任务 evidence seam 及测试
3. 实现 G6 audience-facing synthetic 路由/页面接线、Patient Journey/项目中心流向挑战夹具、结构化视觉测量与 evidence pack 生成，不启动浏览器并完成前端/相邻测试

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
