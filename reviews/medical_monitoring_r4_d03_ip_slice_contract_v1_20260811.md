# R4-D03 研究药暴露、依从性与医学处置关系切片合同 v1.1

日期：2026-08-11  
状态：`FROZEN_R4_D03_CONTRACT_V1_1`  
适用范围：医学监查 AI-native 隔离 R4-D03；仅合成/离线输入；不代表产品、真实项目、正式 PD 判断或临床结论就绪。

修订说明：初始 `FROZEN_R4_D03_CONTRACT_V1`（SHA-256 `859b9fd3…339c`）经独立合同挑战判定 `REVISE`。本版显式补齐 assignment/episode 绑定、实际给药日与治疗跨度、重叠区间、可执行依从性语义、回收缺失状态、计划/实际动作、盲态显示、跨域链接、Journey typed join 和 sibling coverage gap；初始版本保留在任务记录中作为已被替代的历史快照。

## 1. 目标与边界

本切片把版本化方案给药计划、随机/治疗角色、实际研究药暴露、发放回收、依从性算法以及 AE/实验室/检查/疗效触发的医学处置连接为可覆盖、可追溯、可增量重算的医学监查单元，形成：

- “研究药给药与方案不一致”“研究药依从性待核实”“给药调整依据待核实”等具体风险；
- 支持依据、排除依据、原始给药/发放/回收记录、方案条款及相关医学事件的一跳关联；
- “依据＋发现＋行动项”三段式 Query 草稿；
- 受试者医学旅程中的研究药区间、实际给药、发放、回收、暂停、减量、恢复和停药事件及风险锚点；
- N→N+1 的持续、补充记录后解决、规则/算法版本变化、暴露修订和身份歧义处理。

本切片不把 CM 当作研究药暴露，不从单次缺失记录推断漏服，不跨项目复用依从性阈值，不把任何减量/暂停自动判为 PD，不正式报送 PD，不调用真实项目、真实 provider 或产品服务。

## 2. 来源权威与复用决定

1. 上游权威为 `FROZEN_R4_CONTRACT_V1` 共同合同与 D03 行，以及已接受的 R1 coverage、R2 source/identity/lifecycle、R3 mapping/rule/knowledge 和 R4 中性域结果协议。
2. accepted EX/EC/DA/IP listing 说明“记录了什么”；active protocol、随机/治疗分组及适用版本说明“计划是什么”；版本化依从性算法说明“如何计算”；AE/实验室/检查/疗效记录只说明相应医学事件和处置记录；模型只能提出待核实解释。
3. 不引入外部运行库、项目药名、固定给药阈值或通用依从性公式。计划、阈值、端点包含关系、允许调整及分子/分母定义均为版本化输入。
4. D03 复用 `CoverageLedger`、`EvaluationUnit`、公共 R2 identity/lifecycle、`RiskDomainUnitResult`、Query/journey join；不得复制第二套生命周期或弱化 linked-negative 关闭证明。
5. D03 只消费来源引用，不改写 D01/D02 风险；D03 产生的处置线索可作为后续 D04/D08 的只读跨域证据，但不是正式 PD。

## 3. 输入合同

### 3.1 listing 语义角色

| 类别 | 语义角色 | 规则 |
|---|---|---|
| 最小必需 | `ip_exposure`, `subject_identity`, `site_identity`, `temporal_anchor` | `ip_exposure` 是 EX/EC/DA/IP 等来源经 active mapping 接受后的中性角色，不依赖固定表名 |
| 计划/分组 | `randomization`, `planned_treatment`, `study_phase` | 仅在相应控制项适用时成为 required；缺失不得靠药名猜盲态分组 |
| 核算 | `ip_dispense`, `ip_return`, `ip_accountability` | 只有算法明确需要时纳入分子/分母；零行与未覆盖必须区分 |
| 医学处置 | `reported_ae`, `lab_finding`, `exam_finding`, `efficacy_assessment`, `ip_action_reason` | 只用于核对暂停/减量/恢复/停药依据和双向关系 |
| 边界 | `recorded_cm` | 仅用于证明该记录属于 CM 而非 IP；不得生成 D03 暴露 episode |

同一来源行被互斥映射为 `recorded_cm` 和 `ip_exposure` 时为 not_evaluable；只映射为 CM 的行生成零个 D03 单元。

