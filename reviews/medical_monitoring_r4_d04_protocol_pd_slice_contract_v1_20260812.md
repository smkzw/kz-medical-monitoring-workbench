# R4-D04 入排、方案要求与潜在方案偏离纵切合同 v1.1

日期：2026-08-12  
状态：`FROZEN_R4_D04_CONTRACT_V1_1`  
适用范围：医学监查 AI-native 隔离 R4-D04；仅合成/离线输入；不代表产品、真实项目、正式方案偏离判断或临床结论就绪。

修订说明：初稿（SHA-256 `fb5adc12a36e0c3dbe1c709e7d0abfee0047b695895bb350c17cff5c0c8832b0`）经独立工程挑战判定 `REVISE`。本版补齐生产域独占归属、组合规则单一裁决单元、八维 canonical identity、多版本 applicability gate、例外/豁免增量语义、精确跨域 join、R2 risk identity 和关键权益机器关闭阻断；审阅过程保留在会商记录中。

## 1. 目标与边界

本切片把版本化研究方案/修订、适用中心与队列、入排标准、禁限用要求、治疗与处置要求、暂停/退出要求，与 accepted listing、研究者说明、豁免/例外记录逐条关联，形成可覆盖、可追溯、可增量重算的医学监查单元，输出：

- D04 原生输出“入排条件待核实”“方案执行待核实”“退出或终止参与标准待核实”等具体问题；“禁限用要求待核实”等 producer-owned 问题只由总览透传 D02 等 owner 的单一结果；
- 方案原始编号、原文定位、结构化规则、支持依据、排除依据和原始记录的一跳关联；
- “依据＋发现＋行动项”三段式 Query 草稿；
- 受试者医学旅程中锚定筛选、随机、首次给药、治疗阶段、访视或实际日期的方案符合性事件与风险标记；
- N→N+1 的持续、数据补充后解决、方案修订后替代、身份歧义和覆盖缺口处理。

本切片不正式判定、分级、报送、登记或关闭方案偏离（PD）；不建立 PD 待办或外部回复闭环；不替代研究者、申办方或其他有权责任方；不运行 OCR/VLM、真实项目、真实 provider 或产品服务；不把某项目的标准编号、药名、阈值、访视表或 listing 布局写入通用内核。

D04 只评价“本域原生方案控制点与已接受数据是否形成需核实问题”。D02 独占 CM 与禁限用药医学评价，D03 独占研究药计划/实际暴露和给药处置医学评价，D05 将独占计划访视/评估/样本时窗评价。方案解构器仍抽取这些控制点，但必须通过版本化 `ProtocolControlRoutingRecord` 路由到 owner domain；producer-owned 控制点不进入 D04 medical expected-set、不创建 D04 candidate/risk/Query，只在“方案符合性”总览中以 typed reference 投影 producer 的单一结果。D04 可以引用 producer 结果和原始记录作上下文，但不得镜像 L1、升级 producer 不确定性、复制医学裁决或生命周期。D05 尚未冻结/实现时，D04 仅验证路由记录、owner 占位和合成 producer stub，不声称已消费真实 D05 expected-set 或算法。

若同一稳定来源事件/临床动作已由 D02/D03/D05 的 expected-set 覆盖，D04 无权以另一规则名称再次建立风险。只有控制点的临床 claim、触发条件和需要核实的行动与 producer-owned 单元确实不同，且不共享同一 `(subject, producer_unit_id 或 stable_source_event_key, clinical_action)`，才可建立 D04 原生单元。总览层可以把多个不同 owner 的相关问题分组显示，但必须保留各自身份和计数，不能复制、静默合并或重复生成 Query。

## 2. 规范依据、来源权威与时间适用性

### 2.1 规范依据

合同形成时使用以下外部依据，均仅约束方法，不替代项目 active protocol：

