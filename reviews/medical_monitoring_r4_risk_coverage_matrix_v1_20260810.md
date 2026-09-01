# R4 风险域覆盖矩阵与共同风险合同 v1.0

日期：2026-08-10  
状态：`FROZEN_R4_CONTRACT_V1`  
冻结依据：Pi 临床/医学审阅 `ACCEPT`；Grok 工程反证首轮 `VETO` 后同会话差异复核 `ACCEPT`；Codex 主会场完成逐项裁决与文字收口。  
适用范围：医学监查 AI-native 隔离 R4；仅合成/离线输入；不代表真实项目、产品接线或临床结论就绪。

## 1. 冻结目的

R4 在实现任何风险域前，先冻结“检查了什么、凭什么检查、什么才算覆盖、何时不能下结论”。本文件是后续 AE/MH、CM/IP、方案/PD、疗效、安全/实验室、多表、中心和项目级风险节点的共同验收合同，也是看板、Query、Profile/Timeline/受试者医学旅程投影的上游约束。

本合同不把模型输出当作来源事实，不把节点运行成功当作覆盖完成，不把“未检出”自动解释为“无风险”。

## 2. 来源权威与设计决定

### 2.1 本地权威

1. `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`，尤其 9、10、11 节；
2. `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md` R4 步骤 1-13；
3. 冻结 R1 的 AE/MH 纵切和共享访视轴合同；
4. 冻结 R2 的快照、来源、mapping、risk identity、append-only lifecycle、adjudication binding 和 baseline 合同；
5. 冻结 R3 的规则、知识和自然语言规则适配合同；
6. `context/monitoring_p7d_real_evidence_matrix_20260729.md` 只作为既有风险族与证据缺口参考，不作为 R4 真实项目通过证据。

### 2.2 外部一手依据

