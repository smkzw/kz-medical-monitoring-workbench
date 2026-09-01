# R4-D10 项目/跨中心安全与疗效信号聚合合同 v0.6

> 状态：`FINAL_SELF_CONTAINED_FREEZE_CANDIDATE`  
> 日期：2026-08-16  
> 范围：仅离线、合成、typed contract；不含 artifact、runtime、R5 UI、真实项目或正式临床结论。  
> 硬边界：8911 保持停止；不触碰医学写作子系统；不使用真实项目/患者数据；不扩展系统安全设计或测试。

## 1. 目的与用户语义

D10 将 D01-D08 已接受的受试者风险、D09 已接受的中心模式、独立分母/暴露账本、coverage 与版本变化，转化为项目级、跨中心可解释聚合。它回答四类问题：

1. 当前项目有哪些需要优先查看的中高风险、中心分布和热点受试者；
2. 本次相对上一个可比版本发生了什么变化，变化由数据还是方法/规则/覆盖造成；
3. 是否存在值得进一步医学审阅的项目安全或疗效趋势；
4. 某个项目数字、图形或结论由哪些中心、受试者、事件、分母和原始来源构成。

受众界面只使用自然中文，例如“3 个中心出现同类禁用药相关偏离，共涉及 7/126 名已治疗受试者”“中性粒细胞减少在当前累计暴露中增加，需结合暴露时长与病例构成核查”。不得显示 `typed handoff`、`candidate`、`正式事实`、`只读投影`、内部枚举、哈希或运行日志。

D10 不生成项目总风险分、中心红黑榜或自动获益-风险裁决；聚合与推断必须保持可展开、可复算、可质疑。

## 2. Owner 边界

| 层级 | Owner | D10 可做 | D10 禁止 |
|---|---|---|---|
| D01-D08 个体风险/医学事实 | 原域 | 消费 accepted/current typed public objects；引用成员 | 重算或改变个体 disposition、优先级、事实、Query、lifecycle |
| D09 中心模式 | D09 | 消费已验证中心 pattern、measure、coverage、lineage 与热点入口 | 重算中心模式、把中心离群等同中心质量问题、覆盖 D09 Query |
| D10 项目/跨中心聚合 | D10 | 评价项目分布、跨中心异质/异常、项目历时变化、授权范围内的描述性安全/疗效趋势 | 正式因果、最终获益-风险、治疗效果确证、中心惩罚性排名 |
| R2 lifecycle | R2 | 接收 D10 positive 的独立 RiskInstance handoff | D10 自建第二套 lifecycle |
| R5 投影 | R5 | 展示变化优先＋当前全量、中心热图、信号、coverage、深链 | 重新计算数值、隐藏中高风险、用 UI 聚类改变业务身份 |

### 2.1 `D10OwnerRoutingDecision`

```text
clinical_claim_token =
  d10_project_risk_distribution |
  d10_cross_site_pattern |
  d10_project_time_trend |
  d10_project_safety_trend |
  d10_project_efficacy_trend |
  d09_within_site_pattern |
  d01_d08_individual_claim |
  formal_benefit_risk_conclusion |
  confirmatory_treatment_effect |
  site_quality_judgment |
  unresolved

d10_action = evaluate_and_own | consume_only | handoff_only | context_only | routing_gate
```

仅前五个 token 可 `evaluate_and_own`。D09/个体 claim 为 `consume_only`；正式获益-风险、确证治疗效果、中心质量裁决为 `handoff_only`；`unresolved` 只产生 routing gate，零医学 unit。

`D10LegalDefinitionMatrix` 是内容寻址、exact-key 的 compile-time authority：

```text
D10LegalDefinitionMatrix
  matrix_id / matrix_version / row_count / rows[] / matrix_hash

D10LegalDefinitionRow
  row_id
  signal_kind
  clinical_claim_token
  d10_action
  allowed_member_object_kinds[]
  allowed_measure_kinds[]
  allowed_reference_kinds[]
  allowed_scope_kinds[]
  required_conditional_contracts[]
  forbidden_claim_tokens[]
  row_hash
```

exact legal rows：

| signal kind | exact claim/action | member plane | measure/reference/scope | 条件合同 |
|---|---|---|---|---|
| `project_risk_distribution` | 同名 token / evaluate | individual risk、accepted gap、D09 pattern 分叶 | count/proportion；current project；project | population、denominator、coverage、visibility |
| `cross_site_pattern` | 同名 token / evaluate | D09 pattern 或 accepted site ledger；不得把 D06 site efficacy 作为 D09 pattern | count/proportion/rate；project distribution/protocol expected/validated external；cross-site | comparison set、per-site comparability、denominator、coverage、visibility |
| `project_time_trend` | 同名 token / evaluate | current/prior D10 ledgers | count/proportion/rate；self prior window；project | window pair、baseline comparison、change decision、same-method comparability |
| `project_safety_trend` | 同名 token / evaluate | accepted safety measures + source members | count/proportion/incidence/exposure-adjusted/summary；current/self prior；project | safety context、population、exposure、coverage、method、visibility |
| `project_efficacy_trend` | 同名 token / evaluate | accepted efficacy measures + source members | summary/responder/model estimate；current/self prior/authorized treatment comparison；project | efficacy context、estimand、population、method、blind/visibility |

所有 `d09_within_site_pattern/d01_d08_individual_claim` 行只允许 `consume_only`，不能形成 D10 unit；`formal_benefit_risk_conclusion/confirmatory_treatment_effect/site_quality_judgment` 只允许 `handoff_only`；`unresolved` 只允许 `routing_gate`。D06 site efficacy rate/estimand 不能作为 `cross_site_pattern` 的 D09 成员；只有 D10-owned、已授权的 efficacy context 可消费 D06 typed measure 作为 source measure，且不得改写 D06 结论。缺行、重复行、开集值、条件合同缺失、claim/action/kind 不一致、成员种类越权或方法读取未授权治疗角色时，只输出 routing/integrity gate，零医学 unit。

## 3. 闭集信号类型与 expected-set

### 3.1 五种 `D10SignalKind`

1. `project_risk_distribution`：当前全量项目风险在域、等级、中心、受试者和时间窗中的可展开分布；不把异质风险简单相加。
2. `cross_site_pattern`：同一定义在多个可比中心的分布、重复传播或异常中心线索；用于优先核查，不是中心质量结论。
3. `project_time_trend`：同一项目、同一方法与分层在两个以上闭合可比窗口的项目级风险/缺口变化。
4. `project_safety_trend`：在授权分析集、暴露分母、盲态和方法合同下，对 AE、实验室/检查、停药/剂量调整及相关安全维度进行项目内累积或历时描述性评价。
5. `project_efficacy_trend`：在授权分析集、终点/时间点、缺失处理、盲态和 estimand 边界下，对项目内疗效指标进行描述性趋势评价。

`hotspot_site`、`hotspot_subject`、`coverage_gap`、`integrity_gate`、`routing_gate` 不是医学 signal kind；它们是投影或控制面对象。

### 3.2 `D10SignalDefinition`

