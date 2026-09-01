# Execution Context: mm_r7_slice07b_subject_flow_implementation_20260828

Created: 2026-08-28 23:09:21 CST
Objective: 按已冻结的 v0.2 + v0.3 §9 合同实现 R7 Slice-07B synthetic 项目/中心受试者阶段流向看板。严格不运行真实项目、不启动 8911、不修改医学写作。实现后由 Codex 运行回归与 ego(lite) 验收。
Task type: `finite_code_task`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.
Route schedule: `night`; resolved once at packet creation in `Asia/Shanghai`.
Effective worker chain: `codebuddy-cli/glm-5.3-flash:max -> mtplx/mtplx-qwen38-27b-optimized-quality:medium -> openai-codex/gpt-5.6-luna:xhigh`

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor` -> `codebuddy` / `codebuddy-cli` / `glm-5.3-flash`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `reviews/medical_monitoring_r7_slice07b_subject_flow_dashboard_contract_v0_2_20260828.md`
- `reviews/medical_monitoring_r7_slice07b_subject_flow_dashboard_contract_v0_3_20260828.md`（冲突时优先）
- `context/medical_monitoring_subject_flow_dashboard_requirement_20260828.md`
- `services/api/app/medical_monitoring_r5_product_adapter.py` 及同目录 R5 router/tests。
- `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Adapter.mjs`、
  `medicalMonitoringR5RouteState.mjs`、`MedicalMonitoringR5Page.jsx`、`medicalMonitoringR5.css`
  及对应 fixtures/tests。
- 当前文件系统是最终真相；保留任何不属于本任务的现有改动。
- Do not add production paths without explicit Codex authorization.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.
- 不启动 8911 或任何产品服务，不使用浏览器，不运行五个真实项目，不读取或修改医学写作文件。
- 可以运行各自改动范围内的 synthetic/offline 单元测试；不得安装新包。

## Work Items

1. 后端：在 R5 authority packet 中加入兼容旧 schema 的 typed flow stage/path records，构建守恒 subject_flow overview 投影、三态、中心范围和 Journey 跳转窗口；补充后端确定性测试。只改 services/api/app 下 R5 adapter/router 及其测试。
2. 前端数据与路由：严格规范化 subject_flow 三种形态，加入互斥 flow route keys、Journey 往返保留和 adapter/route tests。只改 frontend/src/features/medical-monitoring/r5 的 adapter、route-state 和对应测试，不改页面/CSS。
3. 前端视觉：在现有 R5 OverviewView 中实现全宽横向 SVG 受试者阶段流向、current/reached/link 筛选、风险摘要、折叠明细表、空态/阻断态、键盘隔离与中文 CSS；补充组件/合同测试。只改 R5 Page/CSS/fixtures/render tests，不启动服务或浏览器。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
