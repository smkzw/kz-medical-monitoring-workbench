# Codex Execution Plan: mm_r7_slice_04_progress_implementation_20260828

Objective: 按冻结合同 FROZEN_R7_SLICE_04_PROGRESS_CONTRACT_V0_2 实施 synthetic/offline 持久化 Run 进度事实面：复用未修改的 R1 Store/audience projection，在 R7 POC 增加薄 runtime adapter，在项目级 product router 增加显式 prepare 与只读 progress，并以聚焦测试证明身份、零 I/O、revision、中文投影和 fail-closed。不得启动服务、调用模型、运行真实项目、修改前端、R1 源码或医学写作。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现 R7 POC 薄 runtime progress adapter，仅复用 R1 Store/audience_progress，严格遵守 runtime 路径、身份校验、当前版本幂等和中文包装合同。 | `runs/execution/mm_r7_slice_04_progress_implementation_20260828/worker_01.md` |
| `worker_02` | 在 services/api/app/medical_monitoring_r7_product_router.py 最小挂载 prepare/progress 路由，保持 canonical 项目、权限、catch-all、每请求关闭和既有产品错误边界。 | `runs/execution/mm_r7_slice_04_progress_implementation_20260828/worker_02.md` |
| `worker_03` | 新增 Slice-04 聚焦离线测试与 receipt/README 草案，覆盖冻结合同验收矩阵；运行最小测试并报告，不触碰 R1/前端/医学写作。 | `runs/execution/mm_r7_slice_04_progress_implementation_20260828/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

- Inspect every diff and compare it to frozen v0.2; reject new schedulers, duplicate progress state or R1 edits.
- Run focused Slice-04, full R7, adjacent R1/R6 and product router tests plus Ruff/compileall.
- Rebuild counts/revisions directly from SQLite and scan product JSON for forbidden fields/technical labels.
- Recheck R1/frontend/medical-writing boundaries and 8911/5174 stopped.
- Complete receipt, execution review/metrics and audit-execution before any limited acceptance.
