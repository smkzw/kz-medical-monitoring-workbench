# R4-D05 访视/评估/样本时序合同 — 外部发现与方法决策记录

Date: 2026-08-12
Status: `DECISION_INPUT_FOR_DRAFT_CONTRACT`

## 问题

为 D05 冻结一个与项目表结构无关、可支持 Patient Journey 共享访视轴的确定性合同：从版本化计划访视/评估/样本要求和 accepted actual records 生成 expected-set、分配决定、五类 L1 disposition、待核实风险、Query 与 typed Journey 投影，同时避免把 D05 变成正式 PD 系统或复制 D03/D04/D06/D07/D08 权威。

## 两遍发现

### Landscape

- CDISC SDTMIG 将 TV 定义为每个研究臂的计划访视顺序/数量，将 SV 定义为受试者实际经历的访视；比较 TV 与 SV 可发现缺失/额外访视及计划时点偏离。
- CDISC 同时明确：实际访视起止可能由多域评估日期推导；一个方案访视可跨多日/多次实体就诊，一次住院可包含多个方案访视；触发型访视的 VISITNUM 可能不是时间顺序；非计划评估发生在计划访视期间时，计划/非计划归属并不天然明确。
- ICH E6(R3) 要求方案对评估方法、范围和时点可操作地描述，并要求及时可靠的数据采集、核验、复核和缺失/错误纠正；偏离/变更与立即消除危害的例外须按相应责任记录和处理。
- NMPA 数据递交指导原则要求研究/受试者标识一致，并在适用数据集中保留 VISIT/VISITNUM 等时间变量；原始缺失不得填补。
- FDA 2024 protocol deviation 文件仍为 draft/nonbinding，只用于提醒“分类、记录和报告责任必须分开”，不作为本合同的中国项目强制规则，也不授权系统正式判定 PD。

### Verification

- CDISC SDTMIG v3.3 官方 HTML §5.5、§7.3.1 可直接检索，明确 TV/SV、VISIT/VISITNUM/VISITDY、TVSTRL/TVENRL、触发型/非计划访视和派生 SV 的边界。
- ICH E6(R3) Step 4 最终指南（2025-01-06，2025-10-24 errata）是当前主规范；其 Annex 2（2026-06-03）不作为本次合成 D05 的必需依赖。
- NMPA 指导原则为官方 PDF；其对原始数据不填补、标识和时间变量的要求可用于中国原生数据合同。
- 本阶段不采纳任何新可执行框架或第三方库；因此不存在新增开源许可证/供应链决策。

## 选定方法

1. **计划与实际双对象**：`PlannedVisit/PlannedActivity` 与 `ActualEncounter/ActualActivity` 分离；SV/实际访视起止若为推导值，必须带算法、输入行与不确定性，不能冒充原始记录。
2. **先适用性和 expected-set，后匹配**：只为截止日已到期且对该受试者/中心/队列/阶段/方案版本适用的计划单元建医学 expected-set；未来未到期项保留在计划轴，不污染 L1 分母。
3. **显式分配决定**：显式稳定映射优先；再使用版本化名称/编号/阶段/触发/窗口/活动组合证据。禁止“最近日期”默认吸附，多个可行匹配进入 boundary，证据不足进入 not_evaluable。
4. **VISITNUM 不是时间权威**：保留标识与排序用途；触发型、非计划型和链式相对访视使用显式 `planned_order`、触发事件和 anchor lineage。
5. **时窗算法必须版本化**：锚点、日历/elapsed 语义、Study Day 0 规则、端点包含性、日期/时区精度、依赖前一访视还是固定 Day 1、允许改期/远程/住院/合并访视均来自可定位规则；内核不默认 ±7 天或其他固定窗。
6. **活动双向核对**：计划→实际发现缺失/错时，实际→计划发现错配/额外/重复；评估/样本“是否完成/何时完成”归 D05，结果的医学含义归 D06/D07，研究药动作归 D03，非时窗方案资格/前置关系归 D04，多表关系本身归 D08。
7. **Patient Journey 是只读投影**：顶部共享访视轴区分名义、实际、非计划、触发型、待定归属；风险使用具体中文类型和等级，不显示内部状态名，不因筛选/缩放改变生命周期。
8. **仅待核实问题**：D05 可生成“访视超窗待核实”“评估未见记录”“样本采集时间待核实”等风险与三段式 Query；不建立正式 PD 判定、报送、待办或外部回复闭环。

## 主要来源

- CDISC SDTMIG v3.3：<https://www.cdisc.org/standards/foundational/sdtmig/sdtmig-v3-3/html>
- ICH E6(R3) Step 4 Final Guideline：<https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106_ErrorCorrections_2025_1024.pdf>
- NMPA《药物临床试验数据递交指导原则（试行）》：<https://www.nmpa.gov.cn/directory/web/nmpa/images/obbSqc7vwdm0ssrU0enKb7dtd29u9a4tbzUrdTyo6jK1NDQo6mhty5wZGY%3D.pdf>
- FDA draft《Protocol Deviations for Clinical Investigations...》：<https://www.fda.gov/media/184745/download>

## 回滚与残余风险

- 若后续方案证明一个项目的访视语义无法由本合同表达，新增版本化结构或 adapter；不得在内核写项目名、固定访视号、固定窗口或固定表名。
- 合同会商前不写 D05 产品代码。D04 的 D05 stub 继续只是 owner-boundary 证据，不得计作 D05 完成。