```text
D10SignalDefinition
  signal_definition_id
  signal_kind
  clinical_label_zh
  clinical_claim_token
  d10_action
  risk_or_outcome_domain
  required_producer_domains[]
  accepted_member_object_kinds[]
  allowed_measure_contract_ids[]
  analysis_population_contract_id
  denominator_contract_id
  window_contract_id
  stratum_contract_id
  comparability_contract_id
  visibility_contract_id
  positive_rule_ref
  counterevidence_rule_refs[]
  monitoring_priority_rule_ref
  query_policy_id
  authority_locator
  authority_version / content_hash / effective_interval
  legal_matrix_row_ref / legal_matrix_row_hash
```

公共 kernel 不硬编码最小中心数、最小样本量、随访/暴露时长、临床阈值、统计阈值、疗效 responder 定义或 estimand。这些值只能来自版本化项目 Knowledge Pack、ModeContract、AnalysisPopulationContract 或方法合同。

### 3.3 Expected-set admission

医学 expected-set 只由下式构造：

```text
applicable signal_definition_id
× admitted project scope
× admitted analysis_window_stable_id
× admitted stratum cell
× admitted comparison_reference cell
```

kind/domain 是 definition 属性，不得自由做笛卡尔积。跨中心单位只有在达到 definition 要求的可评价中心集合且 comparability gate 闭合后进入医学 expected-set；不足时形成 `D10ComparisonSetGate`。趋势单位在至少两个闭合可比窗口前不进入医学 expected-set，形成 `D10WindowPairGate`。二者均计入 control-plane oracle leaf，不得伪装成“没有趋势/没有异常”。

首次全量运行没有 prior comparable baseline，只生成 `initial_full_snapshot` 当前全量单位；不得生成 `new/resolved/improved/worsened/reopened` change unit。

```text
D10ExpectedSetAdmission
  admission_id
  project_scope_binding_ref
  signal_definition_refs[]
  admitted_window_refs[] / admitted_stratum_cells[]
  admitted_comparison_reference_cells[]
  expected_unit_stable_cores[]
  expected_unit_count / expected_set_hash
  rejected_cell_refs[] / rejection_gate_refs[]

D10ComparisonSetGate
  gate_id / signal_definition_ref / window_ref / stratum_key
  candidate_site_refs[] / eligible_site_refs[] / excluded_site_refs[]
  per_site_comparability_evidence_refs[]
  required_site_count_ref / observed_eligible_site_count
  comparison_state = insufficient_sites | incomparable_sites | ready
  reason_codes[] / evidence_refs[]
  expected_leaf = control_plane_comparison_set_gate
  permitted_output = gate_only | admit_cross_site_unit

D10WindowPairGate
  gate_id / signal_definition_ref / stratum_key / comparison_reference_ref
  available_window_instance_refs[] / unique_window_stable_refs[]
  required_window_count_ref / observed_unique_window_count
  pair_state = insufficient_windows | incomparable_windows | ready
  reason_codes[] / evidence_refs[]
  expected_leaf = control_plane_window_pair_gate
  permitted_output = gate_only | admit_trend_unit
```

空 expected-set、无 eligible site、空 stratum、相同 stable window 的 opaque 重放或超量 Cartesian fanout 都必须有独立 control-plane gate；不得静默返回零医学结果。global gate、comparison/window gate 与 admitted-unit L1 是互斥叶，不可替换。

## 4. Typed 输入与消费适配器

D10-owned 纯确定性适配器只消费 accepted/current 对象：

```text
D10InboundProjectEnvelope
  envelope_id
  project_ref / run_ref / snapshot_ref / cutoff_ref
  cutoff_identity_and_policy_hash
  mode_contract_version / mode_contract_content_hash / execution_basis
  source_revision_content_pairs[]
  project_scope_binding_id / project_scope_binding_hash / blind_status
  analysis_population_refs[] / treatment_role_authority_ref?
  knowledge_rule_mapping_method_versions[]
  expected_site_refs[] / expected_subject_refs[]
  producer_coverage_refs[]

D10InboundMember
  member_ref
  member_kind = individual_risk | center_pattern | accepted_gap |
                safety_measure | efficacy_measure | denominator_member
  producer_domain / producer_contract_version
  project_ref / project_scope_binding_id / project_scope_binding_hash
  source_revision_content_pairs[] / accepted_current_state
  public_stable_identity / evaluation_content_identity
  site_stable_id / subject_stable_id?
  event_or_outcome_identity?
  monitoring_priority?
  analysis_population_refs[]
  treatment_role_ref?
  event_time_ref / cutoff_relation
  source_locator_refs[] / lineage_refs[]
  projectability_ref
  producer_authority_ref / producer_contract_hash
  aggregation_plane = individual | site_pattern | project_measure
  descendant_member_refs[] / descendant_set_hash?

D10InboundSiteLedger
  ledger_id / project_ref / project_scope_binding_id / project_scope_binding_hash
  run_ref / snapshot_ref / source_revision_content_pairs[]
  site_ref / site_activation_ref / accepted_current_state
  eligible_subject_refs[] / treated_subject_refs[] / evaluable_subject_refs[]
  subject_time_members[] / exposure_time_members[]
  D09_pattern_refs[] / individual_member_refs[]
  safety_measure_refs[] / efficacy_measure_refs[]
  coverage_refs[] / source_locator_refs[]

D10InboundGapMember
  gap_member_id / project_ref / project_scope_binding_id / project_scope_binding_hash
  source_revision_content_pairs[] / accepted_current_state
  gap_definition_id / owning_producer / producer_contract_hash
  obligation_or_opportunity_ref / subject_ref / site_ref
  source_locator_refs[] / provenance_hash

D10MeasureSourceOriginBinding
  binding_id / project_ref / project_scope_binding_id / project_scope_binding_hash
  source_revision_content_pairs[] / source_provenance_hash
  measure_ref / measure_kind / producer_ref / producer_contract_hash
  source_event_or_outcome_refs[] / source_member_refs[] / candidate_risk_refs[]
  verified_same_origin_risk_refs[] / distinct_risk_refs[] / ambiguous_risk_refs[]
  origin_decision = all_verified_same_origin | all_distinct | mixed_verified_and_distinct |
                    ambiguous | wrong_scope | not_evaluable
  candidate_partition_hash / binding_hash
```

每个 member、site ledger、gap、measure/source-origin binding 的 project/scope hash 与 project envelope 必须全等；source revision pair 必须是 envelope admitted paired set 的闭集子集；禁止从两个独立 revision/hash 数组重建配对。mode、cutoff、scope hash 都必须解析为 accepted authority。legal matrix row ref/hash 必须与 definition 及 matrix 全等。适配器不得从中文标题、自由文本、显示顺序、中心名称或模型摘要推断身份、治疗组、终点、严重度或同源关系。无法反向解析、hash/scope/version 不符、非 accepted/current、wrong project/site/subject 或 treatment role 未授权时，必须在医学计算前阻断对应单位。