### 3.2 版本化非 listing 输入

- `PlannedTreatmentAssignment`：稳定 `assignment_id`、受试者/中心、治疗角色 token、随机/队列/阶段、计划药物身份、剂量、单位、剂型、途径、频次、计划起止/周期、内容哈希、assignment lineage、盲态可显示标签及来源定位。不同阶段或角色必须使用不同 assignment；同一时间存在多个可适用 assignment 时不得按药名或日期猜选。
- `IPExposureEpisode`：稳定 episode key、明确 `assignment_id` 链接、受试者/中心、实际治疗角色和阶段及其确认状态、披露状态、实际药物身份、剂量、单位、途径、频次、给药区间/日期、来源语义（单次给药/连续日区间/治疗跨度）、原因及来源定位。缺失或互斥 assignment 链接为 not_evaluable；只有一个经版本化 mapping 明确唯一的 assignment 候选时才可确定性绑定。
- `ExposureOccurrence`：稳定 occurrence id、episode/assignment link、单次给药日期时间或经来源明确声明的连续给药区间、实际剂量/单位/途径/频次、source locator 和 accepted revision。它是“实际给药日/次数/剂量”的权威输入；episode 首末日期只是治疗跨度，不自动证明区间内每日给药。
- `ExposureAggregationPolicy`：版本、内容哈希、输入粒度、日期端点、同 locator/revision 去重、同角色同剂量区间 union、每日多次给药计数、不同角色/剂量重叠冲突、连续区间展开资格和单位换算规则。内核不得自行假设区间内每日用药。
- `ProtocolExposureRule`：规则 id/版本/内容哈希/条款定位、规则类型、适用治疗角色/阶段/时间窗、计划值、允许调整、触发条件、端点包含关系、命中时优先级和理由。
- `AdherenceAlgorithm`：算法 id/版本/内容哈希、`metric_kind(day_ratio|dose_count_ratio|amount_ratio|accountability_proxy)`、分子来源、分母来源、单位与版本化换算、窗口 id/起止及端点、计划暂停/补服/退药/周期调整处理、上下阈值及各自等号、计算精度、舍入模式与舍入顺序、零分母/缺失/重复 observation 策略。只允许结构化枚举，不执行自由表达式。
- `AdherenceObservation`：窗口内原始分子项、分母项、剂量/次数/天数/发放/回收值、单位、逐项 source locators、coverage 状态和 accepted revision；不得只保存最终百分比。多个 observation 只有在算法明确同一窗口的聚合键和去重策略时才可合并。
- `PlannedExposureAction` 与 `ActualIPAction`：稳定 action id、`pause|dose_reduce|dose_increase|resume|stop`、planned/actual 标志、assignment/episode link、开始/结束、动作前后剂量/单位、原因或允许条件、来源、确认状态。动作对依从性分母的影响只由 `AdherenceAlgorithm` 决定。
- `IPActionEvidence`：source role、稳定 source event key、subject/site、`linked_ip_episode_id`、relation type、期望/实际动作、事件时间窗、关系确认状态和 source locator。只有同 subject、同 site、精确 episode link、关系已确认且时间可比较的证据可用于 positive/negative。
- `D03PriorityPolicy`：非规则型风险的版本化优先级与理由；通用内核不得凭风险名称暗定等级。

### 3.3 盲态角色与披露边界

- 内部 `treatment_role_token`、actual treatment identity 与用户可见 `display_role_label` 分离保存；projection 只输出当前披露状态允许的中文标签。
- 盲态项目中，只要 assignment、角色 token、阶段和实际记录角色均由权威来源确认，可以在不暴露药物身份的前提下核对角色/阶段；产品身份被遮蔽不使该项自动 not_evaluable。
- 需要具体产品/剂量身份但该身份在当前披露范围不可用时，该控制项为 not_evaluable；不得从药名、包装或剂量猜分组。
- 随机信息缺失、角色未确认或互斥 assignment 并存时为 not_evaluable；不得在 Journey、Query 或日志中泄露未授权的实际治疗身份。

## 4. EvaluationUnit、expected-set 与身份

D03 `EvaluationUnit` 为：

```text
subject + confirmed treatment role + stable IP exposure episode
+ activated plan/rule/adherence/action control item + temporal window
+ protocol/randomization/mapping/algorithm lineage
```

