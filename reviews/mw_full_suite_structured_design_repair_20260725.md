# 医学写作结构化研究设计全仓失败修复记录

日期：2026-07-25  
范围：结构化研究设计、AI 预填、I 期 Parts、动态方案模板测试  
运行态：未重启 5174/8911，未读写运行态 SQLite

## 结论

本次指定的 3 个测试文件实际复现 10 项失败，不是 9 项。逐项核对后，
10 项均为测试契约落后于当前生产语义，并非生产代码回归：

1. 3 项 `SimpleNamespace` 错误：测试夹具未跟随
   `MedicalWritingStudyDefinition`/结构化设计契约补齐
   `picos.design_archetype`、`state_sha256` 及新增复杂设计字段。
2. 3 项 adopt/replay/regenerate 失败：测试按候选数组下标 0 采用，
   但下标 0 现为“待决定卡”，不是随机或安慰剂事实。
3. 4 项无 AI 预填/I 期 Parts/期中分析失败：旧断言要求
   `confidence=low` 并直接采用首项；当前正确语义是
   `confidence=none + pending_decision + manual_only`，用户显式选择具体
   备选后才成为项目事实。

没有修改生产源码。现有生产行为符合以下边界：

- AI 预填是可修改建议，不自动成为临床结论。
- “待决定卡”不表达随机化、对照、期中分析或 I 期 Part 事实。
- 用户选择具体候选或提交编辑值后，采用结果才进入结构化项目事实。
- I 期 Parts 支持多选；本次采用测试显式选择 `SAD + MAD` 备选。
- 动态章节继续由已确认的 `structured_design` facts 决定出现、标记不适用
  或省略。
- 原子 composite adopt 与三事实检索门未修改。

## 修改

### `tests/test_medical_writing_structured_authority_p1_fix.py`

- 为测试定义补齐空的 `design_archetype` 和合法 `state_sha256`。
- 用真实 `MedicalWritingStructuredStudyDesign` 构造夹具，自动携带新增复杂
  设计字段默认值，避免 `SimpleNamespace` 漂移。

### `tests/test_medical_writing_structured_design_contract.py`

- 为测试 PICOS 夹具补齐空的 `design_archetype`。
- adopt 测试不再假设候选顺序；按结构化值定位“随机”和“安慰剂”候选。
- replay/regenerate 仍验证用户确认后的结构化事实持久化与幂等，不把待决定卡
  当事实。

### `tests/test_worker01_typed_phase1_parts_and_safe_prefill.py`

- 无 AI 设计主卡改验 `confidence=none`、`pending_decision`、
  `manual_only` 和显式限制说明。
- 期中分析改验“待决定”语义，不把 `planned` 脚手架投影当项目事实。
- I 期 Parts 采用测试显式选择 `SAD + MAD` 多选备选，再验证仅写入
  `part_code`，不虚构人群、剂量、PK/PD、安全性、停止规则或 SoA 细节。

## 验证

聚焦测试：

```text
python3 -m pytest -q \
  tests/test_medical_writing_structured_authority_p1_fix.py \
  tests/test_medical_writing_structured_design_contract.py \
  tests/test_worker01_typed_phase1_parts_and_safe_prefill.py

57 passed in 0.70s
```

相邻回归：

```text
python3 -m pytest -q \
  tests/test_medical_writing_authoring_prefill*.py \
  tests/test_medical_writing_design_projection*.py \
  tests/test_medical_writing_protocol_assembly_plan.py \
  tests/test_medical_writing_protocol_template.py \
  tests/test_medical_writing_structured_authority_p1_fix.py \
  tests/test_medical_writing_structured_design_contract.py \
  tests/test_worker01_typed_phase1_parts_and_safe_prefill.py

495 passed, 10 warnings in 9.08s
```

10 个 warning 均为既有 FastAPI `on_event` 弃用提示，与本次结构化设计修复
无关。

## 变更边界

- 未修改前端 App。
- 未修改翻译、PICOS、检索或运行态代码。
- 未重启本地服务。
- 未写运行态数据库。
- 未改变候选生成顺序、原子 composite adopt 或三事实检索门。
