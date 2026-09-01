# ADR-001：框架中立 Graph IR + SQLite 权威存储

## 状态

R1 隔离 synthetic POC 的实现决策。它不是产品架构批准，也不是生产运行
时/框架选型完成的证明。

## 决策

采用 D-R1-01：Python 3.9 标准库、SQLite 显式事务、JSON 内容寻址 artifact
文件，以及不绑定任何供应商 session/message 类型的 `GraphPort` /
`CheckpointPort`。SQLite 保存权威领域状态；artifact 先以 canonical JSON 写入
内容地址，再在单个 SQLite 事务中登记引用、节点结果和审计事件；发布指针只在
事务提交后推进。整个 `poc/medical_monitoring_ai_native_r1/` 可独立移除，
不修改产品数据库或入口。

选择依据已冻结在 R1 context：现有共享环境为 Python 3.9.6；R1 首先需要验证
领域状态、coverage、恢复和审计不变量，而不是先验证外部框架的配置语义。

## 候选与冻结官方来源

以下 URL 和许可证信息转录自本任务已经冻结的本地 R1/架构审计材料；本 worker
没有发起新的网络请求，也没有安装或采用这些框架。

| 候选/基础能力 | 官方来源 | 许可证/本轮结论 |
|---|---|---|
| LangGraph persistence | https://docs.langchain.com/oss/python/langgraph/persistence | 官方仓库为 MIT；保留为后续 adapter spike，不进入 R1 依赖 |
| LangGraph repository/license | https://github.com/langchain-ai/langgraph / https://github.com/langchain-ai/langgraph/blob/main/LICENSE | MIT；需要额外验证生产持久化、历史保留与合规边界 |
| Microsoft Agent Framework Workflows | https://learn.microsoft.com/en-us/agent-framework/workflows/ | 官方 Python package/repository 为 MIT；后续实测，不进入 R1 依赖 |
| Microsoft Agent Framework license | https://github.com/microsoft/agent-framework/blob/main/LICENSE | MIT；当前 Python 集成与成熟度仍需独立验证 |
| Temporal Python SDK | https://github.com/temporalio/sdk-python | MIT；需要 server/worker 和更高运维/迁移成本，R1 延后 |
| Temporal Python SDK license | https://github.com/temporalio/sdk-python/blob/main/LICENSE | MIT；不在本 POC 中安装或运行 |
| SQLite transactions | https://sqlite.org/transaction.html | SQLite 官方事务语义；本地嵌入式权威存储依据 |
| SQLite atomic commit | https://sqlite.org/atomiccommit.html | SQLite 官方原子提交说明；文件与 DB 之间仍保留 orphan recovery 边界 |
| Python sqlite3 | https://docs.python.org/3/library/sqlite3.html | Python 标准库文档；R1 不新增依赖 |

## 未选择的选项

- 直接绑定 LangGraph 或 Microsoft Agent Framework 会把 R1 的首要验证对象
  变成框架版本、checkpoint/superstep 和 Python 版本配置；R1 先保持领域 schema
  与框架解耦，后续用同一 port 合同做隔离 spike。
- Temporal 更适合跨天、跨进程和长运行控制平面，但需要额外 server/worker、
  确定性约束和迁移运维面；R1 的单机 synthetic slice 不足以证明这项成本值得。
- 真实 provider、harness 或现有产品服务不进入 R1：会引入数据外发、凭据、
  服务状态和真实项目边界，且不能替代本轮对状态/恢复不变量的验证。

## 后果与残余风险

正面后果是：公共合同可由不同图引擎实现，SQLite 行和 audit chain 可检查，
candidate/fact、coverage 和四条正交 Run 状态保持分离；失败后只需恢复隔离
POC 目录和 caller 输出目录。

残余风险包括：本轮没有证明多进程高并发、跨机器灾备、长时间 lease、外部框架
适配器、OS 级断电恢复或真实报告/临床语义。artifact 文件与 SQLite 提交并非
同一文件系统事务，提交边界可能留下可审计 orphan，不能把 orphan 当作权威。
worker_04 的 `R1_EVIDENCE.md` 另行记录当前测试暴露的发布再校验和 Store 绑定
接受资格缺口；这些缺口不能由本 ADR 的选型结论覆盖。

## 回滚

删除或隔离整个 R1 POC 目录及 caller 提供的 synthetic 输出目录即可回滚；本决策
没有迁移现有数据库、服务、前端、医学写作数据或真实项目。
