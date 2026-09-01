# Execution Context: mm_r7_slice07a_progress_ui_implementation_20260828

Created: 2026-08-28 18:55:21
Objective: 按已接受的 Slice-07A v1.1 合同实现真实进度、后台恢复与现有运行管理员动作界面，保持医学监察员只读验收边界；增加稳定 run_state，完成前端接线、测试和后续 ego(lite) 验收准备。不得修改医学写作或权限模型，不得运行真实项目或设计测试安全功能。
Task type: `html_ppt_visual_browser`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `visual_executor_kimi` -> `kimi` / `kimi-code` / `kimi-code/k3-256k`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `reviews/medical_monitoring_r7_slice_07a_progress_ui_contract_v1_20260828.md`
- `reviews/codex_conference_mm_r7_slice07a_progress_ui_contract_20260828_review.md`
- `frontend/AGENTS.md`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/background_recovery.py`
- `poc/medical_monitoring_ai_native_r7/src/mm_r7/runtime_progress.py`
- `services/api/app/medical_monitoring_r7_product_router.py`
- `tests/test_medical_monitoring_r7_product_router.py`
- `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx`
- `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5.css`
- `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5RouteState.mjs`
- `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Adapter.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringApi.mjs`
- Existing adjacent frontend tests under `frontend/src/features/medical-monitoring/**`.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.
- Do not modify `frontend/src/features/medical-writing/**`, medical-writing backend/routes/tests, authorization roles, or principal mappings.
- Do not start services or browsers and do not run real clinical projects during worker implementation.
- Work items are sequentially dispatched in one shared workspace; each worker must inspect prior accepted edits and avoid overwriting them.

## Work Items

1. 后端公开进度：增加稳定 run_state、修订用户中文错误文案并补齐产品路由与运行时测试；只改 R7 运行进度相关文件。
2. 前端数据层：实现 R7 progress/action API client 与纯 projection，覆盖路由 run_ref、错误码空态、迟到响应、禁止词和动作映射测试。
3. 前端呈现层：在现有 R5 页面接入紧凑本次监查进度组件，完成真实轮询、离页恢复、内联停止确认、可访问性、中文视觉与组件测试；不触碰 Patient Journey/Sankey。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
