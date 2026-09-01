# Codex Execution Plan: medical_monitoring_r2_kernel_execution_20260810

Objective: 在隔离 R2 namespace 连续实施领域内核、审计与迁移底座，逐批提交可验证代码、测试和证据，保持产品、医学写作、真实项目、R1与8911冻结

## Work Items

| Worker | Assigned item | Report |
|---|---|---|
| `worker_01` | 批次A：实现schema registry、来源/知识/规则/mapping/facts与SnapshotAcceptance状态链及测试 | `runs/execution/medical_monitoring_r2_kernel_execution_20260810/worker_01.md` |
| `worker_02` | 批次B：实现风险身份/生命周期/裁决、双基线、三ModeContract与full/incremental diff及测试 | `runs/execution/medical_monitoring_r2_kernel_execution_20260810/worker_02.md` |
| `worker_03` | 批次C（用户功能最小底座）：实现 SQLite 持久化、原子保存/恢复、幂等提交、发布读取一致性、R1只读adapter及合成迁移/回滚；不扩展系统安全设计/测试 | `runs/execution/medical_monitoring_r2_kernel_execution_20260810/worker_03.md` |

执行严格串行：worker_01 → Codex A gate → worker_02 → Codex B gate → worker_03 → manager。三个 worker 不并发写共享 namespace。

## File Mapping And Gates

| Batch | Owned modules | Required gate |
|---|---|---|
| A | `schema_registry.py`, `domain.py`, `identity.py`, `artifacts.py`, `acceptance.py`, `test_r2_a_*` | registry/compatibility、不可变来源、内容寻址、版本合同、快照资格不可跳级、歧义 fail-closed；批次与全 R2 tests |
| B | `risk.py`, `baselines.py`, `modes.py`, `diff.py`, `test_r2_b_*` | 风险生命周期追加、merge/split/ambiguous/superseded/not_evaluable、双基线、三模式不可静默转换、全量快照 diff；批次与全 R2 tests |
| C | `store.py`, `audit.py`, `migration.py`, `legacy_adapter.py`, `verification.py`, `test_r2_c_*` | 用户功能所需的保存/恢复/读取一致性、幂等提交、发布指针、R1 零写入双读、合成迁移/回滚；不做攻防或额外安全专项；批次与全 R2 tests |

共同标准：Python 3.9 标准库、pytest 临时目录、canonical JSON/hash、显式 SQLite 事务、synthetic/offline、无绝对真实项目路径、无共享依赖变更。失败/中断/partial/truncated/not_evaluable 不可进入可发布状态。安全专项与攻防测试不在本轮范围；验证聚焦用户数据不丢失、可恢复、增量更新与读取一致性。

## Current Gate

- Batch A：独立 ACCEPT，作为不可变历史。
- Batch B：累积独立 ACCEPT；R2 冻结内容清单 `ecf9d07df74fc3ff6a2d775a91683de24a6db2eecf77e6a6ad3f4f9ec02e064f`，全量 `493 passed`。
- Batch C：独立 ACCEPT；R2-C `105 passed`、全 R2 `598 passed`，冻结清单 `69033e28616ca497579d7b3b9bbbd87ab8fc3031eb7d0259ba3954db1a338003`。R2 执行计划完成，转入 R3。

## Manager

| Role | Provider | Model | Report |
|---|---|---|---|
| `finite_code_manager_cursor` | `cursor-cli` | `auto` | `runs/execution/medical_monitoring_r2_kernel_execution_20260810/manager.md` |

## Codex Acceptance

Codex 逐批读取实际实现，运行 compileall、批次测试、全 R2 测试和针对失败模式的复核；检查 R1/产品/医学写作/真实项目/8911 未变。完成三批后由 manager 汇总，再以 fresh-context 独立 reviewer 复核 schema、迁移、篡改、并发和回滚证据。未经过 review gate 不宣称 R2 完成。
