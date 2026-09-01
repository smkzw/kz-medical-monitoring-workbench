# Execution Context: mm_r7_slice07a_progress_ui_ego_acceptance_20260828

Created: 2026-08-28 19:52:51
Objective: 在隔离合成项目上完成 R7 Slice-07A 进度面板的 ego(lite) 用户视角验收，并对发现做最小纠偏；不读取真实临床项目，不触碰医学写作子系统。
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

- `reviews/medical_monitoring_r7_slice_07a_progress_ui_contract_v1_20260828.md` v1.1.
- `context/medical_monitoring_r7_slice_06_review_and_slice07_plan_20260828.md`.
- Current R7 product/runtime sources and tests under `poc/medical_monitoring_ai_native_r7/`,
  `services/api/app/medical_monitoring_r7_product_router.py`,
  `tests/test_medical_monitoring_r7_product_router.py`.
- Current R7 frontend sources under `frontend/src/features/medical-monitoring/r7/` and the
  R5 mount in `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx`.
- Synthetic-only fixture/evidence created by this packet under
  `artifacts/mm_r7_slice07a_progress_ui_ego_fixture_20260828/` and
  `evidence/mm_r7_slice07a_progress_ui_ego_acceptance_20260828/`.
- Do not add production paths without explicit Codex authorization.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 建立隔离合成运行夹具，覆盖医学监察员只读身份与管理员动作身份，验证稳定项目/运行标识和七态进度契约。
2. 使用 ego(lite) 在宽屏及常用视口真实打开医学监查看板，检查进度条、当前工作、阶段节点、中文文案、刷新恢复、键盘与失败态呈现并留存截图和可访问性证据。
3. 审阅视觉与交互证据，对产品代码进行最小修复，运行聚焦与相邻回归，形成 Slice-07A 验收报告和下一阶段建议。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