D10 不从原始 listing 重数 D01-D09 风险、机会或中心模式；只有专属 safety/efficacy measure definition 明确声明原始/派生量 owner 时，才可消费其已接受 typed measure。`accepted_gap` 只能使用完整 `D10InboundGapMember`；raw-only gap 禁止 admission。safety/efficacy measure 必须具有 `D10MeasureSourceOriginBinding`，其所有 source event/outcome/member refs 必须反向解析到 binding 的 paired revisions，且 paired set 是 envelope admitted set 的闭集子集。origin 三集合必须满足 `verified ∪ distinct ∪ ambiguous = candidate_risk_refs`、两两不交、各 ref 唯一；candidate partition/source provenance/binding hash 覆盖全量集合。

`origin_decision` 由集合确定性生成：仅 verified 非空为 `all_verified_same_origin`；仅 distinct 非空为 `all_distinct`；verified 与 distinct 同时非空且 ambiguous 为空为 `mixed_verified_and_distinct`；ambiguous 非空强制 `ambiguous`；scope 错误优先 `wrong_scope`；来源无法解析为 `not_evaluable`。verified same-origin individual risk 与 measure 只允许一个 numerator contribution plane；distinct 保持分叶；mixed 必须按 verified/distinct 两叶分别计量，不得以全量 verified 合并；ambiguous/wrong_scope/not_evaluable 不能进入 positive necessity path。

`member_kind=center_pattern` 时 `descendant_member_refs/descendant_set_hash` 条件必填，必须由 accepted D09 owner identity + contract hash 反向验证；其他 member kind 两字段必须为空。同一 D10 unit 的共同 numerator plane 不得同时纳入 D09 parent pattern 及其 descendants。若项目投影需同时展示中心模式数与个体风险数，二者进入相互独立的展示 leaf，不进入共同 `numerator_member_count`、同一 Query member set 或同一 estimate。缺失或冲突时 not_evaluable。

## 5. 身份、去重与 lineage

```text
D10UnitStableCore = (
  project_id,
  signal_definition_id,
  analysis_window_stable_id,
  stratum_contract_id,
  stratum_key,
  comparison_reference_stable_id
)

D10EvaluationContentIdentity = hash(
  D10UnitStableCore,
  project_scope_binding_hash,
  cutoff_identity_and_policy_hash,
  signal_definition_content_hash,
  window_definition_hash,
  window_instance_identity,
  stratum_contract_hash,
  sorted(source_revision_content_pairs),
  sorted(numerator_member_content_identities),
  sorted(denominator_member_content_identities),
  measure_ledger_hash,
  analysis_population_hash,
  endpoint_estimand_method_hashes,
  treatment_role_authority_hash_or_none,
  denominator_contract_hash,
  comparability_contract_hash,
  visibility_contract_hash,
  visibility_decision_hash,
  projectable_hidden_member_site_set_hashes,
  coverage_and_completeness_hashes,
  positive_and_counterevidence_rule_hashes,
  query_policy_hash,
  mode_contract_version,
  mode_contract_content_hash,
  legal_definition_matrix_hash,
  numeric_execution_policy_hash,
  sorted(knowledge_rule_mapping_model_method_content_pairs),
  algorithm_version="d10_v1"
)
```

run_id、snapshot opaque id、mtime、进程 ID、数组顺序和显示文案不进入稳定核心。source revision/cutoff/window instance/成员内容、population、denominator、method、visibility 和 authority hashes 必须进入 evaluation identity。

`source_revision_content_pairs` 必须保留 `(revision_id, content_hash)` 一一对应，禁止把 revision 与 hash 分别排序后配对。所有 typed object 使用 UTF-8、Unicode NFC、闭集枚举、exact keys、canonical JSON、稳定身份字节序和 SHA-256；十进制数用规范字符串，禁止 NaN/Infinity/-Infinity 和二进制浮点平台差异进入 hash。相同 ID 不同内容必须被 content hash 区分。denominator 实际成员、排除成员、换算后值和 time segments 都通过 ledger hash 进入 identity。

成员去重使用原 owner public identity；事件按 stable event/outcome identity；受试者按 project-scoped subject identity；中心按 project-scoped site identity。D09 center pattern 与其 D01-D08 成员是不同层级，不得相加为一个“总风险数”。同源跨域只有 D08 verified same-origin binding 才可合并事件；歧义时不静默合并，相关率/趋势为 boundary 或 not_evaluable。

lineage relation 闭集：

```text
initial_full_snapshot |
continued_from_data_revision |
continued_from_cutoff_advance |
superseded_by_knowledge_change |
superseded_by_rule_or_mapping_change |
superseded_by_method_or_population_change |
superseded_by_mode_change |
superseded_by_visibility_change |
coverage_regressed |
not_comparable
```

只有 `continued_from_data_revision/cutoff_advance` 可产生临床数据变化叙述。知识、规则、mapping、模型、方法、分析集、visibility 或 coverage 变化不得伪装为风险改善/恶化。

## 6. 项目计量账本

```text
D10MeasureLedger
  unit_ref
  numerator_subject_refs[] / numerator_subject_count
  numerator_event_refs[] / numerator_event_count
  numerator_site_refs[] / numerator_site_count
  numerator_member_refs[] / numerator_member_count
  denominator_kind
  denominator_member_refs[] / denominator_value / denominator_unit
  denominator_excluded_refs[] / exclusion_reason_codes[]
  denominator_state = closed_positive | closed_zero | unclosed
  subject_time_members[] / exposure_time_members[]
  estimate_kind = count | proportion | incidence_rate | exposure_adjusted_rate |
                  summary_statistic | responder_rate | model_estimate
  observed_value / unit / scale / display_precision
  uncertainty_kind / uncertainty_lower? / uncertainty_upper?
  coverage_refs[] / coverage_state
  site_contribution_refs[] / subject_contribution_refs[]
  analysis_population_ref / estimand_ref?
  safety_measure_context_ref? / efficacy_measure_context_ref?
  numeric_execution_policy_ref / ledger_hash
```

任何比例/率必须同时显示绝对量与明确分母。subject-time/exposure-time 保留每个成员可计时段、排除区间和换算。疗效 summary/model estimate 必须保存分析集、终点、时间点、缺失处理、estimand/模型版本与可贡献成员；不能只保存一个均值或 p 值。

允许分母闭集由 definition 选择：`enrolled_subjects/treated_subjects/safety_evaluable_subjects/efficacy_evaluable_subjects/subject_time/exposure_time/expected_assessment_opportunities/analysis_population_members`。运行时不得自动换分母。

`closed_zero` 默认 not_evaluable；只有设计条款证明不适用才为 not_applicable。required coverage 中的 not_evaluable 不得从分母静默剔除；必须进入排除清单并可能阻断估计。

