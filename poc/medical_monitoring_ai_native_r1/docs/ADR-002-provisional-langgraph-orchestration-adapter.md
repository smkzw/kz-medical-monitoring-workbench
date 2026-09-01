# ADR-002：暂定 LangGraph 为下一轮隔离验证的首选编排适配器

## 状态

2026-08-09，**接受但带硬门**。本决策仅适用于医学监查 AI-native R1
隔离 POC 的下一轮验证，不批准产品级依赖、共享运行库升级、真实项目运行、
生产迁移或 R1 完成声明。

本 ADR 确认并延续 `ADR-001-framework-neutral-sqlite.md`，不取代其领域权威
边界。

## 问题

R1 已经证明框架中立领域内核、SQLite 权威状态、内容寻址 artifact、恢复与
审计不变量，并用相同合同隔离验证了 LangGraph 和 Microsoft Agent Framework。
现在需要决定下一轮复杂图与 AI Capability Adapter 验证优先使用哪个编排器，
同时避免把框架 checkpoint、session 或消息对象误升为医学事实、风险、Run 或
发布状态的权威。

## 决策

### 1. 永久保持框架中立的领域边界

以下对象继续由应用拥有，任何编排框架不得替代：

- 版本化 Graph IR、`GraphPort` 与 `CheckpointPort` 合同；
- SQLite 中的 Monitoring Run、manifest、节点、事实、风险、coverage、发布与
  追加式审计状态；
- canonical JSON 内容寻址 artifact 及其来源、哈希、coverage 和 QC 元数据；
- publication gate、身份绑定、幂等键、恢复和回滚规则。

LangGraph、Agent Framework 或未来其他引擎的 checkpoint 只保存可丢弃、可
重建的**运行控制状态**。它们不得写入或覆盖领域权威，也不得成为用户界面进度
分母或医学结论来源。

### 2. LangGraph 作为“下一轮隔离验证的首选编排适配器”

固定验证组合：

| 组件 | 固定版本 | 许可 | 最低运行时 |
|---|---:|---|---|
| `langgraph` | 1.2.10 | MIT | Python ≥3.10 |
| `langgraph-checkpoint` | 4.2.0 | MIT | Python ≥3.10 |
| `langgraph-checkpoint-sqlite` | 3.1.1 | MIT | Python ≥3.10 |

继续强制 `LANGGRAPH_STRICT_MSGPACK=true`、静态 checkpoint metadata 白名单、
必填且精确匹配的 `run_id`、非空 state blob、精确 Graph IR 绑定，以及缺失或
损坏 checkpoint 的公开恢复接口 fail-closed。

这里的“首选”只表示下一轮隔离验证先实现并运行 LangGraph adapter；不表示：

- LangGraph 是领域模型或医学权威；
- 已批准写入产品依赖或共享 `.venv`；
- 已证明多进程并发、断电、跨机器或生产级耐久性；
- 已批准用框架内部进度、消息或 session 直接投影给医学监察员；
- R1 已完成。

### 3. Agent Framework 保留为一致性参照

固定 `agent-framework-core==1.13.0` 作为隔离的 STORE-NORMALIZED 参照适配器。
继续使用 POC 自有的 `StrictJsonCheckpointStorage`；不得启用框架自带的
pickle-in-base64 `FileCheckpointStorage`。

当前残余风险必须原样保留：Agent Framework 可能在领域副作用提交后才保存
superstep checkpoint。现有 synthetic、确定性处理器通过 Store 幂等性抑制重复
副作用，但这不是“提交前零变更”或生产恢复证明。在该边界被可重复故障测试
证伪之前，Agent Framework 不升为首选适配器。

### 4. Temporal 继续延后

`temporalio==1.31.0` 只保留已核验的版本、哈希和 MIT 许可记录，不启动 SDK
验证、server、worker、namespace 或 task queue。

只有同时满足以下条件才重开隔离验证：

1. 产品已出现跨进程多小时/多日 durable timer、signal 或多机器 worker 的明确
   需求；
2. 单机 GraphPort + LangGraph 路径在预先冻结的进程终止、并发 worker 或恢复
   验收中失败，或经证据证明无法表达所需控制语义；
3. Temporal 仍只保存工作流控制状态，SQLite 继续是唯一医学与 Run 权威；
4. 验证使用可删除的 server/worker 环境，不进入产品或真实项目。

若无法保持单一领域权威，终止 Temporal 路径。

### 5. 保留小型 GraphPort runtime 作为最小路径与回滚路径

自有 GraphPort runtime 不被 LangGraph 替换。它继续承担：

- Python 3.9 隔离 POC 的可运行最小路径；
- 框架适配器 conformance 的规范参照；
- 框架版本、许可、打包或安全门失败时的回滚路径；
- 确定性服务、状态迁移和发布门不需要框架能力时的直接执行路径。

## 选择依据

### 已观察证据

- Slice1 领域内核：共享 Python 3.9 环境中 103 项测试通过；Store、artifact、
  coverage、身份、发布与审计边界已接受。
- Slice2 隔离 spike：LangGraph 与 Agent Framework 各 113 项选定测试通过；两者
  对权威 Store 的最终形状、进度、事件顺序、幂等和跨进程恢复一致。
- LangGraph 的 checkpoint 身份、严格反序列化、缺失/损坏 checkpoint 和公开
  resume fail-closed 证据更完整。
