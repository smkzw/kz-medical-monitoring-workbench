# 医学写作子系统：设计驱动动态方案框架专项审阅

日期：2026-07-24  
范围：仅审阅功能完整性、跨投影一致性与医学/科学合理性；未开展安全、后门或漏洞审计。

## 审阅目标

检查 `MedicalWritingStructuredStudyDesign` 和同一 `StudyDefinition` 中的设计事实，是否一致投影到：

1. 方案摘要；
2. 正文章节和目录；
3. 研究流程表（SoA）；
4. 研究流程图；
5. 最终 DOCX 导出。

重点设计项包括 I 期 typed Parts、期中分析、样本量再估计、适应性设计、转组、交叉、开放标签延展（OLE）、SRC 和 DMC。

## 读取的实现与测试

- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/medical_writing_protocol_assembly_plan.py`
- `services/api/app/medical_writing_protocol_template.py`
- `services/api/app/medical_writing_plan_consumption.py`
- `services/api/app/medical_writing_table_templates.py`
- `services/api/app/medical_writing_study_schema.py`
- `services/api/app/medical_writing_document_exporter.py`
- `services/api/app/medical_writing_study_consistency.py`
- `services/api/app/medical_writing_authoring_journey.py`（只读）
- `tests/test_medical_writing_structured_design_contract.py`
- `tests/test_worker01_typed_phase1_parts_and_safe_prefill.py`
- `tests/test_worker02_plan_consumption_cross_projection.py`
- `tests/test_medical_writing_protocol_template.py`
- `tests/test_medical_writing_dynamic_section_matrix.py`
- `tests/test_medical_writing_study_schema.py`
- `tests/test_medical_writing_table_templates.py`
- `tests/test_medical_writing_document_exporter.py`

## 执行步骤与证据

### 现有专项回归

```text
python3 -m pytest -q \
  tests/test_medical_writing_structured_design_contract.py \
  tests/test_worker01_typed_phase1_parts_and_safe_prefill.py \
  tests/test_worker02_plan_consumption_cross_projection.py \
  tests/test_medical_writing_protocol_template.py \
  tests/test_medical_writing_dynamic_section_matrix.py \
  tests/test_medical_writing_study_schema.py \
  tests/test_medical_writing_table_templates.py \
  tests/test_medical_writing_document_exporter.py
```

结果：`158 passed, 8 warnings in 59.19s`。

### 真实函数反例探针

直接构造同一 `StudyDefinition`，调用计划、摘要、SoA 和流程图相关真实函数。关键结果：

```text
design.sample_size_reestimation module present; design driver absent
design.adaptive module present; design driver absent
III期摘要仍显示：含SAD、MAD、first_in_patient模块
typed SAD/MAD + 空 intrinsic_objectives/design_pattern -> 流程图 Part 列表 []
structured treatment_switch/crossover/OLE=true -> 流程图切换识别 False
未填写 population/cohort_dose 的 SAD Part：
  unresolved=True
  module_app=conditional_applicable
  questions=0
  deterministic_projection_allowed=True
