# Codex Execution Plan: medical_monitoring_r4_d08_artifacts_20260814

Objective: 以已双审放行且哈希固定的 D08 v0.5 合同为唯一语义输入，构建不少于200条 synthetic/offline typed fixture catalog、独立 expected-outcome oracle、五列双射 manifest registry、确定性只验证装配 generator 及负向变异测试；不得实现 runtime、启动8911、读取真实项目或触碰产品/医学写作

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 设计并实现 deterministic D08 artifact generator、exact schema/hash/semantic binding 与 replay validation，只复用 D07 工程模式不复制临床语义 | `runs/execution/medical_monitoring_r4_d08_artifacts_20260814/worker_01.md` |
| `worker_02` | 物化不少于200条 D08 typed synthetic fixtures，覆盖合同§12分区、owner zero-risk、cutoff、temporal、identity、propagation、visibility、fanout 与 anti-overfit | `runs/execution/medical_monitoring_r4_d08_artifacts_20260814/worker_02.md` |
| `worker_03` | 独立物化 exact expected-outcome oracle、五列双射 registry/manifest/assertion DSL，并实现负向变异与双遍字节一致性验证 | `runs/execution/medical_monitoring_r4_d08_artifacts_20260814/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