```text
D10TimeSegment
  project_ref / project_scope_binding_id / member_ref / segment_id
  start_anchor_ref / start_value / start_precision / start_source_locator / start_source_hash
  end_anchor_ref / end_value / end_precision / end_source_locator / end_source_hash
  inclusivity / excluded_interval_refs[]
  raw_duration / raw_unit / normalized_duration / normalized_unit
  calendar_and_unit_conversion_contract_ref
  overlap_resolution_ref / segment_hash

D10NumericExecutionPolicy
  policy_id / version
  allowed_estimate_kinds[]
  count_dedup_keys_by_kind{}
  numerator_denominator_pair_rules[]
  subject_time_unit / exposure_time_unit / scale
  time_segment_overlap_policy
  zero_missing_invalid_policy
  decimal_context / rounding_mode / display_precision
  uncertainty_method_refs[]
  content_hash / effective_interval
```

可执行等式：

```text
numerator_subject_count = cardinality(unique numerator_subject_refs)
numerator_event_count = cardinality(unique numerator_event_refs)
numerator_site_count = cardinality(unique numerator_site_refs)
numerator_member_count = cardinality(unique numerator_member_refs on one aggregation_plane)
denominator_value = deterministic aggregate of unique denominator_member_refs after declared exclusions
proportion = numerator_subject_count / denominator_value
incidence_or_exposure_rate = unique eligible events / sum(non-overlapping normalized time segments)
```

validator 必须从不可变 source anchors、日期精度和 conversion contract 重算 raw/normalized duration；不得信任提交时长。refs/count/value、排除清单、time-segment 重叠、单位换算、率和 uncertainty 任一不守恒时 integrity failure；不得只信任提交的汇总值。`uncertainty_kind` 按 estimate method 的 `uncertainty_method_ref` 条件必填；不适用时必须显式 `not_applicable`，不得空缺。

## 7. 跨中心可比性与异常

```text
D10CrossSiteComparabilityContract
  eligible_site_rule_ref
  required_case_mix_covariates[]
  minimum_site_count_ref / minimum_site_denominator_ref
  minimum_followup_ref / minimum_exposure_ref
  site_activation_adjustment_ref
  denominator_alignment_rule_ref
  stratum_alignment_rule_ref
  missingness_adjustment_ref
  comparison_method_id / method_validity_preconditions[]
  reference_kind = project_distribution | protocol_expected | validated_external_baseline
  multiplicity_or_screening_context_ref?
  counterevidence_rules[]
  authority_locator / content_hash / effective_interval

D10SiteComparabilityEvidence
  evidence_id / site_ref / comparison_contract_ref
  eligible_state = eligible | excluded | not_evaluable
  exclusion_reason_codes[]
  denominator_kind / denominator_value / denominator_member_refs[]
  followup_member_segments[] / followup_summary
  exposure_member_segments[] / exposure_summary / site_activation_ref
  required_case_mix_covariates[] / observed_case_mix_covariate_values[]
  required_missingness_measures[] / observed_missingness_values[]
  collection_method_ref / source_revision_refs[] / coverage_refs[]
  method_precondition_results[] / all_required_preconditions_passed
  evidence_hash
```

comparability validator 必须按 contract 重建 eligible/excluded/not_evaluable、required/observed covariate、missingness 和 method preconditions；`all_required_preconditions_passed` 不得自声明。跨中心异常是 `review_priority_evidence`，不能单独创建 positive。至少还需：成员可展开、每个 eligible site 的 evidence 完整、方法前提成立、同类定义/分母/窗口可比、coverage 完整，且病例构成/启动/暴露/随访/数据收集差异不能充分解释。`site_quality_judgment` 永远 handoff-only，D10/R5 不得生成“中心质量差/好”的结论。

小中心、晚启动、短暴露、分母稀疏或覆盖不足不得与完整中心直接排序。R5 可按稳定中心身份、字母或用户选择排序；默认不得按风险率生成惩罚性榜单。

单个高风险受试者始终作为 hotspot 保留；它不因项目率低而隐藏，也不自动证明跨中心模式。

## 8. 安全与疗效专属方法门

### 8.1 项目安全趋势

```text
D10SafetyMeasureContext
  context_id
  safety_analysis_population_ref
  coding_dictionary_and_version_ref
  severity_scale_ref / seriousness_rule_ref / relatedness_rule_ref
  exposure_definition_ref / denominator_contract_ref
  event_identity_and_counting_rule_ref
  risk_window_ref / coverage_contract_ref
  descriptive_monitoring_only = true
  method_ref / content_hash
```

`project_safety_trend` 仅在上述字段、treatment exposure、时间窗和 coverage 闭合时评价。允许描述：事件数、受影响人数、发生比例、暴露调整率、严重度/严重性、停药/剂量调整、实验室/检查趋势及特定风险人群分布。

禁止：由相关性字段自动推出因果；把一般医学风险称为正式安全性信号；用 SAE/AESI 单例的低频隐藏其个案优先级；把当前单研究结果冒充跨研究/产品级累积结论。

### 8.2 项目疗效趋势

```text
D10EfficacyMeasureContext
  context_id
  endpoint_definition_ref / endpoint_version
  analysis_population_ref
  visit_or_timepoint_ref / window_ref
  baseline_definition_ref
  missing_data_rule_ref / intercurrent_event_rule_ref
  estimand_ref / method_ref / method_version
  treatment_role_authority_ref?
  treatment_assignment_exposure_identity_ref?
  treatment_assignment_mapping_hash?
  blind_visibility_contract_ref
  descriptive_monitoring_only = true
  content_hash
```

`project_efficacy_trend` 必须绑定全部通用字段；若 comparison reference 使用 treatment role，则三个 treatment 条件字段、visibility decision hash 均条件必填并可反向解析 accepted assignment/exposure identity。`model_estimate/responder_rate/summary_statistic` 缺任一条件字段都 not_evaluable。只允许项目内、当前数据截止的描述性监查结论。

未授权非盲时不得读取或推断真实治疗分组；只可使用合法盲态汇总。确证治疗效果、优效/非劣、正式 estimand 推断与最终获益-风险均不属于 D10 owner。

### 8.3 治疗组比较

治疗组比较只有在以下条件全部满足时才可作为 D10 描述性 evidence：

- `treatment_role_authority_ref` 明确当前运行与受众可见；
- treatment assignment/exposure identity 已接受且一致；
- 分析集、estimand、分母、方法、缺失处理和时间窗闭合；
- visibility 决策不会通过人数、分母、标签或 tooltip 泄露隐藏组别。

任一条件失败时为 routing/boundary/not_evaluable，不得通过中心差异或给药模式反推分组。

p-value、离群分、相关性字段、模型摘要或模型多数票都只能作为 evidence，不能单独设置 positive、因果性、正式安全信号、确证疗效或获益-风险结论。

## 9. 完整性优先顺序与五类 disposition

### 9.1 两层 gate

```text
D10GlobalAdmissionGate
  gate_id / gate_kind
  project_run_snapshot_cutoff_refs
  authority_and_legal_matrix_refs
  project_site_subject_identity_state
  blind_and_visibility_authority_state
  expected_set_generator_state
  failure_codes[] / source_locator_refs[]
  permitted_output = integrity_gate_only

D10UnitCompletenessDecision
  stable_core_ref / evaluation_content_identity
  required_producer_domains[]
  per_domain_l0_state[]
  per_domain_expected_l1_count[]
  per_domain_observed_l1_count[]
  per_domain_positive_negative_boundary_na_count[]
  per_domain_l1_not_evaluable_count[]
  member_resolution_state / denominator_state / coverage_state
  population_state / window_state / comparability_state / method_state
  completeness_state = complete | not_evaluable
  reason_codes[] / evidence_refs[]
```

