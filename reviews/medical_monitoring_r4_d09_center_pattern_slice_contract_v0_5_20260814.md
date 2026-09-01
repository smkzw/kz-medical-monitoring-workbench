# R4-D09 中心重复模式与系统性风险合同 v0.5

> 状态：`FINAL_SELF_CONTAINED_FREEZE_CANDIDATE`  
> 日期：2026-08-14  
> 范围：仅离线、合成、typed contract；不得据此宣称产品界面、真实项目或临床结论已完成。  
> 硬边界：8911 保持停止；不触碰医学写作子系统；不使用真实项目/患者数据；本阶段不做安全性设计或测试。

## 1. 目的与用户语义

D09 将 D01-D08 已接受的受试者级风险与覆盖信息，转化为可解释、可展开、可复现的**单中心重复模式和系统性问题**。面向资深医学监察员时，界面只说自然中文，例如“AE 漏报在 4/18 名可评价受试者中重复出现”“该中心检验结果临床意义字段在 9/42 次应记录机会中缺失”；不得暴露 `typed handoff`、`candidate`、`正式事实`、`只读`、内部枚举或运行日志。

D09 必须同时避免两种相反错误：

1. 把一个高风险个例误升格为中心系统性问题；
2. 用低比例、均值或小样本提示隐藏一个高风险个例。

因此，中心模式评价与热点受试者展示正交：单例不证明系统性，但始终保留一跳到个体风险、Patient Journey、Profile/Timeline 和原始来源的入口。

## 2. Owner 边界

| 层级 | Owner | D09 可做 | D09 禁止 |
|---|---|---|---|
| D01-D08 受试者风险 | 各原域 | 消费 accepted/current typed public objects；引用成员风险 | 重算医学事实、修改个体 disposition/优先级/lifecycle、复制个体 Query |
| D09 单中心模式 | D09 | 评价同一中心内跨受试者重复、系统性数据/流程缺口、同中心历时变化；生成中心模式风险与非冗余 Query 草稿 | 形成跨中心排名、项目总体结论、治疗组比较、疗效 estimand 或正式安全结论 |
| D10 项目聚合 | D10 | 消费 D09 已验证的中心模式、分母、coverage、lineage | D09 代替 D10 计算项目/跨中心统计推断 |
| R2 lifecycle | R2 | D09 创建中心模式 RiskInstance 后交由 R2 管理状态 | D09 自建第二套生命周期状态机 |
| R5 投影 | R5 | 展示热图、趋势、热点受试者、分子/分母/coverage 和深链 | 黑箱综合评分、红黑榜、惩罚性排名、混算中心模式与个体风险 |

对 D06 合同采用**消费边界澄清而非原合同改写**：D06 仍不得自行形成中心/项目/治疗组聚合；D09 只可在 `d09_repeated_subject_risk` 或 `d09_systematic_data_or_process_gap` 下引用 D06 个体风险/缺口作为成员，且不得输出中心疗效率、应答率、均值变化、estimand 或治疗组比较；D10 仍唯一负责疗效/安全性的中心间比较和项目级推断。既有 D06 医学语义不变。冻结前的 owner-QC 门必须核实所有 required producers 是否已输出 D09 需要的 accepted public risk、gap、obligation/opportunity 和 lineage refs；任何缺口须以独立 additive addendum 闭合，不得由 D09 读取原始 listing 补算。

### 2.1 `D09OwnerRoutingDecision`

```text
clinical_claim_token =
  d09_repeated_subject_risk |
  d09_systematic_data_or_process_gap |
  d09_within_site_time_trend |
  d06_site_efficacy_rate | d06_estimand |
  d10_cross_site_outlier | d10_treatment_arm_compare | d10_project_trend |
  d01_d08_individual_fact | unresolved

d09_action = evaluate_and_own | consume_only | handoff_only | context_only | routing_gate
```

仅前三个 token 可 `evaluate_and_own`。其余 token 必须路由到原 owner；`unresolved` 产生 routing gate 和零个医学 unit。

## 3. 闭集模式与适用性目录

### 3.1 医学 expected-set 的三个 `D09PatternKind`

1. `repeated_subject_risk`：同一中心内，同一版本化 pattern definition 命中的已接受个体风险跨受试者重复。
2. `systematic_data_or_process_gap`：同一中心内，同一字段、记录义务或流程缺口跨受试者/机会重复；映射或导出问题只能先作为反证或完整性门处理。
3. `within_site_time_trend`：同一中心、同一可比层内，在两个或以上已闭合分析窗之间的风险绝对量、分母率或暴露调整率变化。

`hotspot_subject`、`routing_gate`、`coverage_gate`、`integrity_gate` 均不是医学 pattern kind：前者是投影，后三者是阻断对象。D08 跨域关系风险可以作为 `repeated_subject_risk` 的成员输入；D09 不另设“跨域聚类”以免重做 D08。

若 current D01-D08 风险实例已满足成员谓词，路由 token 为 `d09_repeated_subject_risk`、pattern kind 为 `repeated_subject_risk`；若问题只存在于已接受的义务/机会缺口且没有个体 RiskInstance，路由 token 为 `d09_systematic_data_or_process_gap`、pattern kind 为 `systematic_data_or_process_gap`；历时模式的 token/kind 双射为 `d09_within_site_time_trend` ↔ `within_site_time_trend`。只允许这三组双射，其他组合 authority fail closed。两类 definition 同时存在时必须具有互斥成员谓词；同一个缺口只能有一个 owning definition。

