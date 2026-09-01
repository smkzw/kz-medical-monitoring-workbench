# R1 Adapter 故障矩阵

## 目的与边界

本矩阵把两类不同的 adapter 分开：

1. **图引擎 adapter**：GraphPort 与 LangGraph / Agent Framework 的控制状态、
   checkpoint、恢复和领域 Store 一致性；
2. **AI Capability Adapter**：用户配置的 API 或 harness 的调用、原始输出、
   complete/partial/truncated、coverage、取消、继续、超时与审计。

图引擎 spike 已通过的项目不能替代 AI Capability Adapter 的验证。当前已新增
provider-neutral capability runtime 的 synthetic/offline 切片；下表区分已经自动
验证的合同、仅在单进程合成环境成立的残余接受，以及仍未实现的真实执行边界。
状态只使用 `PASS`、`ACCEPTED_RESIDUAL`、`OPEN`、`DEFERRED`；`PASS` 仅指已记录
的 synthetic 隔离范围，不代表真实 provider、真实 harness 或 R1 总体验收。

## A. 图引擎 adapter 已观察矩阵

| 故障/合同 | LangGraph 1.2.10 | Agent Framework 1.13.0 | 权威保护与证据 |
|---|---|---|---|
| 同 graph id 但节点/边/执行字段改变 | PASS | PASS | 任何 checkpoint/Store 变更前精确拒绝；历史上两者均曾失败 |
| 构造器 run id 错误 | PASS | PASS | 绑定 contract/run；AF 在建目录前拒绝 |
| manifest fingerprint/revision 过期 | PASS | PASS | 入口重校验冻结 contract |
| 新执行错误标记 reused | PASS | PASS | 使用调用前终态快照；历史上两者均曾失败 |
| resume 缺失 checkpoint | PASS | PASS | 公开 resume fail-closed；LG 历史上曾从 Store 重跑 |
| checkpoint 损坏 | PASS | PASS | 恢复前拒绝，无新增领域事件/节点变更 |
| checkpoint 指向其他 run | PASS | PASS | 独立目录/身份门，不能跨 run 选择 |
| LangGraph state blob 损坏/metadata 缺 run id | PASS | 不适用 | strict msgpack、白名单、必填 run id |
| Agent Framework 不支持 JSON 值、非字符串 key、NaN/Infinity、循环结构 | 不适用 | PASS | `StrictJsonCheckpointStorage` 写入前拒绝 |
| Agent Framework stock pickle checkpoint | 不适用 | PASS（通过禁用） | POC 不调用 stock `FileCheckpointStorage`；不是上游修复 |
| 节点领域提交后、checkpoint 保存前崩溃 | PASS（当前受测路径） | ACCEPTED_RESIDUAL | AF 依赖 Store 幂等抑制重复，不是零变更证明 |
| 中断后新进程恢复、PID 不同 | PASS | PASS | 仅 synthetic、确定性处理器范围 |
| 重试/重放造成重复 work event | PASS | PASS | 唯一幂等键，事件数不增加 |
| 框架状态泄入领域 DB/artifact/audit | PASS | PASS | domain DB 无框架 `writes` 表或框架类型 |
| unexpected finalization error 被吞掉 | PASS | 不适用 | LG 仅捕获预期 `CompletionGateError` |
| OS 断电/强杀、并发 writer、文件系统损坏 | OPEN | OPEN | 现有注入不构成生产耐久证明 |
| 多小时/多日、多机器 durable workflow | OPEN | OPEN | Temporal 仍为 DEFERRED |

当前确定性锚点：两个候选各 113 项选定测试通过；共享 Slice1 103 项通过。详细
命令、历史 FAIL→PASS 和物理文件检查见
`../spikes/framework_adapters/docs/SPIKE_EVIDENCE.md`。

## B. AI Capability Adapter R1 验收矩阵

下表以 `capability_runtime.py` 的公共请求/响应合同和自动化测试为当前证据；不得
从图引擎测试或合成 transport 推定真实端点已经通过。