- [ICH E2A](https://database.ich.org/sites/default/files/E2A_Guideline.pdf)：AE 可由不利且非预期的体征、实验室异常、症状或疾病构成，不以已证明因果关系为前提；严重性与严重程度不是同一概念。
- [CDISC SDTMIG v3.3](https://www.cdisc.org/standards/foundational/sdtmig/sdtmig-v3-3/html)：AE、MH、CE 的边界与相对研究起始时间及方案报告口径有关；AE、MH、CM、EX、DV、HO、LB、EG、VS、PE、PR、IE 等为可分别追溯并关联的域。
- [国家药监局《药物临床试验数据递交指导原则（试行）》](https://www.nmpa.gov.cn/directory/web/nmpa/images/obbSqc7vwdm0ssrU0enKb7dtd29u9a4tbzUrdTyo6jK1NDQo6mhty5wZGY%3D.pdf)：强调研究/受试者唯一标识、适用数据集中的访视变量、变量来源/衍生规则和从原始数据到分析与报表的可追溯性，并要求中文表达一致、便于审阅。
- [ICH E6(R3) Step 4 说明](https://admin.ich.org/sites/default/files/inline-files/ICH_E6%28R3%29_Step%204_Presentation_2025_0123.pdf)：采用与试验复杂度和关键质量因素相称的、适用目的的风险方法。
- [NCI CTCAE 与 AE 报告](https://dctd.cancer.gov/research/ctep-trials/for-sites/adverse-events)：CTCAE 是不良事件严重程度分级体系。研究必须绑定方案指定的 CTCAE 版本，不能默认套用网站当前版本。

### 2.3 方法选择

- 不引入新的外部执行库；R4 复用冻结 R1/R2/R3 公共合同，在新隔离包内实现域覆盖与 AE/MH 纵切。
- CDISC 域名只作为输入语义参照，不要求用户数据必须已经是 SDTM；异构 listing 先由 mapping 合同映射到项目语义角色。
- 规则、方案、IB、数据字典和医学词典都版本化；项目特异阈值、禁限用药、时间窗和基线定义不得写入通用内核。
- 模型可发现、解释和生成文本，但唯一标识、时间计算、单位换算、确定性阈值、coverage、来源绑定和状态迁移优先使用可重复服务。

## 3. 共同风险合同

### 3.1 每次域评估必须冻结的输入

| 类别 | 必需内容 | 允许缺失时的结果 |
|---|---|---|
| 运行身份 | project、Run、监查模式、cutoff、当前全量 SourceRevision/Snapshot、上次已接受基线（若需要） | 任一身份歧义：L0 `status=not_evaluable` 并阻断 L1 医学完整性评定 |
| 数据范围 | 预期文件/表、预期受试者、记录范围、实际读取范围、排除理由、行级 locator | 缺分母或范围不闭合：不得声明完整覆盖 |
| Mapping | 数据表语义、字段角色、单位、日期、受试者/中心、治疗角色、访视/阶段映射及版本 | 必需角色缺失或冲突：L0 记录缺口，相应 L1 单元 `eval_disposition=not_evaluable` |
| 项目知识 | 方案/修订版本、IB/药物资料、数据字典、适用条款、规则版本及定位 | 需要项目规则却无权威条款：不得用常识补成确定结论 |
| 时间锚点 | 知情同意、研究参考起点、首次给药/随机、治疗阶段、访视窗、cutoff；按域取适用子集 | 关键锚点缺失或冲突：保留待定时间，不伪造日期 |
| 医学参照 | MedDRA/药物词典/CTCAE/实验室范围/终点定义等名称和版本；仅在该域需要时强制 | 需要受控参照却未绑定：相应 L1 单元 `eval_disposition=not_evaluable`，或只保留已明确标注不确定性的弱线索 |
| 执行证据 | 输入哈希、规则/知识/mapping/identity 版本、原始输出、解析状态、coverage、QC | partial/truncated/来源漂移：不进入完整分析 |

### 3.2 四层状态命名空间

R4 不复用同一个字符串代表不同层的状态。四层分别保存、分别计量：

| 层 | 对象 | 合同 |
|---|---|---|
| L0 执行覆盖 | 输入/表/行/受试者/中心/风险域是否实际被读取和处理 | 复用冻结 R1 `CoverageUnitStatus`：`covered/partial/truncated/not_applicable/not_evaluable/failed/missing`；它只说明执行/输入 coverage，不证明医学域可评价 |
| L1 医学评价 | 一个版本化 EvaluationUnit 的医学结果 | 每单元恰好一个互斥 disposition：`positive/negative/boundary/not_applicable/not_evaluable` |
| L1b 证据方向 | 与 EvaluationUnit、线索或风险关联的证据 | 可多选：`supporting/counterevidence/context`；排除依据不是第六个 disposition，可与 negative、positive 或 boundary 共存 |
| L2 领域对象 | 源数据记录、待核实线索、风险实例、Query 草稿 | 四类对象分别计数并通过 ID 关联，不由 L1 数量反推 |
| L3 风险生命周期 | 已建立风险的追加式状态 | R2 `RiskLifecycle` 是 R4 唯一生命周期权威；字段必须使用 `risk_state` 等限定名，不能与 L0/L1 的 `not_evaluable` 混用 |

R1 `CoverageManifest.is_fully_covered()` 允许带理由的 L0 `not_evaluable` 作为“执行缺口已说明”，R4 只能据此判断流程是否交代，**不得**据此声明医学域完整。L1 `not_evaluable` 不自动改变现有风险的 L3 状态。

### 3.3 五类互斥医学评价与证据方向

| L1 disposition | 含义 | 成立条件 | 禁止替代 |
|---|---|---|---|
| `positive` | 该评估单元存在可定位、需要呈现或核实的问题 | 适用、输入足够、命中规则/医学分析、保留支持依据与不确定性；其候选/风险对象在 L2 单独计数 | 模型主张本身不是 positive；不能因已建立风险而重复计数 |
| `negative` | 在明确分母内完成评估且未发现问题，或线索被充分排除 | 必需输入齐全、范围完整、排除依据已检查、QC 通过 | 空表、未运行、未命中或缺字段不是 negative |
| `boundary` | 位于日期、阈值、基线、严重性、归类或身份边界，尚不能归入 positive/negative | 保留两侧规则、日期精度和不确定性 | boundary 不得折入 negative 以提高通过率 |
| `not_applicable` | 权威方案/设计和数据范围证明该单元在当前版本/阶段不适用 | 必须给出条款/设计依据和适用区间 | 输入缺失、没有记录、模型不会判断不是不适用 |
| `not_evaluable` | 单元适用或适用性未知，但必需输入、范围、身份、版本或质量不足 | 明确列出缺口、受影响分母和可恢复动作 | 不得折入 negative，也不得宣称医学域完整 |

排除依据必须与同一受试者/中心、EvaluationUnit、事件身份、时间窗和规则版本绑定；仅同名但身份/时间不符不能作为反证。一个被充分排除的线索在 L1 为 `negative`，同时在 L1b 至少有一个 `counterevidence`；存在相互冲突的支持与排除依据时可保持 `positive` 或 `boundary`，不能用反证对象自动抹掉线索。

`非问题` 不是 disposition 或生命周期状态：未建立风险时记录为 `negative + counterevidence + adjudication rationale`；已有风险时通过 R2 adjudication `rejected_by_evidence` 和显式 close reason 关闭，保留原身份、证据和复验证据。

### 3.4 EvaluationUnit、计量与分母

EvaluationUnit 是医学评价的最小且版本化的分母单元：

```text
unit_id = hash(
  project_id, domain_id, scope_type, scope_key,
  normalized_concept_or_rule_item, temporal_window,
  rule_or_knowledge_lineage, unit_algorithm_version
)
```

每次 Run 的 expected-set 只能从已接受全量快照、active mapping、适用性合同和冻结算法生成，并保存 `expected_set_hash`。不得为获得更好结果临时合并/拆分单元。

| 风险域 | 默认 EvaluationUnit |
|---|---|
| D01 | 受试者＋目标归类（AE/MH/uncertain）＋医学概念＋事件时间窗 |
| D02 | 受试者＋标准化药物暴露 episode＋激活规则 |
| D03 | 受试者＋治疗角色＋暴露 episode |
| D04 | 受试者＋入排/方案控制点＋适用时间窗 |
| D05 | 受试者＋计划访视/评估/样本单元 |
| D06 | 受试者＋终点/评估项＋分析时间窗 |
| D07 | 受试者＋检查指标/医学发现＋基线/治疗后时间窗 |
| D08 | 受试者＋关系规则＋参与比较的 record identities |
| D09 | 中心＋风险域/模式＋聚合时间窗＋分层 |
| D10 | 项目＋风险域/趋势＋聚合时间窗＋分层 |

每个域、项目、中心、受试者都至少维护：

1. expected-set hash、预期单元数、已赋值数、五类 L1 disposition 数；
2. 已读取原始记录数、被规则纳入的记录数、未映射/冲突记录数；
3. supporting/counterevidence/context 对象数及有排除依据的单元数；
4. 待核实线索数、已建立风险实例数、Query 草稿数，三者分别计量；
5. 风险受影响人数、事件数及其明确分母；中心/项目比例不得只给百分比；
6. 已接受基线后的新增、持续、升级、降级、关闭、重开、身份不明和不可评估。

必须满足以下可执行不变量：

- `expected_units = positive + negative + boundary + not_applicable + not_evaluable`；每个 unit_id 恰好出现一次。
- 每个 positive unit 至少关联一个当前待核实线索或活动风险；每个当前线索必须关联至少一个 positive/boundary unit。
- negative unit 不产生当前新线索/风险，但可以关联已关闭的历史风险；boundary 可以形成保留不确定性的线索。
- 当前活动风险在本次 `not_evaluable` 时保持 carry-forward 并显示覆盖缺口，不因 L1 状态被关闭；如果风险 identity/lineage 本身无法延续，才使用 L3 `risk_state=not_evaluable`。
- 每个 Query 必须关联来源、EvaluationUnit 以及线索或风险；Query 数不计入风险数。
- 候选线索不得进入已记录 AE/MH/CM/IP 等源数据计数。中心模式不得回写、复制或伪造多个受试者风险。

### 3.5 三个不得混用的医学维度

| 维度 | 说明 | 例子 |
|---|---|---|
| 严重程度/等级 | 事件强度或方案指定量表/CTCAE 等级 | mild/moderate/severe；CTCAE Grade 1-5 |
| 严重性 | 死亡、危及生命、住院/延长住院、显著功能障碍、先天异常或其他重要医学事件等判据 | `serious=yes/no/unknown` 与具体判据 |
| 监察优先级 | 基于潜在伤害、证据强度、紧迫性、系统性和可行动性的高/中/低风险 | 看板“AE漏报·高” |

三者独立保存。严重程度字段只承载强度/等级，禁止写入 `serious/SAE/AESI`；这些值只能进入严重性判据/临床标志。高 CTCAE 等级不自动等于 SAE，SAE 也不要求事件强度一定为 severe；监察优先级不得伪装成 CTCAE 或严重性结论。未知强度/优先级保持 unknown，不得像冻结 R1 简化排序那样默认为零。

接入 R2 时，`RiskInstance.severity` 明确投影为**监察优先级**，而非 CTCAE/事件强度；`clinical_risk_flags` 独立承载 SAE/AESI 等硬阻断。CTCAE/严重程度可经项目规则影响监察优先级，但不得直接冒充生命周期等级。

### 3.6 证据、身份与生命周期

- 每个线索必须绑定行级来源、实际/部分日期、访视/阶段、规则/知识/mapping/快照版本和产生它的分析 artifact。
- 身份键至少包含 project、subject/site scope、风险域、来源/事件身份、标准化医学概念、相关时间窗、规则/知识 lineage 与算法版本。
- 仅在同一身份与时间窗内合并支持依据和排除依据；身份不明时保持 `identity_ambiguous`。
- 模型输出只能形成待核实线索。低/中风险若满足已批准的确定性规则、完整 coverage 和独立 verifier，可由机器 adjudication 记录显式建立；不是“候选自动升级”。
- R2 是唯一生命周期权威。Design/R1 的 `resolved_by_data` 在 R4 映射为 R2 `closed`，绑定 `rejected_by_evidence` adjudication 和 `close_reason=resolved_by_data`，不是第二套状态枚举。
- 高监察优先级、SAE/AESI、重要冲突、低置信度和曾由用户确认/升级的风险不得机器自动关闭，也不得因多数票或后续未命中而静默隐藏。
- 低/中监察优先级只在下一已接受全量快照、同一身份算法、完整 L0/L1 范围、真实 AcceptanceService 和显式 machine adjudication 证明问题消失/纠正时自动关闭。
- 规则/mapping/knowledge/identity algorithm/来源范围改变使用 R2 `superseded`，或在 risk identity 本身无法继续时使用终态 `risk_state=not_evaluable`；不能伪装成 `resolved_by_data`。L1 `eval_disposition=not_evaluable` 只记录本次评价缺口，不终止风险。
- `identity_ambiguous` 使用 R2 风险状态并阻断自动合并/关闭。R2 `risk_state=not_evaluable` 为终态；后续恢复只能由新 Run 产生带 lineage 的新候选/实例，不能原状态重开。
- 正式补录 AE/MH/CM/IP 等记录后，保留“原待核实线索—后续记录”的匹配和解决历史。

### 3.7 来源权威与冲突处理

权威只在各自 claim scope 内成立：accepted listing 说明“记录了什么”，active protocol/IB/SAP 说明“应当如何收集/判断”，受控词典/量表说明“如何编码或分级”，确定性衍生说明“按哪个版本化算法算出什么”，模型只提供语义线索/解释，不能覆盖前四者。

| 风险域 | 主权威 | 辅助权威 | 冲突处理 |
|---|---|---|---|
| D01 | accepted AE/MH 及交叉域源记录；active protocol 报告口径 | MedDRA、CTCAE、IB、版本化匹配策略 | 时间/口径/编码冲突进入 boundary 或 not_evaluable，模型不得裁成源事实 |
| D02 | accepted CM；active protocol 禁限用规则 | 版本化药物词典/成分与类别、AE/MH/IP | 成分/治疗角色/窗口未确认不得判命中或排除 |
| D03 | accepted EX/EC/DA/IP、随机/治疗角色；active protocol | AE/检查/疗效/处置 | 计划与实际、治疗角色或阶段冲突 fail-closed |
| D04 | active protocol/修订及适用性 | accepted listing、研究者/豁免记录 | 条款与数据不足只生成待核实 Query，不正式判 PD |
| D05 | active protocol 访视/采样计划 | accepted 实际日期、改期/非计划访视记录 | 锚点/精度不足进入 boundary/not_evaluable |
| D06 | active protocol/SAP/量表算法 | accepted 原始评估、读片/中心实验室记录 | 不能由模型补算权威终点 |
| D07 | accepted 原始结果/中心范围；active protocol/IB | CTCAE、复测、AE/CM/IP/处置 | 单位/范围/版本冲突进入 boundary/not_evaluable |
| D08 | accepted records、active mapping/identity/data specification | 各参与域的规则与知识 | 任一上游 coverage/identity 不完整即 fail-closed |
| D09-D10 | 已验证的上游风险、coverage、分母和 cutoff | 分层/暴露/随访配置 | 聚合不得反向改写个体结论或以模型替代分母 |

无法按 claim scope 解决的权威冲突必须保留来源和冲突，落为 `boundary` 或 `not_evaluable`；不得由模型投票决定。

### 3.8 部分日期与比较精度

部分日期复用冻结 R3 `normalize_partial_date` 语义，保存原值、归一化值、精度和 uncertainty。比较只能在两侧共享精度上进行；无法判断先后或是否命中窗口时进入 `boundary` 或 L1 `not_evaluable`，不能静默补日、按月首末日伪造精确位置或使用固定日差。

### 3.9 用户界面投影

- 内部对象名可留在代码与审计；界面显示“已记录 AE”“疑似 AE 漏报”“当前 AE/MH 中未发现对应记录”“依据”“排除依据”等医学中文。
- 不显示“正式事实”“候选信号”“已建立风险”“只读投影”“正反证”等研发语言。
- 风险标签必须为“临床域＋具体问题＋等级”，例如“AE漏报·中”“禁用药偏离·高”“访视超窗·中”，不使用“通用风险点”。
- 中高风险优先显示；已记录 AE/MH/CM/IP/检查/住院/症状疗效/方案符合性使用稳定且不同的图形、线型和域名短标签，不只靠颜色。
- 任一风险一跳进入：支持依据、排除依据、原始 listing、方案/IB、Query，以及同一访视轴上的受试者医学旅程/指标趋势/事件明细。

## 4. 风险域覆盖矩阵

### R4-D01 AE/MH 一致性、严重性与疑似漏报

| 项目 | 冻结合同 |
|---|---|
| 适用前提 | 方案收集 AE/MH 或其他可反映医学事件的数据；AE/MH 边界必须由方案的研究参考期、知情同意、首次给药/随机及例外共同确定，不能全局硬编码为首次给药日 |
| 必需输入 | `reported_ae/reported_mh/subject_identity/site_identity/temporal_anchor` 为最小语义角色；按适用性增加 `symptom_event/cm_indication/lab_finding/exam_finding/healthcare_encounter/procedure/ip_action/seriousness_clue/death_event/visit`，角色来自 active mapping 而非固定表名；另需方案时间边界、版本化事件匹配策略、实际/部分日期、严重程度、严重性判据、因果性、结局、处置、编码及来源定位 |
| L1 positive | 跨表医学事件无相应 AE/MH；已有 AE/MH 与严重性、等级、日期、结局、处置或相关记录不一致；既往病史在研究期新发/恶化却未按方案记录；住院/死亡/重要医学处置缺少对应事件 |
| L1 negative | 全部适用证据源已覆盖，候选医学事件与已记录 AE/MH 在概念、身份和时间窗内匹配，或权威数据说明其不属于需报告事件 |
| L1 boundary | 首次出现/诊断/恶化恰在研究起点；部分日期跨界；疾病症状既可能是疗效事件也可能是 AE；同一事件严重程度变化；同名不同事件；方案排除的 endpoint/clinical event |
| L1b 排除依据 | 已记录 AE/MH；明确 NCS 且无症状/处置/复测恶化（只作为组合反证）；确认的替代诊断；纠正后的原始数据；方案明确不作为 AE 收集的临床事件 |
| L1 not_evaluable | 关键时间锚点、`reported_ae/reported_mh` 角色数据、事件日期、受试者身份、适用域 coverage 或方案报告口径缺失/冲突；需要 CTCAE/MedDRA 但版本或映射不可用 |
| 误报控制 | NCS 不等于“绝不可能是 AE”；异常结果不自动生成 AE；同名不跨日期窗口硬合并；候选与已记录 AE/MH 的匹配窗口由方案收集期、事件持续期、日期精度和版本化匹配算法共同确定，不得继承冻结 R1 的固定 30 天简化；策略不足时进入 boundary/not_evaluable；方案 endpoint 不自动转 AE；CM 适应证只形成线索 |
| 漏报控制 | 扫描症状、实验室/检查、住院/操作、CM 适应证、给药处置、死亡/严重事件和跨表矛盾；检查 SAE 严重性判据而非仅 SAE 标志 |
| 医学裁决 | 分别审阅事件概念、研究时间边界、新发/恶化、严重程度、严重性、因果性、临床处置和已有记录；不确定时保留待核实，不替研究者完成医学判断 |
| 输出 | 受试者风险、支持/排除依据、三段式 Query、受试者医学旅程风险锚点、指标趋势/事件明细联动、中心重复模式和项目汇总 |

### R4-D02 CM 用药合理性、适应证与禁限用药

| 项目 | 冻结合同 |
|---|---|
| 适用前提 | 项目收集既往/合并用药，或方案存在禁用、限制、抢救、预防或稳定剂量要求 |
| 必需输入 | CM；药名原文、标准化成分/类别/剂型、剂量/途径/频次、起止/持续、适应证；方案禁限用规则、阶段和时间窗；AE/MH/诊断、IP 暴露；受控药物词典及版本（需要分类时） |
| L1 positive | 用药无可解释适应证；医学事件有治疗却缺 AE/MH；明确命中禁限用成分/类别和时间窗；剂量/途径/频次或时间与方案/适应证明显矛盾；处置关系不一致 |
| L1 negative | 药物身份、适应证、时间窗和方案规则均可核实且无问题；明确不属于被限制类别 |
| L1 boundary | 复方药、商品名/成分不明；开始或结束恰在禁限用窗口端点；预防用药与治疗用药；长期稳定治疗与新启用；部分日期 |
| L1b 排除依据 | 方案允许的稳定治疗/抢救用药；词典证明不同成分/类别；日期在适用窗外；明确适应证与 AE/MH/病史记录一致 |
| L1 not_evaluable | 无法确认药物成分/类别、治疗角色、日期、阶段、适应证或权威禁限用条款 |
| 误报/漏报控制 | 不从药名猜类别；仅凭 J07 等上位分类码不能判定具体记录为活/减毒活疫苗，须核实产品/成分/类型；CM 与 EX/EC/DA/IP 严格分层；复方成分逐一核查；反向从适应证扫描 AE/MH |
| 输出 | “用药依据待核实”“禁限用药待核实”等具体风险、Query、CM 区间事件、关联 AE/MH/方案条款和来源 |

### R4-D03 IP 暴露、依从性与医学处置关系

| 项目 | 冻结合同 |
|---|---|
| 适用前提 | 存在研究药、对照、安慰剂或方案背景治疗的计划与实际暴露 |
| 必需输入 | EX/EC/DA/IP 语义角色；计划/实际剂量、剂型、频次、途径、给药/暂停/减量/停药日期、发放/回收、原因；随机/阶段；方案允许调整、依从性算法与阈值；AE/实验室/检查/疗效/PD 线索 |
| L1 positive | 暴露与随机/计划不一致；漏服/过量/依从性越界；无方案依据的暂停、减量、恢复或停药；AE/实验室触发处置与实际用药不一致；多治疗角色混并 |
| L1 negative | 计划、实际、阶段、原因和允许调整闭环一致，依从性分母完整 |
| L1 boundary | 阈值等号、窗口端点、部分给药日期、回收量缺失、导入期与治疗期、允许暂停与剂量调整、背景治疗与盲态研究药 |
| L1b 排除依据 | 方案规定的调整/补服/暂停；有记录的临床原因；药物核算解释；数据更正 |
| L1 not_evaluable | 治疗角色、计划/实际剂量、分母、阶段或调整规则缺失；不能区分 CM 与 IP |
| 误报/漏报控制 | 不跨项目复用依从性阈值；不把任何减量都判 PD；不由单次缺失记录推断漏服；从 AE/实验室处置和 IP 两端双向检查 |
| 输出 | 具体暴露/依从性/处置风险、Query、IP 区间、与 AE/检查/疗效的时间联动 |

### R4-D04 入排、方案要求与潜在 PD

| 项目 | 冻结合同 |
|---|---|
| 适用前提 | 有版本化方案、适用日期/中心/受试者和可定位的入排或执行要求 |
| 必需输入 | 方案条款与版本适用性；IE/DM/MH/AE/CM/LB/VS/EG/PE/RS/QS/EX 等条款所需字段；筛选/随机/给药锚点；豁免/修订/研究者判断记录 |
| L1 positive | 数据与入排标准、禁限用规则或关键方案要求表面矛盾；只能称“潜在 PD/请核实”而不正式报送 PD |
| L1 negative | 条款前提、所需字段、时点和例外均完整核查且符合 |
| L1 boundary | 临界值、复测规则、窗口端点、方案修订切换、医学判断条款、部分日期、缺失的等价检查 |
| L1b 排除依据 | 适用版本的豁免/例外、复测合格、中心实验室确认、条款不适用、数据更正 |
| L1 not_evaluable | 条款不可计算、适用版本/日期不明、关键字段或单位缺失、条款依赖人工医学判断且无记录 |
| 误报/漏报控制 | 先计算条款适用性再比较；禁止把 AI 判断写成正式 PD；跨表搜索可能满足/违背条款的替代证据 |
| 输出 | “入排条件待核实”“方案执行待核实”等风险及三段式 Query；不建立 PD 提交/关闭工作流 |

### R4-D05 访视、评估、样本与时序符合性

| 项目 | 冻结合同 |
|---|---|
| 适用前提 | 方案存在计划访视、窗口、阶段性评估或样本采集要求 |
| 必需输入 | Trial Visits/项目访视表；实际 SV/事件/采样/评估日期；名义和实际访视、非计划访视、阶段、cutoff；窗口和允许例外 |
| L1 positive | 访视超窗/错序/重复/缺失；关键评估或样本缺失/错时；实际事件被错误归入名义访视；方案时序矛盾 |
| L1 negative | 计划分母、实际记录和所有允许例外均可核实并在窗口内 |
| L1 boundary | 窗口端点、跨午夜/时区、部分日期、访视合并、非计划访视、阶段切换、cutoff 后数据 |
| L1b 排除依据 | 方案允许窗、记录的改期/住院/远程访视、非计划访视、适用性证明 |
| L1 not_evaluable | 计划锚点、实际日期、访视映射、阶段或适用窗口缺失/冲突 |
| 误报/漏报控制 | 不用文件行序代替计划访视；不强迫访视间事件吸附到名义访视；同一检查从计划和实际两端核对 |
| 输出 | 访视/采样/评估待核实风险、Query、顶部访视轴和方案符合性轨道标记 |

### R4-D06 疗效终点与个体趋势

| 项目 | 冻结合同 |
|---|---|
| 适用前提 | 方案定义疗效终点、量表、PRO、疾病活动、反应/进展或替代指标 |
| 必需输入 | 版本化终点定义、分析/观察窗、基线规则、评分算法、必要组成项、RS/QS/检查/实验室/症状、治疗暴露和缺失解释 |
| L1 positive | 必需组成项缺失/矛盾；评分或反应分类与原始项不一致；不合理突变、恶化/改善与治疗/事件时间不一致；报告趋势与个体数据不符 |
| L1 negative | 算法、基线、时间窗、组成项和来源全部可重现且趋势一致 |
| L1 boundary | 基线访视选择、最差/最佳值、临界反应阈值、救援治疗、死亡/退出、部分缺失、非计划评估 |
| L1b 排除依据 | 方案指定插补/复核规则、确认的临床解释、重复评估、读片/中心实验室更正 |
| L1 not_evaluable | 终点定义/算法/基线/组成项/单位/评估者版本不足；不得由模型补算权威终点 |
| 误报/漏报控制 | 个体趋势与汇总双向核查；异常改善和恶化都检查；区分疾病症状、疗效事件和 AE 收集口径 |
| 输出 | 疗效数据一致性/趋势待核实风险、受试者级指标趋势图、时间轴联动，以及供 D10 聚合使用的稳定个体结果与 coverage；中心/项目/治疗组分母和聚合趋势仅由 D10 生成 |

### R4-D07 安全性、实验室与检查

| 项目 | 冻结合同 |
|---|---|
| 适用前提 | 收集 LB/VS/EG/PE/影像或其他安全检查，或方案/IB 有监测阈值和处置要求 |
| 必需输入 | 原始结果、单位、参考范围、异常标记、CS/NCS 与说明、复测、基线、访视/日期、CTCAE 版本化阈值（需要时）、AE/MH/CM/IP/住院/处置 |
| L1 positive | 新发/加重异常、趋势性恶化、临床意义/AE 判断与数据矛盾、异常缺复测/处置/解释、检查与 AE/CM/IP 关系不一致、严重事件线索 |
| L1 negative | 单位/范围/基线/版本齐全，异常与 CS/NCS、复测、处置和 AE 判断形成一致闭环 |
| L1 boundary | 等于 ULN/LLN 或分级端点；基线异常；范围或单位变化；溶血/样本质量；NCS 文本；部分日期 |
| L1b 排除依据 | 可靠复测恢复、明确 NCS 理由且临床链一致、基线长期稳定、样本问题、方案允许变化 |
| L1 not_evaluable | 单位、范围、基线、CTCAE 版本/可映射项目、CS 说明、日期或关键关联缺失 |
| 误报/漏报控制 | 先识别 NCS 再识别 CS，避免中文子串误判；CTCAE 与非 CTCAE 阈值分离；基线正常→异常与基线异常→等级恶化分开；异常不自动等于 AE |
| 输出 | 具体检验/检查风险、指标趋势、AE/CM/IP/处置联动、Query、中心/项目趋势聚合 |

### R4-D08 多表医学逻辑与数据质量

| 项目 | 冻结合同 |
|---|---|
| 适用前提 | 两个及以上域共享受试者、事件、治疗、访视或时间关系 |
| 必需输入 | 统一 subject/site、record/risk identity、时间轴、mapping、字段语义、来源/修改版本；被比较域各自 coverage |
| L1 positive | 日期逆序/不可能重叠；同一事件/药物/剂量/状态跨表冲突；孤立引用；缺少预期关联；修改后派生结果未更新；重复记录或身份错配 |
| L1 negative | 共享身份、时间、单位和语义均可解释，关联完整 |
| L1 boundary | 同日无时刻、部分日期、一个事件多记录、合并/拆分、时区、别名、修订导致身份变化 |
| L1b 排除依据 | 明确的多记录建模规则、数据修订、不同治疗角色/不同事件、方案允许并行过程 |
| L1 not_evaluable | 任一必需域 coverage 不完整、身份算法/映射不一致、日期精度不足以判顺序 |
| 误报/漏报控制 | 不用字符串相等代替医学身份；比较前统一单位/时间精度；双向孤立检查；身份不明 fail-closed |
| 输出 | 跨表矛盾/缺链风险、受影响域和来源、Query、受试者旅程关联高亮 |

### R4-D09 中心重复模式与系统性风险

| 项目 | 冻结合同 |
|---|---|
| 适用前提 | 有中心身份、足够分母和已完成受试者级风险/coverage |
| 必需输入 | 中心受试者/暴露/随访分母、风险实例、域 coverage、时间窗口、来源版本；小样本/短随访标记 |
| L1 positive | 同类问题跨受试者重复、同一流程/字段系统性缺失、中心趋势显著且可展开到个体证据 |
| L1 negative | 分母和 coverage 足够且无重复模式；不得仅因风险数为零宣称中心无问题 |
| L1 boundary | 小样本、不同暴露/随访、中心启动时间不同、单个高风险个例、数据导出差异 |
| L1b 排除依据 | 病例组合/暴露/随访差异、项目范围的数据收集变更、已确认的映射问题 |
| L1 not_evaluable | 分母、中心身份、核心域 coverage 或时间窗口不足 |
| 误报/漏报控制 | 同时显示人数、事件数、分母和 coverage；不做黑箱综合评分/惩罚榜；单个高风险不被聚合稀释 |
| 分母门 | 最小分母/随访/暴露阈值由 project + ModeContract + version 冻结；不足时为 boundary 或 not_evaluable，不得给出“中心无问题”negative |
| 输出 | 中心热图、重复模式、热点受试者、变化趋势及一跳到个体来源 |

### R4-D10 项目级安全/疗效趋势与风险聚合

| 项目 | 冻结合同 |
|---|---|
| 适用前提 | 项目层已有可比较的受试者/中心覆盖、明确 cutoff 和分母 |
| 必需输入 | 全项目风险实例、事件/受试者/暴露分母、中心 coverage、治疗组/阶段、时间、知识/规则/mapping/模型版本和上次基线 |
| L1 positive | 跨中心/时间的风险聚集、发生率/暴露调整趋势、重要疗效或安全变化、规则/数据更新导致的新增 gap |
| L1 negative | 范围、分母、分层和 coverage 完整且未发现项目级模式；不消除个体高风险 |
| L1 boundary | 小样本、短随访、组间暴露不均、中心构成变化、模型/规则/数据版本变化、稀有严重事件 |
| L1b 排除依据 | 分母/暴露/病例组合解释、重复计数消除、数据批次更正；仅可降级项目模式，不能删除个体证据 |
| L1 not_evaluable | 项目范围、分母、关键域 coverage、组别/暴露或版本不可比 |
| 误报/漏报控制 | 区分数据变化与知识/规则/mapping/模型变化；绝对量与比例并列；高风险/SAE/AESI 不被多数/平均值隐藏 |
| 输出 | 项目驾驶舱、风险簇、中心热图、疗效/安全趋势、数据覆盖和变化原因分解 |

## 5. 共用服务合同

### 5.1 三段式 Query

每条草稿必须包含：

1. `basis`：方案条款、医学判断、数据逻辑或前后关系，带来源；
2. `finding`：具体受试者/中心、日期、值、药物或矛盾；
3. `action`：请核实、说明、补充、更正或评估。

疑似 PD 写成“请核实是否为 PD”，系统不正式认定、报送或关闭 PD。Query 可生成、编辑、用户可选确认和导出；不发送、不追踪外部回复，不形成全局待办或看板完成门。

### 5.2 多模型与基座

- `ensemble_size=1` 不显示一致度/分歧；`>=2` 使用同输入版本、隔离上下文独立分析。
- 所有执行者可见同一 reference baseline，但必须回查原始来源并执行 gap search；基座不是金标准。
- 原始模型输出不可改写；按 risk identity、时间窗和证据形成共同发现、单模型新增、分级冲突、相互否定和基座漏检。
- 确定性 evidence verifier 先核身份、版本、日期、单位、来源、规则和 artifact；独立 adjudication binding 再裁决。
- 高风险或重要分歧始终可见；多数票不能静默关闭。只有一个执行模型时保留 `needs_user_attention`，不显示虚假多模型一致度。

### 5.3 Profile、Timeline 与受试者医学旅程

- 三个视图共享同一 Subject Temporal Spine、时间窗、选择和来源 identity。
- 顶部固定访视轴显示阶段、cutoff、名义/实际/非计划访视；访视间事件保持实际日期。
- AE、MH、CM、IP、检验与检查、住院与操作、症状与疗效、方案符合性为独立可折叠轨道；不适用/未提供须可解释。
- 风险标记锚定日期/区间/访视；部分日期、日期冲突和访视归属不确定进入待定区。
- 点击风险同时联动依据、排除依据、原始记录、方案/IB、Query、指标趋势和事件明细；筛选/缩放不得改变生命周期。

## 6. 测试与接受矩阵

每个风险域实现前必须准备并独立计量：

1. 五类互斥 L1 disposition；supporting/counterevidence/context 可多选证据；L0/L1/L2/L3 不串层；
2. hidden case：表面正常但跨表/时间/单位/版本后才暴露；
3. false-positive 挑战：NCS、基线异常、允许用药、允许访视窗、方案例外、同名不同事件；
4. false-negative 挑战：部分日期、别名/复方、后续补录、严重事件线索、跨表孤立、单位变化；
5. coverage 挑战：缺表、缺字段、缺分母、partial/truncated、mapping/规则/知识/identity 漂移；
6. 增量挑战：N→N+1 新增、修订、删除、`closed + close_reason=resolved_by_data`、重开、superseded、L1/L3 not-evaluable 分层；
7. 受众投影：中文原生、具体风险类型、等级、分子/分母、一跳来源、访视轴同步；
8. 聚合挑战：中心/项目汇总不得改变个体身份或隐藏高风险；
9. Query 挑战：依据＋发现＋行动项齐全，PD 仅请求核实；
10. EvaluationUnit 和对象 join 不变量；候选线索、源数据记录、风险实例、Query 草稿四类计数绝不互相污染；
11. 中心模式不得复制受试者风险，Query 导出不等于发送。

域级医学完整覆盖必须同时满足：L0 没有 partial/truncated/failed/missing、适用性可解释、必需输入齐全、expected-set hash 已冻结、全部 EvaluationUnit 恰有一个 L1 disposition、L1 `not_evaluable=0`、行级来源可达、规则/版本冻结、join 不变量和 QC 通过。只要存在 L1 `not_evaluable`，看板必须显示缺口且不得声明医学域完整。运行成功、R1 coverage 已交代、模型返回 complete 或风险数为零均不足以单独通过。

## 7. R4 首条实现切片

AE/MH 首纵切只在新的隔离 R4 包中实现，复用冻结 R1/R2/R3 公共合同，不改它们：

1. 结构驱动的最小语义角色合同：`reported_ae/reported_mh/subject_identity/site_identity/temporal_anchor`，以及按适用性启用的 `symptom_event/cm_indication/lab_finding/exam_finding/healthcare_encounter/procedure/ip_action/seriousness_clue/death_event/visit`；不依赖固定表名；
2. 方案驱动的 AE/MH 时间边界与版本化适用性；
3. 症状、CM 适应证、实验室/检查、住院/操作、死亡/严重事件和给药处置的多来源线索；
4. 已记录 AE/MH、NCS/复测、替代诊断、方案例外等反证；
5. 严重程度、严重性、监察优先级分离，并按 §3.5 明确投影到 R2；
6. 行级来源、EvaluationUnit、expected-set hash、部分日期精度、风险身份、L0/L1 coverage 和 adjudication binding；
7. 三段式 Query、受试者旅程/Profile/Timeline 的 projection payload 和中心聚合数据；本切片不冒充 R5 audience cockpit/UI acceptance；
8. 五类 L1 disposition、三类证据方向、hidden cases 和四类 L2 对象计数；
9. N→N+1 补录、持续、升级、R2 关闭/重开、身份不明、superseded 和版本变化；
10. 独立临床/工程反证与聚焦、相邻回归。

本切片不连接真实项目，不调用真实模型/provider，不启动产品服务，不设计/测试系统安全，不宣称临床或监管就绪。