每个 episode 按适用控制项独立展开：

1. `plan_actual:<rule_id>`：计划与实际剂量/单位/剂型/途径/频次/窗口；
2. `role_phase:<assignment_id>`：随机/治疗角色/研究阶段；
3. `adherence:<algorithm_id>:<window>`：一个明确算法和计算窗口；
4. `allowed_action:<rule_id>:<action>`：暂停/减量/恢复/停药及允许条件；
5. `medical_action:<rule_id>:<source_event_key>`：医学触发事件与实际处置关系；
6. `accountability:<algorithm_id>:<window>`：仅当方案把发放回收核算作为独立控制项时建立。

缺少治疗角色、episode identity 或适用规则时，不得把多个角色/阶段合并成一个总单元；建立相应 not_evaluable 单元并阻断域医学完整。episode 汇总只是只读视图，不得覆盖子单元 disposition。

assignment 与 episode 的绑定顺序固定为：

1. 优先使用 accepted source 中的稳定 assignment/episode link；
2. 无直接 link 时，只有 active mapping 明确规定且按 subject＋site＋role＋phase＋非歧义时间窗得到唯一 assignment，才可确定性派生；派生规则版本和输入 locator 必须进入 lineage；
3. 零个候选为 not_evaluable；两个或以上可行候选为 boundary（均有充分来源支持）或 not_evaluable（关键字段缺失/冲突），不得按药名、最近日期或输入顺序选择；
4. 重叠 assignment、阶段切换和角色冲突必须分别建立控制单元，不得用 episode 汇总状态掩盖。

八个哈希维度固定映射为：

```text
domain_id = D03_ip_exposure
scope_type = subject
scope_key = subject_ref
normalized_concept_or_rule_item =
  stable_ip_episode_key | treatment_role | control_item | signal_type
temporal_window = versioned exposure/control window descriptor
rule_or_knowledge_lineage = assignment | protocol | mapping | adherence algorithm lineage
unit_algorithm_version = d03_unit_v1
```

风险 `classifier/stable_core` 不得含 snapshot/revision、规则/算法版本或可修改自由文本；`scope/lineage_fingerprint` 必须包含 site、时间精度、治疗角色、阶段、assignment/rule/mapping/算法版本与哈希。版本变化导致不再命中时为 superseded/not_evaluable，不伪装为数据解决。

## 5. L1 医学评价合同

### 5.1 `positive` 六类主问题

1. `planned_actual_exposure_mismatch`：计划与实际剂量、单位、剂型、途径、频次或确定给药窗口明确不一致，且无适用允许条件。
2. `treatment_role_or_phase_mismatch`：实际暴露与已确认随机/治疗角色或适用阶段明确冲突；盲态显示只用可披露标签。
3. `adherence_out_of_range`：版本化算法、完整分子/分母、计算窗口与端点规则均可核实时，结果确定超出允许范围。
4. `unsupported_ip_action`：暂停、减量、恢复或停药明确发生，但与适用方案允许条件/已记录原因不一致。
5. `medical_trigger_action_inconsistent`：权威 AE/实验室/检查/疗效触发条件与已确认实际研究药处置在同一受试者、中心、episode 和可比较时间窗内明确冲突。
6. `ip_accountability_inconsistency`：发放、回收、记录给药和算法核算在完整来源与同一窗口内形成确定矛盾。

同一单元只有一个 primary subtype；不同控制项可共享来源但不能互相关闭。任何 positive 只表示“需核实”，不得显示为已确认 PD。

### 5.2 `negative`

仅在本单元的治疗角色、阶段、计划、实际、时间精度、active 条款、允许调整及所需 coverage 全部完整且相互一致时使用。依从性 negative 还必须有完整、可重算、单位一致的分子/分母及版本化算法。风险数为零、未发现记录或模型未提示不足以判 negative。

### 5.3 `boundary`

- 计算值恰在阈值或等号边界，但算法未定义包含关系；
- 部分日期可能跨给药/暂停/阶段/规则窗口；
- 导入期与治疗期、背景治疗与盲态研究药存在两个以上各有来源支持的可行角色解释；
- 允许暂停/补服/减量存在两个以上可行解释且不能唯一选择；
- 已确认发生回收且存在 accepted 回收记录，但回收量为部分值、范围值，或单位转换存在两个以上经版本化依据支持的可行结果。

