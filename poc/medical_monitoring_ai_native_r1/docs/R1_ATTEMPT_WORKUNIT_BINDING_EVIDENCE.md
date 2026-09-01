# R1 capability attempt 与工作单元绑定证据

日期：2026-08-09  
范围：隔离 `medical_monitoring_ai_native_r1` synthetic/offline POC。未运行 UI、服务、
真实 provider/harness/项目或 8911，未触碰医学写作与产品源码。

## 1. 问题与选择

权威工作单元台账此前允许调用方直接提供 provider/model/attempt 等执行身份。
即使字段白名单能够阻止 token 或任意日志进入进度，也不能证明身份来自实际执行。

本切片不引入调度框架或依赖，而是在两个既有应用权威之间建立版本化关系：

- `ExecutionManifest`/`work_unit_runs` 定义逻辑工作及真实进度；
- `capability_attempt_journal` 冻结执行请求、profile fingerprint、binding、输入哈希、
  manifest revision、租约和终态。

新增 schema v6 `work_unit_capability_attempts` 只保存二者的严格关联；provider/model/
adapter/profile/attempt 身份由已校验的 journal request 自动推导，不接受调用方填报。

## 2. 状态合同

- 确定性工作单元继续使用既有 direct begin/complete。
- AI 工作单元必须先调用 `bind_capability_attempt_to_work_unit()`；直接 begin/complete
  失败关闭。
- 首个 attempt 原子建立 binding、把工作单元从 pending 迁移到 running，并追加
  `work_unit_begin`。
- 重试必须引用最新 attempt 的精确 `continued_from`，且前一 attempt 只能处于
  interrupted/failed/timeout/cancelled/partial/truncated；新 binding 按 ordinal 追加，
  既往 attempt 不改写，并产生结构化 `work_unit_attempt_bound`。
- 同一 attempt 全局只能属于一个 work unit；两连接并发绑定只有一个可提交。
- 只有最新 binding 可以结束工作单元。`complete` 映射为 passed；interrupted 映射为
  blocked；failed/timeout/cancelled/partial/truncated 均映射为 failed。调用方不能提交
  自选成功状态。
- manifest、work-unit 行、binding ledger、capability journal 与哈希链工作迁移必须精确
  对账；身份、ordinal、continuation、detail、状态或审计事件任一漂移均拒绝投影。

内部 execution identity 仅用于审计和控制器关联。面向资深医学监察员的后续中文 UI
不得显示 provider/model/attempt/backend 等技术标签；进度页面只显示“正在分析某受试者/
中心/风险域”等临床工作语句与真实数字。

## 3. 决定性验证（首次 VETO 纠偏后重新冻结）

```text
attempt/work-unit focused: 37 passed
domain/store/failure adjacent: 110 passed
capability runtime: 51 passed
R1 core: 191 passed
scoped Ruff: pass
compileall: pass
```

聚焦用例覆盖：调用方身份绕过、成功与六类非成功映射、严格续接链、重复 attempt、
跨 revision、确定性节点误绑、两连接并发、binding 协同篡改，以及 v5→v6 空绑定表迁移。
首次独立复核进一步复现两条失败关闭缺口并给出 VETO：公共 `Store` 可直接制造能力终态，
且重算行级结果哈希后，能力 journal 未与其审计生命周期逐事件对账。纠偏后：

- `Store` 的公开接口只保留能力尝试只读查询；声明、认领、中断与终态写入仅由
  `CapabilityRuntime` 获取的私有窄 facade 调用；
- declaration/claim/interruption/terminal 四类能力生命周期事件均为保留事件，公开
  `append_audit` 不得伪造；journal 当前行必须与保留事件顺序及终态哈希一致；
- 终态能力尝试在绑定权威进度前，必须携带与冻结请求、binding、原始输出哈希、
  work events、候选 artifact 及 transport raw output 一致的运行时证据包；最小伪造
  `{"forged": true}` 不再可绑定；
- 审阅者原始“重算终态行但不补终态审计事件”和“无 transport/runtime 直接宣称成功”
  路径已固化为聚焦回归。

冻结 SHA-256：

- `domain.py`: `039f197ff01f4d689db01327bf08ef917551c06105d1907eaa920c9bdb5b01dc`
- `store.py`: `b73b721a500c420c2434562bf05bdf742b59c20c50632099423ada5871128768`
- `__init__.py`: `955be008d640247cb6076a6312489569ea2840fc6b97c8a81876a4352e77d5e5`
- `test_authoritative_progress.py`: `2436738ffa188c3ea773661044d507e3e9012d5bb9a2903974ad83465e322798`
- `test_capability_runtime.py`: `7334f61227fef8b1387bda33afca38841fd1769f7df7f11d21d7f19d72a49842`
- `capability_runtime.py`: `f2b223481e0dd9882bf20b3e055525e2f23e8026438fe4dfc1f752182353dc33`

同一独立 Luna 会话 `019fe6e5-48b2-7292-ba62-f8ed6ad64a5d` 在纠偏后返回
**ACCEPT**；P0-P3 为零，P4 仅保留“Python 私有接口不是敌对同进程安全沙箱”的边界。
审阅者独立复跑 focused 37、adjacent 110、capability 51、Ruff、compileall，并验证
4/4 公共生命周期写方法不存在、4/4 保留事件被公开 append 拒绝；起止哈希一致。

## 4. 尚未声称

- 本文件只证明 isolated synthetic/offline R1 的能力尝试—工作单元绑定切片；不代表
  R1 总体完成或产品集成接受。
- 尚未实现后台 controller 自动监听 attempt 并推进 work unit；当前是可由 controller
  调用的权威状态合同。
- 结构化 store 投影仍包含内部执行身份，未来 audience controller/UI 必须显式剥离，
  不得把模型、provider 或 attempt ID 显示给医学监察员。
- 未验证真实长任务、真实多进程压力、真实 provider/harness/项目或产品迁移。
- Python 私有方法不是恶意同进程代码的安全沙箱；本切片证明的是应用公开合同失败
  关闭与审计一致性，不是生产级进程隔离或防数据库管理员篡改。
