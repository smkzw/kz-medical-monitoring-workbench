# 医学写作设计事实单一权威 P0 实现合同

Updated: 2026-07-20
Owner: Codex architecture and final acceptance
Status: awaiting Hy3 focused evidence and execution-manager decomposition

## Confirmed Architecture

- 是否计划期中分析及其目的、时点、信息分数、统计边界、alpha控制、独立
  委员会和操作防火墙，唯一权威是
  `framing.structured_design.interim_analysis`。
- 阳性对照的存在和名称可由`structured_design.comparator_type`及
  `comparator_intervention`标识；剂量、频次、途径和治疗期唯一权威必须是
  `picos.intervention_rules.ip_regimens`中
  `product_role=active_comparator`的对象。
- 背景治疗、补救治疗和其他非试验治疗唯一权威必须是
  `picos.intervention_rules.non_ip_treatment_rules`；背景治疗使用
  `rule_class=background`。普通CM只使用`allowed_cm/prohibited_cm`。
- `dose_adjustment`及其他试验药物变更只属于IP action rules；CM是非试验
  用药，二者不得互相投影。
- `design_pattern`、`comparator_summary`、
  `required_background_rules`等旧字段只能是结构化权威的确定性兼容投影，
  不能继续作为可独立编辑的第二事实源。

## Current Gaps To Verify/Fix

1. `design.comparator_type`采纳目前只写
   `structured_design.comparator_intervention`及自由文本
   `picos.comparator_summary`，不会创建或更新active-comparator IP
   regimen；因此剂量/频次/途径仍可能被用户或测试塞入自由文本。
2. AI/确定性prefill的背景治疗候选目前落在
   `picos.required_background_rules`自由列表，未证明会桥接为结构化
   non-IP BACKGROUND规则。
3. 前端同时展示旧自由文本字段和结构化InterventionRulesEditor；在
   `authority=structured`时仍允许双录，存在事实漂移。
4. `interim_analysis.planned=false`虽有章节适用性逻辑，但必须用真实DOCX
   定位每个“期中分析”命中，区分目录/模板标签/不适用说明与错误正文。

## Target Behavior

- AI预填返回结构化方案包，不只返回摘要句。用户采纳阳性对照候选时：
  - `structured_design`记录对照类型和药物身份；
  - 同一事务upsert active-comparator IP regimen；
  - `comparator_summary`由结构化对象投影。
- 用户采纳复杂背景治疗候选时，同一事务upsert一个或多个BACKGROUND
  non-IP规则；`required_background_rules`由结构化规则投影。
- `authority=structured`后：
  - 旧字段在UI中隐藏或只读展示“由结构化规则生成”；
  - API拒绝只改旧字段造成结构化事实不变的写入；
  - 投影hash和来源revision随结构化对象更新。
- `planned=false`时，方案摘要、目录、统计章节、动态章节树和DOCX中不出现
  期中分析模块；若公司模板要求保留编号，必须以明确的设计规则选择“省略”
  或“不适用”，且全篇一致。
- `planned=true`时，同一权威投影到方案摘要、统计章节、DMC/SRC关系、
  研究流程图、SoA相关操作和DOCX；不得从自由文本重新推断。

## Acceptance

1. 保存一个含具体剂量/途径/频次的阳性对照AI候选后，所有具体方案只存在
   于active-comparator IP regimen；结构化设计中无剂量字段。
2. 背景治疗只存在于BACKGROUND non-IP规则；旧列表与正文均由该对象投影。
3. CM、背景治疗、补救治疗、IP剂量调整和停药/重启规则在模型、UI、章节和
   DOCX中保持边界。
4. Phase I `planned=false`与Phase III `planned=true`各保留一份真实DOCX及
   OOXML上下文证据。
5. 编辑任一结构化事实后，方案摘要、章节矩阵、对应正文、流程图和导出同步
   更新；未受影响章节保持原revision/hash。
6. 旧项目以显式一次迁移生成结构化规则；迁移前后语义diff可审阅，原记录和
   审计链保留。
7. 前端无重复可编辑真相源，医学经理主要通过AI默认填充后修订确认。