关键输入只是缺失或冲突时为 not_evaluable，不得用 boundary 包装 coverage gap；二者并存时 not_evaluable 优先。

### 5.4 `not_evaluable`

- 不能区分 CM 与 IP，或治疗角色/阶段/assignment 冲突；
- 计划或实际剂量、单位、频次、关键日期、active 条款缺失；
- 依从性算法、分子、分母、单位、窗口、阈值或 coverage 不完整；
- 处置关系需要精确 episode/source link 但链接缺失或跨受试者/中心；
- 部分日期无法在共享精度上判断；
- 一个来源行缺失且不能证明该行本应存在。

发放/回收 coverage 的状态优先级固定如下：

| 来源状态 | 语义 |
|---|---|
| 所需表/角色未覆盖 | not_evaluable，不得当作零行 |
| 表已覆盖但算法必需字段不存在或 accepted 行字段为空 | not_evaluable |
| 方案/计划明确期望回收，但完整覆盖中没有可定位回收记录 | not_evaluable，并生成“研究药物核算信息待核实”数据缺口；不得推断未归还或未服药 |
| accepted 行明确记录回收量为 `0` 且单位有效 | 已知零值，进入算法；不等于缺失 |
| accepted 行确认回收发生但数量为范围/部分值或存在多个有依据的换算 | boundary |
| 方案明确当前窗口无需发放/回收 | not_applicable |

### 5.5 `not_applicable`

只在权威方案/设计证明某控制项在当前治疗角色、阶段或窗口明确不适用时使用。零行、未映射、无风险或文件缺失不是不适用。

## 6. 依从性与研究药核算 fail-closed 规则

1. 依从性结果必须可由原始值、版本化算法和单位重算；不得只接收自由文本百分比。
2. 算法必须显式定义分子、分母、窗口、暂停/补服/退回/漏记处理和端点包含关系。
3. 单位不一致时必须有版本化换算依据；否则 not_evaluable。
4. 单次给药记录缺失不等于漏服；只有完整期望单元、来源 coverage 与算法证明差额时才可 positive。
5. 发放－回收不自动等于已服；若方案算法允许该代理，必须保留代理口径及不确定性。
6. 计划暂停天数是否进入分母由算法决定；内核不硬编码。
7. 阈值等号按算法明确规则处理；未定义时 boundary。
8. 不跨项目、方案版本、队列或阶段复用阈值。

### 6.1 实际给药日、治疗跨度与重叠区间

- `exposure_span` 是 episode 首次至末次记录的时间跨度；`actual_exposure_days` 是 `ExposureOccurrence` 能证明存在给药的唯一日集合；二者分别保存和展示，绝不互换。
- 单次/短区间 occurrence 只贡献其明确日期；长区间只有来源语义明确表示区间内连续每日给药，且 aggregation policy 允许展开时，才按包含端点展开为日期集合。
- 同一天多次给药对“实际给药日”只计一天，对“给药次数/剂量”按明确 occurrence 分别计量；不能用 unique day 代替 dose count 或 amount。
- 先选择每个 stable source event 的 accepted revision，再按完整 locator 去重；snapshot/revision 不进入稳定 clinical identity，但决定当前 accepted row。
- 同 subject/site/assignment/role、相同剂量/单位/途径/频次且语义相同的重叠连续区间，可对 day-set 做 union；不得对区间长度求和。
- 不同角色、阶段、剂量、单位或来源语义的重叠不得静默 union。全日精度且存在版本化优先级规则时可在变化点拆分；两个可行解释均有依据时 boundary；关键字段缺失/冲突时 not_evaluable。
- 治疗跨度 28 天但仅有 D1、D15 两次 occurrence 时，实际给药日为 2；没有 occurrence 或连续给药语义时不得推导 28 天实际用药。

### 6.2 可执行依从性计算

依从性计算固定为：先按 accepted revision/聚合策略建立规范分子与分母项，再在原始精度上计算比值，最后按算法指定精度和舍入模式显示/比较。算法必须冻结：

