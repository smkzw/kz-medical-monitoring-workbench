# Codex Execution Plan: mm_r7_slice07c3_result_publication_implementation_20260829

Objective: 按冻结 07C-3 v0.2 合同实现 synthetic/offline 原子结果发布、R5 authority bridge、registry v2、progress/result-entry，并以故障矩阵和 R5/R7 产品回归证明；保持 8911、真实项目和医学写作停止。

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 在 R5 POC 内实现 R5PublicationAuthorityInputAssembler 与 R5PublicationAuthorityBridge，唯一复用既有 S4 builder/validator，补聚焦测试；仅改 R5-owned 文件。 | `runs/execution/mm_r7_slice07c3_result_publication_implementation_20260829/worker_01.md` |
| `worker_02` | 在 R7 launch_registry 中实现 schema v2 additive migration、ResultPublication store/state/CAS/原子 finalize 与迁移/故障测试；仅改 registry 及其测试。 | `runs/execution/mm_r7_slice07c3_result_publication_implementation_20260829/worker_02.md` |
| `worker_03` | 在 R7 产品 router/harness 接入 receipt 公共分类、双 manifest/site/member 门禁、publication progress/history/result-entry，并补产品故障矩阵和相邻回归；不得预造 07C-4 Journey UI。 | `runs/execution/mm_r7_slice07c3_result_publication_implementation_20260829/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

- Review all three worker reports plus Worker 02 follow-up 1 and Worker 03 follow-ups 1-2.
- Reject pre-reservation runtime reads; require registry CAS binding and a source-order assertion.
- Independently reproduce R5 bridge, registry, product fault matrix, combined R7/R5 regression, compile and stopped ports.
- Run execution audit, then an independent code acceptance conference before cleanup.
