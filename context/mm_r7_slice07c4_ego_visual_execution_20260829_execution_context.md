# Execution Context: mm_r7_slice07c4_ego_visual_execution_20260829

Created: 2026-08-29 09:12:49 CST
Objective: 在隔离 synthetic/offline 主机使用 ego(lite) 验收 R7 Slice-07C-4 中文产品闭环的 1280/1440/1920 桌面视觉与交互，不接触真实项目、真实模型或医学写作，并在结束后关闭所有测试监听。
Task type: `html_ppt_visual_browser`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.
Route schedule: `day`; resolved once at packet creation in `Asia/Shanghai`.
Effective worker chain: `kimi-code/k3-256k:low -> grok-build/grok-4.6:medium -> cursor/auto -> openai-codex/gpt-5.6-luna:max`

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `visual_executor` -> `pi` / `kimi-code` / `k3-256k`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `reviews/medical_monitoring_r7_slice07c4_user_product_loop_contract_v0_2_20260829.md`
- `context/medical_monitoring_r7_slice07c4_user_product_loop_contract_acceptance_record_20260829.md`
- `frontend/src/features/medical-monitoring/r7/MedicalMonitoringR7ProductLoop.jsx`
- `frontend/src/features/medical-monitoring/r7/medicalMonitoringR7ProductLoop.css`
- `frontend/src/features/medical-monitoring/r7/medicalMonitoringR7ProductApi.mjs`
- `frontend/src/features/medical-monitoring/r7/medicalMonitoringR7ProductProjection.mjs`
- `frontend/src/features/medical-monitoring/r7/medicalMonitoringR7ProductState.mjs`
- `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx`
- Current `frontend/dist` produced by the accepted implementation build.
- Existing isolated fixture pattern: `artifacts/mm_r7_slice07a_progress_ui_ego_fixture_20260828/`.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.
- Synthetic/offline only. Do not read or run any real clinical project, call any model/provider, or touch medical-writing source/runtime/data.
- Do not modify product source. Worker 01 may create only `artifacts/mm_r7_slice07c4_product_loop_ego_20260829/` and its tests. Workers 02/03 may write only screenshot/DOM/network/measurement evidence below that artifact directory.
- Use ego(lite), never Playwright/Chrome/browser MCP. Use an isolated non-protected port (default 8978); 8911 and 5174 must remain stopped throughout.
- Dispatch is serialized because workers 02/03 consume worker 01 fixture. Each browser worker must stop any listener it starts, close its ego task space, and record the stop evidence.
- The fixture may return synthetic published results for browser acceptance, but product source must retain its fail-closed no-fixture-fallback rule.
- Desktop acceptance widths are 1280, 1440 and 1920; 1440 assumes the real 180px sidebar. Page-level horizontal overflow, overlapping controls, hidden critical actions, internal identity leakage, fixture/debug labels and English translation-like user copy are blocking.

## Work Items

1. 构建只读隔离 07C-4 HTTP fixture：服务 frontend/dist 与冻结公开 setup/history/progress/result-context 合成响应，补 fixture contract tests；不得修改产品源码。
2. 使用 ego(lite) 真实操作 1440 宽主流程：工作条、四步向导、历史、进度、发布结果、中心流向与 Journey/Profile/Timeline/证据跳转，记录截图与 DOM/网络证据。
3. 使用 ego(lite) 复核 1280/1920 布局、中文文案、焦点/溢出、公开 URL 身份和离页恢复，汇总缺陷分级与停止端口证据。

## Codex Repair State Before Worker 03

- Use the current rebuilt `frontend/dist` (bundle `index-DiMPWFEE.js`). The prior undefined `setEntryLoading` defect is repaired; the progress-to-result button path passed ego(lite) Round 3 with zero runtime exceptions.
- The synthetic fixture now honors `site_ref` for center overview and includes the canonical subject identity object. Its focused contract suite passes 14 tests and the true frontend contract verifier passes 13/13.
- Center-view result identity now prefers the active center label from the filtered public projection instead of the project-wide site range. Focused render/state tests pass 27 + 48.
- At both 1280 and 1920, also confirm that center 006 shows only center 006 data and flow, the identity strip says only `中心 006`, and the subject banner says `受试者 001` / `中心 006` rather than fallback copy.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