### 3.2 `D09PatternDefinition`

每个项目 + ModeContract + version 冻结一组适用定义：

```text
D09PatternDefinition
  pattern_definition_id
  pattern_kind
  clinical_label_zh
  risk_domain
  clinical_claim_token
  d09_action
  required_producer_domains[]
  accepted_member_risk_kinds[]
  numerator_contract_id
  allowed_denominator_kinds[]
  window_contract_id
  stratum_contract_id
  comparability_contract_id
  positive_rule_ref
  counterevidence_rule_refs[]
  monitoring_priority_rule_ref
  center_query_policy_id
  minimum_member_subject_count_ref?
  opportunity_contract_id?
  authority_version / content_hash / effective_interval
```

公共合同不写死样本量、比例、随访、暴露或统计阈值。所有数值与临床规则来自版本化 definition/ModeContract，并可追溯到方案、IB、项目规则或明确的方法依据。

`D09LegalDefinitionMatrix` 是 compile-time authority，不允许开集组合。每个合法行精确声明 `pattern_kind/clinical_claim_token/d09_action/allowed_risk_domains/allowed_member_object_kinds/allowed_measure_contracts/allowed_comparison_references`。三种 ownable token 只能聚合 accepted 个体风险、accepted gap/obligation 或既有 D09 窗口账本；明确禁止 `site_efficacy_rate/responder_rate/mean_change/estimand/treatment_arm_compare/cross_site_outlier/project_trend` 作为 D09 owned member/measure/positive rule。definition 不在 legal matrix、字段开集、risk domain 与成员对象不相容或 positive rule 试图读取上述禁用量时，authority fail closed、零医学 unit。

### 3.3 `D09ExpectedSetAdmission`

医学 expected-set 只由以下集合构造：

```text
applicable pattern_definition_id
× admitted site_stable_id
× admitted analysis_window_stable_id
× admitted stratum cell
```

不得再自由迭代 `pattern_kind × risk_domain × definition`。kind/domain 是 definition 属性，必须与 unit envelope 一致。空 stratum cell 默认不产生 unit，除非 definition 明确要求。`within_site_time_trend` 在至少两个已闭合且可比的窗口存在前不进入医学 expected-set，而生成一个 `window_pair_gate`；这不是省略或“趋势正常”。不完整中心不得从 expected-set 静默消失：全局身份/authority admission 失败时留完整性 gate；已 admission 后的单元缺口必须形成 L1 `not_evaluable`。

```text
D09WindowPairGate
  gate_id / site_ref / pattern_definition_id / stratum_key
  available_window_instance_refs[]
  required_window_count_ref
  pair_state = insufficient_windows | incomparable_windows | ready
  reason_codes[] / evidence_refs[]
  expected_leaf = control_plane_window_pair_gate
  permitted_output = gate_only | admit_trend_unit
```

`insufficient_windows/incomparable_windows` 不创建 trend 医学 unit、风险或 Query，但必须出现在 control-plane expected gate set 与 oracle leaf 中，不能被静默省略。

## 4. Typed 输入与消费适配器

D09 不要求回改已冻结的 D01-D08 合同。由 D09-owned、纯确定性适配器将 accepted/current 公共对象封装为：

```text
D09InboundSubjectEnvelope
  envelope_id
  project_ref / run_ref / snapshot_ref / source_revision_set
  site_stable_id / subject_stable_id / scope_binding_id
  producer_domain / producer_contract_version
  producer_object_refs[] / producer_content_hashes[]
  accepted_current_state
  domain_coverage_ref / domain_coverage_state
  public_risk_refs[]
  accepted_gap_or_obligation_refs[]
  query_draft_refs[]
  event_time_refs[] / cutoff_relations[]
  source_locator_refs[]
  lineage_refs[]

D09InboundRiskMember
  public_r4_risk_identity
  source_event_identity
  subject_stable_id / site_stable_id
  producer_domain / risk_kind / monitoring_priority
  event_time_ref / cutoff_relation
  source_locator_refs[]
  query_draft_refs[]

D09InboundGapMember
  gap_opportunity_id
  gap_definition_id / owning_pattern_definition_id
  normalized_field_or_process_identity
  accepted_producer_object_ref
  producer_domain / gap_kind
  subject_stable_id / site_stable_id
  obligation_or_opportunity_ref
  visit_or_time_anchor_refs[]
  source_locator_refs[]

D09ChangeLedgerMember
  change_ledger_member_id
  owning_pattern_definition_id
  current_window_instance_ref / prior_window_instance_ref
  current_measure_ledger_ref / prior_measure_ledger_ref
  comparable_state = comparable | boundary | not_evaluable
  change_kind = increased | decreased | unchanged | not_comparable
  absolute_delta / rate_delta? / unit
  change_cause = data | denominator | coverage | rule_or_mapping | method | mixed
  supporting_member_refs[] / visit_or_time_anchor_refs[] / source_locator_refs[]
```

适配器只复制 typed identities/refs，不从中文标题、风险文本、`evidence_ref_id` 或模型摘要推断/合并身份。共享 `evidence_ref_id` 只允许形成展示簇；除非存在 D08-verified same-origin binding，两个 public risk identities 始终是两个成员。机会/义务必须解析为 accepted、版本化的 D05 计划对象、共享计划对象或 producer 域义务对象；D09 不得从原始 listing 行重数机会。任一 producer object 无法反向解析、不是 accepted/current、哈希不符或 scope 不一致，则对应 pattern 进入完整性阻断，不得继续计算。

