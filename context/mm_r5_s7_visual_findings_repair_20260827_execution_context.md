# Execution Context: mm_r5_s7_visual_findings_repair_20260827

Created: 2026-08-27 09:56:53
Objective: 按当前三模型真实浏览器发现，对R5-S7合成离线产品做最小纠偏：连续真实访视日期、八域轨道与可见语义缩放、受试者身份条一致、原始来源精确字段可见；保持GET-only、合成离线、医学写作542文件边界，不改安全实现；完成聚焦/相邻回归与build。
Task type: `long_horizon_code`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_opencode_flash` -> `codex-subagent` / `codex` / `gpt-5.6-luna`
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

1. 后端与夹具：仅修改services/api/app/medical_monitoring_r5_product_adapter.py及对应tests/test_medical_monitoring_r5_product_adapter.py、tests/test_medical_monitoring_r5_product_router.py；修正40访视连续实际日期，确保来源evidence已有record_ref/canonical_location/excerpt可供前端直观呈现；不得修改鉴权、安全或医学写作。
2. 前端体验：仅修改frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx、medicalMonitoringR5.css及同目录现有R5测试；实现八域分轨展示与+/-/0键盘及可见按钮语义缩放、身份条从canonical route回填项目/批次/版本、来源页展示原始定位/记录号/引文；保持中文原生与GET-only。
3. 独立验证：只读核验前两项当前bytes，运行R5聚焦及相邻测试、production build、禁止词/GET-only/医学写作542文件摘要/8911和5174停止检查；输出ACCEPT或REVISE，不修改源码。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
