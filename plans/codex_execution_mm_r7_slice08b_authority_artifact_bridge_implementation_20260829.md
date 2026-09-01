# Codex Execution Plan: mm_r7_slice08b_authority_artifact_bridge_implementation_20260829

Objective: 按已冻结R7 Slice-08B合同v0.1+v0.2实施真实R5/R6/R1权威-产物桥接、LaunchRegistry v4与最小产品接线；synthetic/offline，保持UI、8911/5174、真实项目/模型及医学写作不变

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现最小continuity_bridge.py及聚焦测试：只复用R5 typed packet、R6 frozen ModeContract/validators、R1 Store ArtifactEnvelope，完成四输出摘要、五类原子提取、成员/字节复核与机器计算验证结果 | `runs/execution/mm_r7_slice08b_authority_artifact_bridge_implementation_20260829/worker_01.md` |
| `worker_02` | 实现LaunchRegistry v3到v4 additive migration、ResultPublication/CarryForwardPlan新摘要与成员字段、序列化、故障注入、finalize同事务CAS和重放冲突测试；不得重写R2或R1-R6 | `runs/execution/mm_r7_slice08b_authority_artifact_bridge_implementation_20260829/worker_02.md` |
| `worker_03` | 完成最小产品路由接线与synthetic provider测试，核对R5/R6/R1跨层身份、三模式四输出和结果发布；运行聚焦/相邻回归并报告未覆盖边界，不启动服务或真实项目 | `runs/execution/mm_r7_slice08b_authority_artifact_bridge_implementation_20260829/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