## 5. 身份、去重与确定性

### 5.1 稳定核心与版本化单位

```text
D09UnitStableCore = (
  project_id,
  site_stable_id,
  pattern_definition_id,
  analysis_window_stable_id,
  stratum_contract_id,
  stratum_key
)

D09WindowInstanceIdentity = hash(
  analysis_window_stable_id,
  computed_window_start,
  computed_window_end,
  cutoff_id,
  scope_binding_stable_id
)

D09EvaluationContentIdentity = hash(
  D09UnitStableCore,
  D09WindowInstanceIdentity,
  sorted(source_revision_set),
  sorted(source_content_hashes),
  mode_contract_version,
  pattern_definition_content_hash,
  window_definition_content_hash,
  stratum_contract_content_hash,
  legal_definition_matrix_content_hash,
  numeric_execution_policy_content_hash,
  algorithm_version="d09_v1"
)
```

稳定核心是跨 run/R2 连续性的 revision-free 语义键，不含 run ID、快照 ID、计算日期、mtime、进程 ID、数组顺序或显示文案。实际窗口实例、cutoff、source revisions/content hashes 及全部决定性 authority/method hashes 进入 `D09EvaluationContentIdentity`，使滚动窗口实例可区分，而相同不可变内容在新 run 重放仍得到同一 content identity。run_id/snapshot_ref 只进入 envelope/audit。数据修订或 cutoff 推进保持 stable core，通过 `continued_from_data_revision` 或 `continued_from_cutoff_advance` 连接；legal matrix、numeric policy、规则、mapping、窗口定义、分层或算法语义变化以 `superseded_by_rule_or_method_change` 连接，禁止伪装为 `resolved_by_data`。

`pattern_kind` 与 `risk_domain` 仅为 definition 属性，不是可自由组合的身份轴；kernel 必须拒绝属性、claim token 与 definition 不一致的 envelope。`analysis_window_stable_id=(window_kind, window_definition_id, inclusivity, anchor_kind)`；实际计算出的 start/end 只进入 run envelope，滚动窗口端点变化不得伪装为方法变化。

D09 public stable identity 明确使用：`project_ref / domain_id=D09 / scope_type=site / site_stable_id / stable_source_or_event_identity=(pattern_definition_id, analysis_window_stable_id, stratum_key) / normalized_concept=(pattern_kind, pattern_definition_id) / temporal_window=(window_kind, window_definition_id) / public_identity_version=d09_public_v1 / scope_binding_id` 的 canonical tuple/hash，且永不与 D01-D08 public identity 合并。evaluation unit id、source revision、实际端点、cutoff 和 rule lineage 不进入 public stable hash，而进入 versioned envelope；规则语义变化由 supersession 明确连接旧、新 public identity version envelope。

### 5.2 成员身份与防多计

同一 pattern unit 的成员按 `(public_r4_risk_identity | gap_opportunity_id | change_ledger_member_id, subject_stable_id)` 去重；受影响人数按唯一 `subject_stable_id` 计数，事件数按 `source_event_identity` 去重并单列。跨域声称同源时，只接受 D08 已验证的关系身份或上游 typed same-origin binding。无法确认同源时：

- 不静默合并；
- `dedup_state=ambiguous`；
- pattern unit 为 `boundary`，若歧义影响是否适用、分母或完整性则为 `not_evaluable`；
- 投影明确显示“部分记录关系待确认”，不显示虚假精确率。

输入、成员、分母、证据和输出都使用 canonical Unicode、闭集枚举、排序后的稳定身份数组及内容哈希；重排输入、重复导出同一 revision 或改变显示名不得改变结果。

`D09OriginDecision.status` 闭集为 `verified_same_origin/distinct/ambiguous/wrong_scope/not_evaluable`。同一风险的多个 revision 只计一个成员，revision 只进入 lineage envelope。

## 6. 分子、分母、coverage 与机会量

### 6.1 `D09MeasureLedger`

```text
D09MeasureLedger
  unit_id
  numerator_subject_refs[]
  numerator_subject_count
  numerator_event_refs[]
  numerator_event_count
  numerator_gap_opportunity_refs[]
  numerator_gap_opportunity_count
  denominator_kind
  denominator_member_refs[]
  denominator_eligibility_rule_ref
  denominator_excluded_member_refs[] / exclusion_reason_codes[]
  denominator_value
  denominator_unit
  denominator_state = closed_positive | closed_zero | unclosed
  opportunity_definition_ref
  expected_opportunity_refs[]
  expected_opportunity_count
  observed_opportunity_refs[]
  observed_opportunity_count
  missing_opportunity_refs[]
  opportunity_value / opportunity_unit
  opportunity_state = sufficient | insufficient | unknown
  subject_time / exposure_time? / unit
  dedup_state = verified | ambiguous
  coverage_contract_id / coverage_refs[]
  coverage_state = complete | partial | truncated | missing | failed | not_evaluable
  required_domain_medical_completeness_refs[]
  cutoff_contract_id / window_contract_id / stratum_contract_id
  source_revision_set / ledger_hash
  numeric_execution_policy_ref
```

允许分母闭集：`enrolled_subjects`、`treated_subjects`、`evaluable_subjects`、`subject_time`、`exposure_time`、`expected_assessment_opportunities`。每个 pattern definition 只能选择其声明的子集；不得在运行时自动换分母。

