# Execution Context: mm_r7_slice_04_progress_implementation_20260828

Created: 2026-08-28 08:26:37
Objective: 按冻结合同 FROZEN_R7_SLICE_04_PROGRESS_CONTRACT_V0_2 实施 synthetic/offline 持久化 Run 进度事实面：复用未修改的 R1 Store/audience projection，在 R7 POC 增加薄 runtime adapter，在项目级 product router 增加显式 prepare 与只读 progress，并以聚焦测试证明身份、零 I/O、revision、中文投影和 fail-closed。不得启动服务、调用模型、运行真实项目、修改前端、R1 源码或医学写作。
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

- Frozen contract: `context/medical_monitoring_r7_slice_04_durable_run_progress_contract_20260828.md`
  SHA-256 `a5033b871ffd025cc5dd6345fb9a1bd214e41f01e3893ef2f94ca7ac6d830745`.
- Contract conference review/metrics and both participant reports for defect context only.
- R1 read-only reuse sources: `poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py`, `store.py`,
  `audience_progress.py`, `background_progress.py`.
- R7 sources: `poc/medical_monitoring_ai_native_r7/src/mm_r7/run_entry.py`, `run_binding.py`,
  `profile_store.py`, existing tests and README.
- Product surface: `services/api/app/medical_monitoring_r7_product_router.py` and
  `tests/test_medical_monitoring_r7_product_router.py`.

Authorized writes are limited to:

- new `poc/medical_monitoring_ai_native_r7/src/mm_r7/runtime_progress.py`;
- minimal `poc/medical_monitoring_ai_native_r7/src/mm_r7/__init__.py` export only if actually required;
- `services/api/app/medical_monitoring_r7_product_router.py`;
- new Slice-04 tests under `poc/medical_monitoring_ai_native_r7/tests/` and/or
  `tests/test_medical_monitoring_r7_product_router.py` additions;
- `poc/medical_monitoring_ai_native_r7/README.md` and new
  `poc/medical_monitoring_ai_native_r7/evidence/r7_durable_progress_receipt.json`.

No other source or artifact path is write-authorized in this execution pass.

## Risk Boundaries

- No frontend, R1/R6 source, real-project, medical-writing or unrelated product writes.
- Do not start 8911/5174, background workers, browser, model/harness calls or real project execution.
- Offline TestClient, temporary directories, SQLite fixtures, pytest, Ruff and compileall are allowed.
- Workers run serially in declared order. Each worker must inspect the prior worker's current filesystem result
  before editing and preserve it; no worker may undo another worker's changes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.

## Work Items

1. 实现 R7 POC 薄 runtime progress adapter，仅复用 R1 Store/audience_progress，严格遵守 runtime 路径、身份校验、当前版本幂等和中文包装合同。
2. 在 services/api/app/medical_monitoring_r7_product_router.py 最小挂载 prepare/progress 路由，保持 canonical 项目、权限、catch-all、每请求关闭和既有产品错误边界。
3. 新增 Slice-04 聚焦离线测试与 receipt/README 草案，覆盖冻结合同验收矩阵；运行最小测试并报告，不触碰 R1/前端/医学写作。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
