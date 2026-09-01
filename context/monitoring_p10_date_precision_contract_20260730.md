# 医学监查 P10：部分日期精度合同闭环

## 问题

真实 EDC listing 中存在 `YYYY`、`YYYY-MM`、`YYYY-MM-UK` 等部分日期。候选层只读审计
能提示这类值，但独立 AI 不一定主动输出日期精度声明；如果正式 draft 只依赖模型声明，
精确访视窗、洗脱期、持续时间和固定天数阈值可能被错误启用。

另一个边缘情况是：AE/MH 等日期字段在尚未进入标准角色目录时会落入通用来源角色。
即使系统已经从冻结 profile 注入日期约束，旧质量门仍会因角色不是 `date/datetime`
而跳过检查。

## 修订

1. draft 组装从冻结 field-profile 的 `representative_values`、`top_values` 和
   `anomaly_examples` 确定性识别部分日期。
2. 对日期样字段注入不可由模型覆盖的 `value_constraints`：
   - `date_precision`
   - `supports_exact_date=false`
   - `observed_precisions`
   - `basis=frozen_field_profile_observation`
3. 语义质量门只要看到显式日期合同，就执行日期精度判断；不再要求独立 AI 使用特定
   标准角色名。
4. 部分日期保留原值并允许来源审阅；`precise_temporal_rules` 受阻，
   `subject_timeline` 只能受限展示。

## 验证

- `test_monitoring_mapping_draft_repository.py`
- `test_monitoring_mapping_semantic_quality.py`
- 结果：79 passed
- 能力门禁下游定向回归：48 passed

## 当前边界

- 候选层只读审计仍会报告“未声明日期精度”，因为其审阅的是独立 AI 原始候选；
  正式 draft 组装会以确定性约束消化该缺口。
- 完整 V13 队列结束前，不确认、不激活任何正式映射。
