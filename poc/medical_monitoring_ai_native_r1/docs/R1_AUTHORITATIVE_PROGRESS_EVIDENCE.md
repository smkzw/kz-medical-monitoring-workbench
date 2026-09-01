# R1 权威工作单元台账与结构化进度证据

日期：2026-08-09  
范围：`medical_monitoring_ai_native_r1` synthetic/offline POC；不包含 UI、真实 provider/harness/项目、服务、8911、医学写作子系统或产品发布。

## 1. 决策

R1 不引入新调度框架或新依赖。权威进度继续由应用自有的
`ExecutionManifest` + SQLite 台账掌握，外部框架未来只能投影这一状态，
不得反向替换分母、revision 或终态真相。

一手资料的决定性启示：

- Microsoft Durable Functions 的 [custom orchestration status](https://learn.microsoft.com/en-us/azure/durable-task/durable-functions/durable-functions-diagnostics)
  是由应用设置、供外部查询的 JSON，可承载完成百分比、当前步骤或错误概要；
  它是状态投影通道，不会自动定义医学监查业务分母。
- Kubernetes [Pod conditions](https://kubernetes.io/docs/concepts/workloads/pods/pod-condition/)
  用 `status/reason/message` 表达观测结果，并用 `observedGeneration` 绑定已观测的 spec 版本。
  R1 同理把每个 work-unit 回调绑定到 manifest revision，拒绝旧 revision 迟到结果。

访问日期均为 2026-08-09。

## 2. 已实现合同

### 2.1 冻结分母

- `ManifestWorkUnit` 明示 `node_id`、中文可读 `label`、`stage`、`scope`、
  `target_ref`、稳定 `ordinal`、强制性和依赖。
- 显式 work-unit manifest 必须覆盖每个节点，ID/ordinal 唯一，依赖存在且无环。
- `set_manifest()` 在同一 SQLite 事务中追加 revision、初始化全部
  `pending` work-unit 行、更新 Run 当前 revision，并把 denominator hash 写入审计链。
- 未声明 work units 的旧 manifest 保持节点级 `manifest_progress()` 语义和原三键返回形状。
- manifest 定义哈希排除由 store 分配的 `revision/created_at`；因此
  `set_manifest(get_manifest(...))` 是原 revision 幂等重放，不会静默换分母。

### 2.2 权威迁移与播报

- `begin_work_unit()` 只能打开当前 revision 的 `pending` 单元，必须提供幂等键、
  用户可理解的当前工作句和受限的执行身份字段；依赖未满足时失败关闭。
- `complete_work_unit()` 只能关闭已运行单元；终态指纹绑定 status、中文说明、
  执行身份和证据数，相同重放不产生第二个事件，冲突重放不改写历史。
- `work_unit_begin/work_unit_complete` 是原有 SHA-256 哈希链的结构化审计事件；
  播报直接由这些事件投影，不另建可与审计链漂移的日志真相。
- 执行身份仅接受 provider/model/selector/adapter/harness/transport/profile fingerprint/
  attempt ID/endpoint alias 等列入白名单的字段；不接受 token、credential 或任意原始日志字段。
- begin 请求的说明+执行身份另有不可变指纹；即使单元已终态，同键但不同说明/身份
  仍会拒绝，不会借“重放”静默接受。
- work-unit 事件类型为 store 内部保留类型，公共 `append_audit()` 不得伪造；投影时还会对账
  审计链、完整 payload 形状、manifest 定义、状态、证据数与身份白名单。
- 审计链使用持久尾锚；追加事件前物理尾部必须与锚一致，校验时重算结果也必须与锚一致，
  因而尾部截断不能伪装成较短但完整的历史。
- 进度不是仅按台账行计数：manifest 定义、当前行及 begin/complete 审计迁移必须三方一致。
  工作单元所属节点、推导状态、说明、执行身份、证据数及指纹任一漂移均失败关闭。

### 2.3 进度投影

`structured_progress()` 返回：

- Run ID、manifest revision、是否当前 revision、denominator hash；
- `completed/total/percent/by_status`；终态表示已处理，失败/阻断仍单独显示，不伪装成通过；
- 当前正在运行的工作单元、开始时间、已运行秒数和执行身份；
- 按顺序的有界最近事件（最多 100 条）。

如果台账行的数量或 ID 集与 manifest 分母不同，或审计链/payload 已损坏，
`structured_progress()` 失败关闭，不返回伪正常百分比。全局幂等账本的查重和写入均在
`BEGIN IMMEDIATE` 中完成，两个独立 SQLite 连接并发提交同一 manifest 仅产生一个 revision。

显式 work units 尚有非终态时，所属节点不得完成；单元失败/阻断时，节点不得记为
`passed/reused/skipped/not_applicable`。

旧式节点级 manifest 使用 revision-keyed `manifest_node_progress`；`node_runs` 与每个不可变
`node_attempts` 也绑定打开时的 manifest revision。旧 revision 回调不能污染新 revision，
新 revision 可建立独立 attempt。v5 迁移依据 attempt 创建时间与 manifest 冻结时间恢复旧
node/attempt 所属版本，并从 manifest/node 审计事件重建历史节点进度。

## 3. 决定性验证

```text
authoritative progress focused: 16 passed
domain/store/failure adjacent: 89 passed
capability runtime: 51 passed
R1 core: 170 passed
AE/MH audience: 18 passed
Patient Journey: 16 passed
grouped runnable evidence: 204 passed
compileall: pass
scoped Ruff: pass
8911 listener: none
```

根目录无选择收集不是接受命令：两个可视切片存在同名测试模块，且一次性
framework spikes 的依赖已按原计划清理；因此使用 `tests/` 核心套件与两个 slice
各自独立运行的分组命令，不为重建旧 spike 环境安装依赖。

## 4. 相邻隔离证据纠正

用工作台文档指定的 `.venv/bin/python` 重跑时，Seatbelt 正确拒绝了未声明的
`.venv/pyvenv.cfg`，使 3 项隔离测试失败。纠正仅修改 synthetic 测试 profile：
当测试解释器处于 virtualenv 时，把该 venv 根目录显式冻结为只读运行时闭包。
产品默认策略未放宽，非声明用户目录仍拒绝内容读取。纠正后：

```text
focused .venv isolation: 3 passed, 48 deselected
capability runtime under .venv: 51 passed
R1 core under .venv: 170 passed
```

## 5. 独立审阅 VETO 与修复记录

Luna fresh-context 首轮审阅会话 `019fe6a4-b42f-7403-8279-4940a6ae073c`
给出 VETO，复现了台账缺行、终态 begin 冲突重放、retrieved manifest 重设增加 revision、
公共入口伪造 feed 及事务外幂等预检问题；均已修复并有负测。

fresh reviewer 续作会话 `019fe6b0-30da-7343-beca-9f0c41624942` 又分三轮发现并推动闭环：

1. 同数量错误 work-unit ID、审计尾截断、历史 legacy 查询复用当前 revision；
2. work-unit `node_id` 未对账、行级合法终态绕过完成事件、legacy 旧 revision 回调污染新版本；
3. 真实 v4→v5 迁移把 rev1 终态误绑定当前 rev2。

对应纠偏为精确 ID/定义/迁移三方对账、持久审计尾锚、revisioned legacy 节点分母、
revision-bound node/attempt，以及按 attempt/manifest 时间恢复旧版本归属。

最终同会话复核结论：**ACCEPT**，P0/P1/P2/P3/P4 均为 0。审阅者重跑焦点测试
`16 passed`、相邻测试 `89 passed`、全部既往对抗探针及真实 v4→v5 缺列迁移探针，
并确认 Ruff、compileall 与冻结 SHA-256 稳定。审阅器自身的嵌套沙箱无法再次嵌套
`sandbox-exec`，因此其中 3 项 Seatbelt 用例出现
`sandbox_apply: Operation not permitted`；这是审阅环境限制，不计为产品通过证据。
同一组用例已在父环境以 `51 passed` 独立运行，边界分别记录，不互相替代。

最终冻结 SHA-256：

- `domain.py`: `0c3d7e7133d86f4f57826c9452a0d2ec272b3cd82d36f5c3c87f3db024ab3bbd`
- `store.py`: `9a6e344840c90e67c584e95a5a44d41f91015ee09dba7ea0b35f84aef2c41c16`
- `__init__.py`: `955be008d640247cb6076a6312489569ea2840fc6b97c8a81876a4352e77d5e5`
- `test_authoritative_progress.py`: `fbe1457d3c2fc0d19bee3768a71c6289426dab3e6ec26566e1a9f867421beffe`
- `test_capability_runtime.py`: `ab1dd16ccf2f14a84b1726aa866f74d66906cd9e249771028e109209cdf83828`
- `capability_runtime.py`: `906c48fe1eefc8a9aeb34aafedbbd0c0d74d7b3529c9f5280dd32bf11a2bee9f`

## 6. 残余边界

- 本切片已实现台账和 UI-safe 投影，没有实现后台 worker/service、页面轮询/通知或真实长任务。
- 当前执行身份由调用方提供并受字段白名单约束；尚未与 capability attempt journal 自动绑定和对账。
- 未进行真实多进程并发、长时运行、海量 work-unit 或 UI 可视验收。
- R1 整体、多模型风险分析、真实 provider/harness/项目及产品集成仍未验收。
