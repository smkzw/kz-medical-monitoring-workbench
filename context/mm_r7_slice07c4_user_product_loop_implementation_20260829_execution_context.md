# Execution Context: mm_r7_slice07c4_user_product_loop_implementation_20260829

Created: 2026-08-29 06:39:37 CST
Objective: 实现已冻结的 R7 Slice-07C-4 synthetic/offline 中文产品闭环；按后端公开身份桥、前端纯数据层、前端组件接线顺序完成，保护医学写作，不启动服务/真实项目/模型。
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.
Route schedule: `unscheduled`; resolved once at packet creation in `Asia/Shanghai`.
Effective worker chain: `openai-codex/gpt-5.6-luna:max -> openai-codex/gpt-5.6-terra:high -> codex/gpt-5.6-luna:max`

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor` -> `pi` / `openai-codex` / `gpt-5.6-luna`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `reviews/medical_monitoring_r7_slice07c4_user_product_loop_contract_v0_1_20260829.md`
- `reviews/medical_monitoring_r7_slice07c4_user_product_loop_contract_v0_2_20260829.md`
- `context/medical_monitoring_r7_slice07c4_user_product_loop_contract_acceptance_record_20260829.md`
- 07C-3 accepted launch registry/publication/product router/R5 bridge source and tests.
- Existing R5 page/adapter/route state/Subject Flow/Journey, 07A progress API/store/component/CSS and their tests.
- `frontend/AGENTS.md` desktop-first, Subject Timeline and Patient Profile contracts.

## Allowed Paths And Ordering

- Worker 01 may edit only `poc/medical_monitoring_ai_native_r7/src/mm_r7/launch_registry.py`,
  `services/api/app/medical_monitoring_r7_product_router.py`, and directly related R7/product tests.
- Worker 02 may edit only new or existing files under `frontend/src/features/medical-monitoring/r7/` ending in
  `.mjs` / `.test.mjs`; no JSX/CSS/App or internal R5 adapter changes.
- Worker 03 may edit only medical-monitoring R5/R7 JSX/CSS/render tests and the minimal App route integration;
  no medical-writing files, backend, internal R5 validator or fixtures-as-publication.
- Dispatch is serialized: Worker 01, then Worker 02, then Worker 03 consumes their current-tree outputs.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.
- Do not start 8911/5174, services, browser, ego, real projects or models in execution workers. Codex owns the later
  isolated synthetic browser lifecycle and final visual acceptance.
- Preserve MTPLX slow-run semantics: frontend decisions use server state/lease/heartbeat, never local response timing.

## Work Items

1. 后端公开身份桥：在 launch_registry additive 持久化不可重铸 result_context_token，增加一 in-flight 门禁、八字段历史 status_text、public_run_token progress 和三个 result-context R5 projection GET；复用既有 R5 provider/assembler，补 product/R7/R5 tests。
2. 前端纯数据层：新增 07C-4 setup/history/public progress/result-context API、公开 envelope 验证、selected-run/向导/idempotency/离页恢复纯状态投影及 Node tests；不得修改现有 internal R5 validateEnvelope，不碰 JSX/CSS。
3. 前端产品接线：在 R5 项目页实现紧凑本次监查工作条、四步中文向导、历史抽屉、selected-run progress/result 切换、公开结果看板/Journey 路由与非叠加身份条，补 render tests/CSS；只消费已实现的 API/纯状态模块，不用 fixture 冒充发布结果。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
