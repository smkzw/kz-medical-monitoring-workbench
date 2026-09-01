# Codex Execution Plan: medical_monitoring_r5_s4_runtime_20260819

Objective: 实现并验证已接受合同限定的R5-S4 synthetic/offline renderer-neutral Risk Inspector runtime薄切，关闭89个运行语义挑战并保持R4/R5 S1-S3及8911边界

## Work Items

Execution order is strict `worker_01 -> worker_02 -> worker_03`; the files are coupled and workers
must not run in parallel.

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | W1：新建s4_contracts.py与s4_runtime_fixtures.py，落实typed contracts、closed mappings、hash/history/source/unavailable语义及focused tests | `runs/execution/medical_monitoring_r5_s4_runtime_20260819/worker_01.md` |
| `worker_02` | W2：新建s4_authority_builder.py、s4_projection.py及对应两项测试，从typed R4/R5 authority构建packet并确定性投影中文audience/audit/hash，关闭W1三项对齐，禁止runtime读取oracle文件 | `runs/execution/medical_monitoring_r5_s4_runtime_20260819/worker_02.md` |
| `worker_03` | W3：只新建validator、validator/read-only/challenge tests及SHA evidence；逐条真实关闭89 runtime cases，执行0-skip兼容相邻normal/O2/Ruff/compile/import/AST/8911门禁 | `runs/execution/medical_monitoring_r5_s4_runtime_20260819/worker_03.md` |

## Manager

No execution manager is dispatched for this route; Codex reviews the worker outputs directly.

## Codex Acceptance

TODO: verify artifacts, tests, source claims, rendered surfaces, blockers, and user-facing completeness.
