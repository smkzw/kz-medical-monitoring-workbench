# P7B 逐记录方案与规则包解析合同

## 目标

医学监查运行不得仅按项目和当前日期选择规则包。每条待分析记录必须以其中心编号、可选受试者编号和真实事件日期解析已确认的方案适用性，再绑定该方案版本下唯一、完整、已发布的规则包。

## 来源与边界

- 来源：当前工作区代码、P7A 已验收的方案适用性 assignment/resolver、医学监查 PRD 与当前 Goal。
- 仅修改医学监查后端及其测试，不修改医学写作模块、共享独立 AI 配置或前端。
- 不推断中心启用日期，不使用方案版本日期、伦理日期、培训日期、文件名、导入日期或当前日期兜底。
- 受试者级确证 assignment 优先于中心级 assignment；只接受精确编号和闭区间事件日期命中。
- 未解析、冲突、无已发布规则包、同一方案版本存在多个可用发布包时均须关闭失败并返回稳定诊断，不得解释为“未发现风险”。
- 相关记录只作为医学上下文，不得改变当前记录的方案适用性锚点。

## 成功标准

1. Repository 可按 `project_id + protocol_version_id` 唯一读取已发布且完整的规则包。
2. Runtime resolver 可按记录锚点返回方案 assignment、方案版本和规则包的可审计身份。
3. 日常监查运行快照持久化实际 assignment id/state version、protocol version id、rule pack id/revision/hash；不得生成伪复合规则包 ID。
4. 同一批次跨中心或跨受试者方案版本不同的记录可以使用不同规则包。
5. 所有失败路径稳定、可测试、无隐式回退；现有 project-effective 规则包路径保持兼容。
6. 目标与相邻回归测试通过，工作区无医学写作文件变更。

## 允许写入

- `services/api/app/monitoring_protocol_rule_repository.py`
- `services/api/app/monitoring_protocol_rule_service.py`
- `services/api/app/monitoring_daily_run_service.py`
- `services/api/app/monitoring_daily_run_repository.py`
- 可新增一个医学监查专用 runtime resolver 模块
- 对应 `tests/test_monitoring_*.py`

## 验收与回滚

- Codex 复核冲突点、不可变身份和失败关闭语义，并运行目标及相邻回归。
- 任何需要改写现有数据库列或破坏旧运行记录的实现均不接受；仅允许向后兼容的增量迁移。
- 写入前保留当前文件内容；本工作区非 Git，变更必须在交接中逐文件列出。