```text
algorithm_id/version/hash
metric_kind
numerator_source + denominator_source
canonical_unit + conversion_lineage
window_id/start/end + endpoint inclusivity
lower/upper threshold + inclusivity
planned pause/rescue/makeup/return handling
calculation_precision + rounding_mode + compare_before_or_after_rounding
zero_denominator + missing_item + duplicate_item policy
```

- 默认 fail-closed：未声明的零分母、缺失项、重复项、单位冲突或窗口冲突均为 not_evaluable。
- `79.95` 是否因显示为 `80.0` 而合格必须由 `compare_before_or_after_rounding` 明确；内核不得选择。
- 阈值等号只有上下界 inclusivity 均明确时可判 positive/negative，否则 boundary。
- `accountability_proxy` 必须在用户投影中标注“按发放/回收核算”，不得显示成已证明的实际服药天数。

### 6.3 计划与实际动作

- planned 与 actual action 分别建模，按 stable action id、assignment、episode、动作类型和可比较时间窗精确匹配。
- 允许暂停/减量/恢复/停药只有在方案条款、适用阶段、前后剂量、原因和时间窗闭环一致时才可 negative；仅动作名称相同不足以排除风险。
- 计划暂停是否从依从性分母剔除、补服如何计入、恢复日是否包含，完全由 active `AdherenceAlgorithm` 决定。
- 动作重叠时，存在唯一版本化优先级才可确定性解析；否则 boundary/not_evaluable。实际 25 mg 不得因计划“允许减量至 50 mg”而自动视为允许。

## 7. 时间、阶段、调整与跨域关系

- 日期复用冻结部分日期语义，只在共享精度上比较；不得静默补日。
- episode 与 rule window 确定重叠才可据此 positive/negative；可能重叠为 boundary，无法比较为 not_evaluable。
- 暂停、减量、恢复、停药是不同动作，必须有动作起止、原因、实际剂量与 episode link；不得合并成“研究药处置”。
- 医学触发关系必须满足同一 subject、site、稳定 IP episode link、确认的关系和可比较时间窗；仅时间接近不能证明因果或应当处置。
- `IPActionEvidence` 的 verified link key 固定为 `source_role + stable_source_event_key + subject + site + linked_ip_episode_id + relation_type + relation_confirmation`；公共 `SourceLocator` 单独不足以证明身份关系。
- wrong subject、wrong site、wrong episode、仅 record id 相同、仅日期接近或 relation 未确认均不得形成 positive/negative，必须 not_evaluable 或作为不参与裁决的上下文。
- D01/D02/D07 来源作为支持/排除依据，不由 D03 改写其结论；共享 locator 不等于共享风险 identity。
- 多条相同来源以完整 locator 去重；同 stable event 的 revision 只保留当前 accepted row，同时保留历史 lineage。

## 8. 优先级、Query 与用户语言

优先级来自版本化规则/策略：关键随机或治疗角色冲突、严重医学触发处置冲突可为高；重要暴露/依从性/调整问题通常为中；影响有限但需澄清的问题可为低；依据不足为 unknown。not_evaluable 不显示成“未知风险等级”。

界面只使用医学监查中文：

| 工程 subtype | 用户标签 |
|---|---|
| `planned_actual_exposure_mismatch` | 研究药给药与方案不一致 |
| `treatment_role_or_phase_mismatch` | 治疗分组或阶段待核实 |
| `adherence_out_of_range` | 研究药依从性待核实 |
| `unsupported_ip_action` | 给药调整依据待核实 |
| `medical_trigger_action_inconsistent` | 给药处置与医学事件不一致 |
| `ip_accountability_inconsistency` | 研究药物核算待核实 |

不得显示“正式事实”“候选信号”“已建立风险”“只读投影”等研发语言。

Query 固定为三段：

- 依据：定位方案版本、条款、计划/算法/医学触发要求；
- 发现：定位受试者、时间窗、治疗角色和原始记录中的确定差异或待核实缺口；
- 行动项：请核实计划、实际记录、原因及相关数据；如属实，请确认是否构成方案偏离并按项目流程处理。

Query 不写“已构成 PD”，不要求医学监察员代替研究者补造临床事实。

## 9. Journey 投影与一跳追溯

D03 只提供 R5 可消费的 projection payload，不实现最终 UI。事件至少区分：研究药给药、发放、回收、暂停、减量、恢复、停药、AE、实验室检查、其他检查、疗效评估、访视；风险标记按六类用户标签区分，不得统一为“已记录事项”或“风险项”。

