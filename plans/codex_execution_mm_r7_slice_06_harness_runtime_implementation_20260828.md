# Codex Execution Plan: mm_r7_slice_06_harness_runtime_implementation_20260828

Objective: 按冻结合同在 R7 实现 synthetic/offline harness capability runner、R6-R1 profile/receipt bridge、有限续作与恢复，完成聚焦和相邻回归；不修改 R1/R6、前端或医学写作，不启动 8911/5174，不调用真实模型或真实项目。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现 R7 profile/receipt bridge 与 CapabilityRuntime 薄包装，覆盖双身份、预检、JSON-RPC envelope、terminal CAS 和 in-flight lease renew。 | `runs/execution/mm_r7_slice_06_harness_runtime_implementation_20260828/worker_01.md` |
| `worker_02` | 把 AI_CANDIDATE、continuable_ai_unit、两次 attempt 上限、停止/继续/重建语义最小接入 R7 background/runtime product seam。 | `runs/execution/mm_r7_slice_06_harness_runtime_implementation_20260828/worker_02.md` |
| `worker_03` | 补齐 fake catalog/transport 故障注入、并发/租约/状态映射/泄漏/产品回归，并更新 README、receipt、阶段记录。 | `runs/execution/mm_r7_slice_06_harness_runtime_implementation_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

- Review every worker diff and current bytes; participant output is not acceptance.
- Require matrix 1–16 focused evidence, then R7/R1/R6 functional/product adjacent regression.
- Confirm R1/R6/frontend/medical-writing non-cache bytes unchanged and ports 8911/5174 stopped.
- Do not run real smoke until offline implementation and independent implementation conference pass.

## Completion State

- All three governed work items have terminal reports on the declared Luna/max
  CLI-compatibility route; no fallback was used.
- Codex corrected the timeout-plus-identity-drift retry defect and independently
  verified harness 30, product 33, R7 155, R1 functional 311, R6 functional 758,
  determinism/boundary 15, isolated compilation and receipt digests.
- Execution status: offline implementation accepted after Codex correction.
- Still pending outside this execution packet: independent implementation
  conference, then separately authorized MTPLX/DeepSeek synthetic live smoke.
