# 商业化与开源产品基线调研增补

日期：2026-07-10

## 调研目的

本轮只回答一个问题：现有工作台从“可运行脚手架”走向“可商业交付产品”时，哪些交互与后端合同应当成为全系统共用能力。具体子系统进入实现前仍需追加该子系统的专项产品、开源、监管和技术调研。

## 证据分级

| 等级 | 来源 | 用途 | 限制 |
|---|---|---|---|
| A | ICH/FDA/NIH/官方技术文档 | 监管、质量、可追溯和工作流原则 | FDA AI 文件为草案，不可表述为已实施强制要求 |
| B | 厂商官方产品文档 | 已商业化工作流与交互模式 | 功效、效率和合规表述属于厂商口径，不能直接当作独立效果证据 |
| B | 官方开源项目与维护组织 | 可复用技术路径与实现边界 | 开源包不等同于验证过的生产系统，需要本地验证与治理 |

## 外部产品观察

### 1. 多源医学审阅不是“上传后出一张风险表”

Veeva DQS 官方文档将 Study Connector、统一研究骨架、Workbench、内部 observation、对外 query、自动 checks、KRI/QTL 和增量数据接口放在同一条数据审阅链路中。对本工作台的直接启示是：原始 listing 映射、批次 diff、内部医学判断、中心 Query 和审计状态必须使用同一稳定对象模型，不能由各页面分别拼装。

采用：`SourceArtifact -> DataBatch -> Observation/RiskCase -> Query/Action -> Approval/Audit` 统一链路。

不采用：照搬 Veeva 的数据管理产品边界；本产品只构建医学经理需要的审阅与协作能力，不代替 EDC/CDMS。

### 2. 医学监查需要“内部观察”和“外发 Query”两层

Veeva DQS 将内部 observation 与对研究中心/数据提供方的 query 分开；Medidata Remote Source Review 也强调结构化提交、任务路由、权限、状态报告和全量审计。杉云 iMRDP 的官方页面则将临床、实验室和安全数据的一体化查看作为医学监查核心卖点。

采用：风险识别后先进入内部医学复核，只有明确发起动作后才生成 Query；已读、处置、外发、回复、确认、关闭/重开是不同状态。

不采用：把运营 SDV/SDR 或现场监查任务直接扩张为本系统模块。

### 3. 风险应当围绕受试者安全和关键数据可靠性闭环

ICH E6(R3) 要求识别可能实质影响关键质量因素的风险，并按发生可能性、可检测性以及对受试者保护和结果可靠性的影响进行评价；风险控制、沟通、复核和报告需要形成连续过程。

采用：风险对象必须保存触发依据、影响维度、可检测性/严重性解释、控制动作、复核周期和关闭依据；项目看板的风险聚合必须能回到单个受试者、数据点和来源。

不采用：把所有异常都等同为高风险，或只展示算法分数而不展示医学依据。

### 4. 入排审核的最小可信单元是“标准逐条判断 + 原文证据”

NIH TrialGPT 将匹配拆为 criterion-level 判断，并为每条标准定位患者文本证据。其官方说明同时明确没有官方 Web 系统，因此只能借鉴解释性匹配方法，不能把研究原型当作可直接部署产品。

采用：每条 `IN-xx`/`EX-xx` 独立保存标准版本、结构化条件、受试者证据片段、缺失问题、AI建议和人工结论。

不采用：只输出“符合/不符合”的总分，也不把患者到试验的招募排序扩展为本系统目标。

### 5. 医学写作的核心不是生成，而是句级追溯、复核和批准

Yseop 官方产品页面将 source-grounding、句级追溯、已批准内容复用、Word/Veeva 集成以及“人类决定”作为监管写作核心。其效率与返工率数字属于厂商口径，本项目不据此估算 ROI。

采用：编辑器与 AI 修订栏为首页主工作面；每条建议保留源段、提示词版本和差异；接受建议仍只生成待医学批准内容；批准内容可锁定并跨章节/文档复用。

