# Codex Execution Plan: mm_r7_slice_06_matrix14_live_smoke_20260828

Objective: 在不启动产品服务、不使用真实项目、不修改产品源码的前提下，串行完成 R7 Slice-06 matrix-14 的两个 synthetic 最小真实 OMP smoke：默认 MTPLX medium 与显式 DeepSeek max；固定 profile/catalog/argv/终态/receipt，不允许 fallback 或模型替换。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 只读核对冻结合同、R7/R6 当前入口和前次 R6 smoke 证据，给出本次 R7 end-to-end synthetic smoke 的最小可执行方案、断言、临时输出边界；不得调用模型或修改文件。 | `runs/execution/mm_r7_slice_06_matrix14_live_smoke_20260828/worker_01.md` |
| `worker_02` | 仅在 Codex 已确认前置核对后，使用独立临时 workspace 通过当前 R7 RunEntry→RuntimeProgress→HarnessRuntime→R6 OmpPrintAdapter 路径执行一次默认 MTPLX medium synthetic smoke；不得 fallback、不得真实项目、不得服务；返回去敏 profile/catalog/argv/时长/终态/receipt/hash。 | `runs/execution/mm_r7_slice_06_matrix14_live_smoke_20260828/worker_02.md` |
| `worker_03` | 仅在 MTPLX smoke 已由 Codex 判定终态后，使用另一独立临时 workspace 通过同一 R7 路径执行一次显式 DeepSeek max synthetic smoke；不得 fallback、不得真实项目、不得服务；返回去敏 profile/catalog/argv/时长/终态/receipt/hash。 | `runs/execution/mm_r7_slice_06_matrix14_live_smoke_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

Codex will verify worker route identity, exact R7/R6 call path, serial ordering,
temporary-only writes, frozen profile/catalog/argv identity, empty fallback
chain, terminal R1/R7 state, receipt/stdout hashes, stopped ports, and the
absence of real project/source-tree changes. A smoke passes only when the single
work unit is terminal `PASSED`, receipt state is `complete`, parse is `parsed`,
coverage is complete, `analysis_complete=true`, and `fallback_used=false`.
Failure is recorded exactly and does not trigger substitution or an automatic
second call.

Codex rejected worker_01's fake-`popen_factory` suggestion because matrix 14 is
an authentic OMP/model connectivity gate with synthetic data, not a second
offline fake transport test. Workers 02/03 are authorized only for the full
background R7 path described in the execution context.

## Current Gate State — 2026-08-28

- MTPLX initial live attempt: failed before spawn with
  `invalid_invocation_id`; preserved as history.
- R7-only mapping/output-contract repair: independently reviewed and offline
  accepted (`34` focused, `158` R7, `33` product, `311` R1, `758` R6).
- Controlled MTPLX repair retry: authentic model call timed out at 120.046 s;
  no fallback. Its linked attempt was recovered as interrupted after the outer
  evidence reader ended; retry limit is reached.
- DeepSeek worker_03 remains pending. The serial gate is not released because
  MTPLX did not satisfy the PASS criteria.
