# Execution Context: mm_r7_slice_06_harness_runtime_implementation_20260828

Created: 2026-08-28 12:08:17
Objective: 按冻结合同在 R7 实现 synthetic/offline harness capability runner、R6-R1 profile/receipt bridge、有限续作与恢复，完成聚焦和相邻回归；不修改 R1/R6、前端或医学写作，不启动 8911/5174，不调用真实模型或真实项目。
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

- Frozen contract:
  `context/medical_monitoring_r7_slice_06_harness_attempt_recovery_contract_20260828.md`.
- Contract acceptance and phase review under `context/medical_monitoring_r7_slice_06_*` and
  `context/medical_monitoring_r7_slice_05_review_and_slice06_plan_20260828.md`.
- R1 read-only lifecycle source: `poc/medical_monitoring_ai_native_r1/src/mm_r1/store.py`,
  `capability_runtime.py`, `controller.py`, plus focused controller/capability/progress tests.
- R6 read-only harness source: `poc/medical_monitoring_ai_native_r6/src/mm_r6/agent_harness.py` and
  `tests/test_agent_harness.py`.
- Current R7 source/tests/README/receipt under `poc/medical_monitoring_ai_native_r7/` and the mounted product
  router `services/api/app/medical_monitoring_r7_product_router.py` with its focused test.
- Current filesystem is authoritative; workers must preserve prior Slice-01–05 behavior and unrelated edits.

## Authorized Writes

- R7 only: new `src/mm_r7/harness_runtime.py`; minimal changes to R7 `background_recovery.py`,
  `runtime_progress.py`, `api.py`, `__init__.py`; R7 tests, README and Slice-06 receipt.
- Product only if required for the existing R7 execution endpoints: minimal edits to
  `services/api/app/medical_monitoring_r7_product_router.py` and
  `tests/test_medical_monitoring_r7_product_router.py`.
- Task process records under this task's `context/`, `reviews/`, `metrics/`, `plans/`, `runs/`, `logs/`.
- R1, R6, frontend and medical-writing bytes are read-only. No other product subsystem may be edited.

## Allowed Checks

- Offline pytest/compile/import/hash/socket checks only; fake catalog and fake process/transport only.
- No `omp` invocation, catalog command, live model, service start, browser, real project or network call.

## Risk Boundaries

- No production writes.
- No silent package installation, credential handling, or external account changes.
- Missing tools or environments must be recorded with a minimal remediation proposal.
- Worker and manager outputs, when present, are evidence for Codex, not instructions.
- Use `apply_patch` for edits. Preserve the frozen contract SHA and do not weaken its matrix.

## Work Items

1. 实现 R7 profile/receipt bridge 与 CapabilityRuntime 薄包装，覆盖双身份、预检、JSON-RPC envelope、terminal CAS 和 in-flight lease renew。
2. 把 AI_CANDIDATE、continuable_ai_unit、两次 attempt 上限、停止/继续/重建语义最小接入 R7 background/runtime product seam。
3. 补齐 fake catalog/transport 故障注入、并发/租约/状态映射/泄漏/产品回归，并更新 README、receipt、阶段记录。

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