全局 project/scope/identity/authority/blind/visibility/legal matrix/expected-set generator 失败时只输出 global gate，零医学 unit。expected-set 已 admission 后的 required coverage、成员、分母、population、window、comparability 或 method 缺口必须形成该 unit 的 L1 `not_evaluable` 并参与守恒。非 required 域缺口不连坐。

固定处置优先顺序：

```text
global admission failure -> global gate, zero medical unit
comparison/window admission failure -> control-plane gate, zero corresponding medical unit
admitted unit required completeness failure -> L1 not_evaluable
explicit design non-applicability with authority locator -> not_applicable
complete but limited/ambiguous evidence -> boundary
complete evaluation -> positive or negative
```

required producer L0 complete 但任一 required L1 `not_evaluable` 时，当前 D10 unit 必须 not_evaluable，不得以 numerator=0 走 negative。accepted gap 的 opportunity/obligation ledger 未闭合时同样 not_evaluable。

### 9.2 五类 L1

| Disposition | 条件 |
|---|---|
| `positive` | 适用；完整性、coverage、分母、population、window、comparability、method、visibility 全通过；命中 definition；反证不足以解释 |
| `negative` | 全部门闭合并完成检查；未命中或反证充分解释；零事件/空表本身不够 |
| `boundary` | 存在可定位线索，但小样本、短随访/暴露、异质性、同源歧义、病例构成或方法不确定性不足以形成 positive |
| `not_applicable` | ModeContract/设计条款明确证明当前项目阶段/分析集/窗口不适用，带 locator 和有效区间 |
| `not_evaluable` | identity、required coverage、成员、分母、population、cutoff、window、blind/visibility 或方法前提缺失/冲突 |

每个 expected unit 恰好一个 disposition：

```text
expected = positive + negative + boundary + not_applicable + not_evaluable
```

negative 不创建 risk/query；boundary 可形成 project clue；仅 positive 可创建 D10 RiskInstance。

## 10. D10 风险、计数与生命周期 handoff

```text
D10R2RiskHandoff
  handoff_id = hash(public_d10_risk_identity, evaluation_content_identity,
                    action, lineage_relation, prior_risk_instance_ref_or_none,
                    change_decision_hash, completeness_decision_hash)
  idempotency_key = handoff_id
  public_d10_risk_identity / stable_core_ref
  evaluation_content_identity
  prior_risk_instance_ref
  action = create | continue | update | propose_close | reopen | supersede
  lineage_relation
  change_decision_ref / change_decision_hash
  member_refs[] / measure_ledger_ref / completeness_decision_ref / completeness_decision_hash
  monitoring_priority / no_auto_close_reasons[]
```

D10 positive 创建 `aggregation_level=project_signal, owner=D10` 的独立 RiskInstance，不复制或改变 D01-D09 风险。相同 immutable 内容重放必须得到同一 evaluation identity/handoff idempotency key；R2 只应用一次。

`action=create` 仅允许 `prior_risk_instance_ref=none`，且 lineage 为 `initial_full_snapshot/continued_from_data_revision/continued_from_cutoff_advance`；后两者还必须证明 prior evaluation unit 存在但没有 prior R2 risk，且 current 是 first positive。`continued_from_cutoff_advance` 还必须由 derived-only `D10CutoffAdvanceDecision` 证明 `decision_state=strict_advance`，并要求所绑定 `D10ChangeDecision.non_data_change_present=false`、全部 denominator/coverage/knowledge/rule/mapping/model/method/population/visibility/mode change refs 为空、前后 mode/method/population/visibility 可比。same-window replay、仅数据修订、cutoff 策略改变或 cutoff 与任一非数据变化混合均不得走该 lineage。`continue/update/propose_close/reopen/supersede` 必须解析为同一 public D10 identity/stable core 的 current R2 instance。已有 prior risk 时，`continued_from_data_revision/cutoff_advance` 只允许 continue/update/reopen/propose_close 且 change decision 可比；knowledge/rule/mapping/method/population/mode/visibility 变化只允许 supersede；coverage_regressed/not_comparable 只允许 continue carry-forward。错误/缺失 prior、action×lineage 非法或已应用 idempotency key 均 fail closed。高风险、SAE/AESI、用户确认/升级或正式外部处置链保持 no-auto-close。

计数分层保存且禁止混加：

- `individual_risk_count`：D01-D08 个体风险；
- `affected_subject_count`；
- `event_or_outcome_count`；
- `center_pattern_count`：D09 模式；
- `affected_site_count`；
- `project_signal_count`：D10 positive；
- `clue_count`；
- `query_count`。

既往 D10 风险只有在当前 accepted full snapshot、相同 definition/method/population、完整 coverage 下不再命中时才可 propose_close。not_evaluable、coverage 回退、visibility 限制或方法变化不得关闭既往风险；方法/规则变化走 supersede。高风险、SAE/AESI、用户确认/升级或正式外部处置链不自动关闭。

## 11. 项目 Query 草稿边界

仅 positive 且存在项目流程级、跨中心协调级或项目数据核实级新增行动信息时，每 unit 最多一条 D10 Query 草稿。不得复制成员个体或 D09 中心 Query，也不得生成给研究者的笼统“请关注”。

```text
D10QueryRedundancyDecision
  decision_id = hash(unit_ref, evaluation_content_identity, decision,
                     query_policy_hash, sorted_unique(unit_member_refs), unit_member_set_hash,
                     sorted_unique(covered_member_refs), sorted_unique(uncovered_member_refs),
                     sorted_unique(member_query_content_identities), coverage_proof_hash)
  unit_ref / evaluation_content_identity / query_policy_hash
  decision = project_delta_present | fully_covered_by_member_queries |
             members_unlistable | not_applicable
  unit_member_set_hash
  covered_member_refs[] / uncovered_member_refs[]
  member_query_refs[] / member_query_content_identities[]
  coverage_proof_hash / decision_hash

D10QueryDraft
  query_id = hash(canonical_full_query_object_hash)
  owner = D10
  public_d10_risk_identity / evaluation_content_identity
  query_policy_ref / query_policy_hash
  unit_member_refs[] / unit_member_set_hash
  redundancy_decision_ref / redundancy_decision_hash
  basis_parts[] / finding_parts[] / action_parts[]
  rendered_basis_sentence / rendered_finding_sentence / rendered_action_sentence
  source_locator_refs[] / center_subject_record_refs[]
  pd_wording_state = not_pd | verify_whether_pd
  sentence_content_hash / canonical_full_query_object_hash / query_content_hash
```

