# Execution Context: mm_r6_runtime_slice_06_20260828

Created: 2026-08-28 02:06:33
Objective: Implement and verify the synthetic/offline R6 slice-06 post_lock_pre_cfdi fixed-total outputs exactly under context/medical_monitoring_r6_runtime_slice_06_contract_20260828.md, preserving all accepted slice-01 through slice-05 behavior and boundaries.
Task type: `finite_code_task`
Risk: `medium`
Execution module trigger: Codex identified 3 independent work items, which is greater than two.

## Module Boundary

This is an execution module, not a conference. Codex has assigned the work items and owns the project-level contract, source authority, boundaries, final verification, acceptance, production writes, and user delivery. Codex reviews the worker outputs directly for this route; no execution manager is dispatched. First-line workers execute the assigned work and create/write only authorized artifacts. Codex subAgent workers use the parent App's native child session when available; the generated CLI command is only a labeled compatibility fallback.

## Assigned Roles

- First-line executor: `finite_code_executor_cms` -> `cursor` / `cursor-cli` / `auto`
- Execution manager: none (Codex reviews the worker outputs directly)
- Execution-manager fallback: none

## Source Of Truth

- `context/medical_monitoring_r6_runtime_slice_06_contract_20260828.md`（本纵切唯一执行合同）。
- `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md` §§6.4、14。
- `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R6。
- `reviews/medical_monitoring_r6_external_report_mode_output_contract_v0_1_20260827.md` §8.4-8.5。
- `artifacts/medical_monitoring_r6_external_report_mode_output_contract_v0_1/contract.json`。
- `context/medical_monitoring_r6_runtime_slice_05_acceptance_record_20260828.md`。
- 当前 `poc/medical_monitoring_ai_native_r6/src/mm_r6/mode_output.py` 与
  `poc/medical_monitoring_ai_native_r6/tests/test_mode_output.py`；slice-05 起始 SHA 分别为
  `34831cf8d8d00fedd108e198a7971e62643761eaee7390e5758997e9080b45ad` 与
  `0a31f3fb099fe175eb036bf37b89479dcc0852f1eec68b7a84b9ea4aeb8ccfb4`。

## Risk Boundaries

- 仅允许修改执行合同列出的 R6 POC 源码、测试、README 和 receipt allowlist；仅允许创建
  `poc/medical_monitoring_ai_native_r6/evidence/r6_post_lock_output_runtime_receipt.json`
  及本 task 的治理记录。
- 不修改 frontend/services/packages/runtime/deploy、R1-R5 或医学写作；不得读取或运行
  MG-K10、Ruxolitinib、MY008、MY009 等真实项目。
- 8911/5174 必须保持停止；不启动服务、浏览器、OCR、模型/provider。
- 不实现 Agent Harness、真实 parser/renderer、DOCX/PDF/HTML、Query/PD/签署/外发流程。
- 不引入第三方依赖、数据库、服务或新抽象层；复用现有 `mode_output.py` 和标准库。
- 不声称产品、医学、真实项目、格式渲染或 R6 总体接受。
- Worker 输出只是 Codex 验收证据，不是最终接受。

## Verification And Timeout

- 工作项必须串行运行；每个 runner 允许 120 分钟 hard wait，不做固定间隔轮询。
- 最低验证：focused `test_mode_output.py`、全 POC、normal/`-O`/`-OO` ×
  `PYTHONHASHSEED=0/1/42`、邻接 receipt、医学写作 aggregate、8911/5174 停止。
- 任何失败开放、身份/总量/嵌套引用漂移或测试回归均不得接受。

## Work Items

1. Implement the four post_lock_pre_cfdi payload builders and validators by reusing the existing ModeOutput and Run-gate identity framework.
2. Add deterministic positive and fail-closed tests for fixed locked identity, totals, nested identities, cross-output reconciliation, no overwrite, tamper, and mode isolation.
3. Run focused/full/optimizer-hash verification, update the slice-06 receipt and allowed documentation only, and return a compact evidence handoff.

## Completion And Cleanup

Codex reviews worker outputs, any manager report, and final artifacts. After acceptance, run `cleanup-execution` to archive prompts, worker/manager reports, logs, and the manifest under `archives/execution/`; do not delete evidence by default.