分母成员由 ModeContract 的适用范围独立生成，不以是否得到 L1 或风险作为进入条件。required producer 的 L1 `not_evaluable` 是 coverage/机会缺口，不是零风险观察，也不得从分母静默删除。趋势窗口必须使用相同 denominator kind、stratum contract 和数值执行策略；否则不可比。

`D09NumericExecutionPolicy` 冻结时间单位、暴露单位、率的分子/分母配对、scale、rounding mode、missing/zero 处理和显示精度。subject-time/exposure-time 必须保存每个成员的起止锚点、可计时段、排除区间、单位换算和总和；禁止只有汇总值而无成员构成。任何 rate 必须能由 ledger 字节级复算。

### 6.2 各模式计量

- `repeated_subject_risk`：主分子为至少命中一次定义的去重受试者数；事件数另列。分母通常为可评价/治疗受试者或 subject/exposure time。
- `systematic_data_or_process_gap`：同时列受影响受试者数和缺口机会数；主分母为可评价受试者或预期记录/评估机会；成员必须来自 accepted gap/obligation 对象，不要求伪造 D01-D08 RiskInstance。
- `within_site_time_trend`：每窗使用完全相同的分母合同、分层和方法；至少两个闭合窗口。日历计数不得替代 subject-time/exposure-time 率。

### 6.3 negative 与零事件门

只有以下全部成立才允许 `negative`：中心身份、适用范围、required producer domains 的 L0 coverage 与该中心该域 L1 医学完整性、分母成员、机会定义、cutoff、窗口、来源版本、分层和 QC 均闭合，`opportunity_state=sufficient`，且规则已完整运行并留下排除依据。required producer L0 complete 但 L1 含 `not_evaluable` 时不得按零成员走 negative。`risk_count=0`、空表、未命中、未运行、空分母或导出缺列均不能直接形成 negative。

`denominator_state=closed_zero` 默认 `not_evaluable`；只有 ModeContract 以可定位的设计条款证明该模式在该阶段不适用时才是 `not_applicable`。

`opportunity_state=insufficient` 按 ModeContract 映射为 boundary/not_evaluable；`unknown` 为 not_evaluable。非 required 域缺口不连坐。

## 7. Cutoff、分析窗、分层与可比性

### 7.1 Cutoff

复用共享 cutoff 语义：`in_cutoff`、`out_of_cutoff`、`spans_cutoff`、`time_missing_not_evaluable`，并区分 `snapshot_as_of` 与 `clinical_event_cutoff`。修订时间晚于 cutoff 不等于临床事件 out-of-cutoff。

- 全体成员 out-of-cutoff：不进入该窗医学分子，但保留可解释上下文；
- 同一候选跨 cutoff：生成独立 cutoff boundary gate，不伪造医学单位；
- 关键时间缺失：not_evaluable；
- cutoff 身份或策略冲突：在所有医学计算之前 fail closed。

### 7.2 `D09WindowContract`

```text
window_kind = calendar_interval | study_day_interval | subject_time_interval | exposure_time_interval
anchor_kind = calendar_date | site_activation | consent | randomization | first_dose | domain_event
inclusivity
minimum_observation_requirement_ref
late_activation_policy
content_hash / effective_interval
```

计算日期只进入运行 envelope。晚启动中心、短暴露或短随访不得与完整窗口直接比较；不足时为 boundary/not_evaluable，且不得给 negative。

`window_start/window_end` 只存在于 `D09RunWindowEnvelope`，不属于 `D09WindowContract`，也不进入 window definition content hash；hash 只覆盖稳定定义。趋势 envelope 使用当前 window stable id，并带 `prior_window_ref`。跨窗 rule/method/stratum 版本不同或中心身份发生合并/拆分时，不得显示虚假改善/恶化，而应 not_evaluable/boundary 或拆分 superseded lineage。

### 7.3 `D09ComparabilityContract`

```text
allowed_stratum_keys[]
required_case_mix_covariates[]
minimum_denominator_ref / minimum_followup_ref / minimum_exposure_ref
comparison_reference_kind = self_prior_window | protocol_expected | validated_external_baseline
method_id / method_validity_preconditions[]
authority_locator / validity_interval / method_boundary
counterevidence_rules[]
```

D09 仅在单中心内部进行历时比较，或使用预先冻结的方案/外部参考；不使用运行中其他中心分布直接生成 D09 医学结论。跨中心统计、中心构成调整和项目级异常由 D10 负责。R5 可以并列展示各中心已完成的 D09 units，但不得将排列解释为排名。

盲态项目禁止把可能揭盲的治疗组/治疗角色作为 D09 分层键；仅在项目明确允许且当前用户/运行作用域为合法非盲分析时，才可使用已冻结的非盲分层合同。

病例组合、暴露、随访、启动时间或项目数据收集变更若足以解释差异，作为 L1b 反证降为 negative/boundary；不得删除底层个体风险。统计/规则信号只是证据，只有方法有效性前提满足且可展开到成员来源时才可支持 positive。

`D09StatisticalSignal` 仅为 L1b evidence：`method_id/method_preconditions_state/reference_kind/observed_value/reference_value/uncertainty/member_expansion_refs[]/authority_locator`。任何 p-value、z 值、KRI、模型分数或排序都不得直接设置 L1；无法展开到成员来源时不得支持 positive。