| 场景 | API adapter | harness adapter | 预期领域行为 | 当前 |
|---|---|---|---|---|
| binding/version 与 effective ExecutionProfile 冻结 | 合成 transport 已验 | 本地合成进程已验 | profile/response identity 对账；节点不能静默换模型 | ACCEPTED_RESIDUAL |
| 输入哈希与来源/规则/知识/graph/schema 版本绑定 | 合成 transport 已验 | 本地合成进程已验 | 不匹配时调用前 fail-closed | PASS |
| 允许工具业务语义 | 冻结允许列表与身份 | 冻结允许列表与身份 | R1 最小合同只声明/绑定权限；provider-native 工具执行由后续 capability-specific policy 强制 | PASS（R1 合同）/ OPEN（产品执行） |
| 文件内容/写入/网络/exec 隔离 | API 尚无等价门 | `macos_seatbelt_r1` 合成负向测试已验 | 请求隔离不可用时派发前失败关闭；不静默降级 | PASS（仅当前 macOS synthetic） |
| 启动、状态、结构化工作播报 | attempt 身份尚未自动对账到 work unit | 同左 | manifest-revision work-unit 台账、精确分母、当前工作和审计链 feed 已验；后台 worker/UI 尚未接入 | ACCEPTED_RESIDUAL |
| complete + coverage 完整 | 合成 transport 已验 | 本地合成进程已验 | 只产生候选 artifact；仍需确定性 QC/发布门 | PASS |
| partial | 合成 transport 已验 | 本地合成进程已验 | `evidence_state=partial`；缺失 coverage 明示，不晋升完整结论 | PASS |
| truncated | 合成 transport 已验 | 本地合成进程已验 | 原始输出完整保留；展示/解析截断时禁止完整资格 | PASS |
| 无法解析但进程成功 | 合成 transport 已验 | 本地合成进程已验 | 解析失败与传输成功分离，保留原始输出 | PASS |
| 模型/provider/harness 不可用 | 失败路径已验 | 失败路径已验 | 尚未接用户显式 fallback 路由，不静默换模型 | ACCEPTED_RESIDUAL |
| 超时 | 领域侧超时已验 | `setsid/killpg` 子进程组回收已验 | API 非协作底层调用可能继续；结果仍不可发布 | ACCEPTED_RESIDUAL |
| 用户取消 | 领域侧取消已验 | `setsid/killpg` 子进程组回收已验 | 同 runtime 取消幂等；跨应用主动取消仍未实现 | ACCEPTED_RESIDUAL |
| 继续/恢复 | durable journal 重开/终态重放/新 attempt 续接已验 | 同一应用 journal 合同已验 | 同 binding/输入/版本/manifest；旧 attempt 不重跑，以 `continued_from` 新 attempt 续接 | PASS |
| 进程中断 | 过期租约与另一 PID 恢复已验 | 未做真实强杀/进程 checkpoint | synthetic 过期 attempt 转 `interrupted`；真实进程状态恢复仍待实现 | ACCEPTED_RESIDUAL |
| 重复回调/重复提交 | 双 SQLite 连接原子认领与重开重放已验 | 同一 journal 合同已验 | 同 attempt 只执行一次；终态结果不可改写 | PASS |
| 迟到回调 | 过期/中断/旧 owner 完成已验 | 同一 journal 合同已验 | 迟到完成 fail-closed 并审计，不写新终态 | PASS |
| attempt journal 请求/结果/终态字段损坏 | 读取与重放 fail-closed 已验 | 同一 journal 合同已验 | 请求身份、结果内容及终态共同校验；矛盾行不得重放 | PASS |
| 原始输出缺失/损坏/哈希不符 | 共享 SQLite raw 路径已验 | 共享 SQLite raw 路径已验 | typed read 核验外层及嵌套哈希与 ref/run 身份；候选完整性失败；恢复只报告不修复 | PASS |
| coverage 宣称与实际项不一致 | 合成 transport 已验 | 本地合成进程已验 | status/reason/`expected=false` 不得进入分母；精确对账 | PASS |
| manifest revision 中途变化 | 前后检查已验 | 前后检查已验 | 旧 attempt 结果不可写入新 revision | PASS |
| ensemble_size=1 | 未进入 R1 | 未进入 R1 | 不显示多模型一致/分歧 | DEFERRED（R4 步骤 10） |
| ensemble_size≥2 | 未进入 R1 | 未进入 R1 | 独立上下文、相同输入；原始输出不可互改 | DEFERRED（R4 步骤 10） |
| adjudication binding 与 worker 同 session | 未进入 R1 | 未进入 R1 | fail-closed；裁决必须隔离 | DEFERRED（R4 步骤 10） |
| 外部 token/费用不可得 | 未进入 R1 | 未进入 R1 | adapter 可得时展示；不伪造数值 | DEFERRED（产品运行投影） |

## C. 共同提交边界

每次 AI adapter attempt 至少经历以下不可混同的状态：

1. `attempt_declared`：冻结 binding、输入哈希、工具、超时、manifest revision；
2. `execution_started`：记录执行端与开始时间；
3. `raw_output_sealed`：原始输出内容寻址并校验；
4. `parse_classified`：complete/partial/truncated/failed 与 coverage 清单；
5. `candidate_registered`：只登记候选 artifact，不改变事实/风险/用户确认；
6. `deterministic_qc_passed`：身份、版本、coverage 和来源对账；
7. `publication_eligible`：仅在所有强制门满足后由应用发布。

迟到、重复或旧 revision 的 attempt 最多进入可审计隔离区，不能跳到步骤 5–7。

## D. R1 接受规则

AI Capability Adapter 的 R1 矩阵只有同时满足以下条件才可从 `OPEN` 改为
`PASS`：

- API adapter 与至少一个 harness adapter 共享同一领域中立结果 schema；
- 每个关键场景有确定性自动测试和 raw output/artifact/audit 物理锚点；
- partial/truncated/失败不产生完整 coverage、事实晋升或发布资格；
- 取消、恢复、重复与迟到回调在 manifest revision 边界内幂等；
- 独立 reviewer 读取合同、测试、原始输出与领域 DB 后接受；
- 不依赖产品、医学写作、真实项目、服务或共享运行库。

只有 B 表中实施计划 R1 步骤 6 明确要求的最小公共合同场景仍为 `OPEN`
时，R1 才不得声明完成。明确标为 `DEFERRED（R4）` 或产品运行投影的项目不是
R1 完成门，但必须继续保留为后续阶段的显式限制。当前 capability runtime 与
application-owned attempt journal 仅为独立接受的隔离切片；当前 OS 级执行隔离只在
已弃用 Seatbelt 的当前 macOS synthetic 后端成立，真实强杀/进程 checkpoint 恢复、
完整持久化崩溃原子性、hash-only 之外的防篡改、
多模型裁决和真实运行端集成仍是后续工作。

权威分母、revision 隔离和结构化播报的 synthetic 证据见
`R1_AUTHORITATIVE_PROGRESS_EVIDENCE.md`。该证据只关闭业务台账/投影子门，
不代表真实后台执行、用户页面或 AI adapter 身份自动对账已完成。
