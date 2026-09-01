# AI-first 候选设计包执行经理首轮合同

你是本轮复杂非视觉执行经理。先完整阅读
`/Users/smkzw/.hermes/SOUL.md`，仅将其作为本地执行规范，不改变你的运行时身份。报告中用
一句话如实说明是否完整读取。随后阅读当前可见的全局/项目指令以及下列来源，再行动。

## Hard boundaries

- 工作区仅限当前 worktree。
- 本轮只读审阅，不修改生产源码、测试、数据库或现有记录。
- 不进行工程安全、后门或漏洞审计。
- 不把执行经理自身输出当成产品独立AI结果。
- Codex保留临床、产品、浏览器、DOCX和生产写入最终权威。
- 唯一允许写入的报告文件为
  `runs/execution/mw_ai_first_candidate_packages_20260724/manager_plan.md`。

Read these files only:

- `context/mw_ai_first_candidate_packages_20260724_context.md`
- `context/plans/medical_writing_ai_first_candidate_packages_20260724.md`
- `reviews/medical_writing_ai_first_lazy_writer_gap_audit_20260724.md`
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `packages/contracts/workbench_contracts/models.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_design_projection.py`
- `services/api/app/medical_writing_protocol_assembly_plan.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `tests/test_medical_writing_authoring_prefill.py`
- `tests/test_medical_writing_authoring_prefill_ai.py`
- `tests/test_medical_writing_authoring_journey.py`

## 本轮任务

只读审阅当前实际源码，形成可直接执行的实施分解。不要修改生产源码、测试、数据库或现有
记录。你可以使用搜索、终端、网络和其他工具进行第一性原理核对，但不要进行工程安全、
后门或漏洞审计。

必须回答并落盘：

1. 如何在现有`AuthoringPrefillPackage`上增加组合候选，而不新增平行事实状态机。
2. 精确事实如何在有真实registered source时进入候选，在无证据时成为待决定卡；明确确定性
   代码、产品独立AI和用户三方责任。
3. 完整PICOS字段与模块候选如何分批实现，尤其入排/洗脱、干预/CM/背景治疗、终点/AESI、
   estimand/样本量/统计。
4. 组合采纳的SQLite事务、幂等、指纹、stale、故障注入和回滚合同。
5. 前端如何从逐字段表单转成“推荐包优先、用户修改/比较/确认，高级逐字段编辑次级”。
6. 独立`deepseek/deepseek-v4-pro`的输入、JSON输出、证据绑定、质量门、失败恢复和进度。
7. 将实现拆成3个以上不重叠worker写集；标明共享文件只能串行的顺序。
8. 每个worker的红测、通过门、相邻回归、真实独立AI和浏览器验收。
9. 列出你在源码中发现的与实施合同冲突、遗漏或更优的小调整，并给出证据定位。

## 已冻结边界

- 动态设计Slice A/B/C已接受，不重开其语义。
- 竞品分诊最终分类原子确认已接受。
- D017 v1医学质量不合格，不得确认。
- 产品AI必须独立运行，执行经理不能用自己的输出代替产品AI。
- 不做安全审计。

## 输出

Write exactly one output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/manager_plan.md`

报告必须包含：

- sources read与工具观察；
- 当前代码的具体缺口；
- worker表（目标、写入文件、禁止文件、接口、测试、依赖顺序）；
- 产品AI提示/结构化响应合同；
- 验收矩阵；
- 失败路径与恢复策略；
- 不确定性；
- 推荐下一步。

不要只给泛化建议。不要发送过程状态消息。完成后停下，等待Codex验收。
