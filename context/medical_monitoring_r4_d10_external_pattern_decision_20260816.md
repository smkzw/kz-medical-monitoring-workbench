# R4-D10 外部模式核验与本地设计决策

日期：2026-08-16  
范围：项目级、跨中心安全与疗效聚合合同；不选择或安装新依赖，不进入 runtime/UI。

## 核验来源与证据等级

### A 级：监管/国际指南原文

1. ICH E6(R3) Principles + Annex 1，Step 4 Final Guideline，2025-01-06，2025-10-24 勘误版。其 3.9-3.10 要求监督与质量管理按研究复杂性和风险相称，关注可能实质影响受试者权益、安全和结果可靠性的关键质量因素，并及时升级、跟进问题。  
   <https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106_ErrorCorrections_2025_1024.pdf>
2. FDA《Oversight of Clinical Investigations — A Risk-Based Approach to Monitoring》，2013。集中监查可跨中心识别缺失、不一致、异常分布、缺乏预期变异、方案违背与系统性错误；结果用于聚焦进一步核查，不等于中心有过错或医学因果已成立。  
   <https://www.fda.gov/media/116754/download>
3. FDA《A Risk-Based Approach to Monitoring of Clinical Investigations: Questions and Answers》，Final Guidance，2023-04。监查是确认研究活动是否按计划执行的质量控制工具，监查方法需按研究特征和风险定制。  
   <https://www.fda.gov/regulatory-information/search-fda-guidance-documents/risk-based-approach-monitoring-clinical-investigations-questions-and-answers>
4. ICH E2F《Development Safety Update Report》，2010。项目累积安全审阅应关注新出现的问题、既有问题频率/严重程度变化、剂量/疗程/时间过程、可逆性、风险因素、特殊人群、停药、实验室毒性、依从性和缺乏疗效可能造成的受试者风险；累积获益-风险变化需要简明表达，但不等于完成全面获益-风险评估。  
   <https://database.ich.org/sites/default/files/E2F_Guideline.pdf>

### B 级：成熟开源参考实现

5. `SafetyGraphics/safetyGraphics` 2.1.1：MIT；R/Shiny；以灵活数据映射承载安全性图形、交互下钻和可复现报告。GitHub 默认分支最后推送于 2023-10-20；2.1.1 release 发布于 2023-02-02。  
   <https://github.com/SafetyGraphics/safetyGraphics>
6. `openanalytics/clinDataReview` 1.6.1：MIT；支持临床监查的交互表格、listing、图形，以及两个数据批次的比较；包含 patient profile 可视化适配。GitHub 版本文件日期 2024-06-17。  
   <https://github.com/openanalytics/clinDataReview>

## 采用决策

采用外部实现的**交互与可追溯模式**，不在 R4 引入 R/Shiny runtime 依赖：

- 项目总览与中心分布并存，图形必须能下钻到成员、分母和原始 listing；
- 当前全量与前次可比版本的变化同时呈现；
- 图形、表格与 listing 使用同一过滤/身份/版本上下文；
- 所有率同时保留绝对人数/事件数、分母、暴露或随访机会量及不确定性；
- 项目级信号只作为需要医学审阅的可追溯结论，不能由离群值、p 值、综合评分或模型多数票直接建立；
- 跨中心异常用于优先核查，不生成中心质量结论、惩罚性排名或黑箱总分；
- 小样本、短随访、中心启动差异、病例构成、覆盖变化和盲态限制必须进入可比性门；
- 项目级累积安全/疗效只在当前 ModeContract、分析集、分母、治疗角色和估计方法均有权且可比时评价；否则明确为边界或不可评价。

## 不采用项

- 不直接采用 `safetyGraphics` 或 `clinDataReview` 的 R/Shiny 应用层。理由：当前 R4 是 renderer-neutral、Python synthetic/offline typed kernel；直接引入会扩大运行时、状态权威和部署面，并绕过已冻结的事实/风险/lineage 合同。
- 不照搬任何成品的中心评分、阈值或图形默认值。具体阈值、分析集、分层、暴露单位和疗效 estimand 必须由项目 Knowledge Pack、ModeContract 与版本化方法合同提供。
- 不把 E2F 的开发计划级 DSUR 语义直接冒充单研究项目的正式获益-风险结论。D10 只形成项目内、当前数据截止下的描述性监查结论及需核实事项。

## 对 D10 合同的约束

1. D10 是唯一项目/跨中心聚合 owner；不得重算 D01-D09 的个体或中心医学语义。
2. 安全、疗效、数据/流程、方案符合性分别计量；不得把异质指标相加为“项目总风险分”。
3. 首次全量运行只形成“初始全量”，不伪造新增、关闭或改善/恶化。
4. 每个项目聚合单位必须具有可重建的成员集合、分子、分母、coverage、窗口、cutoff、方法与来源版本。
5. 数据变化与知识、规则、mapping、模型、方法、可见性或 coverage 变化分开；只有数据变化才可描述为风险新增/持续/关闭或临床趋势变化。
6. `ensemble_size=1` 不显示“一致性”；多模型意见不改变确定性数据、分母或权威门。
7. 项目看板默认“本次变化＋当前全量”，完整显示中高风险，低风险可聚合展开；全部聚合可一跳到中心、受试者、Patient Journey/Profile/Timeline 和原始来源。