`D09VisibilityDecision` 分离 `evaluation_member_set` 与 `projectable_member_set` 并记录 `hidden_member_count`。计算可使用合法 evaluation set；受众只看可投影成员。存在隐藏成员时不得显示分子或分母一侧混入隐藏成员的误导性精确率，必须显示 visible_n、eligible_n、hidden_member_count 与 coverage 提示，或不显示该率。R5 多中心并列默认按稳定中心身份排序，不按风险率排序。

## 8. 完整性优先顺序

### 8.1 两层 typed gate

```text
D09GlobalAdmissionGate
  gate_id / gate_kind
  project_run_snapshot_cutoff_refs
  authority_and_legal_matrix_refs
  site_identity_state / expected_set_generator_state
  failure_codes[] / source_locator_refs[]
  permitted_output = integrity_gate_only

D09UnitCompletenessDecision
  unit_stable_core / evaluation_unit_id
  required_producer_domains[]
  per_domain_l0_state[]
  per_domain_expected_l1_count[]
  per_domain_l1_not_evaluable_count[]
  denominator_state / opportunity_state / window_state / source_state
  completeness_state = complete | not_evaluable
  reason_codes[] / evidence_refs[]
```

Global run/project/site identity、authority/legal matrix 或 expected-set generator 失败时，只输出 `D09GlobalAdmissionGate`，零个医学 unit。全局 admission 已通过后，某个已 admission unit 的 required-domain/分母/机会/窗口缺口必须输出该 unit 的 L1 `not_evaluable`，并计入守恒；两条路径不可互换。

每个 expected unit 严格按下列顺序处理：若在医学 expected-set admission **之前**触发 `D09GlobalAdmissionGate`，不得产生医学 disposition、风险或 Query；若全局 admission 已通过、某个已 admission unit 在下列第 4-6 项失败，则必须产生该 unit 的 L1 `not_evaluable`，不得继续产生风险或 Query：

1. run/project/snapshot/source revision/cutoff 身份；
2. site/subject/shared-spine scope 身份；
3. ModeContract、pattern/window/stratum/comparability authority 与内容哈希；
4. required producer domain 的 L0 coverage、该中心该域 L1 医学完整性与 accepted/current 状态；非 required 域不连坐；
5. producer refs、内容哈希、source locator 与反向解析；
6. 分母成员、机会定义、分子成员与 origin/dedup；
7. expected-set completeness、唯一性与 canonical order；
8. 医学规则、反证和 disposition；
9. 风险、Query、Journey/R5 投影。

完整性 gate 只产生 typed gap，不进入医学 expected-set，也不增加“风险数”。

## 9. 五类 L1 disposition

| Disposition | D09 条件 |
|---|---|
| `positive` | 适用；全部完整性/coverage/分母/方法门通过；满足下述 kind-specific 前件；反证不足以解释 |
| `negative` | 全部门闭合；检查完整；未命中，或反证充分解释中心模式；零事件本身不够 |
| `boundary` | 小样本、短暴露/随访、晚启动、孤立高风险个例、同源去重歧义、信号存在但系统性证据或可比性不足 |
| `not_applicable` | ModeContract/设计条款明确证明该模式 × 域 × 阶段 × 窗口不适用；必须有 locator 与适用区间 |
| `not_evaluable` | 身份、required coverage、分母、机会量、cutoff、时间窗、版本或方法有效性前提不足/冲突 |

不变量：每个 expected unit 恰好一个 disposition；`expected = positive + negative + boundary + not_applicable + not_evaluable`。每个 positive 至少一个 current member risk、accepted gap member 或 change-ledger member，并具有可解析来源；negative 不产生 clue/risk/query。

Kind-specific 前件：

- `repeated_subject_risk`：至少一个 current member risk、来源可展开，且满足 ModeContract 的 `minimum_member_subject_count`；“重复”的最小人数不得低于 2。仅一名受试者时强制 boundary + hotspot，不得 positive；字段缺失/非法时 authority fail closed、零医学输出。
- `systematic_data_or_process_gap`：accepted、可定位的 gap members 与闭合 opportunity ledger；不要求 D01-D08 RiskInstance。
- `within_site_time_trend`：至少两个闭合可比窗口和可展开 change ledger。

boundary 可持有 D09 clue；仅 positive 创建 D09 RiskInstance；negative 不创建。

## 10. 中心模式风险与计数隔离

D09 positive 创建独立 `RiskInstance(kind=center_pattern, aggregation_level=site_pattern, owner=D09)`，其 public stable identity 使用 D09 unit stable core。它只引用本 unit 成员（current risk、accepted gap/obligation 或 change-ledger member），不复制、合并或改变 D01-D08 个体风险和来源对象。

```text
D09R2RiskHandoff
  handoff_id = hash(public_d09_risk_identity, evaluation_content_identity,
                    action, prior_risk_instance_ref_or_none)
  idempotency_key = handoff_id
  public_d09_risk_identity / stable_core_ref
  current_evaluation_content_ref / run_snapshot_audit_refs[]
  prior_risk_instance_ref
  action = create | continue | update | propose_close | reopen | supersede
  lineage_relation = first_seen | continued_from_data_revision |
                     continued_from_cutoff_advance | superseded_by_rule_or_method_change
  pattern_definition_hash / mode_contract_version
  member_refs[] / measure_ledger_ref / completeness_decision_ref
  monitoring_priority / no_auto_close_reasons[]
```

