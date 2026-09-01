# 医学监查 P10：Capability Guard 下游接线切片

## 1. 目标

本切片将字段映射激活时生成的 capability snapshot 接入医学监查实际计算边界，确保：

- `blocked_by_quality`、`disabled_by_design` 不会以“0 条风险”“0 条趋势”伪装成功；
- `ready` 正常运行；
- `limited` 仅运行合同允许的安全子集，并保留来源事实；
- 旧冻结批次若没有能力快照，规则执行失败关闭；
- 一个局部能力受阻不会自动阻断无关规则。

本切片未修改独立 AI 仓储、服务、worker、`main.py`、前端或真实 runtime DB，也未重启
服务。

## 2. 实现

### 2.1 能力快照随冻结批次固化

冻结 mapping payload 从 `monitoring_project_mapping_v1` 升级为 v2，新增并完整固化：

- 语义质量报告 SHA-256；
- capability manifest SHA-256；
- 激活处置；
- 有效能力集合及 SHA-256；
- 每项能力状态、finding 关联和 limitation code。

仓储仍可只读解析 v1，但 v1 不含能力快照。daily run 执行规则时会明确返回
`monitoring_capability_contract_required`，要求基于当前质量门重新冻结，不会按“全部可用”
处理历史批次。

### 2.2 Daily run 按规则族门禁

新增项目中立的规则族与能力依赖目录：

| 规则语义 | 能力门 |
|---|---|
| AE/MH 对账 | `ae_mh_reconciliation` |
| CS/NCS、实验室异常、CTCAE 纵向加重 | `lab_ctcae_rules` |
| 访视窗、时序、temporal executor | `precise_temporal_rules` |
| 合并用药方案政策、试验药物变更 | `protocol_medication_rules` |
| 试验药物依从性 | `protocol_medication_rules` + `ip_exposure_adherence` |
| 标准编码语义字段 | `standard_coding_rules` |
| 量表复算语义字段 | `scale_recalculation` |

规则 runner 在每条规则实际执行前检查所需能力。受阻规则：

- 不执行；
- 生成 `monitoring_capability_unavailable` 或能力合同缺失诊断；
- 记录 capability、状态、limitation 和 `rule_execution_skipped=true`；
- 使 daily run 的 `analysis_complete=false`，进入人工处理边界；
- 不影响同批次其他 ready/limited 规则继续运行。

record-applicability 多方案路径与 project-effective 单规则包路径均已接线。规则快照输入哈希
加入 capability manifest 和有效能力集合哈希，恢复执行时重新读取不可变冻结合同。

### 2.3 Subject Timeline / Patient Profile restricted 投影

监查项目适配层新增统一 resolver 绑定入口，并调用
`require_monitoring_capability(project_id, capability_id)` 兼容签名检查：

- Timeline limited 或精确时间能力不可用：保留来源日期，清除研究日、访视偏差等精确推断；
- Profile 可用但量表复算不可用：保留来源值，清除标准化值及依赖复算的基线变化；
- Profile 可用但 CTCAE 不可用：保留实验室来源结果，清除自动 CTCAE 分级与版本；
- Timeline 或 Profile 单项不可用：仅清空受影响视图，并在结构化能力状态与 review focus
  明确说明；
- 两项主能力都不可用：抛出明确错误，禁止返回空页面伪装成功。

响应合同新增：

- `capability_mode=full|restricted`；
- `capability_states`；
- `capability_limitations`。

由于本切片明确禁止修改 `main.py`，项目注册表的 resolver 生产绑定和 HTTP 错误状态映射尚未
落盘；restricted 投影已完成服务级实现及测试，下一集成切片必须绑定后才能称为运行态启用。

## 3. 已接线能力

- daily run：标准编码、精确时间、实验室/CTCAE、方案用药、试验药依从性、量表复算、
  AE/MH 对账；
- project-effective 与 record-applicability 两种规则执行模式；
- Subject Timeline：主能力、精确时间受限模式；
- Patient Profile：主能力、量表复算受限模式、CTCAE 受限模式；
- 旧 v1 冻结批次失败关闭。

## 4. 尚未接线

1. 在运行态 `main.py` 中把 activation service 的
   `require_monitoring_capability` 绑定到 `MonitoringProjectRegistry`；
2. 将 `MonitoringProjectCapabilityUnavailableError` 映射为明确 409/422 产品错误，而非
   通用 404；
3. 风险汇总、风险处置和 Safety/PV 深钻入口按风险类别执行同一能力门；
4. 前端只读显示 restricted 摘要，并保持“不把技术日志常驻主界面”的设计边界；
5. 双真实项目正式 mapping 激活后，用完整/受限两类快照校准规则族依赖目录，尤其验证
   规则文本出现 `score` 等词时不会过度要求量表复算；
6. 对 source-only Timeline/Profile 与未来通用批次派生服务之间的替换路径做集成收口。

## 5. 验证证据

- capability、daily run、record resolver、Timeline/Profile 聚焦回归：`48 passed`；
- V13 旧修复合同修订后联合回归：`68 passed`；
- 全部 `test_monitoring*.py` 首轮：`773 passed, 2 failed`；两项均为旧测试仍将
  `VISIT/VISITNUM` 视为歧义字段；
- 修订为 V13 已冻结技术角色后，定向测试通过；
- 真实 RUX/MY009 来源修订及全受试者 drilldown：`15 passed`；
- Ruff：`All checks passed`；
- Python 编译检查通过；
- 未读写真实 runtime DB，未重启 API。

## 6. 关键文件 SHA-256

- `monitoring_capability_guard.py`:
  `1a09c87b119dae8462750b644a177f302b423d3b3703ca249f9530ed46bd8d50`
- `monitoring_batch_repository.py`:
  `3acbdffb1e1d5a1c0fba280e113f626e8cbbd8d383af5f2ed03ebad48ddde793`
- `monitoring_mapping_batch_lifecycle.py`:
  `33e37139ba4af5498d666785798ab775137ddd496c7b6a8552f0d4746d4870d5`
- `monitoring_batch_rule_runner.py`:
  `2a63da5b71df7e56d599e7271ffa59b4fca3415570e681e252a55f12aa722e05`
- `monitoring_record_rule_resolver.py`:
  `b0a5ed4cf03351289bac7a4fdf573df1b3e738ccd483260db06712f99db84d15`
- `monitoring_daily_run_service.py`:
  `99db76b88f1d220ee77f0483e5def70d13232973cd39ea2e5846c7f10fdedcdc`
- `monitoring_project_registry.py`:
  `dd64bdd512509bc3baaa61b415162e687ee9e8dae47820404feef82c71f290a3`

