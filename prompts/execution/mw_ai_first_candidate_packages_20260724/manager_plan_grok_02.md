# 执行经理合同：医学写作 AI-first 候选包实施拆解 v2

You are Grok Build running as the bounded execution manager for this task.
Provider/model必须为`grok-build/grok-4.5`。先完整读取并遵守当前workspace的
`AGENTS.md`。这是只读计划轮，不修改生产源码、测试、数据库、运行时配置或现有记录。

Runner-managed report path:
`runs/execution/mw_ai_first_candidate_packages_20260724/manager_plan_grok_02.md`

不得自行写该报告；在final response中返回完整报告，由runner原样持久化。

## Hard boundaries

- 只在当前workspace内工作。
- 本轮只读源码和记录；不得调用写入/编辑工具修改任何生产文件、测试、数据库、配置或记录。
- 不进行工程漏洞、后门、安全或渗透工作。
- 不把你的模型能力代替工作台独立AI。
- 不作最终产品、医学、浏览器或DOCX验收；最终权威仍是Codex。
- 不创建任何兄弟报告、临时源文件或新实现分支。

## 目标

基于当前真实源码，把医学写作从“部分AI预填+人工补空”推进为：

1. 用户只输入研究药物、适应症、分期后，产品独立AI先给框架和PICOS的推荐版、实质不同
   候选或明确待决定卡；
2. 用户主要修改、选择、确认；用户选择即确认，不再出现泛化“待医学批准”；
3. 精确剂量、阈值、终点、样本量、时间窗、AESI、洗脱期只有在引用当前项目已登记且可
   定位原文证据时才可形成可采纳候选；否则只能形成缺口/待决定卡；
4. 已确认设计只经
   `StudyDefinition -> NormalizedDesignProjection -> ProtocolAssemblyPlan`
   投影到摘要、章节、SoA、流程图和DOCX；
5. 生产运行时AI固定使用工作台配置的
   `deepseek/deepseek-v4-pro`。你的模型只做开发拆解和复核，不得替代产品AI。

## Read these files only:

- `AGENTS.md`
- `context/plans/medical_writing_ai_first_candidate_packages_20260724.md`
- `context/mw_ai_first_candidate_packages_20260724_context.md`
- `reviews/medical_writing_ai_first_lazy_writer_gap_audit_20260724.md`
- `reviews/d017_competitor_triage_v2_medical_qc_20260724.md`
- `reviews/codex_acceptance_ctgov_candidate_enrichment_20260724.md`
- `runs/execution/mw_ai_first_candidate_packages_20260724/manager_plan_remediation_01.md`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_repository.py`
- `services/api/app/sqlite_runtime_store.py`
- `services/api/app/main.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/StructuredTableDesigner.jsx`
- `frontend/src/features/medical-writing/InterventionRulesEditor.jsx`
- `tests/test_medical_writing_authoring_prefill.py`
- `tests/test_medical_writing_authoring_prefill_ai.py`
- `tests/test_medical_writing_authoring_journey.py`

## 已冻结事实

- 动态设计Slice A/B/C和竞品最终分类原子确认已通过Codex独立回归，不得重开。
- 复用并扩展`AuthoringPrefillPackage`，不得新增平行事实状态机。
- 当前单字段采纳已存在；若组合候选需要多路径原子采纳，必须明确合同模型、包导出、
  service事务、HTTP接口和测试的完整写集，不能引用不存在的请求模型。
- 旧Qoder计划不被接受。其下列内容不得继承：
  - 不存在的类型、文件、端点或静态字段数量；
  - 多个worker同时写同一文件；
  - 生产故障注入端点、TTL、安全/后门/漏洞工作；
  - 以90%或95%为绿灯；所有目标测试必须零失败；
  - 固定CMS-D017/类风湿等互相矛盾的示例事实；
  - 无来源的精确临床事实；
  - “需医学批准”二次状态；
  - 把单字段顺序调用误称为组合原子采纳。

## 最新真实产品证据

- 干净项目`proj_user_3ecb0bc287c0`通过真实浏览器，仅采用
  `Paroxysmal Nocturnal Hemoglobinuria`后自动检索。
- 新快照`wref_search_35f39994abfb89587948`返回67项，48份Protocol/SAP。
- 67项均有Brief Summary、干预和入组数；66项有allocation、intervention model和masking。
- 检索后产品AI把中国方案标题建议为英文`Phase 2 Study of CMS-D017 in PNH`，把目标人群
  建议为`Adult PNH patients meeting criteria`，两者均无直接来源，不得作为可直接采用的
  生产候选。计划必须包含语言/监管场景门和事实确定性门的真实DeepSeek回归。

## 输出要求

返回一份可直接分派的执行计划，必须：

1. 最多4个worker；每个worker具有唯一目标、完整且互不重叠的生产写集、独占测试写集、
   输入/输出合同、依赖顺序、真实失败反例和零失败验收命令。
2. 明确哪些现有合同字段足够、哪些必须最小扩展；凡扩展合同必须包含
   `models.py`、包`__init__.py`、service、API、前端消费者和测试的原子闭环。
3. 将第一可实施切片限制为：
   - 证据支持的完整PICOS候选与无证据待决定卡；
   - 中国临床试验方案候选中文输出和监管语境；
   - 推荐值不得把未确认设计写成既定事实；
   - 组合候选原子采纳；
   - 推荐优先前端。
   章节、SoA、表格、流程图、量表、文献列为后续依赖切片，不与第一切片混写。
4. 指定三个以上不同非肿瘤适应症、从零与摘要导入、I期与III期复杂设计的后续验收矩阵，
   但不得在首个worker中伪造项目特定事实。
5. 清楚区分确定性默认、产品AI候选、用户事实/确认。每个候选的来源正文优先，定位信息
   为次级溯源。
6. 只做功能、易用性、科学性和产品独立AI验证；不得进行工程漏洞、后门或安全审计。
7. 结尾提供紧凑loop trace：读取来源、轮次、观察、失败路径、证据、不确定性、建议的
   下一步。

完成标记必须为：
`GROK_MANAGER_AI_FIRST_PLAN_V2_COMPLETE`