SoA 只产生固定表头和五个固定活动名称，其余单元格为空
```

这证明现有绿测主要覆盖“projection gate 可消费”，没有覆盖“实际消费者呈现了同一设计事实”。

## 发现

### P0-1：设计事实存在并行权威，不能保证同一 StudyDefinition 的一致投影

`MedicalWritingStructuredStudyDesign` 是声明的结构化权威，但不同消费者仍读取其他字段：

- 计划层读取 `framing.structured_design`；
- 正文章节 I 期适用性读取 `framing.intrinsic_objectives`；
- 非 I 期流程图是否随机读取 `picos.design_archetype`；
- 转组/交叉/OLE 流程图读取 `design_pattern`、PICOS 文本和 `study_epochs`。

可复现矛盾：

- `structured_design.randomization_mode="randomized"`，但 `picos.design_archetype=""` 时，流程图不生成随机节点；
- typed `phase1_parts=[SAD, MAD]` 已完整填写，但 `intrinsic_objectives=[]` 时，流程图不生成任何 I 期 Part；
- `treatment_switch_planned=True` 但自由文本未出现“转组”时，流程图不生成转组关系。

定位：

- `models.py:2375-2420`
- `medical_writing_protocol_template.py:1012-1092`
- `medical_writing_authoring_journey.py:1187-1191`
- `medical_writing_authoring_journey.py:1324-1405`
- `medical_writing_authoring_journey.py:3446-3500`

最小修复：

1. 建立一个只接受 `StudyDefinition` 的规范化设计投影器；
2. 结构化字段已决定时，所有消费者禁止再从自由文本反推；
3. `picos.design_archetype` 改为由结构化设计确定性派生的兼容字段，或增加强一致性校验；
4. 自由文本仅在结构化状态为 `undecided/None` 时作为迁移输入。

### P0-2：I 期 typed Parts 目前只是“Part 名称选择”，尚未成为摘要、正文、SoA 和流程图的单一权威

`MedicalWritingPhase1Part` 已包含人群、队列/剂量、PK/PD、安全性、停止规则、SoA 和 Part 间转换依赖，但下游没有完整消费：

- assembly plan 只读取 `part_code`；
- `unresolved=True` 不产生阻断问题，仍允许确定性投影；
- 摘要只显示 Part code，不显示各 Part 的人群、剂量、PK/PD、安全、停止规则和转换条件；
- 公司章节适用性仍从 `intrinsic_objectives` 识别 SAD/MAD/食物影响/特殊人群；
- 流程图仍从 `intrinsic_objectives/design_pattern` 识别 Part；
- SoA 是固定空模板，未由 `soa_summary` 和 Part 结构生成。

定位：

- `models.py:2287-2334`
- `medical_writing_protocol_assembly_plan.py:367-423`
- `medical_writing_protocol_template.py:1051-1092`
- `medical_writing_protocol_template.py:1163-1170`
- `medical_writing_protocol_template.py:1918-1930`
- `medical_writing_authoring_journey.py:3484-3500`
- `medical_writing_table_templates.py:55-70`

最小修复：

1. I 期选中 Part 但 `unresolved=True` 时，对摘要、章节、SoA、流程图和 DOCX 形成 blocker；
2. I 期章节适用性直接读取 typed `part_code`；
3. 每个 Part 的正文初稿绑定该 Part 的 typed 字段，而不是 `intrinsic_objectives`；
4. SoA 按 Part 分区生成访视列和活动行；
5. 流程图按 `transition_dependencies` 生成 Part 间依赖；
6. 为 `qt`、`ba_be` 和 `first_in_patient` 增加公司章节语义节点，避免计划层有模块而正文无落点。

### P0-3：转组、交叉、OLE、样本量再估计和适应性设计只有布尔开关，信息不足以科学生成方案

当前字段只能表示“有/无”，不能表达：

- 转组：适用人群、原治疗、目标治疗、触发条件、时间点、盲态处理和分析策略；
- 交叉：序列、周期、洗脱期、周期效应、残留效应和分析方法；
- OLE：进入条件、治疗方案、持续时间、盲态试验到开放期的衔接和长期随访；
- 样本量再估计：盲态/非盲态、时间点、参数、规则、上限和 alpha 保护；
- 适应性设计：适应性类型、决策规则、模拟依据、操作偏倚控制和监管沟通状态。

因此即使布尔值为 `True`，系统也无法可靠生成摘要、正文、SoA 或流程图。

定位：`models.py:2403-2410`。

最小修复：将上述布尔值升级为带 `planned: Optional[bool]` 的 typed 子对象；`planned=True` 但关键字段缺失时阻断对应投影。保留只读迁移器把历史布尔值迁移成“已选择但内容未解决”。

### P1-1：计划层声明的模块没有对应章节语义节点

assembly plan 有以下模块：

- `design.sample_size_reestimation`
- `design.adaptive`
- `design.treatment_switch`
- `design.crossover`
- `design.open_label_extension`
- `governance.src`
- `governance.dmc`

但公司章节树没有对应 semantic node；正文事实映射也没有这些设计字段。计划显示 applicable，并不会产生相应章节或可靠正文。

定位：

- `medical_writing_protocol_assembly_plan.py:917-975`
- `medical_writing_protocol_template.py:396-520`
- `medical_writing_protocol_template.py:1720-1791`

最小修复：不要机械增加七个同名独立章节。按临床含义映射：

- 转组/交叉/OLE：总体设计、研究周期、干预、退出/停药、统计分析，必要时生成条件子章节；
- 样本量再估计：样本量和期中/适应性分析；
- 适应性设计：总体设计、决策规则、统计方法；
- SRC/DMC：安全性委员会/试验监督；仅在确实参与剂量递增决策时进入 I 期流程图。

### P1-2：design driver 集合漏掉样本量再估计和适应性设计

两个 module 已存在，但 `resolve_protocol_assembly_design_drivers` 未生成相应 driver，合同的 `driver_kind` 也不包含这两类。消费者无法获得其来源引用、状态和影响目标。

定位：

- `models.py:3911-3942`
- `medical_writing_protocol_assembly_plan.py:1157-1200`

最小修复：新增 `sample_size_reestimation` 和 `adaptive_design` driver kind，并在 driver 生成器中写入来源路径、状态、值摘要和正确投影目标。

### P1-3：摘要投影不完整，且未按研究分期过滤 I 期 Parts

摘要“研究设计”当前会显示随机、盲法、对照、分配、中心、I 期 Part、适应性、SRC、DMC；但不显示转组、交叉、OLE、样本量再估计。它也没有校验研究分期，因此 III 期 `StudyDefinition` 中残留的 I 期 Part 会直接显示。

定位：`medical_writing_protocol_template.py:1864-1953`。

最小修复：

1. 先消费已确认 plan 的 synopsis manifest；
2. 仅渲染该 manifest 中 applicable 的设计模块；
3. 对复杂设计使用 typed 子对象的规范化摘要，不从布尔值生成模糊短语；
4. 增加 III 期残留 I 期 Part 的反例测试。

### P1-4：SoA 当前仅“过计划门”，没有从设计事实生成内容

`schedule_of_activities` 实例化时会核对 `soa` projection，但生成内容仍是固定五列、五行空模板；计划只作为 metadata 写入，不驱动访视、Part、转组、交叉周期、OLE、PK/PD、安全活动或附注。

定位：`medical_writing_table_templates.py:55-70`、`258-288`、`427-434`。

最小修复：新增 `StudyDefinition -> SoA draft` 投影器。至少消费：

- typed Phase I Parts 及其 `soa_summary`；
- `study_epochs`、`visit_strategy`、终点评估时点；
- 干预、PK/PD、安全和量表；
- 转组/交叉/OLE typed 设计；
- 结构化附注（时间窗、条件、例外、采样集）。

### P1-5：流程图把“交叉设计”与“转组治疗”混为一类，医学语义不成立

`crossover/cross-over` 被 `_study_schema_epoch_kind` 直接映射为 `treatment_switch`。真正交叉设计需要治疗序列、周期、洗脱期和序列/周期效应；它不等同于安慰剂组进入 OLE 后转为试验药。

定位：`medical_writing_authoring_journey.py:3402-3434`。

最小修复：新增独立的 crossover period/sequence 图模型和 edge kind；转组、交叉、OLE 三者分别生成，不共享“转组治疗”语义。

### P1-6：现有跨投影测试只验证计划对象，不验证真实输出

`test_worker02_plan_consumption_cross_projection.py:494-642` 在每个 projection 上重复读取同一 plan，并检查 module 状态；没有断言：

- 摘要实际行和文本；
- 正文实际章节、初稿和来源绑定；
- SoA 实际列、行、单元格和附注；
- 流程图实际 Part、节点、边和 SVG；
- DOCX 实际目录、章节、表格和图。

这解释了为什么 `158 passed` 仍未发现上述矛盾。

最小补测矩阵：

1. I 期 SAD+MAD；
2. I 期 SAD+MAD+首次患者；
3. III 期复杂背景治疗安慰剂对照；
4. III 期“期中分析+安慰剂组转组+OLE”；
5. III 期阳性药对照；
6. 2×2 交叉设计；
7. 盲态样本量再估计；
8. 适应性无缝 II/III 期；
9. SRC 与 DMC 分别存在/不存在。

每个用例必须断言五个实际成品投影，而不是仅断言 plan 可消费。

## 已确认可保留的实现

- `MedicalWritingPhase1Part` 的字段边界合理，能够作为后续单一权威；
- `MedicalWritingInterimAnalysisDesign` 已有目的、时点、信息分数、统计边界、alpha 控制、委员会和操作防火墙，结构明显优于其他布尔设计项；
- assembly plan 对 `planned=None/False/True` 的三态模块决策方向正确；
- 期中分析已能动态控制摘要行和统计章节；
- StudyDefinition/文档绑定与一致性服务能够阻断旧定义直接作为当前终稿，但不能替代内容投影本身；
- DOCX 导出器能够输出已经组装好的表格和流程图；当前主要缺口位于上游设计内容生成，而不是 DOCX 图形嵌入函数。

## 建议实施顺序

1. 先消除并行权威：建立规范化结构化设计投影器和一致性校验。
2. 补齐复杂设计 typed 子对象，并把 `planned=True + 关键字段缺失` 设为投影 blocker。
3. 修复 I 期 typed Parts 的章节、SoA 和流程图消费。
4. 增加复杂设计的条件章节映射和正文事实映射。
5. 建立真实 SoA draft 投影器。
6. 区分转组、交叉和 OLE 的流程图语义。
7. 增加五类实际输出级跨投影回归，再运行 DOCX 成品检查。

## 修改文件

本轮未修改生产代码及测试代码。仅新增本审阅记录，并同步更新总任务日志。