同一 immutable source revisions/content hashes、cutoff、窗口实例和 authority/method hashes 即使由不同 run/snapshot opaque IDs 重放，也产生同一 evaluation content identity 与 handoff idempotency key，R2 必须 no-op。`prior_risk_instance_ref` 仅 `action=create` 时允许显式 `none`；continue/update/propose_close/reopen/supersede 时必填且必须解析为同一 public stable identity 的 current R2 instance，否则 fail closed。R2 只按 idempotency key 应用一次。gap-only positive 的 `individual_risk_count=0`，但 `affected_subject_count/numerator_gap_opportunity_count/center_pattern_count` 可为正。所有计数必须携带 `evaluation_window_instance_ref`；R5 折叠视图另有 `fold_contract_id`，折叠值不得回写原窗 ledger 或 R2 risk。

计数必须分层显示：

- `individual_risk_count`：D01-D08 成员风险数；
- `affected_subject_count`：分子受试者数；
- `event_count`：去重事件数；
- `center_pattern_count`：D09 中心模式数。

禁止把上述四项相加成“总风险数”。D09 风险交由 R2 lifecycle；规则/方法变化走 supersession，数据修订才可形成新增、持续、关闭或重开。

中心模式关闭必须证明：当前 accepted snapshot、同一 pattern definition hash、完整 required L0/L1 coverage 下，该模式已不再命中。成员风险个体关闭不等于中心模式关闭。本次 run not_evaluable、admission gate 或 coverage 退化不得关闭既往 D09 RiskInstance，而应 carry-forward 并显示缺口。高监察优先级、曾由用户确认/升级或成员涉及 SAE/AESI 的中心模式不得机器自动关闭，只能经 R2 adjudication。

`D09ProjectionCountSurface` 还必须分别保留 `clue_count/query_count`；六项计数任意混加均为 integrity failure，Query 数永不当作风险数。多窗口同模式在 R5 默认按 pattern kind × risk domain 折叠，窗口可展开，避免二次聚合误导。

## 11. 热点受试者与证据展开

`D09HotspotProjection` 不是 L1 unit 或 RiskInstance，其 exact fields 为：`projection_id/site_ref/evaluation_window_instance_ref/subject_ref/member_risk_refs[]/gap_member_refs[]/monitoring_priority/priority_rule_ref/visit_or_time_anchor_refs[]/source_locator_refs[]/projectability_decision_ref`。它按已冻结优先级规则列出中心内高风险或多域受试者。任何 negative/小样本/中心低比例均不得隐藏高风险成员。

`D09VisibilityDecision` exact fields：`audience_scope_id/blind_status/authorized_unblinded_contract_ref?/evaluation_member_refs[]/projectable_member_refs[]/hidden_member_refs[]/hidden_reason_codes[]/visible_n/eligible_n/rate_projection_state=permitted|suppressed|qualified`。不得通过受试者排序、缺口数量、分母差或 tooltip 暴露隐藏组别/角色；隐藏与可见成员混在同一率时必须 suppress/qualified。

一跳链路必须可验证：

`中心模式 → 分子/分母清单 → 受试者风险或义务/机会/change-ledger 对象 → Patient Journey 的对应访视/时间窗 → Profile/Timeline → 原始 listing 行/单元格、方案/IB 条款、已有 Query`。

无 locator 时显示“来源暂无法定位”，不得构造虚假跳转。

`D09DeepLinkTarget` 必须保存 project/run/snapshot/site/subject、evaluation window instance、visit/time anchor、member object ref、source locator 与返回状态键；gap/trend 成员不能只有中心级汇总而无可定位锚点。

## 12. 中心级三段式 Query 草稿

仅当以下条件全部满足时，每个 positive pattern unit 最多生成一条 D09 Query 草稿：

1. 模式提供了个体 Query 之外的中心流程级、系统性可行动信息；
2. 分子可绑定到有限的受试者/记录/字段清单；
3. 未被已有个体 Query 完整覆盖；
4. `query_owner=D09`，且 basis/finding/action 全部可追溯。

`D09QueryRedundancyDecision=site_process_delta_present|fully_covered_by_member_queries|members_unlistable|not_applicable`。仅 `site_process_delta_present` 可生成 Query，且成员数不得超过 ModeContract 的 `max_query_member_fanout`；超限只展示，不截断清单。

`D09CenterQueryPolicy` exact fields：`policy_id/mode_contract_version/max_query_member_fanout/member_order_policy/redundancy_rule_ref/allowed_action_kinds[]/pd_wording_rule_ref/content_hash/effective_interval`。运行时不得提供默认 fanout 或改写成员顺序。

该 decision 必须携带 `unit_member_set_hash/covered_member_refs[]/uncovered_member_refs[]/member_query_refs[]/coverage_proof_hash`；只有 uncovered set 非空且存在中心流程级 delta 才能生成中心 Query。任何“已完整覆盖”必须由集合全等证明，不得由文本相似度或模型判断。

固定三分句：

- **依据**：模式定义、方案/项目规则、时间窗与版本；
- **发现**：中心、受影响人数、事件/机会数、明确分母、coverage、有限记录清单及来源版本；
- **行动项**：要求核实具体记录、字段或判定。涉及 PD 时写“请核实是否为 PD”，因为 PD 也进入 Query；不得写“请中心整改”“说明整体情况”等无边界指控。

boundary/not_evaluable、成员不可列出、非冗余门未过或个体 Query 已完整覆盖时，只展示中心模式，不生成 Query。Query 只是草稿，不发送、不作为用户待办或完成门。

