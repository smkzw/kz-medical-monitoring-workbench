# R4-D09 外部模式核验与本地设计决策

日期：2026-08-14  
范围：中心重复模式与系统性风险合同；不选择或安装新依赖。

## 核验来源

- EMA 的 ICH E6(R3) 当前页面：原则与 Annex 1 自 2025-07-23 生效；强调风险相称、fit-for-purpose、质量源于设计，并将受试者保护与结果可靠性作为整体目标。<https://www.ema.europa.eu/ga/ich-e6-good-clinical-practice-scientific-guideline>
- FDA《Oversight of Clinical Investigations — A Risk-Based Approach to Monitoring》：集中监查可用于发现缺失、不一致、异常分布、潜在 PD、中心间异常模式及较高错误/违背/脱落频率；结果用于聚焦核查与现场监查，但监查方法应按研究关键数据、关键流程和研究风险定制。<https://www.fda.gov/media/116754/download>
- Kirkwood 与 Hackshaw 的中心统计监查实例：中心比较需同时考虑人数/在试时间等机会量，异常中心应作为需审阅的线索；方法对适用场景仍存在限制。<https://pmc.ncbi.nlm.nih.gov/articles/PMC3287772/>
- 2024 年多中心监查方法模拟研究：统计方法的识别性能受中心数、样本量、结局类型与异常机制影响，不能把单一统计阈值视为普适事实门。<https://pubmed.ncbi.nlm.nih.gov/38796099/>

## 对 D09 合同的决定

1. D09 是“已验证个体风险的中心模式评价”，不是新的个体医学事实 owner，也不是中心质量评分器。
2. 每个中心模式必须同时展示独立的受试者人数、风险事件数、适用分母、暴露/随访机会量、coverage、时间窗和来源版本；不得只显示百分比或风险数。
3. 中心间比较仅在 project/mode/version 冻结的可比性合同内进行；启动时间、病例组合、暴露、随访、数据导出范围和规则版本不可比时为 boundary/not_evaluable。
4. “没有发现重复模式”的 negative 需要证明适用分母、核心域 coverage、时间窗口和检出机会充分；零风险数本身不是 negative。
5. 单个严重/高风险受试者永不被均值、比例或小样本门隐藏；它保留为个体风险并在中心面板单列，但不自动升级为“系统性中心问题”。
6. 统计异常、KRI 或离群仅为结构化证据之一；D09 positive 必须能展开到同类模式定义、分子成员与个体来源，不以 p 值、综合分或模型排序直接形成医学结论。
7. 不建立黑箱中心总分、红黑榜或惩罚性排名。中心热图显示模式/风险域、绝对量、分母率、coverage 和变化原因。
8. 规则、mapping、分层或阈值变化必须以 superseded lineage 与数据变化分开；不得伪装成中心风险改善/恶化。

## 候选合同核心

- unit stable core：`project × site × pattern_kind × risk_domain × analysis_window × stratum_contract`；版本、run、snapshot、规则/算法哈希进入具体 unit identity 和 lineage，不进入跨 run stable core。
- numerator：按风险稳定身份和受试者稳定身份去重后的受影响人数；事件数另列；重复导出、同一风险 revision、同源跨域重复不得多计。
- denominator：至少支持 enrolled/treated/evaluable/subject-time/exposure-time/expected-assessment opportunity；每个 pattern 只允许合同声明的分母种类。
- coverage gate：中心身份、风险域输出、分母构成、时间窗、来源版本和适用受试者范围均闭合后才可 negative。
- 输出：中心 pattern unit、趋势点、热点受试者、个体风险/旅程一跳、中心级中文解释；不反向修改 D01-D08 个体 disposition，不生成项目级 D10 结论。

## 未在此记录预先决定的事项

- 最小分母、最短随访/暴露、统计阈值和分层键的具体值由 project + ModeContract + version 冻结，公共 runtime 不硬编码。
- 是否为中心模式生成 Query 草稿、何时只展示而不生成 Query，留给 D09 独立合同会商；任何 Query 必须列出依据、发现、行动项并可定位分子/分母与个体来源。
