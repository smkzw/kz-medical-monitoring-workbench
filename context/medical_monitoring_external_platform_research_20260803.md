# 医学监查外部方案复核｜2026-08-03

## 目的与边界

本记录是面向产品架构和验收设计的外部方案复核，不是供应商选型、临床结论或本项目完成证据。没有采用任何闭源平台、SDK、模型或外部数据；所有外部材料只作为设计参考，当前文件系统、原始方案/listing、医学经理确认和发布门仍是本项目权威。

## 检索路径

本轮按 `external-tech-research` skill 做了两遍检索：第一遍查找英文和中文平台公开产品能力，第二遍回到 FDA/ICH 官方风险监查与 GCP 资料核对可迁移原则。页面访问日期：2026-08-03（Asia/Shanghai）。

## 观察到的公开模式

### 英文平台：Medidata Clinical Data Studio

Medidata 的官方发布资料描述了一个把 Medidata 与非 Medidata 数据放到统一工作区的模式，并将 AI 辅助数据核对、异常检测、自助 data listing、风险质量管理、工作流和可视化放在一起。该模式的可迁移点是“多源数据 → 一致的风险/质量工作区 → 以动作和可视化收口”，不是照搬其产品或宣传的效率数字。

### 中文平台：i-MR / CogniCRO 等公开产品页

国内公开页面普遍强调医学监查数据整合、数据质量可视化、风险信号发现和知识/数据融合；这些页面属于供应商自述，不能作为临床正确性、合规性或本项目可用性的证据。可迁移的只是“把受试者、中心、项目层级及风险处置集中到一个工作区”的产品方向，具体字段、证据和规则必须回到本项目方案/listing 与医学审阅。

## 官方原则核对

- FDA 2023 RBM Q&A 将监查定位为判断研究是否按计划实施的质量控制，并强调风险基础的监查计划和结果沟通。
- FDA 的集中统计监查材料强调按关键数据和关键过程聚焦、跨中心聚合比较、尽早发现遗漏/不一致和指导针对性现场监查；这支持本项目的 trial→site→subject 汇总、趋势和待行动优先队列。
- FDA/ICH E6(R3) 2025 文本要求质量控制贯穿数据处理，监查目标同时包括受试者权利/安全/福祉与结果可靠性；集中监查可以由具备相应训练的医学监查员、数据科学家或数据管理人员执行，但必须按方案和风险比例确定范围。
- E6(R3) 还强调关键质量因素前瞻识别、fit-for-purpose、风险比例、盲态保护、数据生命周期、计算机化系统适用性与基于风险的验证；因此 AI 只能生成可追溯候选，不能绕过来源完整性、方案事实、医学确认或审计链。

## 对本项目的具体决策

1. 保留“一个风险底座、三种运行策略”的方向：日常增量、锁库前全量、核查前三级汇总不复制风险台账。
2. 主页面继续采用 trial→site→subject 的显式摘要和一键聚焦；任何中心/个例身份必须来自结构化字段，不能从标题或自由文本推断。
3. 把跨源核对拆成确定性层与 AI 候选层：schema/行/字段/完整快照/来源 token/风险身份由确定性合同控制；AI 只做语义映射、证据摘要、候选问题和趋势解释，低置信度/来源缺失时降级并要求医学经理确认。
4. 所有趋势图同时显示来源修订、批次、实际日期、规则/引擎版本和证据绑定状态；图形只表达观察到的变化，不表达因果或“无风险”。
5. 把“动作闭环”作为商业化验收核心：风险打开→事实/方案依据→Timeline/Profile→医学处置→未读/审计→下一批次重开/持续/替代，不能用一个风险分数或供应商的“AI accuracy”代替。
6. 产品选型暂不引入外部可执行依赖；当前路线继续使用项目已有本地数据、可替换 AI 网关和自有契约，先完成真实三项目、连续批次、独立 AI、浏览器和科学性门禁。

## 证据与局限

外部平台页面多为厂商产品介绍，未提供本项目所需的原始方案/listing 逐条证据或医学 reviewer 结果；其宣传性能力不升级本项目任何发布门。FDA/ICH 文件是设计原则参考，不替代本项目数据、方案适配和用户验收。

## 来源

- FDA RBM Q&A（2023）：<https://www.fda.gov/regulatory-information/search-fda-guidance-documents/risk-based-approach-monitoring-clinical-investigations-questions-and-answers>
- FDA Oversight of Clinical Investigations RBM guidance：<https://www.fda.gov/media/116754/download>
- FDA E6(R3) GCP guidance（2025）：<https://www.fda.gov/media/169090/download?attachment=>
- Medidata Clinical Data Studio official release：<https://www.3ds.com/newsroom/press-releases/medidata-launches-clinical-data-studio-leveraging-ai-modernize-data-experience-clinical-trials>
- 上海杉云 i-MR 公开产品页（供应商自述）：<https://sprucecloud.com.cn/znyxjcsjpt>
- CogniCRO 公开产品页（供应商自述）：<https://www.onemedicaldata.com/>