所有 identity-bearing ref arrays 都按 stable identity `sorted unique` canonical encoding；输入重排不得改变 decision/query identity，重复 ref 直接拒绝。只有 `project_delta_present` 且 uncovered set 非空可生成。必须证明 `covered ∪ uncovered = unit_member_refs` 且交集为空；redundancy validator 从 authoritative unit ledger、policy 和 content-addressed member Query 全量重建 decision/hash，不接受提交集合。每个 evaluation unit 的唯一键只允许一个 D10 Query。草稿必须由 `D10AudienceTextContract` 的 typed sentence parts 渲染成“依据＋发现＋行动项”三分句，引用可定位中心/受试者/记录清单与分母口径；涉及 PD 只允许模板“请核实是否为 PD”。成员过多时完整清单作为附件/展开层，不得截断后冒充完整。canonical full Query hash 覆盖 owner、risk/evaluation identity、policy、全部 member/proof、三类 typed/rendered sentences、source locators、PD state 和中心/受试者/记录 refs。validator 必须从 authoritative evaluator result 重建整份 Query 并要求 dataclass/typed object 全等；不得接受提交者自行重哈希的改写内容。

D10 只生成、核验、导出草稿，不跟踪外部回复、关闭或待办状态。

## 12. R5 项目驾驶舱与深链合同

`D10ProjectProjection` 必须同时提供：

- 本次变化：新增、升级、持续、降级、关闭、重开、不可评价，以及变化原因；
- 当前全量：全部高/中风险，低风险聚合可展开；
- 中心分布：绝对量、明确分母率、coverage、小样本/短随访提示；
- 项目安全/疗效趋势：分析集、窗口、分母、方法与不确定性；
- 热点中心/受试者，但不使用惩罚性排序或黑箱总分；
- 每个数字、图形、信号到分子、分母、中心、受试者、成员风险、Patient Journey/Profile/Timeline 和原始来源的一跳链路。

```text
D10DeepLinkTarget
  target_kind = member | site | subject_site_pair
  project/run/snapshot/cutoff refs
  signal_definition_ref / evaluation_window_instance_ref
  site_ref? / subject_ref?
  member_object_ref / event_or_outcome_ref?
  visit_or_time_anchor_refs[] / source_locator_refs[]
  visibility_decision_ref / visibility_decision_hash
  return_state_key

D10ProjectionVersion
  projection_version_id
  project/run/snapshot/cutoff refs
  source_evaluation_content_identities[]
  source_ledger_hashes[] / source_risk_refs[]
  visibility_decision_refs[] / audience_contract_ref
  projection_content_hash / supersedes_projection_ref?

D10ProjectProjection
  projection_id = hash(projection_version_id, projection_content_hash)
  projection_version_ref
  change_section_refs[] / current_risk_refs[]
  center_distribution_refs[] / safety_efficacy_trend_refs[]
  hotspot_site_refs[] / hotspot_subject_refs[]
  count_surface_ref / coverage_refs[] / warning_refs[]
  deep_link_targets[] / return_state_keys[]
  audience_text_refs[] / projection_content_hash
```

图表过滤、表格、Inspector 与 Journey 使用同一 projection identity 与可见成员集合。projection validator 从 authoritative D10 result、ledgers、visibility 与 lifecycle refs 独立重建并要求全等；不得信任提交的 count、denominator、hidden refs、lifecycle 或 source link。R5 不得重算数值；聚类/排序/筛选不得改变风险 lifecycle 或隐藏中高风险。

`D10AudienceTextContract` 将用户字段限制为闭集 `sentence_part_kind` 与版本化中文模板：`authority_basis/observed_finding/denominator_context/uncertainty/counterevidence/action_verify/action_reconcile/action_pd_verify/source_business_identifier`。每个 part 只接受对应 typed values；业务 ID 只能走专用 identifier part。模板闭集明确禁止“正式安全性信号、确证治疗效果、优效、非劣、获益-风险裁决、中心质量差/好”及内部 disposition/state/enums。渲染后再执行 UTF-8/NFKC、category C/control/format/invisible marks、跨脚本 confusable allow-list 与工程引用语法审计。任何 `pattern/rule/mode/window/revision/scope/policy/hash/id/ref` 的键值式、紧凑式、全角式、同形字符或语义化工程引用均拒绝。医学自由文本只能作为明确标记的引用摘录，不能产生业务身份、authority、结论或模板外措辞。

## 13. Visibility、盲态与多模型

```text
D10VisibilityDecision
  decision_id / audience_scope_id / blind_status
  authorized_unblinded_contract_ref?
  evaluation_member_refs[] / projectable_member_refs[] / hidden_member_refs[]
  evaluation_site_refs[] / projectable_site_refs[] / hidden_site_refs[]
  visible_n / eligible_n / hidden_member_count / hidden_site_count
  numerator_visibility_state / denominator_visibility_state
  rate_projection_state = permitted | suppressed | qualified
  deep_link_eligible_member_refs[] / deep_link_eligible_site_refs[]
  projectable_subject_site_pairs[]
  deep_link_eligible_subject_site_pairs[]
  projectable_hidden_member_set_hash / projectable_hidden_site_set_hash
  hidden_reason_codes[] / decision_hash
```

集合必须满足 `projectable ∪ hidden = evaluation`、`projectable ∩ hidden = ∅`、三组各自唯一、`visible_n=|projectable members|`、`eligible_n=|evaluation members|`、hidden counts 等于集合基数，site 集合同理。`projectable_subject_site_pairs` 由 projectable members 的 authoritative subject/site scope 生成，且 pair 中 site 必须属于 projectable site set。强制 `deep_link_eligible_member_refs ⊆ projectable_member_refs`、`deep_link_eligible_site_refs ⊆ projectable_site_refs`、`deep_link_eligible_subject_site_pairs ⊆ projectable_subject_site_pairs`；validator 独立重建三项子集关系。deep-link target 必须绑定同一 visibility decision/hash：`member` kind 只允许 member ref 且 ref 在 eligible member set；`site` kind 只允许 site ref 且在 eligible/projectable site set；`subject_site_pair` kind 强制同时提供 subject 与 site 并精确匹配 eligible/projectable pair，禁止 subject-only target。member 若携带 subject/site，也必须与其 authoritative scope 和 eligible pair 一致。隐藏成员不得通过中心数、分母、组别颜色、tooltip、排序、Query 或 deep-link 泄露。任一隐藏分子/分母混入 audience rate 时必须 suppress/qualified；盲态 stratum key、treatment role label 和 unblinded deep-link 无授权时直接拒绝。

```text
D10ModelEvidence
  model_evidence_id
  role = candidate_explanation | counterevidence_suggestion
  evaluation_content_identity / input_content_hash
  source_revision_content_pairs[] / source_refs[]
  model_binding_hash / model_version / independent_context_hash
  ensemble_id / ensemble_size / member_analysis_refs[]
  output_hash / adjudication_state
  permitted_leaf = model_candidate_only | counterevidence_suggestion_only
```