1. [ICH E6(R3) Step 4 final guideline](https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106_ErrorCorrections_2025_1024.pdf)：方案定义入排、治疗、剂量调整、禁限用药、依从与偏离处理；重要方案偏离应按试验特异标准识别，监察应支持纠正与防止复发。
2. [中国《药物临床试验质量管理规范》（2020）](https://ypjg.ln.gov.cn/ypjg/zwgk/flfg/zcjd/EC143FD7C4374A2C86E76DB42118D2AA/index.shtml)：研究者遵循伦理批准方案，偏离须记录和说明，紧急消除危害等例外另行处理。
3. [国家药监局、国家卫生健康委、国家中医药局、国家疾控局关于发布药物临床试验质量管理规范的公告（2026年第50号）](https://www.nmpa.gov.cn/xxgk/ggtg/ypggtg/ypqtggtg/20260608103856150.html)（[上海市药监局转载定位](https://yjj.sh.gov.cn/qtgzwj/20260608/89cbf084b5cb4eab8fd0fb56d8538a1d.html)）：2026 年修订版自 2026-09-01 起施行，2020 年第 57 号公告同时废止。系统必须按评价时点选择适用规范版本，不得永久硬编码单一版本。
4. [CDISC CDASHIG v2.1](https://www.cdisc.org/standards/foundational/cdashig-v2-1)：IE 用于入排标准；DV 用于入组后方案偏离。IE 汇总/是否满足字段不能替代逐条标准证据；偏离来源也不应只依赖单一 DV 表。
5. [ICH E3 Structure and Content of Clinical Study Reports](https://database.ich.org/sites/default/files/E3_Guideline.pdf)：重要偏离应按入排、试验实施、受试者管理或评估等类别和中心/受试者总结。
6. [FDA Protocol Deviations for Clinical Investigations, December 2024 draft](https://www.fda.gov/media/184745/download)：仅作为尚未实施的咨询性补充，不作为中国项目或本合同的强制规则；其“重要偏离类型可预先规定并随数据审阅更新”的思路只进入版本化策略设计。

### 2.2 项目内来源权威

| 来源 | 权威范围 | 不得越界 |
|---|---|---|
| 伦理/监管已接受的 active protocol/amendment | 当前受试者、中心、队列、阶段和时间窗“应当满足什么” | 不说明实际发生了什么 |
| accepted listing/source record | 当前快照“记录了什么” | 不自行证明符合方案或构成 PD |
| 受控随机/队列/阶段/中心开放记录 | 方案版本及规则适用性 | 不以药名、输入顺序或最近日期猜选 |
| 研究者判断、例外/豁免记录、紧急处置、方案允许例外 | 先分类其是方案预先允许的例外路径、经正式修订生效的规则变化，还是仅解释既往偏离的记录 | “已批准”字样、自由文本、未签署草稿或事后说明均不能自动把未满足的方案要求改写为符合方案 |
| 受控数据字典、单位与术语绑定 | 字段、单位、概念和代码解释 | 不补写缺失临床事实 |
| 模型/OCR/规则抽取结果 | 候选条款、候选证据和解释线索 | 未经来源定位与结构验证不能成为裁决依据 |

冲突不能按模型多数票解决。项目方案与 accepted data 各自在其 claim scope 内保留；无法唯一适用或解释时进入 `boundary` 或 `not_evaluable`。

### 2.3 方案版本适用性解析

每次评价必须先产生 `ProtocolApplicabilityDecision`，至少包含：

```text
protocol_id + protocol_version + amendment_id/hash
ethics_or_authority_approval_date + effective_start/end
site_activation_or_adoption_start/end
amendment transition scope + grandfathering/new-enrollment-only policy
re-consent requirement/actual status when relevant
cohort/phase/arm/treatment_role + control-point applicability
subject applicability + decision_time_anchor + event-time rule scope
source locators + decision_status + rationale
```

解析顺序固定为：

1. accepted source 中的显式 protocol/amendment link；
2. 伦理/监管批准与中心实际启用/采用日期；
3. 修订的过渡条款：仅新入组、既有受试者继续旧版、全部在组受试者切换、下一访视/重新知情后切换等；
4. 受试者筛选、知情/重新知情、随机、首次给药、阶段切换和被评价事件时点；
5. 队列、阶段、治疗角色、受试者范围及该具体 control point 的适用范围；
6. 仅在所有条件共同得到唯一 active version 时确定适用。

不得默认最新方案版本、全项目统一启用日、中心启用即自动覆盖所有在组受试者，或选择“离事件最近”的版本。site adoption 只是必要输入，不足以替代修订过渡条款和受试者/控制点适用性。旧版与修订版均可能适用、中心尚未启用修订、既有受试者 grandfathering 或重新知情条件存在两个有依据的解释、事件跨版本窗口、适用日期为部分日期或存在两个可行版本时，为 `boundary`；批准/启用/过渡条款/重新知情/事件关键日期缺失或冲突导致无法比较时，为 `not_evaluable`。

这里有两个不可混用的时钟：项目方案适用性由 `subject event time + site adoption time + amendment transition/re-consent/control-point scope` 共同决定；外部规范元数据以 `Run evaluation_time` 决定本次方法说明应引用哪个当时有效版本。外部规范版本变化不倒推改写既往受试者事件所适用的方案，也不自动改变临床 rule identity。2026-09-01 前后不得混用中国 GCP 版本；若需要重新解释既往结果，必须形成新的 knowledge lineage 和新 Run，而非覆盖历史。

## 3. 方案解构合同

### 3.1 原文层与规则层分离

方案原文必须不可变保存，结构化规则不得覆盖或改写原文。每条控制点保留：

```text
official_section_id + official_criterion_id + official_heading
parent_rule_id + component_id + display_order + nesting_path
verbatim_text + source_locator + source_revision_hash
structured_rule + extraction_status + verification_status
```

- 保留原始编号、标题、顺序、层级、脚注、表注和“以下任一/全部/除外”等逻辑。
- 包含多个条件的包级标准保留 parent rule，并按可执行原子条件拆为 components；不得把“任一”改成“全部”，也不得删除包级语义。
- 无官方编号时生成稳定派生编号，但前台清楚显示方案原文定位，不伪装为官方编号。
- OCR/模型输出只有在逐条对回可显示方案原文、页码/章节和内容哈希后，才可进入 verified structured rule；抽取成功不等于医学规则正确。
- 任何自由表达式都不能在通用内核执行；规则必须转换成受控 operator、value、unit、temporal anchor、exception 和 evidence requirements。

### 3.2 规则类型

`ProtocolControlPoint` 至少支持：

1. `inclusion`：入选条件；
2. `exclusion`：排除条件；
3. `prohibited_or_restricted_treatment`：抽取后路由给 D02；若非 CM/合并用药且确属其他行为，才可按该行为 owner 的原生规则评价；
4. `required_procedure_or_assessment`：计划访视、检查、评估或样本时窗路由给 D05；不属于 D05 计划单元的其他前置/处置要求才由 D04 原生评价；
5. `dose_or_treatment_management`：给药、暂停、减量、恢复或停药要求路由给 D03；D04 不重复评价同一研究药动作；
6. `discontinuation_or_withdrawal`：受试者退出、终止试验参与或其他 D04 原生处置标准；研究药暂停、恢复、终止治疗及其给药动作路由 D03，D04 不重复评价；
7. `consent_randomization_enrollment`：知情、筛选、随机、入组之间的前置关系；
8. `other_protocol_requirement`：只有原文可定位、适用性明确且受控结构足以执行时使用。

一个来源事实可参与多个控制点，但每个控制点独立评价；不得以“总体符合入排”覆盖逐条状态。

`ProtocolControlRoutingRecord` 至少包含 `control_point_id/component_id`、`owner_domain`、`owner_signal_type`、`routing_rule_version/hash`、`producer_unit_id 或 routing_gap`、来源定位和决定理由。路由必须先于 expected-set 生成；owner 无法唯一确定时，D04 只生成一个 `protocol_routing` not_evaluable gate，不得在两个域各建风险。

路由决定表是关闭集合：CM/合并用药禁限用 claim → D02；研究药计划/实际暴露、剂量或给药动作 claim → D03；名义/实际访视、检查/评估/样本计划和时窗 claim → D05；知情/筛选/随机/入组时序、入排资格、非计划型前置动作及退出触发条件 claim → D04；多表关系本身 → D08。入排/前置条款可以把 CM 或 IP 记录作为事实证据，但只要临床 claim 是“是否满足入组资格”，仍为 D04 native，并通过 accepted record/精确 `CrossDomainEvidenceRef` 消费用药事实；它不因此创建 D02 禁限用或 D03 暴露单元。反之，claim 是治疗期禁限用或研究药动作合规时由 D02/D03 独占。一个控制点跨两个 owner 且无法按 component 拆分时，不分派双重 expected unit，只生成一个 D04 `protocol_routing` not_evaluable gate 并保存候选 owners。

### 3.3 结构化运算与安全失败

允许的规则语义包括：存在/不存在、等于/不等于、集合包含、数值比较、范围、时间先后/包含、持续时长、次数、组合逻辑、已批准例外和研究者判断。每条规则必须声明：

```text
operator + value_set/threshold + canonical_unit
lower/upper inclusivity + precision/rounding policy
temporal anchor + evaluation window + endpoint inclusivity
required evidence roles + alternate evidence roles
retest/confirmation policy + exception/waiver policy
missing/conflict policy + rule priority policy
```

缺少等号语义、单位换算、舍入顺序、窗口端点、复测优先级或例外条件时不得由内核推断。通用内核不采用固定 30 天窗口、统一正常范围、统一年龄算法或通用药物禁限用列表。

## 4. 输入、证据门槛与跨域引用

### 4.1 语义角色

| 类别 | 中性语义角色 | 规则 |
|---|---|---|
| 身份与适用性 | `subject_identity`, `site_identity`, `cohort_phase`, `randomization`, `protocol_adoption` | 关键身份或版本适用性冲突先阻断医学裁决 |
| 入排 | `eligibility_assessment`, `demographics`, `medical_history`, `adverse_event`, `concomitant_medication`, `laboratory`, `vital_sign`, `ecg`, `physical_exam`, `questionnaire`, `pregnancy_test`, `other_assessment` | 只按规则声明的证据角色纳入 |
| 执行 | `ip_exposure`, `procedure`, `assessment`, `visit`, `sample`, `disposition`, `consent`, `randomization_event` | D03/D05/D08 的已验证结果可引用，不复制结论 |
| 例外 | `approved_waiver`, `protocol_exception`, `investigator_judgment`, `urgent_hazard_action`, `documented_explanation` | 来源标签只表示“存在一份例外/豁免类记录”；评价前仍须分类其法律/方案效力，并绑定受试者、规则、时窗、批准/确认状态和来源 |
| 辅助 | `aggregate_ie_status`, `deviation_listing`, `monitoring_note`, `email_or_edc_note` | 只能提示候选；不能单独证明某条规则符合或不符合 |

### 4.2 逐条证据门槛

每个控制点先生成 `RuleEvidenceRequirement`，再匹配 `RuleEvidenceBinding`。绑定至少包含 subject/site、官方规则 id/component、source role、stable source event key、值/单位/日期/精度、来源定位、accepted revision、关系确认状态和适用性 lineage。

以下不得单独作为某条标准的 positive 或 negative 依据：

- “符合全部入排标准”或 IEYN/IE 汇总 Yes/No；
- IE 表没有该条记录、DV 表没有记录或风险数为零；
- OCR/解析/模型返回成功；
- 无来源定位的人工备注、邮件或 EDC 摘要；
- 同受试者但 wrong site、wrong rule、wrong phase、wrong time window 的记录；
- 只凭字段名、表名、行号相似或日期接近建立的关系。

只有 rule-specific、identity-matched、time-comparable、accepted 且满足 required evidence roles 的证据，才可用于确定裁决。原始检查/诊断/用药记录优先；IE/DV/监查表和说明可作为辅助或排除依据。alternate evidence 只有在规则明确允许且映射版本化时才能替代主证据。

### 4.3 证据缺失与“未见记录”

“没有记录”只有在以下条件全部成立时才可能成为确定证据：

1. 该规则预期该记录存在或明确要求某状态不存在；
2. 对应来源角色在 accepted full snapshot 中完整覆盖；
3. 规则、适用时窗、受试者、中心和字段映射均明确；
4. 不存在允许的 alternate source、豁免、复测或研究者判断路径。

否则为 coverage gap/not_evaluable，不能推断“未发生”“不符合”或“符合”。纯存在性排除标准若规则明确“任何记录即排除”，完整覆盖下的零记录可作为 negative 依据；仍须保存 coverage 证明。

## 5. EvaluationUnit、expected-set 与稳定身份

D04 `EvaluationUnit` 对应一个可独立形成医学结论的官方控制点，而不是每个语法子句：

```text
subject + protocol applicability decision
+ official protocol control point + evaluation root (atomic|package)
+ applicability/evaluation temporal window + signal type
+ rule extraction/mapping/algorithm lineage
```

只有唯一 active version 下、归属 D04 的 evaluation root 进入 D04 medical expected-set；其中也包括经权威适用性决定明确为不适用、需要记录 `not_applicable` 的控制点：

- 原子标准生成一个 `evaluation_node_id=atomic` 的 unit；组合标准生成一个 `evaluation_node_id=package` 的 unit。组合标准的 children 保存为 `ProtocolComponentAssessment`，不是 EvaluationUnit、不进入 expected-set/L1/L2/lifecycle，也不各自产生风险或 Query；
- `ProtocolRuleEvaluationPlan` 必须冻结哪些官方节点是可独立裁决的 evaluation roots、哪些仅是 component-only nodes。章节标题或展示分组不伪装成 unit；同一临床要求不得同时以 parent 和 child 两层建 unit；
- 每个 component assessment 保留 official component id、原文定位、证据绑定、`issue_predicate_result=issue_true|issue_false|boundary|not_evaluable|not_applicable`、缺口和 counterevidence。它只描述该子条件对“本控制点是否存在方案问题”的贡献；
- 规则抽取必须从原文冻结一个只引用 component ids 的 `parent_issue_expression`（受控 `AND|OR|NOT|AT_LEAST_N`），其含义始终为“该 evaluation root 是否存在方案问题”。例如“至少满足任一入选子条件”的 issue expression 通常为各子条件未满足谓词的 AND；“全部入选子条件均须满足”通常为未满足谓词的 OR；不得直接把原文连接词机械复制为 issue expression；
- evaluator 对 boundary/not_evaluable component 的所有可行 truth assignments 执行表达式：恒 true → unit L1 `positive`；恒 false → unit L1 `negative`；true/false 都可能且参与不确定项含 not_evaluable → `not_evaluable`；否则 → `boundary`；全部 component 明确不适用且控制点也由权威适用性证明不适用 → `not_applicable`；component set、原文逻辑或表达式不完整 → `not_evaluable`；
- 原文未显式、脚注冲突或无法无歧义解析“任一/全部/除外/至少 N”时，`verification_status` 不得为 verified，禁止默认 AND/OR，整个 evaluation root 为 `not_evaluable`；
- 若表达式在部分 component 缺口下仍恒 true/false，L1 可为 positive/negative，但 unit L0 必须反映尚未覆盖的 component gap，D04 domain complete 仍被阻断；只为 evaluation root 建立至多一个 candidate/risk/Query，并在其中列出决定性 component ids 与未决缺口；
- 同一标准在筛选、随机、首次给药或治疗后有不同评价时点时拆分不同窗口；
- 明确不适用的标准也生成 `not_applicable` 单元并绑定依据；
- `ProtocolApplicabilityDecision.decision_status` 只允许 `unique_active|multi_feasible_boundary|not_evaluable`：`unique_active` 才按该版本生成正常 evaluation-root units；其余情况每个 stable applicability decision 只生成一个 `control_point_id=protocol_applicability`、`evaluation_node_id=applicability_gate`、`signal_type=protocol_applicability` 的受试者级阻断单元，分别为 boundary/not_evaluable，受影响 control point ids 和可行版本 ids 只保存在 decision/context 中，不生成 N 份 control-point gate 或 N 份版本×规则医学单元，也不按输入顺序选一个版本；
- applicability gate 的 `protocol_applicability_id` 是对 subject/site、decision anchor、日期精度、排序后的 feasible version fingerprints 与稳定来源内容键做 canonical hash 的内容 id，禁止含 run/snapshot/revision；gate 的 `temporal_window` 固定为 `eval_anchor_kind=other, window_start/end="", precision=unknown, endpoint_inclusivity=gate`；其 lineage 使用 `protocol_version/amendment_id_or_hash=multi_feasible|undetermined`、`rule_content_hash/extraction_hash=applicability_gate` 和排序后的 feasible version fingerprints，保证输入顺序不改变 unit id/expected-set hash；
- producer-owned 控制点不生成 D04 medical unit；路由缺失或 owner 竞争时只生成一个 `evaluation_node_id=routing_gate`、`signal_type=protocol_routing` 的 not_evaluable 单元。

八个哈希维度固定映射为：

```text
project_id = current run project_id
domain_id = "D04_protocol_compliance"
scope_type = "subject"
scope_key = subject_ref
normalized_concept_or_rule_item = canonical_json({
  "control_point_id": stable control point id,
  "evaluation_node_id": "atomic"|"package"|"applicability_gate"|"routing_gate",
  "signal_type": closed enum
})
temporal_window = canonical_json({
  "protocol_applicability_id": stable decision id,
  "eval_anchor_kind": screening|consent|randomization|first_dose|on_treatment|discontinuation|other,
  "window_start": original normalized value,
  "window_end": original normalized value,
  "precision": date precision,
  "endpoint_inclusivity": versioned inclusivity
})
rule_or_knowledge_lineage = canonical_json({
  "protocol_id": protocol id,
  "protocol_version": protocol version,
  "amendment_id_or_hash": amendment id/hash,
  "rule_content_hash": verified rule hash,
  "extraction_hash": extraction hash,
  "mapping_version": mapping version,
  "unit_term_policy_version": unit/term policy version
})
unit_algorithm_version = "d04_unit_v1"
```

`signal_type` 关闭枚举为 `inclusion|exclusion|required_protocol_action|discontinuation_or_withdrawal|consent_randomization_enrollment|other_protocol_requirement|protocol_applicability|protocol_routing`。不得用 `|` 拼接裸字符串或使用自由 signal type；所有嵌套对象先按公共 canonical JSON 序列化为单个字符串，再交给冻结 `EvaluationUnit` 八维哈希。component assessment 使用独立稳定 assessment id，不伪装为 unit id。相同 fixture 必须有 golden unit id、component-assessment ids 与 expected-set hash。

风险身份只通过公共 R2 `make_risk_identity` 建立：

```text
domain = "D04_protocol_compliance"
classifier/stable_core = canonical_json({
  "subject_ref": subject_ref,
  "control_point_id": control_point id,
  "evaluation_node_id": atomic|package,
  "signal_type": closed enum,
  "eval_anchor_kind": closed enum,
  "evaluation_window_id": stable canonical id over anchor, bounds, precision and inclusivity
})
scope/lineage_fingerprint = canonical sorted payload(
  site_ref, protocol_id/version/amendment_hash, cohort/phase,
  rule_content_hash, date_precision, mapping_version,
  unit_term_policy_version, unit_algorithm_version
)
```

`classifier/stable_core` 不得含 protocol version、snapshot/revision、可变自由文本或 Query；版本信息只进 lineage。`evaluation_window_id` 必须区分相同锚点类型下两个不同筛选/重筛/治疗窗口，且不得含 Run/snapshot/revision。同一窗口的规则/mapping/knowledge lineage 改变时 classifier 持续、lineage 改变并走 superseded/not_evaluable；不同窗口不得被 linked-negative 互相关闭。

## 6. L1 医学评价合同

### 6.1 `positive`

仅在适用方案版本和控制点唯一、决定性证据的身份与时间可比较、规则表达式在所有可行 component assignments 下恒为 issue=true，且无足以改变该确定结论的适用排除依据时使用。普通原子规则仍要求其 required coverage 完整；组合规则若存在不影响恒真结论的非决定性 component gap，可保留 L1 positive，但 L0 必须为 partial/相应缺口状态、生成 coverage-gap notice，并阻断 D04 domain complete：

1. `inclusion_requirement_not_met`：入选条件确定未满足；
2. `exclusion_condition_present`：排除条件确定存在；
3. `required_protocol_action_not_met`：未归属 D02/D03/D05 等 producer 的必要处置或前置动作确定未按要求完成；
4. `discontinuation_or_withdrawal_requirement_inconsistent`：已达到 D04 原生退出/终止试验参与等触发标准，但受试者处置记录确定不一致，或已退出而必要依据不一致；研究药暂停、恢复、终止治疗及其给药动作一律路由 D03，不由 D04 重复建风险；
5. `consent_randomization_sequence_inconsistent`：知情、筛选、随机、入组或首次给药的确定时序冲突；
6. `other_protocol_requirement_inconsistent`：经受控结构明确定义、且未由 D02/D03/D05 覆盖的其他要求确定不一致。

positive 只产生“待核实”线索/风险和 Query 草稿，不等于已确认 PD。一个单元只有一个 primary subtype；相同事实命中不同规则时保持各自规则身份和 Query 依据，不静默合并。

### 6.2 `negative`

只有以下全部满足时使用：适用版本/队列/阶段/时窗唯一；决定性证据足以证明规则表达式在所有可行 component assignments 下恒为 issue=false；值、单位、阈值、端点、复测和例外策略可重算；所有支持该结论的来源可定位。普通原子规则仍要求其 required coverage 完整；组合规则若存在不影响恒假结论的非决定性 component gap，可保留 L1 negative，但 L0 必须为 partial/相应缺口状态、生成 coverage-gap notice，并阻断 D04 domain complete。

“总体符合入排”、IEYN=Yes、DV 零行、模型未提示或风险数为零不能单独判 negative。

### 6.3 `boundary`

- 两个或以上方案版本/阶段/队列都可能适用，且各有充分来源支持；
- 数值恰在阈值，规则未定义等号、舍入或单位换算顺序；
- 部分日期在共享精度上可能命中也可能不命中窗口；
- 有两个或以上同等权威的复测、确认值或例外解释，规则未规定优先级；
- 研究者判断、豁免或紧急处置的适用范围存在两个有依据的解释；
- 组合逻辑的不同可行解析均可回到方案原文，但结构规则未能唯一化。

关键字段单纯缺失、来源未覆盖、关系未确认或冲突不可解释，且该缺口使 issue expression 仍可能为 true 或 false 时为 `not_evaluable`，不得用 boundary 包装 coverage gap；结果无法确定且 boundary 与 not_evaluable 同时参与时 `not_evaluable` 优先。若表达式不论该缺口取值都恒真或恒假，则按 §5/§6.1/§6.2 保留 determinate L1，同时以 L0/coverage-gap 阻断完整性。

### 6.4 `not_evaluable`

- 适用方案/修订、中心启用、队列/阶段/受试者身份无法确定；
- 官方标准原文/编号/层级无法可靠定位，或抽取规则未验证；
- required source role 未覆盖、字段缺失、单位未知、关键日期冲突；
- IEYN/IE 汇总或无 DV 行是唯一证据；
- 主证据和 alternate evidence 的允许关系未版本化；
- 研究者判断/豁免/例外需要批准或确认但状态缺失；
- 需要逐条证据却只有自由文本、OCR/模型解释或无定位摘要；
- wrong subject/site/rule/window 或关系未确认；
- 一个来源行缺失且不能证明它本应存在。

not_evaluable 生成“资料不足，暂无法核实”的 `ProtocolCoverageGapNotice`，但不产生新的确定风险、不创建 L2 QueryDraftRef，也不显示成“未知风险等级”。同一 notice 也用于 §6.1/§6.2 中 L1 已确定但 L0 partial 的非决定性 component gap。notice 至少包含 `notice_id/unit_id/reason_code/missing_evidence_roles/protocol_locator_ids/reachable_source_locator_ids/audience_text`；`notice_id` 对 unit、reason、排序后的缺失角色与定位做 canonical content hash，禁止含运行时自由文本。它单独计入 coverage gap，不进入 Query count。若已有活动风险，本次 not_evaluable 只 carry-forward 并显示覆盖缺口。

### 6.5 `not_applicable`

仅在 active protocol/设计、队列/阶段和受试者范围共同证明该控制点在当前评价窗口明确不适用时使用，并绑定条款和适用性决定。没有记录、未映射、未执行或模型不会判断均不是不适用。

## 7. 关键医学与时间规则

### 7.1 数值、单位、阈值与复测

- 原始值、原始单位、规范值、换算 lineage、比较精度和舍入顺序分别保存；无版本化换算不得比较。
- 年龄、实验室、生命体征、量表和时长算法均由项目规则冻结；不得采用通用默认值。
- 等号与上下界 inclusivity 必须明确；未明确时 boundary。
- 初筛异常后复测合格能否覆盖初筛、需要几次、在哪个时间窗、使用本地或中心实验室，由规则决定。
- 同日多个值只有版本化选择策略才可确定裁决；不能挑对结论最有利的值。

### 7.2 日期、窗口与关键锚点

- 复用冻结部分日期语义，只在共享精度上比较；不静默补日。
- 筛选、知情、随机、首次给药、治疗阶段、退出和 cutoff 是不同锚点，不得互换。
- 访视间实际事件保持真实日期；只有规则明确以名义访视为锚点时才关联访视。
- 事件跨方案修订时必须按事件时点和中心启用日期选择规则，不得用 Run 日期倒推。

### 7.3 豁免、例外、紧急处置与研究者判断

例外类记录必须精确绑定 subject/site/rule/component/window，并保存授权者、批准/确认状态、决定日期、生效时点、来源和 `exception_effect`。`exception_effect` 为关闭枚举：`protocol_defined_exception|effective_rule_change|urgent_hazard_justification|retrospective_explanation|unresolved`。只有 active protocol 本身预先允许的例外路径，或在评价事件时点已经生效且适用于该受试者/中心/队列的正式规则变化，才参与规则运算并可能使当前单元得到 `negative + counterevidence`。仅有“批准豁免”字样、申办方/研究者事后同意、事后说明或对既往偏离的追认，不能把未满足的入排或方案要求改写为符合方案；它们只作为处置/解释上下文，原子单元仍按事件时有效规则评价。紧急消除危害可解释特定处置，但不抹除已发生的偏离事实，也不自动使其他入排或方案要求变为满足。效力类型、事件前后顺序或适用范围无法唯一确定时为 `boundary` 或 `not_evaluable`。不得在原地改写既往 positive `UnitEvaluation`；N+1 重新评价和既往风险关闭仍须满足 §10 的 linked-negative、完整 coverage 与 R2 adjudication。研究者判断不能被模型推断，未记录判断也不能由临床常识补写。

### 7.4 跨域引用

- D02 禁限用药、D03 给药处置、D05 访视/评估/样本、D07 检查、D08 多表关系只通过公共中性 `CrossDomainEvidenceRef` 引用；该对象必须使用公共字段和 canonical content hash，严禁加 consumer candidate/risk/Query/L1/lifecycle。
- producer-owned 控制点由 `ProtocolControlRoutingRecord.producer_unit_id` 指向 owner expected-set；D04 总览投影 producer 的现有 marker/Query，不复制为 D04 EvaluationUnit 或第二个 R2 risk identity。
- D04 原生单元若消费跨域事实，只有 `subject_ref + site_ref + producer_unit_id + stable_source_event_key/content_hash + rule/component + 可比较 time window + relation_type enum` 全部精确验证，才可用于 positive/negative；任一 wrong/missing/unconfirmed 为 not_evaluable 或 context-only。仅 record id 相同、日期接近、行号相同或说明文字相似均不得建立医学关系。
- 同一来源可支持多个真正不同的 D04 原生控制点，但 L2 source count 仍按稳定记录去重；相同 producer unit/clinical action 不得重复建立风险。
- D04 不以 D02/D03/D05 总状态替代具体证据，不升级 producer boundary/not_evaluable。上游 not_evaluable 阻断依赖它的 D04 原生单元；producer-owned 控制点直接沿用 producer coverage gap。
- `ProtocolEventMarkerJoin` 固定为 `event_id + marker_id + unit_id + risk_identity_id + join_reason + typed_ref_ids`；`join_reason` 关闭枚举为 `unit_identity|anchor_event|source_locator|producer_reference`。每个 id 都须可达且同 subject/site/window，tamper 在投影前失败。

## 8. 监察优先级、中文标签与 Query

### 8.1 监察优先级

优先级来自版本化、内容寻址的 `D04PriorityPolicy`（policy id/version/hash/reason），至少考虑潜在受试者伤害、关键权益、对主要终点/数据可靠性的影响、紧迫性、系统性和可行动性；不由模型自由评分，也不等于已确认重要 PD。候选 detail 的 `rights_or_safety_critical` 与 `machine_close_forbidden` 为冻结布尔键；公共 `contracts.py` 提供严格布尔读取器 `candidate_rights_or_safety_critical` 与 `candidate_machine_close_forbidden`，缺失为 false、非布尔值 fail closed。它们只用于公共 R4 lifecycle adapter 建立风险前的保守优先级归一化；冻结 R2 `RiskInstance` 不新增任意 detail 字段。以下只是非规范性示例，具体映射必须来自 active policy：

- 可能直接影响入组资格、知情同意、重大禁忌、关键处置或受试者权益的确定问题通常优先显示为高；
- 影响方案执行或关键数据完整性的确定问题通常为中；
- 影响有限但需澄清的问题可为低；
- not_evaluable 不投影“未知风险等级”。
- boundary clue 的优先级若策略无法确定则保留 `unknown`；`unknown` 不得默认 low，也不得机器关闭。

高优先级仍只是待核实问题；不得在 Query 或界面写“已确认重大方案偏离”。

### 8.2 中文受众标签

| 工程 subtype | 用户标签 |
|---|---|
| `inclusion_requirement_not_met` | 入选条件待核实 |
| `exclusion_condition_present` | 排除条件待核实 |
| `required_protocol_action_not_met` | 方案要求执行情况待核实 |
| `discontinuation_or_withdrawal_requirement_inconsistent` | 退出或终止参与标准待核实 |
| `consent_randomization_sequence_inconsistent` | 知情与入组时序待核实 |
| `other_protocol_requirement_inconsistent` | 方案执行情况待核实 |

界面不得显示 `positive`、`candidate`、`formal fact`、`候选信号`、`正式事实`、`只读投影`、`规则引擎命中`、`后端`、`模型置信度` 等研发语言。

### 8.3 三段式 Query 草稿

每条 L2 Query 草稿必须绑定 subject/site、protocol version、official criterion/决定性 components、source locators、EvaluationUnit 和 candidate/risk；not_evaluable 的资料不足提示使用 §6.4 `ProtocolCoverageGapNotice`，不伪装成 Query：

生成行动项前必须冻结 `query_context=enrollment_not_occurred|enrolled_or_post_enrollment|enrollment_state_unresolved`，由可定位的筛选、随机、入组、首次给药和处置记录决定，不能由当前页面或模型猜测：

- `enrollment_not_occurred`：只请核实入排结果、筛选结论或数据记录，不写“评估是否构成方案偏离”；
- `enrolled_or_post_enrollment`：若确定问题与已入组/随机/接受研究干预后的方案执行有关，才可使用“如确认不符合方案，请评估是否构成方案偏离并按相应流程处理”；
- `enrollment_state_unresolved`：先请核实是否已随机/入组/接受研究干预及事件时序，明确当前资料不足，不写确定 PD 方向。

```text
依据：写明适用方案版本、原始条款编号/要点及适用时点。
发现：写明受试者的具体日期、值、单位、用药、检查或时序，以及当前支持/排除依据。
行动项：请核实、说明、补充或更正；只有 `enrolled_or_post_enrollment` 情境才可追加“如确认不符合方案，请评估是否构成方案偏离并按相应流程处理”。
```

示例仅用于合成格式：

```text
依据：方案 V2.0 入选标准 5.1.3 要求筛选期指标 X 不低于 10 U/L。
发现：参与者 SYN-001 筛选期 2026-01-03 记录为 8 U/L，当前未见符合方案复测要求的后续结果。
行动项（该合成示例假设参与者已入组）：请核实该指标及复测记录；如确认不满足入选要求，请评估是否构成方案偏离并按相应流程处理。
```

系统只生成、编辑、可选用户确认和导出 Query 草稿；不发送、不跟踪回复/关闭，不创建强制待办。boundary 且已有 candidate 的 Query 应明确不确定边界；not_evaluable 只显示 coverage gap notice，任何用户可见资料不足提示都不得写成确定不符合。

## 9. 受试者医学旅程投影与一跳追溯

D04 只提供 renderer-neutral payload，不宣称 R5 UI 已完成：

- 每个规则评价投影到“方案符合性”轨道，保留筛选/随机/首次给药/治疗/退出等实际日期或访视锚点；
- 入排问题优先锚定实际筛选证据日期和名义/实际访视；知情/随机时序锚定各事件；退出/终止参与锚定触发条件与处置区间；producer-owned 禁限用、研究药暂停/恢复/停药和计划访视/评估/样本 marker 仅通过 typed producer join 出现在方案符合性总览，保持 producer marker/risk identity，不生成 D04 marker/risk identity；
- 不存在精确日期时进入独立待定区域，不伪造时间点；
- D04 原生风险标记使用“入选条件·高”“知情与入组时序·高”等具体标签；“禁限用要求·中”等仅保留 owner domain 的中文标签并经 producer typed join 投影。AE/MH/CM/IP/检查/方案符合性维持不同轨道、形状和线型，不只靠颜色；
- 中高风险全部优先显示；重叠标记可聚类，但点击后必须展开每条官方规则与独立评价；
- 点击可双向到方案原文、结构化规则、支持依据、排除依据、原始 listing 和 Query；Profile/指标趋势、Timeline/事件明细共享同一访视轴与选中时间窗。

最小字段：

```text
ProtocolJourneyEvent:
  event_id/domain_track=protocol/subject_ref/site_ref
  anchor_kind/start/end/date_precision/nominal_visit/actual_visit/phase
  protocol_version/control_point_id/evaluation_node_id/decisive_component_ids/display_label
  source_locator_ids/unit_ids

ProtocolRiskMarker:
  marker_id/risk_family/audience_label/monitoring_priority
  anchor_kind/anchor_start/anchor_end/date_precision
  unit_id/candidate_or_risk_id/protocol_locator_ids
  supporting_locator_ids/counterevidence_locator_ids/query_ids/coverage_gap
```

所有双向 join 通过稳定 id 验证，不以说明文字、相同日期或相同编号替代。

## 10. 增量、方案修订与生命周期

1. 同一 accepted full snapshot、相同规则/适用性/mapping/算法 lineage 和相同稳定事实重跑，unit/candidate/payload 哈希确定且不重复建风险。
2. N+1 新增/修订记录后仍命中同一稳定身份，风险持续并追加证据；普通 snapshot/revision 变化不改变临床 identity。
3. 低/中风险只有在随后 accepted full snapshot、完整 closed coverage、相同身份与规则 lineage、精确 linked-negative 和显式 machine adjudication 下，才可 `resolved_by_data`；保留原线索—后续纠正记录历史。
4. 高优先级、用户确认/升级、关键权益问题、身份歧义和重要冲突不机器自动关闭。D04 候选若 `rights_or_safety_critical=true`，同时必须有 `machine_close_forbidden=true`。唯一公共 `R4LifecycleAdapter.establish_positive_candidate` 在建立 R2 risk 前通过公共读取器检查任一 flag：即使调用方误传 medium，也强制 effective monitoring priority/high severity；建立后必须断言 `RiskInstance.severity=high`，否则 fail closed。最终冻结的 high severity 成为持久化关闭禁令；后续现有 `must_carry_forward` 与 `machine_close_by_data` 依其 high severity 拒绝机器关闭。flag 不写入 R2 RiskInstance、不扩展 `clinical_risk_flags`、不改冻结 R2。允许对公共 R4 `contracts.py/lifecycle.py` 做最小、行为保持的读取与 pre-establishment normalization 适配及 D01-D03 回归，不得在 D04 建第二套关闭服务。
5. 方案修订、中心启用、规则抽取、mapping、单位/术语或算法 lineage 改变导致不再命中时，使用 R2 `superseded` 或终态 `not_evaluable`；不得伪装为数据问题已解决。
6. 同一 stable clinical event 的适用版本无法唯一延续时使用 `identity_ambiguous` 并阻断合并/关闭。
7. 本次 not_evaluable 只 carry-forward 已有风险并显示覆盖缺口；不产生新的确定风险。
8. 新增用户自然语言特殊规则经受控拆解、来源/适用性/版本确认并形成新 rule lineage 后，只影响相应新 Run；不得回写既往已接受结果或静默改变旧规则。

## 11. 覆盖、计数与聚合不变量

- `expected_units = positive + negative + boundary + not_applicable + not_evaluable`，每个 unit id 恰好一次；
- L0 与 L1 是正交层：组合规则的非决定性 component gap 可使 L0 partial 而 L1 仍为 logically determinate positive/negative；这类 unit 永远阻断 domain complete，且 coverage notice 不改变五类 L1 分母；
- source records、verified rule evidence、candidate、risk instance、Query draft 分别计量，不相互推导；
- 每个 positive 至少关联一个 D04 candidate/risk；negative 不创建新 candidate；boundary 只创建保留不确定性的 clue；
- `ProtocolComponentAssessment` 保留全部 component assessment ids、issue predicate results 与 gap/counterevidence；它不进入 expected-set/L1/L2/lifecycle。每个 evaluation root 只有一个 UnitEvaluation，至多一个 candidate/risk/Query，且不得隐藏任何 component gap；
- producer-owned 控制点不进入 D04 expected-set，路由清单的 `delegated_control_points` 与 D04 五类 L1 计数分别保存，且每个 delegated item 必须精确关联一个 owner expected unit 或一个 routing gap；
- L0 partial/truncated/failed/missing 或任一 L1 not_evaluable 时不得声明 D04 医学完整；
- IEYN/IE/DV/监查说明进入辅助来源计数，不得污染逐条 rule evidence count；
- Query 必须关联本单元、方案条款、决定性 components、可达来源及本单元 candidate/risk；not_evaluable coverage notice 不进入 Query count，Query count 不进入 risk count；
- 中心/项目聚合只聚合个体结果与明确分母，不复制或改写个体风险身份，不用多数票隐藏高风险/coverage gap；
- `lifecycle.py` 保持唯一公共 R2 adapter，D04 不复制状态枚举、关闭逻辑或第二套 risk identity。

## 12. 最小合成挑战矩阵

实现与独立验收至少覆盖：

1. 唯一 active protocol/version/中心启用/队列/阶段，确定 inclusion 不满足；
2. 唯一 active version，完整证据满足 inclusion，negative；
3. exclusion condition 明确存在，positive；
4. exclusion condition 在完整来源中明确不存在，negative；
5. IEYN=Yes 但无逐条证据，not_evaluable；
6. IE 表无失败行、DV 表零行，仍不得判 negative；
7. 官方编号、父标准、component 层级与 display order 原样保存；
8. “以下任一”与“以下全部”各只生成一个 package EvaluationUnit，但按不同 issue expression 得到不同确定逻辑；
9. `ProtocolRuleEvaluationPlan.parent_issue_expression` 按原文语义转换为 AND/OR/NOT/AT_LEAST_N；component assessments 不进入 expected-set/L1/L2/lifecycle，且 package unit 不隐藏任何 boundary/not_evaluable component；
10. 无官方编号时稳定派生 id，但不伪装官方编号；
11. 最新修订尚未在某中心启用，按旧版评价；
12. 同日启用与事件端点未定义，boundary；
13. 两个版本均可能适用且有依据，boundary；
14. 版本批准/中心启用关键日期缺失，not_evaluable；
15. 2026-09-01 前后按不同中国 GCP 版本元数据解析，不混用；
16. 数值明确低于 inclusion 下限，positive；
17. 数值恰在阈值且 inclusive 明确，确定 positive/negative；
18. 等号未定义，boundary；
19. 单位可按版本化关系换算，确定评价；
20. 单位未知或有两个可行换算，not_evaluable/boundary；
21. compare-before-rounding 与 compare-after-rounding 产生可预期不同结果；
22. 规则指定复测合格可覆盖初筛，counterevidence/negative；
23. 复测时间窗、次数或权威来源不满足，positive；
24. 两个同等权威复测且规则无优先级，boundary；
25. active protocol 预先允许的例外或事件时已生效的正式规则变化精确绑定 rule/subject/window，才能作为规则运算中的 counterevidence；
26. 仅有“批准豁免”字样、事后追认/说明、未批准记录、wrong rule、wrong subject/site/window，均不能把未满足要求改写为 negative；效力不明为 boundary/not_evaluable；
27. 研究者判断是规则必需输入但未记录，not_evaluable；
28. 紧急消除危害例外有完整记录，不自动判不符合；
29. 禁用 CM 的 D02 `CrossDomainEvidenceRef + producer_unit_id` 只进入方案符合性总览/typed marker join；D04 medical expected-set 排除该 CM 控制点，新增 D04 risk/Query 数均为零；
30. D02 仅有不确定药物身份时 D04 不升级确定风险；
31. D03 研究药暂停/减量事实只有在支持一个 clinical claim 与 D03 给药动作评价不同的 D04 原生条款时才可精确关联为证据；否则只透传 D03 producer 结果，D04 不建单元/风险/Query；
32. D03 episode/assignment not_evaluable 时 D04 相依单元 not_evaluable；
33. D05 访视/样本责任边界：D05 未冻结前以合成 producer stub 验证路由/typed ref；D04 不复制时窗算法，也不宣称已有真实 D05 结果；
34. alternate lab/diagnostic source 仅在规则允许时替代主来源；
35. wrong subject/site/rule/phase/time window 关系全部 fail closed；
36. 仅日期接近或行号相同不得建立 cross-domain link；
37. 部分日期明确命中、明确不命中、可能命中分别确定/boundary；
38. 知情在首次方案规定程序之后的确定时序冲突；
39. 筛选、随机、首次给药三个锚点不可互换；
40. 入组前 IE 与入组后 DV 语义分开，不用 DV 覆盖 IE 证据；
41. 退出/终止试验参与标准达到但受试者处置记录确定不一致，D04 positive；同一事件涉及研究药停止时，给药动作仅由 D03 评价；
42. D04 原生退出/终止参与标准的适用性或触发条件输入缺失，not_evaluable；研究药暂停/停药输入缺失由 D03 处理；
43. 三段式 Query 含版本、条款、事实、行动项；只有已入组/随机/接受研究干预或入组后情境，PD 才作为请求有权责任方核实/评估的方向；
44. Query 不得出现“已确认 PD/重大 PD/已报送/已关闭”；
45. not_evaluable 单元生成绑定 unit/reason/方案定位/可达来源的 `ProtocolCoverageGapNotice`，不创建 candidate/risk/L2 Query，不写确定不符合；
46. Journey 锚定实际日期/访视、无日期进入待定区；
47. Journey 具体标签、typed join、方案原文/证据/Query 双向可达；
48. 相同输入重跑 unit/candidate/payload 哈希稳定；
49. N+1 精确 linked-negative + 完整 coverage 仅关闭 low/medium；
50. high、用户确认、identity ambiguous 不机器关闭；
51. 数据更正且 lineage 不变为 resolved_by_data；
52. protocol/rule/mapping/algorithm lineage 改变为 superseded/not_evaluable；
53. 新增自然语言特殊规则形成新版本 lineage，仅影响后续 Run；
54. source/evidence/candidate/risk/Query 计数互不污染；
55. D01-D03、R2、R3 相邻回归保持通过，8911 保持停止；
56. D02 禁用 CM positive 与 D04 同一 control point/stable event 只保留一个 producer risk 和一个 Query；D04 总览 typed link，不建第二个风险；
57. D03 `unsupported_ip_action` 与 D04 同一研究药动作只保留 producer risk，D04 不升级或复制；
58. package components 为 issue_true＋not_evaluable 时，由冻结表达式决定唯一 package unit：若所有可行 assignments 都为问题则 L1 positive，否则 not_evaluable；任一 component gap 使 L0/domain incomplete，positive 时也只建一个 package candidate/Query；
59. control point/component id 内含 `|` 仍以 canonical JSON 生成不同 unit/assessment id；package EvaluationUnit 与 component assessment id 永不混用，golden expected-set hash 固定；
60. 两个可行方案版本只生成一个 applicability gate unit，不生成 N 份医学单元，不受输入顺序影响；
61. N 为 positive，N+1 新增事件时已经生效且由方案预先允许的精确例外证据时，可重新评价 package/atomic unit 为 negative＋counterevidence；仅新增事后追认/说明不得改变原评价；历史不改写，只有 low/medium＋完整 linked-negative 可关闭；
62. mapping/rule lineage 改变保持 classifier stable 并走 superseded/not_evaluable，不使用 resolved_by_data；
63. 同 record id 不同受试者、仅日期接近、仅行号相同和 relation 未确认均拒绝跨域 join；
64. 受试者转中心时 site 留在 lineage；两个中心都可能适用时 not_evaluable/identity_ambiguous，禁止自动合并/关闭；
65. V1 入组标准按入组时点评价，中心启用 V2 后的治疗规则按新窗口评价；Run 日期不得把 V2 倒推到 V1 入组事件；
66. 候选 `rights_or_safety_critical=true|machine_close_forbidden=true` 即使调用方误传 medium，公共 adapter 仍建立 severity=high 的 R2 risk，后续拒绝机器关闭；
67. owner routing 竞争只生成一个 routing gate not_evaluable，不在 D02/D03/D04 重复 expected unit。
68. 同一 control point、相同 `on_treatment` anchor 的两个不相交 evaluation windows 生成不同 unit id 和 risk identity；window A linked-negative 不得关闭 window B；
69. 样本/评估计划时窗路由 D05、非计划型知情/入组前置关系路由 D04；无法拆分时只生成一个 routing gate；
70. 公共 lifecycle adapter 对 `rights_or_safety_critical|machine_close_forbidden` 任一 true 在建立风险前强制 effective priority=high；R2 instance 不新增字段，后续依 high severity carry-forward/拒绝 machine close，D01-D03 行为保持；
71. 两个可行版本×多个 control points 仍只生成一个受试者级 applicability decision gate，affected control points 只进 context，不污染 L1 分母。
72. “满足以下任一项”一个 component 已满足、另一 component not_evaluable 时，唯一 package unit L1=negative、L0/domain incomplete，且不建 candidate/Query；
73. “需同时满足全部”一个 component 不满足、另一 component not_evaluable 时，唯一 package unit L1=positive、L0/domain incomplete，只建一个风险/Query并列出决定性与未决 components；
74. `AT_LEAST_N` 在不确定 component 的所有可行 assignments 下恒真/恒假/可变时分别映射到唯一 package unit 的 positive|negative|boundary/not_evaluable；input order 不影响结果，component assessments 不进入 coverage/lifecycle。
75. 筛选条件不满足但确定未随机、未入组且未接受研究干预时，Query 只核实筛选结论/记录，不出现“评估是否构成方案偏离”；
76. 随机/入组/首次给药状态或时序无法确定时，Query 先要求核实状态并说明资料不足，不把入排问题写成已发生 PD。
77. V2 已在中心启用但过渡条款仅适用于新入组者：既有受试者的既往入排仍按 V1，不能仅凭 site adoption 倒推 V2；
78. 修订要求在重新知情或下一访视后切换，但重新知情/访视时点缺失或两种解释均有依据时，生成单一 applicability gate（not_evaluable/boundary），不生成版本×控制点单元。
79. 排除标准“筛选前 28 天内使用 X 药”以 CM 记录为事实证据且命中窗口时，由 D04 建一个 `exclusion_condition_present` 风险；没有独立治疗期禁限用 claim 时 D02 计数为零，两域不重复建险；
80. 年龄类 inclusion 只有出生年和知情日期，且项目未冻结年龄算法时为 boundary/not_evaluable，绝不默认周岁/实足年龄算法；
81. 复测结果合格但落在规则允许复测窗之外时不能作为排除依据，原确定问题保持 positive；
82. 原文仅写“需满足下列标准”且任一/全部/至少 N 语义无法无歧义确定时，package unit not_evaluable，不默认 AND/OR；
83. 两个可行版本以相反输入顺序传入时，排序后的 feasible fingerprints、applicability gate unit id 与 expected-set hash 完全相同。

## 13. 实现与验收边界

### 13.1 允许的实现面

- 新增 `src/mm_r4/protocol.py`、`protocol_projection.py`、`protocol_fixtures.py` 及对应测试；
- 对 `contracts.py`、公共 identity/coverage/lifecycle、根导出做最小行为保持适配；
- 不改冻结 R1/R2/R3，不触碰 R5 UI、真实项目、产品服务或医学写作子系统；
- 所有实现使用合成/离线 fixture，8911 全程停止。

共享文件必须串行单 owner 修改并先跑 D01-D03 回归；任何 worker 不得复制 lifecycle、identity、Query 或 coverage 实现。

### 13.2 完成证据

- §12 全部 83 项挑战有确定性测试或明确映射到相邻已接受测试；
- D04 单元、投影、challenge matrix、N→N+1、identity/lineage、Query 及 count invariant 测试通过；
- 冻结 R2（D04 前基线 598）与 R3（基线 339）保持通过且零行为回归；R4 全量、D01-D03 相邻回归、candidate flag 严格读取/建立期强制 high/建立后 severity 断言与 not_evaluable 零 Query 用例全部通过；
- D05 尚未冻结的依赖仅以合成 producer stub 验证，不把 stub 计作 D05 接受；
- Ruff、compileall、公共导入/对象身份、确定性 payload/hash、8911 停止通过；
- 无项目名、真实受试者、固定阈值、固定表名/字段名、固定访视窗口或通用药物规则；
- 独立 fresh-context 医学/工程挑战接受，Codex 复核 hashes 与实际测试；
- 清理仅限本任务生成的 cache/临时文件，冻结合同、测试、审阅和关键运行证据保留。

## 14. 冻结记录

独立临床/方案 reviewer 与独立工程 reviewer 已在各自原会话接受同一语义快照 SHA-256 `4dce9df5e6416a7f8b8133af9b64cfb5dc8afd09c6949812d7e089204bf35baa`；该快照的最后阻断项为 D04 退出/终止参与中文标签一致性，关闭后两方均返回 `ACCEPT`。本次冻结只把状态由 draft 改为 `FROZEN_R4_D04_CONTRACT_V1_1` 并写入本记录，不改变 §1–§13 的合同语义。实现必须以冻结文件的最终 SHA 为输入，并继续满足 §13 完成证据。
