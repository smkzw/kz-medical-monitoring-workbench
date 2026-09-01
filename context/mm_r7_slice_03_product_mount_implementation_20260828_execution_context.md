# Execution Context: mm_r7_slice_03_product_mount_implementation_20260828

Created: 2026-08-28 05:40:12
Objective: 按冻结 SHA 23a01f90 的 R7 Slice-03 合同实现项目级医学监查 R7 产品挂载：局部中文响应、合法项目解析后打开每项目工作区、每请求关闭连接、MTPLX 默认/显式 DeepSeek、最小 main.py 接线与离线回归；不得启动服务/真实模型/真实项目，不得修改医学写作、前端或 R1-R6
Task type: `finite_code_task`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `cursor` / `cursor-cli` / `auto`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- Frozen contract: `context/medical_monitoring_r7_slice_03_product_mount_contract_20260828.md`, SHA-256 `23a01f905fa1d19566873b0f04bd8a55f38f37e9ce28529a09a39a1f75f89b9b`.
- Accepted core: `poc/medical_monitoring_ai_native_r7/src/mm_r7/{run_entry,api,profile_store,run_binding}.py`; do not modify these files.
- Product seams: `services/api/app/main.py`, `medical_monitoring_r5_product_router.py`, `medical_monitoring_router.py`, `monitoring_identity_authorization.py`.
- Test conventions: `tests/` and `poc/medical_monitoring_ai_native_r7/tests/`.
- Current pins: `main.py a9079352...ffc8`, `run_entry.py b0c0c8c6...fe29`, `api.py e8a7e81c...b53c`.

## Success Criteria

- Product prefix is `/api/projects/{project_id}/modules/medical-monitoring/r7`; isolated `/api/medical-monitoring/r7` is not mounted.
- Project resolution and existing principal/action seam run before any R7 directory or SQLite open.
- Product DTO omits duplicate `project_id`, `project_scope_key`, and cross-run override selection; project/run layers are auto-selected only when the canonical record exists.
- R7 responses are top-level `{code, message}` with Chinese `message`; no app-wide exception handler changes non-R7 responses.
- Per-request entry closes both stores; import/router construction makes no R7 directory/SQLite/schema write; bootstrap alone seeds MTPLX medium; name-only DeepSeek resolves to max without fallback.
- Focused product tests, R7 full, R6 full, compile/Ruff and selected adjacent product tests pass; ports remain stopped; medical-writing aggregate is unchanged.

## Risk Boundaries

- No production writes.
- No service start, browser, real model/provider invocation, real project, or persistent runtime mutation. Tests use temporary directories/apps only.
- No edits to frontend, `medical_writing*`, writing-reference, R1-R6, or frozen R7 Slice-01/02 core.
- Do not register `mm_r7.api.install_exception_handlers` on product `app`.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 实现 services/api/app/medical_monitoring_r7_product_router.py：项目级薄适配、产品 DTO、局部中文错误、自动 scope、每请求生命周期；只改该新文件
2. 实现 tests/test_medical_monitoring_r7_product_router.py：覆盖零导入写入、项目隔离、bootstrap、MTPLX、名称型 DeepSeek、scope、replay/conflict、中文错误与非 R7 错误不变；只改该新文件
3. 完成 services/api/app/main.py 最小 import/include 接线并生成 Slice-03 离线 receipt/README 进度更新；不得触碰其他产品/前端/医写文件

## Authorized Write Paths

- Worker 01: `services/api/app/medical_monitoring_r7_product_router.py` only.
- Worker 02: `tests/test_medical_monitoring_r7_product_router.py` only.
- Worker 03: `services/api/app/main.py`, `poc/medical_monitoring_ai_native_r7/README.md`, and new `poc/medical_monitoring_ai_native_r7/evidence/r7_product_mount_receipt.json` only.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