所有字段 exact-key。不同 input/evaluation identity 不得声称共同发现；`ensemble_size=1` 禁止 consensus leaf。ModelEvidence 不能进入 numerator/denominator/coverage/authority/positive necessity path、不能改写 typed measure 或建议自动关闭高风险。positive 的必要前件始终是 accepted typed member + deterministic measure/coverage/authority。多数票不是医学真值，独立 adjudication 不得静默关闭重要分歧。

## 14. 全量、增量与变化原因

```text
D10BaselineComparisonDecision
  decision_id
  execution_basis = full | incremental
  current_snapshot_ref / current_baseline_eligible_state
  prior_snapshot_ref_or_none / prior_baseline_eligible_state_or_none
  current_cutoff_ref / prior_cutoff_ref_or_none
  current_method_bundle_hash / prior_method_bundle_hash_or_none
  comparison_state = initial_full | comparable | not_comparable
  reason_codes[] / decision_hash

D10CutoffAdvanceDecision
  decision_id
  prior_cutoff_ref / prior_cutoff_identity_and_policy_hash
  current_cutoff_ref / current_cutoff_identity_and_policy_hash
  boundary_kind = calendar_time | study_day | exposure_time
  prior_boundary_value / current_boundary_value
  policy_semantic_hash_equal
  strict_advance_predicate_passed
  decision_state = strict_advance | same_window | policy_changed | not_evaluable
  evidence_refs[] / decision_hash

D10ChangeDecision
  decision_id / stable_core_ref
  baseline_comparison_ref
  cutoff_advance_decision_ref?
  current_evaluation_content_identity
  prior_evaluation_content_identity_or_none
  data_change_refs[] / denominator_change_refs[] / coverage_change_refs[]
  knowledge_change_refs[] / rule_change_refs[] / mapping_change_refs[]
  model_change_refs[] / method_change_refs[] / population_change_refs[]
  visibility_change_refs[] / mode_change_refs[]
  primary_change_cause = data | denominator | coverage | knowledge | rule |
                         mapping | model | method | population | visibility | mode | mixed
  clinical_change_kind = initial_current | new | continued | upgraded | downgraded |
                         resolved | reopened | not_comparable
  permitted_audience_change_text
  non_data_change_present
  decision_hash
```

`D10CutoffAdvanceDecision` 是 deterministic derived-only 对象。validator 必须从 accepted prior/current cutoff authority、边界 source anchors 与 policy semantic hashes 重建所有字段：calendar/study-day/exposure-time 分别按冻结 conversion/ordering contract 判断 `current > prior`；提交的 boundary value、hash-equal、predicate 或 decision state 均不被信任。policy hash 不等、same window、边界不可比较或来源不完整分别只能为 `policy_changed/same_window/not_evaluable`。

- 每次输入仍是已接受的全量 listing snapshot；D10 不接收差异文件替代事实。
- `full` 对当前版本完整重建；首次 full 的 prior 固定为 none、comparison_state 固定 `initial_full`、clinical change 固定 `initial_current`，受众只显示“初始全量”。R2 `action=create` 不得被 R5 映射为“新增”。
- `incremental` 比较两个 baseline-eligible 全量快照，并按稳定身份重算受影响单位；最终投影仍包含当前全量。
- 旧成员消失先核查导出范围、mapping、identity、coverage 和真实删除；不直接视为风险解决。
- `D10ChangeDecision` 必须绑定两个 accepted/baseline-eligible 全量快照；否则 initial_full 或 not_comparable。
- evaluator 从各 refs 集合和前后内容 hash 重建 cause：只要 denominator/coverage/knowledge/rule/mapping/model/method/population/visibility/mode 任一集合非空，或前后 mode content hash 不同，`non_data_change_present=true`。此时 clinical change 必须 `not_comparable`，或在方法合同证明可完全隔离贡献时生成相互独立的 data-change 与 analysis-change leaf；不得提交 `primary_change_cause=data` 后显示总体临床改善/恶化。只有 data refs 或 cutoff advance 非空且所有非数据集合为空、mode/method bundle/coverage/population/visibility 可比时，才可显示临床新增/持续/升级/降级/关闭/重开。仅非数据变化只显示“分析口径变化”，ModeContract 变化只能 analysis-change/supersession。R2 handoff 必须引用这一 change decision/hash。
- 不可比版本不显示新增/关闭或改善/恶化，而显示“分析口径变化，前后不可直接比较”。
- 日常、锁库前、锁库后—CFDI 前分别遵循 ModeContract；跨模式必须新建 Run，不静默继承比较语义。

## 15. 合成挑战矩阵冻结下限

合同冻结后、实现前构建不少于 **312** 个 exact-key、immutable、synthetic/offline cases；catalog、oracle、registry、generator 相互独立，runtime 禁止读取 oracle/registry。以下 primary partition 互斥，配额合计 312：

1. 五个 signal kind 各不少于 12：五类 disposition、counterevidence、FP、FN、hidden、replay；
2. owner routing/越权/consume-only/handoff-only/zero-medical-output 不少于 24；
3. project/site/subject/member identity、wrong scope、duplicate、same-origin ambiguity 不少于 24；
4. 分子/分母/subject-time/exposure-time/opportunity/analysis population 不少于 28；
5. 跨中心可比性：小中心、晚启动、病例构成、随访/暴露、coverage、method invalid 不少于 28；
6. safety：AE/严重度/SAE/AESI/停药/实验室/暴露调整/特殊人群/单例不隐藏，不少于 24；
7. efficacy：endpoint/timepoint/baseline/missing/intercurrent event/estimand/blind treatment role，不少于 24；
8. initial full、incremental、cutoff、rule/mapping/method/population/visibility/coverage change cause 不少于 28；
9. Query redundancy、fanout、PD wording、Project→Site→Subject→Journey/source 深链不少于 20；
10. visibility/blindness/hidden denominators/non-disclosure 不少于 16；
11. Unicode/key exactness、hash/tamper、catalog/oracle/registry/generator bijection 不少于 20；
12. anti-overfit 不少于 16：改变项目/中心/受试者/表/字段显示名、输入顺序与非医学版本字段但保持 substantive semantics。

所有分区以独立 primary partition 互斥计数；总数、并集、交集、quota 和 canonical SHA-256 机器证明。每个 expected medical unit 恰好一个 L1；global gate 与医学 unit 的 oracle leaf 不得互换。

```text
D10TypedFixtureCatalog
  catalog_id / version / case_count / catalog_hash / cases[]

D10FixtureCase
  case_id / primary_partition / family_id / grain
  owner_route / clinical_claim_token / disposition
  fixture_id / fixture_hash / oracle_case_id / manifest_case_id
  expected_leaf_set = null
  expected_trace_leaf_set = null
  expected_source_leaf_set = null
  mutation_class / audience_contract / typed_input

D10OracleCase
  oracle_case_id / case_id
  expected_leaf_set[] / expected_trace_leaf_set[] / expected_source_leaf_set[]
  expected_disposition_or_gate / forbidden_leaf_set[] / oracle_hash

D10RegistryRow
  case_id / fixture_id / oracle_case_id / manifest_case_id / test_id

D10PartitionQuotaManifest
  manifest_id / required_total = 312
  primary_partition_requirements{}
  mandatory_attack_requirements{}
  actual_mandatory_attack_counts{}
  case_to_mandatory_attack_rows[]
  actual_primary_partition_counts{}
  case_id_union[] / pairwise_intersection_counts{}
  union_count / duplicate_case_ids[] / missing_case_ids[]
  catalog_hash / oracle_hash / registry_hash / generator_hash / manifest_hash
```