## 13. 增量与变化原因

对全量运行和基于既有项目的全量 listing 增量更新均记录：

- 数据新增/更正/删除；
- source revision/cutoff 变化；
- denominator/member/opportunity 变化；
- pattern/rule/mapping/window/stratum/method 变化；
- coverage 改善或退化；
- lifecycle 变化。

投影必须把“数据变化”与“规则/方法变化”拆开，解释新增、持续、升级、降级、关闭、重开或不可评估的原因。重复导出同一 revision 不得新增成员、模式、风险或 Query。

## 14. D10 与 R5 输出合同

D09 向 D10 提供：已验证 pattern unit、site stable identity、分子/分母 ledger、coverage、窗口、分层、成员 refs、D09 risk identity 和 lineage；不提供项目级结论或预先计算的中心排名。

R5 中文投影至少显示：

- 明确风险域和模式名称；
- 受影响人数、事件数/机会数、分母率或暴露调整率；
- 当前 coverage、样本/随访/暴露提示；
- 与上一可比窗口的变化及原因；
- 热点受试者；
- 一跳到个体和来源。

严禁“正式事实”“候选信号”“已记录事项”“只读 xx”“通用风险点”等内部或非医学表达。

固定中文：`相关个体风险 N 条`、`受影响受试者 N 名`、`事件 N 起`、`中心模式 N 项`；`coverage` 一律表达为 `本次可评价范围/数据完整性`。disposition 显示 `发现该类中心模式`、`在本次可评价范围内未发现该类中心模式（不代表无个体风险）`、`边界情况`、`不适用`、`暂无法评价（附原因）`；生命周期显示 `进行中`、`已核实关闭`、`已由规则变更取代`。中心模式显示 `clinical_label_zh`，不得暴露枚举。

## 15. 挑战矩阵冻结下限

| 分区 | 最少 cases | 必须覆盖 |
|---|---:|---|
| covered zero / uncovered zero | 6 | 闭合零事件可 negative；coverage/分母不闭合不得 negative |
| 小样本与 n=1 | 8 | 三 pattern kind；孤立高风险 boundary + hotspot 保留 |
| 短暴露/随访与晚启动 | 8 | subject/exposure time；排除不可比窗口；不得虚假改善 |
| 病例组合/项目收集变更反证 | 6 | 可解释 negative/boundary；不可解释 positive |
| 分子/分母/机会量 | 10 | 受试者数与事件数分离；分母漂移；空分母；错误机会定义；受试者不属于任何声明分母桶时须显式映射或 fail closed |
| 重复 revision/导出/排序 | 8 | 双遍确定性；同 revision 不多计；canonical hash 不漂移 |
| 同源与跨域去重 | 8 | D08 verified、ambiguous、wrong scope、不得字符串合并 |
| coverage 与完整性优先 | 10 | required partial/truncated/missing/failed；无关域缺口不连坐；医学输出被阻断 |
| cutoff/窗口 | 8 | 全 out、mixed、time missing、修订时间与事件时间区分、单窗趋势 |
| 方法与统计前提 | 8 | 信号不可展开、有效性不足、可比性通过、统计不能单独定性 |
| center Query | 10 | 非冗余、有限清单、三分句、PD 措辞、只展示边界 |
| owner/lifecycle/计数隔离 | 8 | D09/D10/D01-D08/R2 边界；禁止总风险混算；rule supersession |
| 深链与中文投影 | 8 | 一跳来源、无 locator、不良内部词、热点不被隐藏 |
| hidden / anti-overfit | 16 | 改项目/中心/受试者/字段/表名/顺序无漂移；阈值和规则离开 fixture |

追加且不得与上表 case 复用：

| 分区 | 最少 cases | 必须覆盖 |
|---|---:|---|
| D06/D10 consume-only | 8 | 中心疗效率/estimand/治疗组比较/项目异常 → owner fail、零 D09 医学 unit |
| L1 hole as zero risk | 6 | required L0 complete、L1 not_evaluable、零成员不得 negative |
| gap kind without member risk | 4 | accepted gap 9/42、无个体 RiskInstance 仍可 positive，不伪造风险 |
| first-window trend | 2 | 单闭合窗口 → 零 trend 医学 unit + window_pair_gate |
| Cartesian/stratum fanout | 4 | kind×domain×definition 被拒；空/过量 stratum 不爆炸 |
| visibility/blinded stratum | 6 | 隐藏成员、受众率 fail-closed、盲态键拒绝、合法非盲正向 |
| carry-forward on broken coverage | 4 | 既往 D09 risk + 本次缺口，不得 resolved_by_data |
| window id vs computed dates | 4 | 平移端点、同定义 → 同 stable core；版本改变不可比 |
| evidence_ref display not merge | 4 | 共享 source 但两 risk ids 保持分离，除非 D08 verified |
| Query fanout/redundancy | 4 | 超限只展示；无 process delta 不生成 Query |
| minimum member/authority | 2 | n=1 强制 boundary；min 字段非法 → authority fail |
| opportunity provenance | 2 | raw-only gap 不得 positive；D05 机会枚举冲突 fail closed |
| lifecycle close | 3 | 成员关闭但模式仍命中；coverage 不闭合；高优先级禁止自动关闭 |
| cross-window/site identity | 3 | rule/method/stratum 不同；中心合并/拆分不可比 |
| R5 no cross-site inference | 1 | 两中心并排无比较/排名/D10 文案 |

