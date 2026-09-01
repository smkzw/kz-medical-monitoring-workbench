# R4-D06 疗效终点/量表/个体趋势 — 外部依据与方法决策

Date: 2026-08-12  
Status: `DECISION_INPUT_FOR_DRAFT_CONTRACT`

## 要解决的问题

在不把医学监查子系统变成统计分析系统的前提下，建立跨疾病、跨药物、跨方案和跨 listing 结构的 D06 确定性合同：把方案/SAP/量表手册定义的终点与 accepted 原始评估记录连接起来，复算可复现的量表/反应结果，识别组成项、基线、算法、分类和个体趋势问题，并投影到共享访视轴。系统只提示“待核实”，不从个体波动推断总体疗效。

## 两遍发现

### Landscape

- ICH E9(R1) 将 estimand、estimator、estimate 和 sensitivity analysis 明确分开；终点变量、总体、干扰事件处理和总体层汇总必须预先对齐。停药、换药、救援治疗等干扰事件不能等同于缺失数据。
- FDA Multiple Endpoints (2022) 强调主要、共同主要、次要、探索性、复合和多组成终点的层级/结构，以及多重性不足时错误宣称药物作用的风险。
- FDA PFDD COA Guidance 3 (2025) 将 PRO、ObsRO、ClinRO、PerfO 的概念、使用情境、评估者和适用性作为解释分数的前提；量表计分和缺项规则必须明确、可复制。
- CDISC ADaMIG v1.3 提供 ADSL/BDS 等分析数据结构与变量命名惯例，提示实现需保留参数、分析值、基线、变化值、分析访视和源数据可追溯关系；本阶段只借鉴其结构思想，不把 ADaM 当作所有输入的强制格式。
- EMA Missing Data guideline 要求缺失处理预设且与问题相符，不存在适用于所有情形的单一方法；这支持 D06 禁止隐式 LOCF、零填充或模型补值。

### Verification

- ICH E9(R1) Step 4 官方 PDF 明确：干扰事件会影响测量的解释或存在；撤出研究造成缺失，停药/换药/救援治疗是需在临床问题中处理的干扰事件；缺失应针对具体 estimand 考虑。
- FDA 2022 最终指南官方页面明确：多个终点若不适当控制多重性，可能形成错误或误导性的药效结论。因此 D06 个体看板不得制造统计显著性或总体有效性措辞。
- FDA 2025 最终 COA 指南官方 PDF 明确：COA 是否适用取决于概念和使用情境；计分方法与缺项处理必须记录；缺项情况下仍可计算分数的条件应在算法中明示并可复核。
- CDISC 官方页面确认 ADaMIG v1.3 日期为 2021-11-29，描述 ADSL 与 BDS；无需登录即可核验版本与范围，但完整文件受登录限制，因此本合同不声称采用未核验的具体变量规则。
- EMA 官方页面确认缺失数据指南当前有效版本及预设处理原则。

## 比较与决定

### 当前方法

既有 R4 coverage/L1/L2/L3、稳定身份、增量和 Patient Journey 投影合同可以复用，但 D05 只判断评估是否发生/何时发生，不能承担疗效值、基线或趋势解释。

### 外部候选

- 直接把系统建立为 ADaM 统计流水线：对 listing 不统一、SAP 未完成的日常医学监查过重，也会把 D06 错变成统计编程系统。
- 让模型自由阅读方案并计算终点：不可复现，容易在缺项、反向计分、版本和干扰事件上越权。
- 采用版本化结构合同 + 确定性算法 + accepted analysis result 双路径：最符合当前 R4 POC、可测试、可追溯且可适配不同研究。

### 选定路线

1. 方案/SAP/量表手册先形成版本化 `EndpointDefinition`、`InstrumentDefinition`、`ScoringAlgorithm`、`BaselineRule`、`AnalysisTimepoint` 和 `IntercurrentEventRule`。
2. 原始 item/assessment 与 accepted derived result 分开；系统可用冻结算法确定性复算并比对，但模型不能产生权威值、插补缺项或选择“最合理”的基线。
3. D06 评价单位为“受试者 + 终点/评估项 + 分析时间窗/episode + 规则版本”；D05 的计划活动和访视只作为 typed timing/context reference。
4. 个体趋势显示观察值、基线、变化、阈值、方向、干扰事件和资料缺口；不显示 p 值、组间差异或“研究有效”。
5. 无法唯一确认算法、版本、基线、单位、评估者或缺项处理时 fail closed 为 `not_evaluable`；完整的合法多解释才是 `boundary`。
6. 复合/多组成/响应者/时间至事件结果保留组成项和构造 lineage；不得只保留一个最终标签。
7. D06 不重复 D05 的“评估缺失/错时”，不解释 D07 的安全性实验室异常，不自行建立 D08 跨域医学因果关系，不承担 D10 项目级疗效推断。
8. 本阶段不采用任何新可执行依赖；无需新增许可证或供应链决策。

## 官方来源

- ICH E9(R1) Step 4: <https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf>
- FDA Multiple Endpoints in Clinical Trials (2022): <https://www.fda.gov/regulatory-information/search-fda-guidance-documents/multiple-endpoints-clinical-trials>
- FDA PFDD Guidance 3, Fit-for-Purpose COAs (2025): <https://www.fda.gov/media/159500/download>
- CDISC ADaMIG v1.3: <https://www.cdisc.org/standards/foundational/adam/adamig-v1-3>
- EMA Missing Data in Confirmatory Clinical Trials: <https://www.ema.europa.eu/en/missing-data-confirmatory-clinical-trials-scientific-guideline>

## 回滚与残余风险

- 若具体方案/SAP 使用本合同未表达的终点构造，只新增版本化 strategy/adapter；不得在通用内核写项目名、药物名、固定量表或固定字段。
- D06 合同接受前不写 D06 实现；合同接受后也只做合成/离线 POC。真实项目验证、统计推断、项目级聚合和产品 UI 均属于后续独立门禁。
