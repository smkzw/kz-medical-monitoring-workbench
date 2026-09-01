# Execution Context: mm_r7_slice_05_background_recovery_implementation_20260828

Created: 2026-08-28 09:49:48
Objective: 按冻结合同 FROZEN_R7_SLICE_05_BACKGROUND_RECOVERY_V0_2 实施 synthetic/offline 后台执行与中断恢复：单一 SQLite 进度事实源、R7 run-level 控制租约、依赖感知调度、停止/继续、consistent snapshot 和产品中文 overlay；不得改 R1/R6、前端、医学写作，不启动服务/模型/真实项目。
Task type: `long_horizon_code`
Risk: `high`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `long_horizon_code_executor_opencode_flash` -> `codex-subagent` / `codex` / `gpt-5.6-luna`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- Frozen contract: `context/medical_monitoring_r7_slice_05_background_recovery_contract_20260828.md`, SHA-256 `590285e545a0d61ac9049b278e4b61cfaef8e1a22f56131a842ff7677978d65d`.
- Slice-04 accepted adapter/router/tests are the current integration baseline.
- R1 `background_progress.py`, `store.py`, `audience_progress.py` and tests are read-only reuse sources.

Authorized writes are limited to:

- new `poc/medical_monitoring_ai_native_r7/src/mm_r7/background_recovery.py`;
- minimal `poc/medical_monitoring_ai_native_r7/src/mm_r7/runtime_progress.py` integration;
- `services/api/app/medical_monitoring_r7_product_router.py`;
- new `poc/medical_monitoring_ai_native_r7/tests/test_background_recovery.py`;
- additions to `tests/test_medical_monitoring_r7_product_router.py` and
  `poc/medical_monitoring_ai_native_r7/tests/test_determinism_adjacent.py`;
- `poc/medical_monitoring_ai_native_r7/README.md` and new
  `poc/medical_monitoring_ai_native_r7/evidence/r7_background_recovery_receipt.json`.

No other source or artifact path is write-authorized.

## Risk Boundaries

- No R1/R6 source, frontend, real-project, model/harness or medical-writing writes.
- Do not start 8911/5174 or any live service. Offline threads, TestClient,
  temporary SQLite fixtures, pytest and compileall are allowed.
- Workers run serially and must preserve prior worker changes.

- TODO: Codex must add authoritative source files, screenshots, datasets, or URLs before dispatch.
- Do not add production paths without explicit Codex authorization.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 实现 R7 background recovery/control adapter：控制表、状态机、原子 claim/CAS heartbeat、依赖感知 synthetic worker、停止/继续和一致快照；仅新增 R7 模块并最小接 runtime_progress。
2. 在项目级 product router 最小挂载 start/resume/cancel 与 progress overlay，保持 canonical 项目、权限、catch-all、每请求关闭和中文泄漏阻断。
3. 新增 Slice-05 聚焦离线测试、失败注入、双连接并发、依赖阻断、边界回归、README 与 receipt 草案；不得启动 8911/5174、模型或真实项目。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