全部分区互斥主归属，case 不得跨分区复用。冻结 catalog 下限为各行最小值之和：当前 **179 cases**。最终 case 数只增不减。每个 case 必须有唯一 `primary_partition_id`；同一 `fixture_id/oracle_case_id/manifest_case_id/test_id` 不得出现在两个 primary partitions。`D09PartitionQuotaManifest` 逐分区保存 `required_minimum/actual_count/sorted_case_ids/partition_hash`，并以**当前 catalog 全部 case set**做无交集并集证明；任一 quota 不足、重复或遗漏均失败。

## 16. 非 LLM 验收锚点

1. contract、typed catalog、独立 oracle、challenge registry、generator 分别内容寻址并记录 SHA-256；
2. expected outcomes 只在独立 oracle 中声明，运行时不得读取 oracle，generator 不得从 oracle 回填输入；
3. exact expected-set、disposition、ledger、identity、owner、risk/query/journey/projection leaf 全等；多叶、少叶、额外 key 均失败；
4. 负向变异必须覆盖撤成员、换 origin、断 coverage、改分母、重复 revision、改窗口/规则并得到预期变化或 fail closed；
5. 双遍 deterministic replay 与 hidden/anti-overfit 通过；
6. 独立工程/医学 verifier 对同一不可变快照给出 `ACCEPT_D09_CONTRACT` 后，才允许构建 artifact/runtime；
7. runtime 阶段再运行 D09 focused、全 R4、D07/D08 相邻回归和 R1-R3 回归；合同阶段不以旧回归替代合同验收；
8. 8911 仍为 STOPPED，且无产品 UI、真实数据、真实模型或真实临床结论完成声明。

Artifact exact schemas：catalog 顶层仅 `catalog_id/version/case_count/catalog_hash/cases`；每 case 仅 `case_id/primary_partition_id/family_id/pattern_kind/owner_route/clinical_claim_token/disposition/fixture_id/fixture_hash/oracle_case_id/manifest_case_id/expected_leaf_set/expected_trace_leaf_set/expected_source_leaf_set/mutation_class/audience_contract/typed_input`，且 catalog 内三套 `expected_*` 必须为 `null`。registry 必须实现 `case_id/fixture_id/oracle_case_id/manifest_case_id/test_id` 全双射。generator/runtime import-closure 测试必须证明无法读取 oracle/registry；expected leaves 只能存在于独立 oracle。所有 hash 使用 UTF-8、Unicode NFC、对象键字典序、数组按声明的 stable identity 排序、十进制数按 `D09NumericExecutionPolicy` 规范化、禁止 NaN/Infinity、无空白 canonical JSON；hash 算法固定 SHA-256。quota manifest、catalog、oracle、registry、generator 的双遍字节必须完全一致。

## 17. v0.5 独立冻结修订记录

1. 接受三个医学 pattern kinds；热点受试者仅为投影，完整性/coverage 为 gate。
2. D09 positive 创建独立中心模式 RiskInstance，但与成员风险严格分层计数并由 R2 管理 lifecycle。
3. D09 Query 采用“每 positive 最多一条 + 非冗余 + 有限记录清单 + 只展示兜底”。
4. D09-owned 适配器消费既有公共对象，不要求回改 D01-D08 冻结合同。
5. 方法及有效性前提由版本化 ModeContract 声明；前提不足不得形成 positive/negative。
6. D09 仅做单中心模式和同中心历时评价；跨中心/项目/治疗组推断归 D10。
7. expected-set 以 definition 为唯一模式轴，禁止 kind × domain × definition 笛卡尔生成。
8. required producer 需 L0 与中心域 L1 医学完整性；L1 不可评不得作为零风险 negative。
9. gap 模式允许 accepted gap/obligation member，不要求伪造个体 RiskInstance。
10. 滚动窗口计算端点不进入方法 identity；本次缺口不得关闭既往中心模式风险。
11. 挑战矩阵采用互斥分区 179-case 下限。
12. claim token 与 pattern kind 冻结为三组显式双射；required producer additive 导出缺口统一进入 owner-QC 门。
13. gap/change-ledger 成员贯穿 identity、计数、风险引用与深链，不再被旧句强制转换为个体风险。
14. 窗口实际端点移出 definition；artifact exact keys、oracle null 占位和 import-closure 已冻结。
15. 稳定核心、实际窗口实例、evaluation unit、public risk identity 与 R2 lineage 四层分离，滚动窗口和数据修订不再碰撞。
16. gap/change/window-pair、domain completeness、机会量、R2 handoff、visibility/hotspot/deep-link/Query proof 全部具名 typed。
17. legal definition matrix 禁止 D09 形成疗效/安全中心统计或跨中心/项目推断。
18. 179-case 由 primary partition、quota manifest、无交集并集和 canonical JSON 机器证明。
19. evaluation content identity 与 opaque run/snapshot 分离；同内容跨 run 重放使用同一 R2 idempotency key，非 create 行为强制绑定 prior risk。
20. global gate 与 admitted-unit not-evaluable 语义消除歧义；legal matrix/numeric policy hashes、成员时间锚点及 Query policy 纳入 typed 合同。

本文件为自包含冻结候选；其是否冻结仅由新鲜上下文独立 verifier 对当前不可变 SHA 快照给出的 `ACCEPT_D09_CONTRACT` 决定。任何 `REVISE_D09_CONTRACT` 均保留为历史证据并要求新版本。