catalog 顶层和 case/object 全部 exact keys；catalog 中三个 expected leaf 字段只能是 `null`，真实 expected 只存在独立 oracle。registry 必须一一双射；generator 只从 typed inputs 与冻结 contract 生成，禁止 import/read oracle 或 registry。双遍 replay 排除 wall-clock/PID/mtime，输出 canonical byte/hash 全等。每个 mandatory attack 至少一个独立 exact case，case-to-attack 映射必须双向可查；一个 case 可证明多个 attack，但 primary partition 仍只计一次，不降低 312 总下限。

必须包括以下强制攻击：

- 首次 full 被伪造为“新增/关闭”；
- D09 单中心趋势被 D10 重算；
- 将 D09 pattern、成员风险和 D10 signal 相加为总风险数；
- 只改规则/method/visibility 却显示临床改善；
- 零事件、空分母、缺 coverage 被判 negative；
- 小中心被异常率置顶并标成质量差；
- 未授权盲态下通过人数/分母/颜色推断治疗组；
- 疗效缺失处理或 estimand 不同仍强制比较；
- Safety/Efficacy p 值或模型多数票直接创建 positive；
- 高风险单例被项目低比例或小样本提示隐藏；
- rehashed Query/projection/resolved result 绕过 evaluator identity；
- audience 中文字段注入 pattern/rule/mode/window/revision/scope/policy 等工程引用。

`mandatory_attack_requirements` 至少单列并要求每项 `>=1`：cross-project scope、legal-row mismatch、initial-full fake change、strict-cutoff predicate tamper/same-window replay、cutoff first-positive create、cutoff+rule-or-mode mixed first-positive、required L1 hole、gap-only provenance、measure-origin cross-envelope/mixed-origin、D09 parent-descendant duplication、D07 risk-safety-measure same origin、denominator/time-segment tamper、small/late site stigma、blind hidden-set omission、hidden subject/site deep-link and eligible-set subset violation、treatment assignment missing、formal safety/efficacy wording、model majority/ensemble=1、R2 wrong prior/lineage/carry-forward、Query reorder/source/PD/redundancy tamper、projection/deep-link visibility tamper、Unicode/confusable engineering injection、rule/method/visibility mixed change、high-risk singleton not hidden。

## 16. 非 LLM 验收锚点

冻结与后续 artifact/runtime 必须分别证明：

1. legal definition matrix、expected-set、L1 守恒与零越权医学输出；
2. typed schema/exact keys/closed enums/canonical hash；
3. member、site、subject、denominator、population、window、method 与 source locator 全部可反向解析；
4. 所有率/估计可由 member ledger 独立复算；
5. initial/full/incremental/change-cause/lineage 确定性；
6. blind/visibility non-disclosure 与 evaluation/projectable 集合隔离；
7. D01-D09 risk/count/query/lifecycle 不被修改；
8. project signal、clue、query 与 D01-D09 计数不混加；
9. Query 三分句、冗余证明、成员展开与 audience 工程引用拦截；
10. 双遍 replay、输入重排、重复提交、rehashed tamper、Unicode/格式字符攻击；
11. 8911 停止、真实项目/服务/UI/医学写作零触碰。

## 17. v0.6 独立复核问题

独立 verifier 必须优先挑战：

1. 五个 signal kind 是否仍有 owner 重叠或将正式安全/疗效推断越权交给 D10；
2. cross-site outlier 到 positive 的前件是否足够防止中心污名化；
3. safety/efficacy 的 population、denominator、estimand、blind 与 visibility 门是否可执行且 fail closed；
4. initial full、data change 与 method/rule/coverage change 是否可能混淆；
5. 分层计数、成员去重、D09 pattern 与个体成员是否仍可能重复计算；
6. Query 与 R5 projection 是否能被重哈希对象或工程引用注入绕过；
7. 312-case 互斥 primary 配额是否覆盖最可能的漏报、误报与反过拟合缺口。

## 18. v0.6 修订记录

v0.2 针对首轮独立 verifier 的 15 项阻断完成；v0.3 关闭第二轮 13 项残余；v0.4 关闭第三轮六项窄缺口；v0.5 关闭第四轮五项残余；v0.6 关闭第五轮两个传播缺口：

- 冻结 exact legal rows 与越权零医学输出；
- 补齐 expected-set、comparison/window gate；
- 修复 revision/hash 配对与 evaluation identity；
- 增加 numeric/time 等式、per-site comparability evidence；
- 增加 safety/efficacy 条件 context；
- 固定 completeness precedence、R2 prior/action/idempotency；
- 隔离 D09 parent 与 descendant numerator；
- 增加 Query/projection authoritative rebuild 与 audience 注入拦截；
- 增加 visibility/blind/deep-link non-disclosure；
- 增加 baseline/change 状态机与 mixed-change 阻断；
- 将互斥 primary quota 总下限修正为 312，并补齐 catalog/oracle/registry/generator/quota exact schema。
- 为 member/site/gap/measure 增加逐对象 project/scope/revision/current binding 与 legal-row binding；
- 把 mode 内容、实际 visibility decision/sets 纳入 evaluation identity；
- 将 lineage/change/completeness 纳入 R2 idempotency，冻结 action×lineage；
- 增加 gap、source-origin、time-source recomputation、treatment assignment 条件 schema；
- 固定 visibility 集合代数、Query 全对象 identity、typed 中文模板与 ModelEvidence exact schema；
- 增加 mandatory-attack 子配额与 case-to-attack 证明。
- 顶层 envelope 改用 source revision-content pairs，并承载 scope/mode/cutoff hash；
- 允许经严格证明的 cutoff-advance first-positive create；
- 固定 measure-origin 集合分割、site/subject deep-link 集合守恒；
- 将 Query member/policy 纳入 redundancy identity，并把 ModeContract change 纳入非数据变化原因。
- 为 measure-origin 增加 paired source provenance 与 origin partition 状态映射；
- 增加严格 cutoff-advance decision 并绑定 change/R2；
- 深链使用闭集 target kind，禁止 subject-only 泄露；
- Query redundancy 集合与 member Query content identity 使用 sorted-unique canonical encoding。
- cutoff advance 改为由 accepted authority/anchors 重建的 derived-only decision，first-positive create 禁止任何非数据混合变化；
- deep-link eligible member/site/subject-site pair 强制为 projectable 集合子集并由 validator 重建。

本 v0.6 仍不是冻结合同。只有独立 verifier 对固定 SHA 快照给出明确接受、Codex 复核门通过并形成接受记录后，才可解锁 D10 artifact 构建；runtime 仍需后续独立门禁。