不采用：聊天框一次生成整篇文档，或接受 AI 建议后自动标记为正式批准。

### 6. TFL 应当可复现、可审阅、可导出

pharmaverse 官方组织提供围绕 SDTM、ADaM、Tables/Listings/Graphs 和交互式临床数据探索的维护型开源包生态。对本项目的价值是使用成熟统计/展示组件与可复现代码，而不是在前端手工重写统计逻辑。

采用：数据集清单、分析人群、变量/派生、运行代码、输出版本、审阅处置和写作引用必须关联；交互查看与监管输出使用同一分析结果版本。

不采用：用前端图表计算替代验证过的统计脚本，或把 SDTM 当作所有分析的默认数据源。

### 7. 独立 AI 必须按具体使用情境治理

FDA 2025 年 AI 草案以 context of use 为核心提出风险导向的可信度评估框架。该草案针对支持监管决策的信息/数据，不意味着本工作台每个助手功能都属于同一监管等级，但提示本系统不能只登记“用了什么模型”。

采用：每类 AI 任务独立定义用途、输入来源、允许输出、禁止结论、验证数据、性能门槛、人工复核和回退；模型升级触发再验证。

不采用：把一个通用模型 smoke test 当作所有医学任务均已验证。

## 形成的统一产品合同

1. 一个项目只有一个 canonical project context；来源项目、引用项目和当前业务项目必须显式区分。
2. 原始文件不可变；解析映射、AI 输出、人工修订和正式批准内容逐层派生并版本化。
3. 所有异步处理都生成可恢复任务：`queued/running/blocked/failed/review_required/completed`，并保存 provider、模型、提示词、输入指纹和错误。
4. 所有医学对象都有来源定位、内部复核状态和批准状态；页面不自行推断这些状态。
5. 批次更新使用稳定业务标识和 diff，不按数组位置或一次性随机 id 判断“新增/消失”。
6. 内部观察、风险、Query、审批和写作交接是不同对象，以显式关系相连。
7. 桌面端是完整工作面；移动端只保证灾难性退化检查，不删减桌面能力。

## 后续专项调研门

每个子系统开工前追加：至少 2 个成熟商业产品、2 个活跃开源/标准实现、1 组监管或方法学来源；记录采用项、拒绝项、许可/隐私/部署风险，并映射到可执行验收用例。

## 来源

- Veeva, Clinical Data Applications Overview, accessed 2026-07-10: https://cdmshelp.veeva.com/lr/resources/clinical-data-overview/
- Medidata, Remote Source Data & Document Review, accessed 2026-07-10: https://www.medidata.com/en/clinical-trial-products/clinical-operations/rbqm/remote-source-review/
- 上海杉云医疗科技有限公司, 智能医学监查数据平台（iMRDP）, accessed 2026-07-10: https://sprucecloud.com.cn/znyxjcsjpt
- Yseop, Regulatory-Grade AI for Life Sciences, accessed 2026-07-10: https://yseop.com/
- NIH/NLM, TrialGPT FAQ, accessed 2026-07-10: https://www.ncbi.nlm.nih.gov/research/trialgpt/faq/
- NIH/NLM, TrialGPT source repository, accessed 2026-07-10: https://github.com/ncbi-nlp/TrialGPT
- pharmaverse, official project site, accessed 2026-07-10: https://pharmaverse.org/
- ICH, E6(R3) Good Clinical Practice, Step 4 final guideline, 2025-01-06: https://www.swissmedic.ch/dam/swissmedic/en/dokumente/bewilligungen/klv/guideline-for-good-clinical-practice-e6-r3.pdf.download.pdf/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106.pdf
- FDA, Considerations for the Use of Artificial Intelligence To Support Regulatory Decision-Making for Drug and Biological Products, Draft Guidance, 2025-01: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/considerations-use-artificial-intelligence-support-regulatory-decision-making-drug-and-biological
