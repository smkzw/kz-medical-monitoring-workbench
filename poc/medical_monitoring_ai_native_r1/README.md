# Medical Monitoring AI-Native R1 POC

这是一个仅含人工构造 `SYNTHETIC` 数据的隔离 R1 第一纵切。它验证
框架中立 Graph IR、SQLite 权威状态、JSON 内容寻址 artifact、正交状态、
AE/MH 漏报候选、三模式/报告覆盖合同和恢复失败路径。该目录不连接现有
产品、医学写作、真实项目、服务或 provider。

当前另含一个 provider-neutral capability runtime 隔离切片：它固化用户选择的
执行 profile，以同一 JSON-RPC 形合同验证注入式 API transport 和本地合成 harness，
并保持 raw-first、candidate-only、coverage fail-closed。应用拥有的 SQLite attempt
journal 还验证了跨连接原子认领、终态重放、过期租约隔离、迟到回调拒绝，以及
中断历史通过新 attempt 显式续接。raw 证据读取还会核验外层/嵌套哈希及引用身份；
缺失或损坏会使关联候选完整性失败并被恢复扫描报告，而不会自动修复。该切片不调用
真实端点，也不表示 OS 级执行隔离、真实进程 checkpoint 恢复或 R1 总体验收完成；证据与剩余缺口见
`docs/R1_CAPABILITY_RUNTIME_EVIDENCE.md` 和 `docs/R1_ADAPTER_FAILURE_MATRIX.md`。

## 运行测试

从 workbench 根目录运行完整 POC 测试目录：

```bash
.venv/bin/python -m pytest -q poc/medical_monitoring_ai_native_r1/tests
```

从本目录运行也可以：

```bash
../../.venv/bin/python -m pytest -q tests
```

`tests/test_failure_injection.py` 是 worker_04 的黑盒故障注入和跨模块
回归集。它包含 artifact 写入/提交边界、重复与迟到回调、partial/truncated、
审计链篡改、Store 派生的快照接受资格、adapter 候选隔离、merge/split lineage、
报告 ledger 发布门和 manifest replay 进度分母。快照接受资格同时绑定 live Store、
当前项目与当前 snapshot version；跨项目或旧版本的 eligible snapshot 不得授权风险关闭。

## 运行可检查 demo

demo 必须接收调用者提供的新输出目录；它不会覆盖已有的 `r1.sqlite3` 或
已知输出文件：

```bash
.venv/bin/python poc/medical_monitoring_ai_native_r1/scripts/run_demo.py \
  --output-dir /path/to/a/new/synthetic-r1-output
```

也支持位置参数：

```bash
.venv/bin/python poc/medical_monitoring_ai_native_r1/scripts/run_demo.py \
  /path/to/a/new/synthetic-r1-output
```

输出目录包含：

- `r1.sqlite3`：SQLite 权威状态；
- `artifacts/*.json`：内容寻址 artifact 文件；
- `acceptance.json`：从 Store 读取的 N/N+1 acceptance 与 baseline eligibility；
- `run.json`、`progress.json`：正交 Run 状态和 manifest 进度分母；
- `audit.json`、`recovery.json`：审计链与恢复检查结果；
- `projections.json`：项目/中心/受试者 Profile/Timeline 投影；
- `report_ledger.json`：正文/表/图/脚注 coverage ledger；
- `summary.json`：上述证据的紧凑索引。

demo 只执行本地 synthetic 代码，不启动服务、不调用 provider；输出达到
`draft_exportable` 也只是 POC 内部状态，不是产品发布或医学结论。

## 当前证据边界

R1 证据必须把直接命令观察与剩余限制分开。测试或 demo 通过不代表 UI、
产品迁移、真实项目运行、provider 集成、临床正确性、监管批准或商业化就绪。
当前实现型缺口与 manager 的精确下一步记录在 `docs/R1_EVIDENCE.md`；框架/存储
决策记录在 `docs/ADR-001-framework-neutral-sqlite.md`。