每个 IP journey event 使用 renderer-neutral discriminated schema，至少包含：

```text
event_id                         # 稳定 typed id，不含 snapshot/revision
event_kind                       # administration|dispense|return|pause|dose_reduce|dose_increase|resume|stop|ae|lab|exam|efficacy|visit
planned_or_actual                # planned|actual|context
episode_id / stable_ip_event_key / assignment_id
treatment_role_token / display_role_label / disclosure_state
start / end / date_precision / visit / phase
dose / unit / route / frequency
typed_refs                       # assignment|rule|algorithm|medical_event|source locator refs
source_locator_ids / uncertainty
```

风险 marker 至少包含：`marker_id/unit_id/risk_identity_id/subtype/audience_label/priority/anchor_kind/anchor_event_id_or_interval/typed_refs/source_locator_ids/query_id/uncertainty`。

`IPEventMarkerJoin` 固定保存 `event_id + marker_id + unit_id + risk_identity_id + join_reason + typed_ref_ids`。一个 marker 可关联多个有明确角色的 event，一个 event 可关联多个不同控制单元 marker；每一条边都必须由稳定 id 和 typed ref 校验。不得按文本、相近日期或 episode alone join。

点击事件或风险必须以稳定 id 校验后双向到原始 EX/EC/DA/IP、计划/随机、方案条款、依从性计算明细、相关医学事件和 Query；不得按文本或日期近似 join。

## 10. 增量与生命周期

- 新快照使用全量 accepted listing 重建 expected-set，不把上次结果当当前事实。
- 同 classifier＋同 scope 持续；同 stable core＋不同 lineage 为 superseded；互斥 identity 并存为 identity_ambiguous。
- 只有完整 coverage、相同风险 identity 的精确 linked-negative 才可 `resolved_by_data`。
- 补充原因/允许调整证明后可以关闭；仅缺失记录、算法变化或映射变化不得静默关闭。
- not_evaluable carry-forward 与显式 `terminate_not_evaluable` 分层。
- 同一 episode 的 sibling 单元独立进入 lifecycle：positive/boundary 不会吞掉 adherence/accountability 的 not_evaluable coverage gap。episode rollup 必须同时保留 `has_positive/has_boundary/has_not_evaluable`，其中任一 not_evaluable 阻断域完整性，但不得关闭或降级另一个已建立风险；风险生命周期仍按各自 identity 处理。

## 11. 最小合成验收矩阵

必须至少覆盖：

1. 六类 positive 各一例及对应 negative；
2. 阈值等号、窗口端点、部分日期、允许暂停/补服/减量、背景治疗/盲态研究药 boundary；
3. 缺算法、缺分母、单位冲突、角色冲突、CM/IP 互斥、单条缺失不得推断漏服；
4. 治疗跨度≠实际给药日、稀疏给药、每日多次、连续日区间、同角色重叠 union、不同剂量/角色重叠不得静默合并；
5. cross-subject、cross-site、wrong episode link、未确认关系不得形成处置 positive；
6. 重叠 assignment、缺失/歧义 assignment link、盲态匹配/冲突/遮蔽/显示不得泄露实际身份；
7. `ip_return` 未覆盖、零行、字段空、明确零值、部分值和不适用的 disposition 决策表；
8. planned/actual 暂停、减量、恢复、停药及动作重叠、分母影响和 50 mg/25 mg 不一致；
9. 阈值相等、79.95 舍入、零分母、重复 observation、单位换算和窗口端点；
10. 重复行、revision、乱序输入、同 locator 去重和 byte-deterministic projection；
11. N→N+1 持续、linked-negative 关闭、规则/算法版本 supersede、identity ambiguity，以及 positive＋not_evaluable sibling 并存；
12. Query 三段式、用户中文标签、typed event/risk/join 及原始来源一跳；
13. D01/D02 不回归，R2/R3 冻结包不回归，8911 保持停止。

## 12. 明确不声明

本合同和后续合成纵切不声明真实研究药数据可用、真实依从性算法正确接入、医学结论准确、正式 PD 判定、产品 UI 完成、真实模型编排完成、R4 总体完成或系统生产就绪。