- Agent Framework 存在“领域提交先于 checkpoint 保存”的已接受 synthetic
  残余，且安全路径依赖 POC 自有 JSON checkpoint codec。
- Temporal 未运行；有意义的验证必须引入第二控制平面。
- Slice3 audience workbench 的 121 项整合测试与 8/8 浏览器矩阵证明受众投影
  可由领域权威生成，但不证明任何编排框架已达到产品采用标准。

### 必须保留的历史缺陷

以下问题在 manager 修复前真实存在，ADR 不得只保留修复后的绿色结论：

| 缺陷 | 修复前 | 修复后处置 |
|---|---|---|
| 同 graph id/节点集但边顺序被改变仍可执行 | 两个适配器均失败并可能修改 Store | 精确 Graph IR 比较，在任何 checkpoint/Store 变更前拒绝 |
| 新执行节点被错误标为 reused | 两个适配器均失败 | 以调用前终态快照判定 reuse |
| LangGraph 公开 resume 缺 checkpoint 时从 Store 重跑 | 未 fail-closed | 公开 resume 必须存在持久 checkpoint |
| Agent Framework 构造器接受错误 run id/过期 fingerprint | 失败 | 创建 checkpoint 目录前完成身份门 |
| LangGraph finalization 捕获范围过宽 | 风险 | 仅捕获 `CompletionGateError` |

## 暂不选择的方案

### 仅使用自有 GraphPort runtime

它是最简单、Python 3.9 可运行且最易回滚的方案，但继续独自实现复杂分支、并行、
暂停/继续、运行历史与可观察性会增加维护成本。因此保留为合同规范与最小执行
路径，不作为复杂图验证的唯一实现。

### Agent Framework 作为首选适配器

STORE-NORMALIZED conformance 已通过，但 checkpoint-after-domain-commit 残余与
自有 codec 维护负担使其不优于 LangGraph。保留参照价值，不立即淘汰。

### 立即采用 Temporal

当前没有足以抵消 server/worker/控制平面、打包和迁移成本的已证需求；仅导入
SDK 不能证明耐久编排能力。

## R1 尚未完成的硬门

本 ADR 只关闭 R1 步骤 12–13 中的候选比较与框架/持久化处置，不关闭以下工作：

1. API adapter 与至少一个 harness adapter 的统一公共合同；
2. complete/partial/truncated、模型不可用、取消、超时、恢复、迟到回调和原始
   输出/coverage 对账的 adapter 级故障矩阵；
3. 日常、锁库前、锁库后—CFDI 前三个最小 ModeContract 状态机；
4. 报告 ClaimCoverageLedger、批注锚点及 coverage 不足时禁止“全报告完成”；
5. Python ≥3.10 产品打包、共享运行时或独立 sidecar 的正式 ADR；
6. 非 synthetic、非确定性副作用、真实 OS kill、并发 writer 与断电恢复证据。

在这些硬门完成并由独立 reviewer 接受前，任何“R1 完成”声明均为拒绝。

## 下一轮接受门

LangGraph 继续作为首选隔离适配器必须同时满足：

1. 固定版本/哈希/许可与严格反序列化设置可复现；
2. 精确 Graph IR、run/manifest 身份、reuse、缺失/损坏 checkpoint 回归保持绿色；
3. 框架 checkpoint 表和类型不进入领域 DB、artifact 或审计事件；
4. API/harness adapter 的 partial/truncated/failure/recovery 只能产生候选与审计，
   不得把不完整输出提升为事实、风险或发布资格；
5. manifest 派生的真实进度与框架内部 superstep 解耦；
6. Agent Framework 至少保留关键 STORE-NORMALIZED 参照，直到其残余被修复或
   由新的 ADR 明确降级；
7. 所有验证继续在可删除、Python ≥3.10 的隔离运行时中进行。

## 回滚

1. 删除或隔离 LangGraph/Agent Framework 的 disposable venv、checkpoint 和
   adapter 引用；领域 Store、Graph IR、artifact 与审计合同不变。
2. 若整个 R1 POC 放弃，可删除 `poc/medical_monitoring_ai_native_r1/` 及调用者
   synthetic 输出目录；没有产品 schema、服务或医学写作迁移需要回滚。
3. 回滚后由自有 GraphPort runtime 保持最小可运行路径。

## 独立会商覆盖

- Grok Build `grok-4.5` 在同一只读会话补全独立架构挑战，结论为：领域核心
  ACCEPT、LangGraph ACCEPT WITH GATES、Agent Framework 参照保留、Temporal
  DEFER、R1 完成声明 REJECT。
- Pi 声明路线及全部守卫回退在会话创建前健康检查失败，没有有效 Pi 报告；未
  以临时未声明路线替代。
- 因此本 ADR 有一份有效独立挑战和 Codex 的确定性文件/测试锚点，不声称获得
  两份独立模型共识。

## 相关证据

- `ADR-001-framework-neutral-sqlite.md`
- `../spikes/framework_adapters/docs/DEPENDENCY_DECISION.md`
- `../spikes/framework_adapters/docs/SPIKE_EVIDENCE.md`
- `R1_ADAPTER_FAILURE_MATRIX.md`
- `../../../reviews/codex_execution_medical_monitoring_ai_native_r1_slice2_framework_spike_20260809_review.md`
- `../../../reviews/codex_execution_medical_monitoring_ai_native_r1_slice3_aemh_audience_workbench_20260809_review.md`

