# Codex Execution Plan: medical_monitoring_ai_native_r1_slice1_20260809

Objective: 在poc/medical_monitoring_ai_native_r1内实现并验证R1第一纵切，严格遵循medical_monitoring_ai_native_r1_poc_20260809_context.md；不得触碰现有产品、医学写作、8911或真实项目

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 实现框架中立domain/schema/graph IR与SQLite原子权威存储、audit chain、artifact coverage和恢复协议 | `runs/execution/medical_monitoring_ai_native_r1_slice1_20260809/worker_01.md` |
| `worker_02` | 实现synthetic双快照、AE/MH漏报候选/反证/稳定风险身份/Query与Profile-Timeline-中心-项目投影 | `runs/execution/medical_monitoring_ai_native_r1_slice1_20260809/worker_02.md` |
| `worker_03` | 实现AI Adapter公共状态合同、三类ModeContract与report ClaimCoverageLedger的fail-closed最小能力 | `runs/execution/medical_monitoring_ai_native_r1_slice1_20260809/worker_03.md` |
| `worker_04` | 实现故障注入、幂等/迟到回调/partial-truncated/身份歧义/重放测试与可审计证据说明 | `runs/execution/medical_monitoring_ai_native_r1_slice1_20260809/worker_04.md` |

## Sequence And Ownership

1. `worker_01` 建立公共领域、Graph IR 与持久化合同。
2. `worker_02` 与 `worker_03` 只消费该公共合同，并仅写各自独占文件；可在 `worker_01` 完成后独立执行。
3. `worker_04` 在前三者产物存在后编写跨模块故障注入、demo、ADR 与证据说明。
4. Manager 进行全量集成测试、边界审阅和最小修复；Codex 使用新鲜上下文独立验收。

具体文件所有权、公共接口、风险边界、成功与停止条件以 `context/medical_monitoring_ai_native_r1_slice1_20260809_execution_context.md` 为准。

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `finite_code_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_ai_native_r1_slice1_20260809/manager.md` |

## Codex Acceptance

- 核对所有新增文件均位于 `poc/medical_monitoring_ai_native_r1/`，且无真实项目标识/路径或外部 provider 调用。
- 使用共享 `.venv/bin/python -m pytest -q poc/medical_monitoring_ai_native_r1/tests` 独立运行全量测试。
- 运行 `scripts/run_demo.py` 并检查实际 SQLite/JSON artifact、正交状态、coverage、audit chain 与投影输出。
- 复核 failure-injection 测试不会产生假完成、重复副作用或候选/事实混淆。
- 把本 slice 验收结论写入 task review/metrics/context；不得宣称产品或真实项目完成。
