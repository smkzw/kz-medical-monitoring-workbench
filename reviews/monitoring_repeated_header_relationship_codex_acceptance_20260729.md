# 重复表头字段关系修复 Codex 验收

## 结论

通过。该切片只扩展字段画像中的可观察关系候选，不确认医学语义、编码体系、字典版本或正式字段映射。

## 审阅要点

- `FIELD__2`、`FIELD__3` 先拆分为基础字段名与重复后缀。
- 既有配对规则仅在完全相同的重复后缀组内运行。
- 无后缀字段仍只与无后缀字段配对。
- `__2` 与 `__3` 不会跨组配对。
- 输出仍仅含共现、单侧缺失、唯一配对和一对多计数，不包含行值或业务键。
- 既有普通字段配对行为保持不变。

## 验证

执行：

```text
.venv/bin/python -m pytest -q \
  tests/test_monitoring_ai_field_profiler.py \
  tests/test_monitoring_ai_service.py \
  tests/test_monitoring_ai_v7_deterministic_repair.py
```

结果：`129 passed`。

## 运行边界

- 未重启正在处理 V7 真实项目队列的 API。
- 当前运行队列仍使用旧进程加载的画像逻辑。
- 新关系将在后续新批次/新画像中生效，不追溯改写已经冻结的输入、候选或审计记录。
- 关系证据只提高独立 AI 对重复表头的可解释性；标准化编码仍必须满足同一行配对、明确编码体系、独立字典版本字段和医学确认门禁。

## 非编码同行关系补充验收

在相同隐私与后缀边界下，新增以下聚合关系：

- `site_identity_pair`：`SITEID-SITENM/SITE`；
- `visit_identity_pair`：`VISIT-VISTOID/VISITNUM`；
- `value_unit_pair`：数值画像字段与严格同名 `_UNIT/UNIT` 字段，以及明确的 `CMDOSE-CMDOSU`；
- `performed_reason_pair`：严格同前缀 `*PERF-*REASND`。

Codex 复核确认：

- 只在同域、完全相同重复后缀组内生成；
- 非数值字段不会因存在 `_UNIT` 名称而建立值-单位关系；
- 不接受任意相似名称、不同前缀、跨域或跨后缀配对；
- 输出仍沿用无行值的聚合关系合同。

补充执行字段画像、AI 服务、mapping draft 和真实 AI 映射测试组合，结果
`141 passed`。该关系仍不构成中心主数据、访视定义、单位语义或医学映射确认。
