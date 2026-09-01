# R4-D06 疗效终点、量表与个体趋势纵切合同 v1.18

Date: 2026-08-12  
Status: `FROZEN_R4_D06_CONTRACT_V1_18`  
Scope: 仅限合成/离线 R4 纵切及据此开展 R4 POC 有界实现纠偏；不代表实现、R4 总体、R5 UI、真实项目、统计分析、产品或生产接受。

## 1. 目标、用户问题与禁区

D06 把方案、SAP、量表/终点算法和 accepted 受试者评估记录拆成可追溯、可重放的评价单元，面向中文医学监察员回答：

1. 当前研究实际收集了哪些疗效/症状/功能评估，原始组成项是否足以按指定版本计算；
2. 已记录总分、变化值、反应/进展分类能否由已接受原始项、基线和冻结算法复现；
3. 个体随访中的改善、恶化、突变、反复或持平是否真实存在，是否受缺项、评估者、时间点、重复测量或干扰事件影响；
4. 如何在共享访视轴上快速看到趋势、阈值、资料缺口、风险和原始依据。

D06 只产生“疗效评估数据待核实”“量表计分待核实”“基线选择待核实”“个体变化待核实”等具体问题、风险标记和三段式 Query 草稿。它不宣称试验有效/无效，不进行组间比较、p 值、多重性、敏感性分析或总体获益判断；不替代统计编程、SAP、CSR/TFL；不由模型补算权威终点、补值或选择最有利解释。

D06 输出严格停在受试者级稳定结果、个体趋势和供 D10 消费的 typed inputs；不得形成中心、项目、治疗组或总体分母、聚合趋势、比较或推断。所有中心/项目/治疗组聚合唯一由 D10 生成。

本合同不运行 OCR/VLM、真实项目、真实 provider 或产品服务；不启动 8911；不改 R1-R3、R5 UI、医学写作子系统或安全相关实现/测试；不把项目名、药物名、适应症、固定量表、阈值、访视号、表名或字段名写入通用内核。

## 2. 外部依据与项目来源权威

### 2.1 规范依据

- **ICH E9(R1)**：estimand、estimator、estimate 与 sensitivity analysis 分离；干扰事件会影响结局测量的存在或解释，不能和缺失数据混同。
- **FDA Multiple Endpoints (2022)**：主要、共同主要、次要、探索性、复合和多组成终点必须保持层级与结构；未控制多重性时不得作总体药效结论。
- **FDA PFDD COA Guidance 3 (2025)**：PRO、ObsRO、ClinRO、PerfO 的概念、使用情境、评估者、实施方式、计分算法和缺项规则共同决定结果能否解释。
- **CDISC ADaMIG v1.3**：借鉴参数、分析值、基线、变化值、分析时点和源数据 traceability 的结构思想；不强制要求输入为 ADaM。
- **EMA Missing Data guideline**：缺失处理必须预设并与分析问题对齐，不存在通用插补方法。

外部发现、核验范围和取舍记录在 `context/medical_monitoring_r4_d06_efficacy_external_pattern_decision_20260812.md`。

### 2.2 项目内来源权威

来源按 claim scope 分层，不用多数票或模型置信度解决冲突：

1. **定义权威**：事件时适用的方案/SAP/正式修订、终点定义、量表手册、评分/缺项/重复测量/基线/反应阈值/干扰事件规则；
2. **原始观察权威**：当前 Run accepted full snapshot 中的 item、原始读数、评估者、实施方式、日期/访视和更正 lineage；
3. **派生结果权威**：accepted analysis result 或由冻结确定性算法从 accepted 原始记录重算的结果；二者并存时分别保留并比较，不默认 analysis result 或重算值覆盖另一方；
4. **例外/解释权威**：事件时已生效且可定位的复核、更正、重复测量、量表实施例外和 SAP 预定义处理；
5. **辅助来源**：汇总表、外部监查报告、模型输出、自由文本和历史图表只能帮助定位，不能覆盖定义或 accepted source record。

无法唯一确认适用版本、算法、基线、单位、评估者、时间点或更正顺序时进入 `boundary` 或 `not_evaluable`；不得选“最新”“最完整”“变化最大”或“最符合预期”的值。

## 3. 唯一 owner 与相邻域边界

| Claim | 唯一 owner | D06 可消费/输出 | D06 禁止 |
|---|---|---|---|
| 评估是否按计划完成、是否超窗、访视/活动归属 | D05 | 消费 typed occurrence/timing/assignment ref；在趋势轴上显示 | 重复“缺评估/超窗”风险与 Query |
| 量表组成项、计分、基线、变化、反应/进展分类、个体纵向值 | D06 | 确定性复算、比对、个体趋势和待核实风险 | 总体疗效统计结论 |
| 实验室/检查的单位、参考范围、异常、CTCAE 与安全意义 | D07 | 仅消费已被端点定义明确指定的 typed endpoint value | 复制实验室异常/安全风险 |
| 跨 AE/MH/CM/IP/PD/疗效的关系 | D08 | 显示 producer 已验证的 typed context/relationship ref | 仅凭同日/文本自行建立因果或一致性结论 |
| 项目级疗效聚合、分母、中心/治疗组趋势和统计解释 | D10 | 提供稳定的个体结果与 coverage | 在 D06 形成项目级结论 |
| 正式 PD 判定/分级/报送 | 现有外部责任方；D04 只提示待核实 | Query 可请求核实数据或方案执行 | 正式判定或建立 PD workflow |

方案解构器可提取全域信息，但 owner routing 必须先于 D06 expected-set。owner 不唯一时只生成一个 `EfficacyGate(gate_kind=routing)`，不在多个域复制 evaluation unit、风险或 Query。

## 4. 领域对象与稳定身份

所有对象均为 immutable record；任何更改生成新版本与 lineage。自由文本、模型解释、风险等级、Query 和当前结果不得进入稳定身份核心。

### 4.1 定义对象

```text
EfficacyEndpointDefinition:
  endpoint_definition_id/stable_endpoint_key/project_scope/protocol_or_sap_version
  audience_name/concept_of_interest/endpoint_role
  endpoint_kind=single_measure|change_from_baseline|percent_change|
                responder|time_to_event|composite|multi_component|ordinal_shift
  source_measure_keys/component_keys/combination_rule_id
  percent_change_rule_id?/numeric_policy_id
  responder_confirmation_rule_id?
  directionality=higher_better|lower_better|bidirectional|event_based|undefined
  analysis_timepoint_keys/estimand_context_ref?
  source_locator_ids/definition_hash

AssessmentInstrumentDefinition:
  instrument_definition_id/stable_instrument_key/version
  audience_name/reporter_type=PRO|ObsRO|ClinRO|PerfO|objective_measure
  concept_of_interest/context_of_use/administration_mode/recall_period
  item_definition_ids/allowed_rater_roles/value_domain_definition_id
  source_locator_ids/definition_hash

ScoringAlgorithmDefinition:
  algorithm_id/stable_algorithm_key/version
  instrument_definition_id/ordered_operation_ids
  missing_item_strategy_id/value_domain_definition_id
  numeric_policy_id/implementation_hash
  source_locator_ids

BaselineRuleDefinition:
  baseline_rule_id/stable_baseline_rule_key/version
  eligible_time_relation/eligible_visit_or_phase_keys
  pre_intervention_requirement/selection_policy_id
  prohibited_postbaseline_states
  source_locator_ids/definition_hash

AnalysisTimepointDefinition:
  timepoint_definition_id/stable_timepoint_key/version
  visit_or_window_ref/nominal_time_ref/maturity_rule_id
  repeat_selection_policy_id/cutoff_rule_id
  source_locator_ids/definition_hash

IntercurrentEventRuleDefinition:
  ice_rule_id/stable_ice_rule_key/version
  event_role=treatment_discontinuation|rescue_therapy|treatment_switch|
             death|withdrawal|other_prespecified
  strategy=treatment_policy|hypothetical|composite|while_on_treatment|
           principal_stratum|context_only
  applicability/required_source_roles/source_locator_ids/definition_hash

EfficacyRunScopeBinding:
  scope_binding_id/project_ref/run_ref/monitoring_mode
  source_revision/accepted_snapshot_ref/snapshot_as_of/clinical_event_cutoff
  protocol_version/sap_version/mapping_version/algorithm_set_version
  source_locator_ids/lineage_hash

EfficacyDefinitionBindingDecision:
  binding_decision_id/project_ref/run_ref/monitoring_mode/subject_ref/site_ref
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff/episode_key
  arm_key/cohort_key/phase_key/applicability_input_refs
  stable_endpoint_key
  candidate_endpoint_definition_ids/candidate_instrument_definition_ids
  candidate_algorithm_ids/candidate_baseline_rule_ids/candidate_timepoint_ids
  candidate_ice_rule_ids/selected_endpoint_definition_id?
  selected_instrument_definition_id?/selected_algorithm_id?
  selected_baseline_rule_id?/selected_timepoint_id?/selected_ice_rule_ids
  decision_status=unique|multi_feasible_boundary|not_evaluable|not_applicable
  applicability_rule_ids/predicate_results/rejected_candidate_reasons
  applicability_evaluation_decision_id
  source_locator_ids/lineage_hash

ApplicabilityRuleDefinition:
  applicability_rule_id/version/ordered_predicate_ids
  combination=all|any|ordered_first_match
  no_match_outcome=not_applicable|not_evaluable
  missing_input_outcome=not_evaluable/conflict_outcome=boundary
  source_locator_ids/hash

ApplicabilityPredicate:
  predicate_id/sequence
  left_role=arm|cohort|phase|episode|site|protocol_version|sap_version|
            randomization_state|treatment_state|cutoff_state
  operator=equals|not_equals|in_set|not_in_set|exists|not_exists|
           interval_on_or_before|interval_after
  typed_right_value?/typed_right_set?/temporal_rule_id?
  source_locator_ids/hash

ApplicabilityEvaluationDecision:
  decision_id/project_ref/run_ref/subject_ref/site_ref/episode_key
  scope_binding_id/candidate_definition_ids/applicability_rule_ids
  predicate_result_ids/matched_candidate_definition_ids
  selected_candidate_definition_id?
  decision_status=unique|not_applicable|boundary|not_evaluable
  no_match_rule_outcomes/reason_codes/source_locator_ids/hash

ApplicabilityPredicateResult:
  predicate_result_id/predicate_id/candidate_definition_id
  truth_state=match|no_match|unknown|conflict
  input_ref_ids/reason_codes/hash

NumericExecutionPolicy:
  numeric_policy_id/version/decimal_precision
  rounding_mode=half_even|half_up|half_down|floor|ceiling|truncate
  negative_zero_policy=normalize_zero|preserve
  nan_policy=reject/positive_infinity_policy=reject/negative_infinity_policy=reject
  overflow_policy=reject/underflow_policy=reject
  canonical_decimal_rule/source_locator_ids/hash

ScoringOperation:
  operation_id/sequence/order_key
  operation_kind=select_items|select_measure|validate_range|reverse_score|unit_convert|
                 apply_weight|aggregate_sum|aggregate_mean|aggregate_min|
                 aggregate_max|transform_linear|transform_lookup|
                 handle_missing|round|classify_threshold
  typed_parameters/parameter_schema_kind/input_keys
  typed_producer_consumption_binding_ids/output_key
  numeric_policy_id
  source_locator_ids/operation_hash

SelectItemsParams:
  ordered_item_definition_keys/allow_unlisted_items=false

SelectMeasureParams:
  input_measure_key/expected_unit/direct_endpoint_definition_id

ValidateRangeParams:
  minimum?/maximum?/minimum_inclusive/maximum_inclusive
  allowed_values?/input_unit/out_of_range_outcome=reject|not_evaluable

ReverseScoreParams:
  formula=constant_minus_value|minimum_plus_maximum_minus_value
  constant?/minimum?/maximum?/input_unit/output_unit

UnitConvertParams:
  formula=affine/output_value_unit
  multiplier/addend/input_value_unit

ApplyWeightParams:
  weight_by_input_key/output_value_unit

AggregateParams:
  aggregate_kind=sum|mean|min|max
  ordered_input_keys/empty_input_outcome=reject|not_evaluable
  output_value_unit

TransformLinearParams:
  slope/intercept/input_value_unit/output_value_unit

TransformLookupParams:
  complete_input_to_output_map/input_domain_hash/output_value_unit
  unknown_input_outcome=reject|not_evaluable

HandleMissingParams:
  missing_item_strategy_id/expected_input_keys

RoundParams:
  decimal_places/rounding_mode/output_value_unit

ClassifyThresholdParams:
  comparator=lt|le|eq|ge|gt/threshold/threshold_unit
  true_class/false_class

MissingItemStrategy:
  strategy_id/version
  strategy_kind=reject_score|prorate_mean|prorate_sum|explicit_constant
  minimum_answered_count/minimum_answered_fraction
  execution_stage=before_reverse|after_reverse|before_weight|after_weight|
                  before_aggregate|after_aggregate
  typed_parameters/source_locator_ids/hash

PercentChangeRuleDefinition:
  percent_change_rule_id/version
  numerator_formula=post_minus_baseline|baseline_minus_post
  denominator_role=baseline|absolute_baseline|other_explicit
  explicit_denominator_input_key?/explicit_denominator_unit?
  multiplier/zero_denominator_policy=reject|not_applicable|explicit_constant
  zero_denominator_constant?/zero_denominator_constant_unit?
  negative_denominator_policy=allow|reject|absolute_value
  numeric_policy_id/source_locator_ids/hash

EndpointCombinationRule:
  combination_rule_id/version
  combination_kind=any_component|all_components|ordered_hierarchical|
                   first_event|weighted_sum|multi_component_all
  ordered_component_keys/component_weights?/precedence?
  missing_component_policy=propagate_missing|not_responder|not_event|
                           not_evaluable
  numeric_policy_id/source_locator_ids/hash

ValueDomainDefinition:
  value_domain_definition_id/version/value_kind=numeric|integer|ordinal|categorical
  allowed_values?/minimum?/maximum?/unit_or_scale
  normalization_map?/unknown_value_policy=reject
  source_locator_ids/hash

CandidateSelectionPolicy:
  selection_policy_id/version
  stable_endpoint_key?/value_key?/directionality?
  eligibility_predicate_ids/no_candidate_outcome=not_evaluable|not_applicable
  ordered_predicates=explicit_parent|source_mapping|episode_match|role_match|
                     mode_match|window_match|chronological_first|
                     chronological_last|worst_value|best_value
  tie_outcome=boundary|not_evaluable
  numeric_policy_id?/source_locator_ids/hash

D06PriorityPolicy:
  policy_id/version
  ordered_precedence_rules[
    step/impact_classes?/trigger_any?/high_if_recoverability?/
    high_if_recurrence?/medium_if_recurrence?/otherwise_priority?/
    monitoring_priority?/reason_codes/machine_close_forbidden?/
    high_machine_close_forbidden?
  ]
  source_locator_ids/policy_hash

D06PriorityResolverInput:
  project_ref/run_ref/monitoring_mode/subject_ref/site_ref/episode_key
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  endpoint_definition_id/stable_endpoint_key/stable_timepoint_key
  priority_policy_id/priority_policy_version/priority_policy_hash
  endpoint_role/impact_resolution_state/impact_class?
  recurrence_class/recoverability/actionability
  monitoring_priority/matched_precedence_step/reason_codes
  machine_close_forbidden/source_locator_ids/hash

D06PriorityDecision:
  priority_decision_id/project_ref/run_ref/monitoring_mode/subject_ref/site_ref
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff/episode_key
  unit_id/risk_id/endpoint_definition_id/stable_endpoint_key/stable_timepoint_key
  priority_policy_id/priority_policy_version/priority_policy_hash
  endpoint_role/impact_resolution_state=resolved|unresolved/impact_class?
  recurrence_class/recoverability/actionability
  monitoring_priority=low|medium|high|unknown
  matched_precedence_step/reason_codes/machine_close_forbidden
  priority_resolver_input_hash/source_locator_ids/lineage_hash

TrendPatternRuleDefinition:
  trend_rule_id/version/pattern_kind=absolute_jump|relative_jump|
               direction_reversal|flat_score_item_shift|rate_of_change
  stable_endpoint_key/input_result_role
  threshold/threshold_unit/comparator=ge|gt/minimum_point_count
  relative_multiplier=1|100?/zero_reference_policy=not_evaluable|boundary?
  duration_offset_id?/duration_unit=hours|days|weeks?/duration_normalization=per_unit?
  item_difference_threshold?/minimum_changed_item_count?/score_tolerance_rule_id?
  directionality/window_timepoint_keys?/candidate_selection_policy_id
  required_evidence_roles/source_locator_ids/hash

AssessmentEquivalenceRule:
  equivalence_rule_id/version
  from_stable_instrument_key/to_stable_instrument_key
  stable_endpoint_key?/context_of_use_key
  from_reporter_type/to_reporter_type/from_recall_period/to_recall_period
  from_admin_mode/to_admin_mode/from_central_or_local/to_central_or_local
  equivalence_state=equivalent|not_equivalent
  source_locator_ids/hash

CandidateSelectionDecision:
  decision_id/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  selection_policy_id
  consumer_kind=baseline|repeat|maturity|responder|trend
  consumer_unit_or_result_id/stable_endpoint_key/stable_instrument_key
  stable_timepoint_key/rule_role
  ordered_candidate_ids/selected_candidate_id?
  decision_status=unique|tie_boundary|not_evaluable|not_applicable
  predicate_results/rejected_candidate_reasons
  d05_assessment_binding_ref_ids/shared_spine_hash
  source_locator_ids/hash
```

`endpoint_role` 是关闭集合：`primary|co_primary|multiple_primary|key_secondary|secondary|exploratory|supportive|undefined`。`undefined` 阻断任何基于层级的优先级和总体表述。`estimand_context_ref` 只保存方案/SAP 预设语义；D06 不计算总体 estimand。

量表、算法和终点定义分别版本化。名称相同不证明版本相同；算法版本改变时必须 supersede 或并行保留，不得静默重算既往结果。

`ScoringAlgorithmDefinition.ordered_operation_ids` 只能引用上述关闭 `ScoringOperation`；所有参数必须 typed、按 `sequence` 执行并由 `NumericExecutionPolicy` 规范化。未知 operation、自由表达式、动态代码或未支持的参数一律打开 `algorithm` gate，不得由实现自行解释。缺项、舍入、变换、候选选择和终点组合必须分别解析为上述内容寻址对象；opaque string 或“按手册处理”不能进入执行，复杂手册规则须先编译成关闭 operations 并经确定性 QC。

`ScoringOperation` 的 `parameter_schema_kind` 必须与 `operation_kind` 一一对应：`select_items→SelectItemsParams`、`select_measure→SelectMeasureParams`、`validate_range→ValidateRangeParams`、`reverse_score→ReverseScoreParams`、`unit_convert→UnitConvertParams`、`apply_weight→ApplyWeightParams`、四类 aggregate→`AggregateParams` 且 aggregate_kind 同名、`transform_linear→TransformLinearParams`、`transform_lookup→TransformLookupParams`、`handle_missing→HandleMissingParams`、`round→RoundParams`、`classify_threshold→ClassifyThresholdParams`。每个 operation 恰有一个对应参数对象，其他参数对象禁止；字段少填、多填、单位不兼容、非有限十进制、lookup domain 不完整或 output key 重复均为 schema/QC fail。`unit_convert` 公式唯一为 `output=input×multiplier+addend`；`transform_linear` 同式但只用于方案/手册定义的评分变换；两者不得互相替代。`apply_weight` 要求每个 input key 恰有一个权重，aggregate 的 ordered inputs 与真实消费顺序完全一致。

`EndpointCombinationRule` 的 conditional schema 固定：所有 kind 的 `ordered_component_keys` 非空、唯一且顺序入 hash；`weighted_sum` 恰有与每个 component key 一一对应的有限 `component_weights`，其他 kind 禁止 weights；`ordered_hierarchical|first_event` 恰有与 component keys 等长且无重复的 `precedence`，其余 kind 禁止 precedence；所有 kind 都必须给出 missing policy。`any_component|all_components|multi_component_all` 只消费关闭的 component states；`first_event` 另须绑定 TTE precedence；`weighted_sum=Σ(component_value×weight)` 后仅按 numeric policy 舍入。缺组成项时只执行显式 missing policy，不允许默认零填充、跳过或重分配权重。

适用性 truth function 固定：`conflict` 优先形成 boundary；`all` 在任一 no_match 时 no_match，全部 match 时 match，否则 unknown；`any` 在任一 match 时 match，全部 no_match 时 no_match，否则 unknown；`ordered_first_match` 按 sequence，首个 match 之前若出现 unknown 则 unknown、conflict 则 boundary，全部 no_match 时 no_match。每个 candidate definition 得一个总结果；恰一 candidate match 才 unique，多 candidate match 为 boundary，无 match 且全部 no_match 按 rule 的 no-match outcome，存在 unknown 为 not_evaluable。selected predicate/definition IDs、全部 operand results 和 hash 必须持久化。

跨 candidate/rule 聚合持久化为 `ApplicabilityEvaluationDecision`：任一 conflict → boundary；否则任一 unknown 或任一 no-match rule outcome=not_evaluable → not_evaluable；否则恰一 match → unique；多 match → boundary；零 match 且所有规则一致返回 not_applicable → not_applicable；零 match 但 no-match outcomes 不一致 → not_evaluable。selected candidate 只在 unique 时必填，其余状态禁止。definition binding decision 必须引用该 evaluation decision，不能二次解释。

operator conditional schema：`equals|not_equals` 恰有 typed_right_value；`in_set|not_in_set` 恰有非空 typed_right_set；`exists|not_exists` 不允许任何 right operand；`interval_on_or_before|interval_after` 恰有 temporal_rule_id，且规则冻结 inclusivity/timezone/partial-date propagation。多填、少填或类型不匹配直接 schema/QC fail，不能降为实现自选 operand。

### 4.2 观察、基线与派生对象

```text
ActualAssessmentRecord:
  id/assessment_id/stable_assessment_key/project_ref/run_ref/subject_ref/site_ref
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff/episode_key
  instrument_definition_id/assessment_time_ref
  recorded_visit_ref/reporter_type/reporter_role/reporter_id_role
  actual_recall_period/admin_mode/central_or_local_role/equivalence_rule_id?
  item_record_ids/record_status=accepted_current|superseded|withdrawn
  correction_status=original|corrected|superseding
  prior_assessment_id?/supersedes_assessment_id?/scope_decision_id
  d05_unit_id/d05_planned_activity_key/d05_actual_activity_key
  occurrence_disposition/timing_disposition/assignment_status
  source_locator_ids/lineage_hash

AssessmentItemRecord:
  item_record_id/stable_item_record_key/assessment_id/item_definition_id
  raw_value/normalized_value/value_unit/missing_reason
  record_status=accepted_current|superseded|withdrawn
  correction_status=original|corrected|superseding|superseded
  prior_item_record_id?/supersedes_item_record_id?
  source_locator_ids/content_hash

BaselineSelectionDecision:
  baseline_decision_id/project_ref/run_ref/monitoring_mode/subject_ref/site_ref
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff/episode_key
  stable_endpoint_key/stable_timepoint_key
  candidate_assessment_ids/selected_assessment_id?
  decision_status=unique|multi_feasible_boundary|not_evaluable|not_applicable
  predicate_results/rejected_candidate_reasons
  baseline_rule_id/d05_assessment_binding_ref_ids/shared_spine_hash
  source_locator_ids/lineage_hash

Baseline decision conditional schema: `unique` requires exactly one non-empty selected assessment contained in candidate list; `multi_feasible_boundary|not_evaluable|not_applicable` prohibit selected assessment. Candidate list is canonical sorted, may be empty only for not_evaluable/not_applicable, and never uses null entries.

DerivedEfficacyResult:
  result_id/stable_result_key/project_ref/run_ref/subject_ref/site_ref
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id
  stable_endpoint_key/stable_timepoint_key/episode_key
  result_role=accepted_source|deterministic_recalculation
  producer_kind=accepted_analysis_artifact|deterministic_engine
  accepted_analysis_artifact_ref?
  analysis_value/unit/baseline_value/change/percent_change
  response_or_progression_class?/event_or_censoring_state?
  algorithm_id/input_item_ids/input_result_ids/baseline_decision_id
  maturity_anchor_selection_decision_id
  repeat_selection_decision_id?/candidate_selection_decision_ids
  component_result_refs/responder_confirmation_selection_decision_id?
  responder_confirmation_assessment_refs
  d05_assessment_binding_ref_ids/shared_spine_hash
  time_to_event_result_ref?
  derivation_status=complete|boundary|not_evaluable
  source_locator_ids/lineage_hash/content_hash

AcceptedMonitoringReportClaim:
  report_claim_id/object_type=AcceptedMonitoringReportClaim
  project_ref/run_ref/monitoring_mode/subject_ref/site_ref/episode_key
  source_revision/accepted_snapshot_ref/scope_binding_id
  stable_endpoint_key/stable_timepoint_key
  claim_kind=individual_trend/claim_value
  acceptance_state=accepted/source_locator_ids/content_hash

AcceptedIndividualTrendSource:
  trend_source_id/object_type=AcceptedIndividualTrendSource
  project_ref/run_ref/monitoring_mode/subject_ref/site_ref/episode_key
  source_revision/accepted_snapshot_ref/scope_binding_id
  stable_endpoint_key/stable_timepoint_key/trend
  accepted_result_ids/source_locator_ids/content_hash

ComponentResultRef:
  component_ref_id/component_key/component_result_id
  component_state=observed|event|non_event|responder|non_responder|
                  missing|not_applicable|not_evaluable
  value?/unit?/event_time_ref?/d05_assessment_binding_ref_ids
  shared_spine_hash/source_locator_ids/hash

TimeToEventResult:
  time_to_event_result_id/project_ref/run_ref/monitoring_mode/subject_ref/site_ref
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff/episode_key
  stable_endpoint_key/stable_timepoint_key
  origin_time_ref/event_time_ref?/censor_time_ref?
  status=event|competing_event|censored|boundary|not_evaluable
  target_event_ref?/censor_reason?/competing_event_ref?/time_unit
  tte_endpoint_precedence_binding_id/event_precedence_rule_id/numeric_policy_id
  feasible_interpretation_ref_ids
  source_locator_ids/lineage_hash

TimeToEventInterpretationRef:
  interpretation_ref_id/project_ref/run_ref/monitoring_mode/subject_ref/site_ref
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff/episode_key
  state=event|competing_event|censored/origin_time_ref
  event_time_ref?/censor_time_ref?/target_event_ref?/competing_event_ref?/censor_reason?
  stable_source_identity/validation_state=validated/source_locator_ids/hash

EndpointComparisonDecision:
  comparison_id/scope_binding_id/accepted_result_id?/recalculated_result_id?
  comparison_status=consistent|inconsistent|boundary|not_evaluable
  compared_fields/tolerance_rule_id/reason_codes/source_locator_ids/hash

ToleranceRuleDefinition:
  tolerance_rule_id/version/comparison_kind=absolute|relative|decimal_places|exact
  threshold?/reference_role=accepted_value|recalculated_value|maximum_absolute_value
  decimal_places?/inclusive=true|false
  precomparison_rounding=false|true/numeric_policy_id
  missing_or_nonfinite_policy=not_evaluable|reject
  source_locator_ids/hash

TemporalOffset:
  temporal_offset_id/value/unit=minutes|hours|days|weeks|months|years
  arithmetic=elapsed_duration|calendar_component
  end_of_month_policy=clamp_to_last_day|reject
  source_locator_ids/hash

TimeToEventPrecedenceRuleDefinition:
  precedence_rule_id/version
  ordered_states=event|competing_event|censored
  tie_policy=first_in_order|boundary|not_evaluable
  competing_event_type_refs/source_locator_ids/hash

ResponderConfirmationRuleDefinition:
  confirmation_rule_id/version/required_count
  sequence_rule=consecutive_eligible|any_eligible_in_window|fixed_timepoints
  ordered_required_timepoint_keys?/minimum_gap_offset_id?/maximum_gap_offset_id?
  window_anchor_kind=first_qualifying_assessment|fixed_timepoint|typed_protocol_anchor
  window_anchor_selection_policy_id/fixed_anchor_timepoint_key?
  window_start_offset_id?/window_end_offset_id?
  lower_inclusive/upper_inclusive/partial_date_outcome=boundary|not_evaluable
  intervening_assessment_policy=must_also_qualify|ignored|breaks_sequence
  candidate_selection_policy_id/source_locator_ids/hash

ResponderConfirmationSelectionDecision:
  decision_id/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  stable_endpoint_key/stable_timepoint_key/confirmation_rule_id
  candidate_assessment_ids/selected_assessment_ids
  selected_time_refs/d05_assessment_binding_ref_ids/shared_spine_hash
  decision_status=confirmed|not_confirmed|boundary|not_evaluable
  predicate_results/rejected_candidate_reasons/source_locator_ids/hash

TypedProducerEventRef:
  ref_id/producer_domain/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  stable_event_identity/event_role/effective_time_ref
  producer_version/validation_state=validated/source_locator_ids/lineage_hash

TTEEndpointPrecedenceBinding:
  binding_id/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  stable_endpoint_key/stable_timepoint_key/event_precedence_rule_id
  target_event_role/competing_event_type_refs/source_locator_ids/lineage_hash

TTESourceRegistry:
  stable_endpoint_key/stable_timepoint_key/event_precedence_rule_id/tie_policy
  origin_time_ref/event_time_ref/censor_time_ref
  target_event_ref/competing_event_ref/source_locator_ids/hash

TTEPrecedenceRule:
  event_precedence_rule_id/allowed_tie_policies/source_locator_ids/hash

TypedTTEEventSource:
  event_id/event_role=target_event|competing_event/effective_time_ref
  source_locator_ids/hash

AcceptedAnalysisArtifact:
  artifact_id/project_ref/run_ref/monitoring_mode/source_revision
  accepted_snapshot_ref/scope_binding_id/artifact_kind
  producer_kind=validated_statistical_program|validated_external_analysis
  acceptance_state=accepted/acceptance_decision_id/accepted_at
  immutable_payload_hash/source_locator_ids/lineage_hash

IntercurrentEventContext:
  ice_context_id/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  stable_endpoint_key/stable_timepoint_key/ice_rule_id
  typed_producer_event_ref/effective_time_ref/affected_result_ids
  strategy/estimator_binding_id?/estimator_availability=available|unavailable|not_required
  context_state=applicable|not_applicable|boundary|not_evaluable
  source_locator_ids/lineage_hash

EstimatorBinding:
  estimator_binding_id/project_ref/run_ref/monitoring_mode/subject_ref/site_ref/episode_key
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  stable_endpoint_key/stable_timepoint_key/estimand_context_ref
  estimator_definition_ref/implementation_version
  acceptance_decision_id/source_locator_ids/hash

D07EndpointValueRef:
  ref_id/producer_domain=D07/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  stable_endpoint_key/endpoint_definition_id/input_measure_key
  stable_source_identity/semantic_role=endpoint_input
  value/unit/effective_time_ref/validation_state=validated
  producer_version/source_locator_ids/lineage_hash

D07ConsumptionBinding:
  binding_id/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  d07_endpoint_value_ref_id
  consuming_endpoint_definition_id/input_measure_key/scoring_operation_id
  consumer_kind=select_measure_operation
  source_locator_ids/hash

D08RelationshipRef:
  ref_id/producer_domain=D08/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  left_stable_identity/right_stable_identity
  relationship_type/validation_state=validated/producer_version
  source_locator_ids/lineage_hash

D06RiskBinding:
  risk_id/project_ref/run_ref/monitoring_mode/subject_ref/site_ref/episode_key
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  unit_id/classifier/primary_subtype/priority_decision_id
  public_r4_risk_identity_id/R2_lifecycle_ref/source_locator_ids/lineage_hash

PublicR4RiskIdentity:
  public_r4_risk_identity_id/project_ref/domain_id=D06/risk_id/unit_id
  scope_type=subject_endpoint_timepoint_episode
  scope_key/subject_ref/site_ref/episode_key/scope_binding_id/cutoff
  stable_endpoint_key/stable_timepoint_key
  stable_source_or_event_identity
  normalized_concept=(classifier,unit_kind,stable_endpoint_key,
                      stable_instrument_key_or_none,stable_timepoint_key,
                      stable_item_or_component_key_or_none)
  temporal_window=(stable_timepoint_key,episode_key)
  rule_or_knowledge_lineage/public_identity_version
  canonical_tuple/public_identity_hash

D06UnitStableCore:
  unit_id/domain_id=D06/classifier/unit_kind
  stable_endpoint_key/stable_instrument_key_or_none/stable_timepoint_key
  stable_item_or_component_key_or_none/stable_source_record_id
  temporal_window/rule_or_knowledge_lineage/hash

EfficacyEvidenceRef:
  evidence_ref_id/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  unit_id/risk_id?
  direction=supporting|counterevidence|context|applicability
  stable_source_record_identity/effective_time_ref?/effective_interval_ref?
  rule_id/rule_version/applicability_rationale_code?
  accepted_artifact_ref?/source_locator_ids/lineage_hash

EnrollmentContextDecisionRef:
  decision_id/producer_domain=D04|D05/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  query_context/effective_time_ref
  source_event_refs/randomization_ref?/enrollment_ref?/first_dose_ref?
  decision_rule_id/rule_version/source_locator_ids/lineage_hash

EnrollmentSourceEvent:
  event_id/event_role/query_context/effective_time_ref
  source_locator_ids/hash

EnrollmentDecisionRule:
  decision_rule_id/rule_version/allowed_contexts/source_locator_ids/hash

AudiencePayloadValidationResult:
  validation_id/payload_kind=query|journey|risk_label
  payload_schema_version/payload_hash/language_policy=zh_cn_native
  required_fields_present/three_part_query_valid/pd_wording_valid
  forbidden_lexicon_version/forbidden_lexicon_hash
  forbidden_fragment_hits/forbidden_key_hits/empty_or_loglike_field_hits
  validated_display_string_paths
  validation_state=passed|failed/validator_version/hash

QueryAudiencePayload:
  payload_schema_version/query_id/participant_label/site_label
  endpoint_label/timepoint_label/priority_label
  basis_sentence/finding_sentence/action_sentence/source_jump_targets

JourneyAudiencePayload:
  payload_schema_version/projection_id/participant_label/site_label
  visit_axis_label/endpoint_lane_labels/marker_labels/risk_labels
  source_jump_targets/after_cutoff_section_label?/data_gap_section_label?

RiskLabelAudiencePayload:
  payload_schema_version/risk_id/participant_label/site_label
  endpoint_label/timepoint_label/risk_category_label/priority_label
  concise_finding/source_jump_targets

EfficacyRecordScopeDecision:
  scope_decision_id/actual_or_result_id/scope_binding_id
  event_effective_time_ref
  scope_status=in_scope|out_of_cutoff|boundary|not_evaluable
  reason_codes/source_locator_ids/lineage_hash
```

原始 `raw_value` 永不被规范化值或派生值覆盖。重复/更正记录通过 lineage 连接；`prior_item_record_id` 不等于删除既往记录。`stable_assessment_key` 不含可修订日期显示文本或结果值，必须由冻结业务身份与 episode 构造。

每个 `(assessment_id, item_definition_id)` 的 accepted correction graph 必须无环、无分叉且恰有一个 `record_status=accepted_current` terminal；上游记录为 superseded，撤回为 withdrawn 且不能参与计算。出现两个 current terminals、cycle、broken parent 或无 current terminal 时打开 algorithm/identity gate，禁止按录入时间或输入顺序选择。

同样，每个 `stable_assessment_key` 的 assessment-level correction graph 必须无环、无分叉、parent/supersedes 双向一致且恰有一个 accepted_current terminal；只有该 current assessment 的 item graphs 可进入 repeat/rater/baseline/score selection。两个 current assessments、branch、cycle、broken parent 或无 terminal 打开 identity gate，不得因每个 assessment 内部 item graph 自洽就同时纳入。

每个 assessment/result 在进入 inventory 前必须恰有一个 `EfficacyRecordScopeDecision` 并与当前 `EfficacyRunScopeBinding` 完全一致。`result_role=accepted_source` 时 `producer_kind` 必须为 `accepted_analysis_artifact` 且 `accepted_analysis_artifact_ref` 必填；`deterministic_recalculation` 时 producer 必须为 `deterministic_engine`。`model_output`、自由文本抽取或未接受分析附件不能伪装成任一路径，schema/QC fail closed。

`accepted_analysis_artifact_ref` 必须解析为 `AcceptedAnalysisArtifact(acceptance_state=accepted)`，且 artifact、result、scope decision 与 Run scope 的 project/run/mode/source revision/accepted snapshot/scope binding 全部精确相等，immutable payload hash 可重算，AcceptanceService decision 可定位；否则只能形成 coverage gap。任何模型产物即使数值相同也不能把 producer 改写成 accepted artifact。

`accepted_report_consistency` 只能比较完整 typed `AcceptedMonitoringReportClaim` 与完整 typed `AcceptedIndividualTrendSource`。二者必须同 scope、endpoint、timepoint，均有非空 source locators 且 content hash 可重算；source 的 `accepted_result_ids` 必须逐项解析同 scope 的 accepted source-backed result。仅有 `report.trend/source.trend` 字符串、场景描述或 expected text 不足以建立该单元，必须 fail closed。只有实际消费 report root 与 accepted result source 时才能输出 `accepted_artifact` trace edge；trace 不能由 manifest/expected outcome 补写。

### 4.3 评价、趋势与投影对象

```text
EfficacyEvaluationUnit:
  unit_id/project_ref/run_ref/monitoring_mode/subject_ref/site_ref/unit_kind
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  stable_endpoint_key/stable_instrument_key?/stable_timepoint_key/episode_key
  assessment_id?/derived_result_id?/baseline_decision_id?
  maturity_binding_state=required|not_required
  maturity_anchor_selection_decision_id?/maturity_not_required_reason?
  repeat_selection_decision_id?/candidate_selection_decision_ids
  d05_binding_state=required|not_required_by_unit_applicability
  coverage_unit_status_id/d05_assessment_binding_ref_ids?/shared_spine_hash?
  rule_id/rule_version/classifier/stable_core
  eval_disposition=positive|negative|boundary|not_applicable|not_evaluable
  primary_subtype?/secondary_reason_codes
  lineage_hash/source_locator_ids

EfficacyGate:
  gate_id/gate_kind=applicability|routing|definition|algorithm|
                    baseline|unit_or_scale|dependency|cutoff_scope
  gate_binding_ref_id
  project_ref/run_ref/monitoring_mode/subject_ref/site_ref/episode_key?
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  stable_endpoint_key?
  gate_state=open|closed
  decision_status=boundary|not_evaluable|resolved
  feasible_endpoint_definition_ids/feasible_instrument_definition_ids
  feasible_algorithm_ids/feasible_baseline_ids/feasible_timepoint_ids
  feasible_ice_rule_ids/selected_binding_decision_id?
  affected_timepoint_keys/affected_unit_keys/affected_set_hash
  missing_evidence_roles/reason_codes/source_locator_ids/lineage_hash
  prior_gate_id/resolved_by_decision_id
  counts_in_medical_expected_set=false/blocks_domain_complete

GateBindingRef:
  binding_ref_id/binding_kind=definition|owner_routing|dependency
  definition_binding_decision_id?/owner_routing_decision_id?
  dependency_decision_id?
  project_ref/run_ref/monitoring_mode/subject_ref/site_ref/episode_key?
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  decision_status=unique|resolved|boundary|not_evaluable
  source_locator_ids/hash

NormalizedTemporalValue:
  temporal_value_id/raw_value
  interval_start/interval_end/precision=date|datetime|month|year|unknown
  timezone/date_origin=recorded|derived
  derivation_algorithm_id?/input_locator_ids/uncertainty_reason_codes/hash

EfficacyEvaluationMaturityRule:
  maturity_rule_id/stable_timepoint_key/version
  anchor_kind=fixed_nominal|d05_actual_visit|randomization|first_ip_dose|
              prior_accepted_assessment|other_typed_protocol_anchor
  anchor_ref_role/anchor_selection_policy_id/stable_anchor_identity_required=true
  calendar_semantics=calendar|elapsed|study_day
  study_day_zero_policy=present|absent|not_applicable
  lower_offset_id/upper_offset_id/lower_inclusive/upper_inclusive
  grace_offset_id?/grace_inclusive?/maturity_point=window_open|window_close|grace_close
  timezone/required_precision
  source_locator_ids/hash

CutoffRuleDefinition:
  cutoff_rule_id/version/effective_time_role
  inclusion_rule=interval_fully_on_or_before|interval_start_on_or_before
  cutoff_inclusive/timezone/required_precision
  source_locator_ids/hash

MaturityAnchorSelectionDecision:
  decision_id/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  stable_timepoint_key/maturity_rule_id
  candidate_typed_anchor_ids/selected_typed_anchor_id?
  selected_normalized_time_ref?/selection_policy_id
  decision_status=unique|multi_feasible_boundary|not_evaluable
  predicate_results/rejected_candidate_reasons
  d05_assessment_binding_ref_ids?/shared_spine_hash?
  source_locator_ids/hash

TypedMaturityAnchorRef:
  anchor_ref_id/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  producer_domain/stable_source_identity
  anchor_kind/anchor_role/normalized_time_ref
  producer_version/validation_state=validated/source_locator_ids/hash

FixedNominalAnchorRef:
  anchor_ref_id/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  anchor_kind=fixed_nominal/stable_timepoint_key
  normalized_time_ref/maturity_rule_id/source_locator_ids/hash

D05AssessmentBindingRef:
  binding_ref_id/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id
  d05_unit_id/d05_planned_activity_key/d05_actual_activity_key
  occurrence_disposition/timing_disposition/assignment_status
  actual_time_ref/cutoff/producer_payload_hash/source_record_id/source_locator_ids/hash

D05AssessmentForeignKey:
  binding_ref_id/d05_unit_id/d05_planned_activity_key/d05_actual_activity_key
  occurrence_disposition/timing_disposition/assignment_status
  actual_time_ref/producer_payload_hash/source_record_id/hash

AcceptedD05AssessmentInventoryItem:
  source_record_id/d05_unit_id/d05_planned_activity_key/d05_actual_activity_key
  occurrence_disposition/timing_disposition/assignment_status
  actual_time_ref/producer_payload_hash/hash

D06MaturityConsumerBinding:
  consumer_id/maturity_decision_id/stable_endpoint_key/stable_timepoint_key
  project_ref/run_ref/monitoring_mode/subject_ref/site_ref/episode_key
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  shared_spine_hash/source_locator_ids/hash

SharedTemporalSpineBinding:
  spine_binding_id/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id
  d05_projection_id/axis_version/axis_hash/snapshot_as_of/cutoff
  source_locator_ids/hash

EfficacyTrendPoint:
  point_id/project_ref/run_ref/monitoring_mode/subject_ref/site_ref
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  stable_endpoint_key/stable_timepoint_key/episode_key
  observed_time_ref/nominal_time_ref/date_precision
  value/unit/change/percent_change/response_class?
  value_state=observed|accepted_derived|recalculated|boundary|not_evaluable
  reporter_role/intercurrent_event_refs/d05_assessment_binding_ref_ids
  shared_spine_hash
  trend_rule_id?/input_result_ids
  source_locator_ids/payload_hash

EfficacyJourneyMarker:
  marker_id/project_ref/run_ref/subject_ref/site_ref/episode_key
  monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  stable_endpoint_key/stable_timepoint_key/marker_kind
  anchor_state=dated|partial|pending_time|out_of_cutoff
  actual_time_ref?/nominal_time_ref?/date_precision
  unit_id?/risk_id?/query_id?/d05_binding_ref?
  audience_label/monitoring_priority/source_locator_ids/payload_hash

EfficacyJourneyProjection:
  projection_id/project_ref/run_ref/monitoring_mode/subject_ref/site_ref
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff/episode_key
  shared_temporal_spine_binding_id
  endpoint_lanes/trend_points/baseline_markers/threshold_bands
  assessment_markers/risk_markers/pending_markers/out_of_cutoff_markers
  typed_context_refs/source_locator_ids/payload_hash
```

`unit_kind` 是关闭集合：

1. `item_completeness`：已实施的评估中，算法要求的 item/组成项是否完整；
2. `item_value_validity`：已记录 item 的身份、值域和单位是否满足定义；
3. `score_recalculation`：记录总分/派生分是否与冻结算法一致；
4. `baseline_selection`：基线候选与选择是否符合规则；
5. `change_recalculation`：变化值/百分比变化是否可复现；
6. `response_classification`：反应、进展、缓解等分类是否符合阈值和时间点；
7. `endpoint_composition`：复合/多组成/层级终点是否由正确组成项和组合规则形成；
8. `repeat_selection`：同一时点多次评估采用哪次是否符合预设；
9. `rater_or_mode_consistency`：评估者/实施方式是否满足定义且纵向可比；
10. `individual_trend_pattern`：冻结、可解释的个体纵向异常模式是否成立；
11. `accepted_report_consistency`：外部报告/accepted derived result 与个体 source-backed 结果是否一致。

完整的计划评估完全未见记录归 D05，不建立 D06 `item_completeness`；只有已有 accepted assessment/endpoint result 或 D05 typed ref 确认评估发生后，D06 才评价其组成项和值。

所有实际 assessment/result 派生的 D06 unit 必须 `d05_binding_state=required` 并绑定同 scope 的一个或多个 `D05AssessmentBindingRef`，证明对应评估/结果的发生、时间与归属；缺失、wrong Run/subject/site/episode/cutoff 或 payload hash 不一致时打开 `dependency` gate，不生成正常 D06 medical unit。独立 accepted analysis artifact 若尚不能绑定 D05，只能进入 control-plane coverage notice，不能建立 `accepted_report_consistency` medical unit 或投影到共享访视轴。

只有已 unique 定义、已生成 obligation、且权威 unit-level applicability evidence 证明该 obligation 不适用的 L1 `not_applicable` unit，才允许 `d05_binding_state=not_required_by_unit_applicability`；此时 D05 refs/spine hash 禁止，并要求 §8.5 applicability evidence。任何 positive/negative/boundary/not_evaluable unit 以及消费 assessment/result 的 unit 禁止该 state。maturity 也按 unit obligation 条件化：timepoint/maturity-dependent unit 为 `required` 且 decision ID 必填；定义时不依赖 maturity 的 unit 或上述 unit-level not_applicable 可为 `not_required`，必须给关闭 reason code 并禁止伪造 decision ID。两组 state/字段组合均进入 unit hash 与 challenge assertion。

任何 baseline、repeat、responder、trend 或 composite 决定/结果消费 `n` 个 candidate 或 selected assessment 时，必须保存 canonical-sorted 的 `d05_assessment_binding_ref_ids`，并对每个 assessment 建立恰一条同 scope、同 episode、同 cutoff 的 D05 binding；不得以一个 D05 ref 代表多次评估。所有 refs 的 `SharedTemporalSpineBinding.axis_hash` 必须等于对象保存的 `shared_spine_hash`。candidate 被拒绝也必须保留其 D05 binding 与 rejection reason；错轴、漏绑、重复绑或跨 scope 绑定均 fail closed。`CandidateSelectionDecision.consumer_unit_or_result_id` 必须反向解析到恰一消费对象，消费对象也必须列出该 decision；孤立决定或一份决定跨 endpoint/timepoint 重用均 fail closed。

有效 binding 要求 D05 `occurrence_disposition=negative`（即该计划评估已完成而非“未发现问题”的泛化含义）、assignment 为唯一或方案明确允许的非计划评估，并保留 timing disposition。D05 timing positive 不阻止 D06 对已存在数据计算，但两个 owner 的风险/Query 分离；D05 occurrence positive、boundary、not_evaluable 或 assignment 未决时不建立正常 D06 unit，只保留 dependency gate/context。

合成挑战中的 accepted D05 producer surface 必须先物化为 `AcceptedD05AssessmentInventoryItem`，由 accepted assessment source record 独立冻结 D05 unit、计划/实际活动、occurrence/timing/assignment、actual time 和 producer lineage。`D05AssessmentBindingRef` 与 `D05AssessmentForeignKey` 必须分别逐字段解析该 inventory，不能只要求彼此相等；binding ID 由 source record ID 确定，required 状态必须覆盖该 inventory 的完整 canonical set，不能通过同步删除 registry 项来掩盖漏绑。maturity anchor 的 stable source identity 与 normalized time 必须等于其所指 D05 source record；选择决定的 selected time 必须反向等于 selected anchor。

每个 maturity decision 还必须由 `D06MaturityConsumerBinding` 双向绑定真实消费对象：consumer ID、decision ID、endpoint、timepoint、完整 scope 和 shared spine 必须逐字段相等；孤立的 `consumer_unit_ids` 名单不构成解析证据，向名单和 decision 同时添加任意 ID 也必须 fail closed。

`EfficacyGate` 合法组合是关闭集合：`open + boundary|not_evaluable + blocks_domain_complete=true`，或 `closed + resolved + blocks_domain_complete=false`；其他组合 schema/QC fail。open gate 不进入五类 L1 分母，但始终阻断 D06 域完整性。

每个 gate 必须以 required `gate_binding_ref_id` 引用同 scope `GateBindingRef`。union conditional schema 为：definition 恰有 `definition_binding_decision_id`；owner_routing 恰有 `owner_routing_decision_id`；dependency 恰有 `dependency_decision_id`；其余两个 decision 字段禁止。三个 decision ID 分别解析为 `EfficacyDefinitionBindingDecision`、公共 owner-routing decision、typed producer/dependency decision。closed+resolved 时 `selected_binding_decision_id` 必填且等于 ref 中唯一/resolved decision；open 时禁止 selected binding。definition gate 只有 endpoint、instrument、algorithm、baseline、timepoint 与 ICE 集全部唯一才可关闭；routing/dependency gate 只有各自 typed decision resolved 才可关闭。不同 kind 不能复用错误 decision type。

gate kind→binding kind 也是关闭映射：`applicability|definition|algorithm|baseline|unit_or_scale → definition`，`routing → owner_routing`，`dependency|cutoff_scope → dependency`。不在映射中的组合 schema fail；cutoff dependency decision 必须引用 frozen cutoff rule、normalized temporal inputs 与 scope decision，不能借用普通 producer coverage 状态。

gate 稳定身份精确为 `(scope_binding_id, gate_kind, gate_binding_ref_id, stable_endpoint_key?, episode_key?, canonical affected_set_hash)`；同一稳定 decision scope 每个 gate_kind 一个当前 Run gate。`affected_timepoint_keys/affected_unit_keys` canonical-sort、去重并内容寻址；一个定义/算法歧义影响 20 个 timepoint 时只形成一个 gate 和一个 affected set，不复制 20 个 gate。

### 4.4 稳定身份

`stable_core` 是精确 tuple，不是“至少包含”：

```text
(project_id, domain_id=D06, scope_type=subject_endpoint_timepoint_episode,
 scope_key=(subject_ref, site_ref, episode_key),
 normalized_concept_or_rule_item=(unit_kind, stable_endpoint_key,
   stable_instrument_key_or_none, stable_timepoint_key,
   stable_item_or_component_definition_key_or_none, rule_id),
 temporal_window=(stable_timepoint_key, episode_key),
 rule_or_knowledge_lineage, unit_algorithm_version)
```

这是 R4 公共 unit identity 公式，所有实现逐字段 canonicalize 后内容寻址为 `unit_id`；每个 Run 另保存 canonical-sorted `expected_set_hash`。不得包含 Run/snapshot/revision、显示版本、当前数值、日期文本、自由文本、风险等级、Query 或模型结论。定义/算法/SAP/mapping/来源版本进入 `rule_or_knowledge_lineage` 而不进入可修订事实值。同一临床 obligation 在 N→N+1 保持 classifier；定义或算法语义变化导致不可比时 supersede，不伪装为数据修正。assessment/item/result/artifact record identity、更正时间和显示标签对所有 unit_kind 均严禁进入 obligation identity，只进入 lineage/trace。

每个 positive root 在建立风险前还必须生成 `PublicR4RiskIdentity`；非风险结果与控制面结果严禁生成该对象。其 `canonical_tuple` 精确按 `project_ref, domain_id, scope_type, scope_key, stable_source_or_event_identity, normalized_concept, temporal_window, rule_or_knowledge_lineage, public_identity_version, risk_id, unit_id, scope_binding_id, cutoff` 的顺序采用公共 canonical serialization 和内容寻址，`public_identity_hash=SHA-256(canonical_tuple)`，ID 由该 hash 派生。`domain_id` 必须为 D06，不能借用 D07 等 producer domain。`stable_source_or_event_identity` 必须是经过 correction/supersession 解析的稳定业务来源或事件身份，不得是 display text、行号或自由字符串。`D06RiskBinding.public_r4_risk_identity_id` 与 identity 双向一对一，并与 unit stable_core 的 scope/concept/time window/lineage 精确相等。跨 Run 数据更正保持该 hash；source/event、concept、temporal window 或 rule lineage 语义改变时生成新 identity 并通过 R2 supersession 连接，不能静默合并。

上述 `unit stable_core` 必须作为独立的 `D06UnitStableCore` 物化并解析到 accepted source record、endpoint/instrument/timepoint definitions 和 algorithm lineage；unit kind 由 primary subtype 的关闭映射确定。public identity 的 source、normalized concept、temporal window 和 rule lineage 必须逐字段等于该 stable core，risk binding 的 unit/risk 又必须逐字段等于 priority decision。仅让 identity 的 tuple/hash 自洽，或同时改写 risk binding 与 identity，均不能构成有效身份。

逐 `unit_kind` 的 identity 参与字段固定：

- `item_completeness|item_value_validity`：instrument + item definition key；
- `score_recalculation|repeat_selection|rater_or_mode_consistency`：instrument + `none` item/component；
- `baseline_selection|change_recalculation|response_classification|individual_trend_pattern|accepted_report_consistency`：endpoint + instrument-or-none + `none` item/component；
- `endpoint_composition`：endpoint + component definition key；若逐组件形成 unit，每个 component key 一个 obligation；总体组合另用 `component=overall`。

所有未使用槽位必须 canonical literal `none`，不得选择性省略。actual assessment/result/artifact 的变化只改变 lineage 和本 Run disposition，不改变同一 obligation 的 unit_id。

## 5. 适用性、到期与 expected-set

### 5.1 适用性先行

只有以下内容唯一确定，才生成正常 D06 medical expected-set：受试者/阶段/episode、适用方案/SAP、endpoint/instrument/algorithm/baseline/timepoint 定义、owner routing，以及 D06 依赖的 actual assessment/result inventory。

多份完整、合法定义产生不同结论时形成单一 boundary gate；关键定义、算法或来源缺失/冲突形成单一 not_evaluable gate。open gate 不展开“定义×时间点×item”的伪分母，不生成确定风险或 Query。

控制面与医学评价面的 `not_applicable` 是两个互斥阶段：定义适用性聚合在唯一 binding 前得到 `not_applicable` 时，仅保存 control-plane `EfficacyDefinitionBindingDecision`/coverage 证据，不建立 D06 medical expected unit，也不进入 L1 五类等式；只有 endpoint definition 已 unique、owner/dependency 已 resolved、已到期 unit obligation 已生成后，权威的 unit-level applicability rule 才可把该 unit 评价为 L1 `not_applicable`。实现不得用 control-plane no-match 人为增加 L1 分母，也不得用“无数据”生成 unit-level not_applicable。

### 5.2 时间边界

每个 Run 冻结 `snapshot_as_of` 与 `clinical_event_cutoff`。cutoff 后评估只可进入 Journey 的“截止日后记录”，不得参与当前基线、趋势、L1、风险或关闭。部分日期跨 cutoff 且不同可能日期改变结论时形成 `cutoff_scope` boundary；关键时间角色缺失为 not_evaluable。

所有日期/时间先保留原值并转换为 `NormalizedTemporalValue` 可行区间；不得把月精度默认为月初/月末，不得把年精度补成某日。规则必须冻结 calendar/elapsed/study-day 语义、Day 0、端点包含性、时区、跨午夜、所需精度和 derived-date lineage。若整个可行区间落在同一判断侧，可得确定结论；若区间跨分析窗、基线窗、确认窗、阈值所需时点或 cutoff 且来源覆盖完整，为 boundary；时间角色缺失/冲突或 maturity rule 未冻结为 not_evaluable。

baseline、repeat、responder confirmation 的候选选择使用各自关闭、版本化 precedence：先稳定 explicit parent/source mapping，再适用 episode/角色/方式，再允许窗口，再冻结 tie-break；日期距离只能在规则明确指定时作为 tie-break，永不默认“最近/最后/最大/最差”。

每次选择均持久化 `CandidateSelectionDecision`。policy 使用 worst/best 时 endpoint、value key 和 directionality 必填：higher-better 的 worst=min/best=max，lower-better 的 worst=max/best=min；bidirectional/event-based/undefined 禁止 worst/best，除非另有关闭转换 rule。零 candidate 严格按 no-candidate outcome，tie 严格 boundary；selected ID 只在 unique 时存在。

通用选择决定的 conditional schema：`unique` 要求 selected ID 非空且位于 canonical ordered candidates；`tie_boundary|not_evaluable|not_applicable` 禁止 selected ID。`consumer_kind` 必须与消费对象字段一致：baseline→baseline decision、repeat→unit/result 的 repeat decision、maturity→maturity decision、responder→confirmation decision、trend→trend point/unit；`stable_endpoint_key/stable_timepoint_key/rule_role` 与消费对象精确相等，instrument 不适用时使用 canonical `none` 而非省略。每个 consumer 只可引用当前 scope 的一个 active selection decision；候选集、D05 bindings、spine hash 或 policy hash 改变即新 decision lineage。

时间运算只能消费 `TemporalOffset`：minutes/hours/days/weeks + elapsed duration 以冻结时区的 instant 运算；months/years + calendar component 按日历组件运算并使用显式 end-of-month policy；不允许把“1 月”解释为 30 天。每次 maturity/window 运算必须绑定一个通过 `CandidateSelectionPolicy` 唯一选出的稳定 anchor identity；多 anchor 为 boundary，anchor/offset/timezone/Day-0/精度缺失为 not_evaluable。部分日期使用 interval arithmetic：对区间全部可能值执行同一运算并传播上下界，禁止先补日期。跨午夜比较统一换算到冻结时区后再判端点。

该选择必须持久化为 `MaturityAnchorSelectionDecision`：unique 时 selected anchor + normalized time 必填，boundary/not_evaluable 时两者禁止；candidate set、policy 和 predicate results 入 hash。每个 `maturity_binding_state=required` 的 unit/result 必须引用该 decision，不能重算后丢弃 selected anchor；`not_required` 时禁止引用。

candidate IDs 必须解析为 `TypedMaturityAnchorRef`；fixed_nominal 只能用 `FixedNominalAnchorRef`，其他 anchor_kind 必须与 producer domain/role/type 精确兼容（如 d05_actual_visit→D05 validated actual-visit anchor）。相同 timestamp 但不同 stable source identity 仍是两个候选，不能按时间去重。

当 maturity anchor 的 producer domain 为 D05 或引用 D05 actual visit/assessment 时，`d05_assessment_binding_ref_ids` 与 `shared_spine_hash` 必填，且每个 candidate anchor 一对一绑定 D05 ref；fixed nominal、randomization 或其他非 D05 typed anchor 禁止伪造 D05 ref。unique 状态的 selected anchor 必须位于 candidate 集，boundary/not_evaluable 禁止 selected anchor/time，但仍保留全部 candidate/ref 证据。

### 5.3 expected-set 条件与顺序

原子 unit 仅在该 endpoint/timepoint/episode 已达到规则定义的可评价成熟时点、必要依赖已唯一满足且 owner 为 D06 时生成。未来时间点留在访视轴但不进入 L1 分母。

固定顺序：

```text
冻结 Run/snapshot/cutoff
→ 构建 accepted assessment/item/result identity inventory
→ 冻结 endpoint/instrument/algorithm/baseline/timepoint/ICE definitions
→ owner routing 与 EfficacyGate
→ 消费 D05 occurrence/timing typed refs 和必要 producer refs
→ 生成已成熟 D06 expected-set/hash
→ 确定性复算与 accepted result 比对
→ 逐 unit 评价
→ 生成趋势、风险、Query、Journey 投影
```

输入行序、字典顺序、模型输出顺序、显示排序不得改变 expected-set 或 hash。

## 6. 确定性计算与 fail-closed 规则

### 6.1 量表和组成项

- 仅执行版本化、可定位、确定性的算法操作；模型可辅助抽取草稿，但未冻结前不能执行。
- item code、顺序、反向计分、权重、变换、有效范围、单位、舍入和最少已答题数均为算法输入。
- 缺项只有在明示 `missing_item_rule` 允许时处理；禁止隐式零填充、均值填充、LOCF、最差值/最佳值或模型猜测。
- 原始值超范围、单位不兼容或 item identity 不唯一时不计算权威分数。
- accepted result 与重算值均保留；超出冻结容差才为不一致，不以浮点精度差异制造问题。
- 每一步运算均使用 `NumericExecutionPolicy` 的十进制语义；canonicalization 必须统一 `1`/`1.0`/`1.00`、Unicode、键排序、时区表示和 `-0`，并拒绝 NaN、无穷、overflow/underflow。不得依赖宿主语言二进制浮点默认舍入。
- 缺项处理的执行阶段必须显式；例如 prorate 在反向计分前还是后不能由实现决定。未知/不支持的 operation、missing strategy 或 numeric policy 打开 algorithm gate。
- result comparison 只按关闭公式执行：`exact` 比较 canonical decimal；`absolute` 比较 `abs(A-R)` 与必填 threshold；`relative` 比较 `abs(A-R)/D`，其中 accepted_value: `D=abs(A)`，recalculated_value: `D=abs(R)`，maximum_absolute_value: `D=max(abs(A),abs(R))`；D=0 按 missing/nonfinite policy 转 not_evaluable；`decimal_places` 先按必填 decimal_places 和 numeric policy 舍入两侧再 exact。comparison 统一在 optional precomparison rounding 后计算，最终用 inclusive 字段选择 `<=` 或 `<` threshold；禁止其他隐式舍入。threshold/decimal_places/reference_role 的必需组合缺失即 algorithm gate。

### 6.2 基线与变化值

- 基线候选必须满足 episode、干预前关系、访视/窗口、评估者/方式和预设 repeat selection；“最接近首次给药”不是默认规则。
- 多个完整可行候选且规则不能唯一选择为 boundary；缺规则/关键时间为 not_evaluable。
- `change = postbaseline - baseline` 的方向不等于改善/恶化，须结合 endpoint directionality；percent change 分母为零或不允许负值时按冻结规则处理，否则 not_evaluable。
- 基线更正产生新 lineage 并可 supersede 后续全部变化结果；不得原地回写旧 Run。
- percent change 只能执行 `PercentChangeRuleDefinition`：明确 numerator、denominator、multiplier、负分母和零分母策略，再按 numeric policy 舍入。未冻结时不得默认 `(post-baseline)/baseline×100%` 或绝对值分母。
- conditional invariant：`denominator_role=other_explicit` 时 explicit denominator input key + unit 必填，其他 role 时禁止；`zero_denominator_policy=explicit_constant` 时 constant + unit 必填且须与输出单位兼容，其他 policy 时禁止。缺失、错单位或多填导致 schema/algorithm gate。

### 6.3 反应、进展与复合终点

- 阈值、持续时间、确认评估、允许窗口、组成项逻辑、事件/删失规则必须全部冻结。
- 临界值按规则的包含性和精度判定；合法精度区间跨阈值为 boundary。
- 响应者标签必须能回到基线、timepoint、组成项、阈值和算法；“临床好转”自由文本不能替代定义。
- time-to-event 只生成受试者层事件/删失状态和可追溯时间，不在 D06 生成 KM、HR 或总体结论。
- 复合/多组成/层级终点必须保存每个 `ComponentResultRef`，并按 `EndpointCombinationRule` 的 ordered component、missing propagation 和 precedence 重放；最终标签不能替代逐组件状态。
- responder 持续/确认规则必须保存所有 `responder_confirmation_assessment_refs`；time-to-event 必须保存 time origin、事件/删失时点、删失原因、时间单位和 competing-event precedence。缺任一决定性角色即 not_evaluable。
- endpoint 需要确认反应时 `responder_confirmation_rule_id` 必填并解析关闭规则；`ResponderConfirmationSelectionDecision` 按 required count、sequence/consecutiveness、固定 timepoints、gap offsets、端点包含性、partial-date outcome 和 candidate policy 唯一选择。结果必须引用 decision 及完全相同的 selected assessment refs；确认规则缺失/未达要求/边界分别得到 not_evaluable/not_confirmed/boundary，禁止用“任意两次”替代 consecutive。
- confirmation conditional schema：`consecutive_eligible` 要求 minimum/maximum gap、intervening policy 和 anchor policy，禁止 fixed timepoints；`any_eligible_in_window` 要求 window start/end、anchor kind/policy，禁止 fixed timepoints，窗口 start 必须不晚于 end；`fixed_timepoints` 要求 ordered required timepoint keys 数量恰等于 required_count，禁止 window/gap offsets。`window_anchor_kind=fixed_timepoint` 时 fixed anchor key 必填，其他 kind 禁止；所有 sequence 都要求 candidate selection policy、lower/upper inclusivity 和 partial-date outcome。candidate 够数但合法精度跨窗口/gap 为 boundary；确定不足 required_count 为 not_confirmed；缺规则/时间角色为 not_evaluable。
- TTE conditional schema：所有可评价状态都要求 `tte_endpoint_precedence_binding_id`，并且 binding 的完整 scope、endpoint/timepoint、rule ID 与 result 精确相等。event 要求 origin + event time + validated target_event_ref；competing_event 要求 origin + event time + competing ref；censored 要求 origin + censor time + reason；boundary 要求至少两个 `feasible_interpretation_ref_ids`，分别解析到同 scope 的完整 event/censor/competing typed interpretation，保存全部可行 refs 且不产单一 duration；event/competing/censored 禁止 feasible interpretation list；not_evaluable 不伪造时点。tie_policy=boundary 映射 status=boundary，winner=competing_event 保存独立状态。各状态禁止不相干字段，rule/binding/target identity 缺失为 not_evaluable。
- `TTEEndpointPrecedenceBinding` 必须通过 exact object type 校验，并解析独立的 `TTEPrecedenceRule` 与 `TypedTTEEventSource`。target/competing event ID、role 和 effective time 不能由 TTE record、source registry 与 interpretation 三份字符串相互背书；三者必须分别解析独立 event source。同步改写这些副本或把 binding 类型改成相邻域对象仍须 fail closed。

### 6.4 干扰事件与缺失

- 停药、换药、救援治疗、死亡、退出等按方案/SAP 定义为 typed intercurrent-event context；缺失是针对特定终点而未收集到有意义数据，两者分开计量。
- D06 显示干扰事件相对趋势的位置及预设 strategy，但不自行估计 hypothetical 值。
- 若 SAP 允许使用干扰事件后的实际测量，保留并按规则解释；若不相关，保留上下文但不强行纳入。
- 未预设插补或 estimator 时，D06 不生成替代值；只显示“该时间点无法评价/资料不足”。
- 每个影响某 endpoint/result 的干扰事件必须实例化 `IntercurrentEventContext`，把 producer event、有效区间、affected result、strategy、estimator availability 和 scope 精确绑定。`hypothetical` 等需要 estimator 的 strategy 若 `estimator_availability!=available`，D06 只显示 context/not_evaluable，不得静默使用观察值或构造反事实值。
- `estimator_availability=available` 时 `estimator_binding_id` 必填并与 endpoint/scope/estimand 精确相等；`unavailable|not_required` 时不得伪造 binding。`typed_producer_event_ref` 必须解析为 validated `TypedProducerEventRef`，不能是任意字符串或同日 locator。
- `IntercurrentEventContext`、`EstimatorBinding`、受影响 `DerivedEfficacyResult` 与 producer event 的 project/run/mode/source revision/snapshot/scope/cutoff/subject/site/episode/endpoint/timepoint 必须逐字段相等；estimator binding 不得跨 endpoint、timepoint 或受试者重用。即使 estimator definition 相同，scope 或 estimand context 不同也必须是不同 binding。

### 6.5 评估者、方式、重复和更正

- PRO、ObsRO、ClinRO、PerfO 和 objective measure 不互换；评估者角色/实施方式改变若影响可比性，按冻结规则产生 boundary/positive/not_evaluable。
- actual reporter type、recall period、administration mode 和 central/local role 必须与 instrument definition 精确匹配，或引用 `AssessmentEquivalenceRule(equivalence_state=equivalent)`；缺实际语义、错角色或 equivalence 未冻结时 fail closed。相同 item code 不证明 PRO/ClinRO、7 日/4 周回顾、纸笔/电子或中央/本地值可互换。
- 同一时间点多次评估必须有 repeat selection rule；禁止默认最后一条、最大改善、最差值或录入顺序。
- 中央读片、独立评审和本地评估分别保留；若终点指定某角色，只使用该角色，其他值作为上下文。
- 更正记录以 accepted lineage 决定当前值，旧值仍可追溯；无 lineage 的冲突不是“取最新日期”。

### 6.6 算法与定义版本连续性

版本变化先分类：

- `non_semantic_change`：仅实现/序列化修订，且由内容寻址等价性证明 operation、参数、numeric policy、输入/输出和所有边界结果等价；可保持 classifier，旧执行 lineage superseded；
- `semantic_change`：计分、阈值、组成、基线、ICE、缺项、舍入、单位或适用性语义任一变化；生成新 result lineage，旧结果 superseded，不用作 linked-negative 或自动关闭；
- `equivalence_unproven`：无法证明等价，按 semantic change fail closed。

相同数值不证明语义等价；阈值从 `>=` 改为 `>`、求和改加权求和等即使某受试者结果未变，也不得沿用旧结果作关闭依据。

## 7. 个体趋势与异常模式

趋势由同一稳定 endpoint、可比较单位/量表版本、episode 和方向性组成；不同量表版本、单位或评估者不可直接连线，除非冻结跨版本/换算规则。

允许的 `TrendPatternRule` 必须版本化、内容寻址且可解释，可包含：

- 单次变化超过量表理论可达范围或预设生理/测量上限；
- 相邻短时间内方向相反且变化幅度超过预设复核阈值；
- 记录的 response/progression 与组成项方向相反；
- 连续时间点完全相同但原始 item 组合不同或 source report 不一致；
- 改善/恶化速度达到方案/量表明确的复核条件。

实现中只允许 `TrendPatternRuleDefinition` 的关闭 pattern kinds；threshold、unit、duration/window、minimum points、directionality、input selection 和 evidence roles 全部必填到该 kind 的条件字段并进入 hash。每个 `individual_trend_pattern` unit 的 `rule_id` 和每个相关 TrendPoint 的 `trend_rule_id/input_result_ids` 必须精确引用；未知 pattern、缺阈值/时长/方向或模型自由文本只显示原始趋势，不建 positive。

各 `pattern_kind` 的公式与条件字段固定如下，`Δi=vi-v(i-1)`，所有值先按冻结换算规则归一到 `threshold_unit`，再依 `NumericExecutionPolicy` 计算：

- `absolute_jump`：恰消费相邻两点，`metric=abs(v2-v1)`；只允许 `comparator=ge|gt`，分别计算 `metric≥threshold` 或 `metric>threshold`。`relative_multiplier/zero_reference_policy/duration/item` 字段禁止。
- `relative_jump`：恰消费相邻两点，`metric=abs(v2-v1)/abs(v1)×relative_multiplier`；`relative_multiplier` 仅可为 `1`（ratio）或 `100`（percent），threshold unit 必须对应 `ratio|percent`。`v1=0` 时严格按 `zero_reference_policy` 返回 not_evaluable 或 boundary，不允许加 epsilon。duration/item 字段禁止。
- `direction_reversal`：至少三点；对每对连续非零 `Δ`，仅当 `sign(Δi)≠sign(Δi-1)` 且 `abs(Δi)`、`abs(Δi-1)` 均满足 comparator/threshold 时命中。任一差值等于零不构成反转；relative/duration/item 字段禁止。
- `flat_score_item_shift`：恰比较两个总分结果及各自 canonical-sorted `(stable_item_key,value)` 向量；先用必填 `score_tolerance_rule_id` 证明总分一致，再计算同名 item 的 `abs(item2-item1)`，达到 `item_difference_threshold` 的 item 数须满足 `≥minimum_changed_item_count`。item 集不相等、值缺失或量表版本不可比为 not_evaluable，不允许把缺项当零；relative/duration 字段禁止。
- `rate_of_change`：恰消费按真实时间排序的两点，`elapsed` 必须大于零并以 `duration_unit` 归一；`metric=abs(v2-v1)/elapsed_in_duration_unit`，只允许 `duration_normalization=per_unit`，再按 comparator/threshold 判断。相同/重叠时间区间为 boundary，时间角色缺失为 not_evaluable；relative/item 字段禁止。

除上述每种 kind 明示字段外的条件字段一律禁止；`minimum_point_count` 必须分别为 2、2、≥3、2、2。输入选择 decision、input result IDs、比较顺序、归一化单位、实际 elapsed、metric、threshold comparison 与 evidence refs 全部进入 lineage/hash，因此“20%”和“20 个百分点”不能落到同一 rule。

一般“看起来变化太大”“不符合药物预期”或模型自由判断不能成为 positive。药物暴露、AE、救援治疗等可作为 producer typed context 显示；只有 D08 已验证 relationship 或 D06 规则本身明确以该 typed event 为输入，才可形成跨域一致性判断。

D07 数值进入 endpoint 只能经 `D07EndpointValueRef(validation_state=validated, semantic_role=endpoint_input)`。即使是 `single_measure` 直取值终点，也必须建立 canonical `select_measure` operation 与 `D07ConsumptionBinding(consumer_kind=select_measure_operation)`，不得省略 operation 或制造“直接引用”旁路。ref、binding、operation 的 stable endpoint、endpoint definition、input measure key 和单位必须精确相等，且 operation 的 `typed_producer_consumption_binding_ids` 反向包含该 binding；任一错绑或孤立边即 schema/QC fail。D08 关系进入 D06 只能经 `D08RelationshipRef(validation_state=validated)`。两类 ref 必须与 D06 scope 完全相等并保留 producer identity/version/hash。缺 typed ref 时只并列显示 producer context，不作为 endpoint evidence，不画关系线，也不复制 producer risk/Query。

用户标签使用“评分变化待核实”“反应判断待核实”“个体趋势待核实”，不得使用“正式事实”“候选信号”“算法异常”“模型判断”等研发语言。

## 8. L0/L1/L2/L3 合同

- **L0**：输入、定义、角色、来源、mapping、算法执行和 coverage，直接复用冻结 R1 `CoverageUnitStatus=covered|partial|truncated|not_applicable|not_evaluable|failed|missing`，不得新造同义枚举；
- **L1**：每个 `EfficacyEvaluationUnit` 恰有一个 `positive|negative|boundary|not_applicable|not_evaluable`；
- **L2**：source record、线索、risk、Query、coverage notice、trend point 分别计数，以稳定 ID 关联；
- **L3**：复用 R2 `RiskLifecycle`，D06 不新增状态机。

### 8.1 positive subtype

只有所有必要定义、来源和依赖完整，且所有允许解释下 issue predicate 恒真时为 positive：

| subtype | 用户标签 |
|---|---|
| `required_component_missing` | 疗效评估组成项待核实 |
| `component_value_invalid` | 疗效评估原始值待核实 |
| `score_inconsistent` | 量表计分待核实 |
| `baseline_inconsistent` | 基线选择待核实 |
| `change_value_inconsistent` | 变化值计算待核实 |
| `response_class_inconsistent` | 反应判断待核实 |
| `endpoint_composition_inconsistent` | 疗效终点组成待核实 |
| `repeat_selection_inconsistent` | 重复评估取值待核实 |
| `rater_or_mode_inconsistent` | 疗效评估方式待核实 |
| `individual_trend_inconsistent` | 个体趋势待核实 |
| `reported_result_inconsistent` | 疗效结果记录待核实 |

一个 root 只有一个 primary subtype；同一问题不得因同义 endpoint、重复报告或多个看板投影创建多条风险/Query。

`classifier` 是跨 Run 的稳定医学 obligation 类别，`eval_disposition` 是本 Run 的五类评价，`primary_subtype` 只在 `positive` 时必填；三者不得互相代替。

根粒度由 `unit_kind` 决定：item 完整性、score、baseline、change、response、composition、repeat、rater/mode、trend 和 report consistency 是不同原子 root。上游决定性问题先行：

```text
item identity/completeness/value validity
→ algorithm/rater/repeat/baseline
→ score/change/composition/response
→ trend/report consistency
```

若上游 positive 或 not_evaluable 已使下游无法独立重放，下游为 not_evaluable 并把观察到的差异作为 upstream risk 的 `secondary_reason_codes/supporting evidence`，不得再创建推测性的下游 positive。只有证据可独立证明两个不同 clinical actions 时才保留两个 root。每个 `unit_kind` 的 primary subtype 固定映射：

- `item_completeness → required_component_missing`
- `item_value_validity → component_value_invalid`
- `score_recalculation → score_inconsistent`
- `baseline_selection → baseline_inconsistent`
- `change_recalculation → change_value_inconsistent`
- `response_classification → response_class_inconsistent`
- `endpoint_composition → endpoint_composition_inconsistent`
- `repeat_selection → repeat_selection_inconsistent`
- `rater_or_mode_consistency → rater_or_mode_inconsistent`
- `individual_trend_pattern → individual_trend_inconsistent`
- `accepted_report_consistency → reported_result_inconsistent`

同一 root 内多个 predicate 同时命中时，按表中唯一映射选 primary subtype，其余为有序、去重的 secondary reason；禁止按输入顺序选择。

### 8.2 negative

negative 要求适用性、定义、算法、所需 item/source coverage、单位、基线、时间点、重复规则、干扰事件策略和允许例外完整，且所有解释下 issue predicate 为假。它不是“模型没发现问题”，不能从空表、局部数据或 accepted result 单边推断。

### 8.3 boundary

完整权威来源支持两个及以上合法解释，或合法精度跨阈值/基线/窗口且结论不同，才是 boundary。可生成一条明确保留不确定性的待核实线索；优先级无法确定时为 unknown。缺表、缺算法、缺单位、缺 item 或 mapping 未完成不是 boundary。

### 8.4 not_evaluable

适用但缺失/冲突的定义、算法、基线规则、组成项身份、单位、评估者、时间角色、来源覆盖或 producer dependency 使判断无法完成时为 not_evaluable。只生成 `EfficacyCoverageGapNotice`，不创建新的确定风险、Query 或“未知风险等级”。既有风险只 carry-forward 并显示资料缺口。

### 8.5 not_applicable

只有权威定义证明 endpoint/unit 对该受试者、阶段、episode 或 timepoint 不适用时使用。未来未成熟不进入 expected-set；无数据不等于不适用。

每个 L1 `not_applicable` 必须至少绑定一条 `EfficacyEvidenceRef(direction=applicability)`，其中 stable source identity、方案/SAP/定义 rule ID+version、有效适用区间、完整 scope、source locator、applicability rationale code 与 lineage hash 均非空并可重算。该证据必须证明“已唯一生成的此 unit obligation 不适用”，不能引用控制面定义 no-match、空数据表或模型判断。缺少任一字段时 unit 为 `not_evaluable`，不得计入权威 L0/L1 not_applicable。

### 8.6 L1b 正反证据

每个 L1 评价必须建立 immutable `EfficacyEvidenceRef`，把证据方向与 unit、source identity、时间范围、规则版本、accepted artifact 和 lineage 分开保存：

- positive 至少一个 supporting；排除依据存在时保存 counterevidence，不得丢弃；
- negative 至少一个决定性 counterevidence/符合依据，并证明所需 source coverage closed；
- boundary 至少两个产生不同判断的 supporting/counterevidence interpretation；
- not_evaluable 保存 context 和 missing-role notice，不伪装成 supporting；
- not_applicable 至少一个 applicability ref，并满足 §8.5 的权威规则、有效区间和范围约束；
- context 不能单独把 unit 判为 positive/negative。

证据方向不得由 Query 文案或展示颜色反推。挑战 manifest 必须断言所需 direction、trace edge 与来源 hash。

## 9. 优先级与 Query

### 9.1 监察优先级

优先级由版本化、内容寻址的 `D06PriorityPolicy` 决定，不是疗效证据等级，也不得由模型自由打分。该 policy 必须物化本节五步 precedence 的完整有序定义、各步触发集合、默认结果、reason codes、machine-close 约束和来源定位；`policy_hash` 对除自身外的完整 policy object 计算。仅保存 policy ID/version/hash 的指针对象不构成策略，任意同步改写 policy、resolver、decision 和 expected outcome 但偏离本节 canonical full definition，均在生成阶段 fail closed。它直接复用公共 R4/D05 关闭枚举：

```text
impact_class=rights_safety|critical_treatment|primary_endpoint|
             key_secondary_endpoint|mandatory_critical_sample|
             other_required|administrative
recurrence_class=single|repeated_subject|repeated_site
recoverability=recoverable|time_critical|irrecoverable|unknown
actionability=actionable|context_only|unknown
```

endpoint role 到 impact 的映射先冻结：`primary|co_primary|multiple_primary → primary_endpoint`，`key_secondary → key_secondary_endpoint`，`secondary → other_required`；`exploratory|supportive` 只有在方案/SAP 明确为低影响辅助记录时才可映射 administrative，否则为 other_required；`undefined` 不产生确定优先级。`rights_safety|critical_treatment|mandatory_critical_sample` 在公共 resolver 中保留完全相同的语义，但正常 D06 endpoint-role mapping 不产生它们；若上游传入这三类，必须能按公共 precedence 处理并保留 producer/owner trace，不能报未知枚举或降级。

v1 precedence 命中即停止：

1. `impact_class=rights_safety|critical_treatment`：始终 high + machine-close-forbidden；actionability/recoverability unknown 或 context_only 只追加 coverage/context，不能降级；
2. 其他 impact 若任一必需输入未冻结、`recoverability=unknown` 或 `actionability=context_only|unknown`：priority=unknown；
3. `primary_endpoint|mandatory_critical_sample`：`time_critical|irrecoverable` 为 high，其余 medium；若结果已用于/即将用于主要终点锁定、正式输出或不可逆决策，recoverability 必须为 irrecoverable，因此 high；
4. `key_secondary_endpoint|other_required`：基线 medium；`repeated_site|irrecoverable` 升 high；
5. `administrative + single + recoverable + actionable`：low；其余 administrative 基线 low，`repeated_subject` 升 medium，`repeated_site|irrecoverable|time_critical` 升 high。

所有决定保存 policy id/version/hash、四项输入、endpoint-role mapping、命中的 precedence step、reason code 和 `machine_close_forbidden`。high、用户确认/升级、identity ambiguity、primary endpoint 且不可逆的问题 machine-close-forbidden。

优先级求解前先物化内容寻址的 `D06PriorityResolverInput`；它是求解输入，不是风险决定。只有形成风险时才允许实例化 `D06PriorityDecision`，且必须保存 resolver input hash；非风险 medical unit 只保留 resolver result，控制面 no-match 连 resolver input 也不得生成，所有临床语义结果字段保持空。resolver 与 expected outcome 必须同时精确断言 endpoint definition ID、stable endpoint/timepoint、reason codes；这些字段分别解析冻结定义和 matched precedence step，不能通过同步改写 resolver 与 outcome 逃逸。`D06PriorityDecision`、`D06RiskBinding` 和 `PublicR4RiskIdentity` 必须先通过 exact object type 检查。risk binding 与 decision 的 unit/risk/endpoint/timepoint/full scope 双向一对一；policy ID/version/hash、五项输入（含 endpoint role）、matched step、resolved priority、reason codes 和 machine-close flag 全部参与 lineage hash。risk priority、Journey marker priority 与 Query priority label 只能由该 decision 投影，不得二次计算。

这只是看板排序。D06 不以此宣称研究成功/失败、临床获益或统计学显著。

### 9.2 三段式 Query 草稿

每条 Query 先消费 D04/D05 冻结的 typed enrollment context，不得由页面或模型猜测：

```text
query_context=enrollment_not_occurred|enrolled_or_post_enrollment|
              enrollment_state_unresolved

D06QueryDraft:
  query_id/project_ref/run_ref/monitoring_mode/subject_ref/site_ref/episode_key
  source_revision/accepted_snapshot_ref/scope_binding_id/cutoff
  query_context/enrollment_context_decision_id
  unit_id/risk_id/stable_endpoint_key/stable_timepoint_key
  definition_ids/algorithm_id/baseline_rule_id?
  item_or_result_ids/source_locator_ids/rule_version
  basis_sentence/finding_sentence/action_sentence/payload_hash
```

每条 Query 绑定 subject/site、定义版本、endpoint/timepoint、原始 item/result、算法/baseline rule、unit 和 risk：

```text
依据：写明适用方案/SAP/量表版本、计分/基线/阈值或组成规则。
发现：写明具体时间点、原始项、记录值、确定性复算值、支持/排除依据和不确定性。
行动项：请核实并说明，必要时补充或更正原始记录/派生结果；只有 `query_context=enrolled_or_post_enrollment` 时，才可追加“如确认不符合方案，请评估是否构成方案偏离并按相应流程处理”。
```

示例：

```text
依据：方案 V2.0 和量表手册 V1.1 规定总分由 6 个组成项求和，至少需 6 项完整，分值范围为 0–24 分。
发现：参与者 SYN-001 第 4 周记录总分为 18 分；6 个原始项按指定版本重算为 15 分，当前未见允许的替代计分或更正记录。
行动项：请核实原始项及总分记录并说明差异原因，必要时更正相应数据；如确认不符合方案，请评估是否构成方案偏离并按相应流程处理。
```

上例仅适用于 `enrolled_or_post_enrollment`。`enrollment_not_occurred` 只请求核实/补充/更正数据，不出现 PD 措辞；`enrollment_state_unresolved` 先请求核实随机、入组或首次给药状态及事件时序，并明确当前资料不足，不出现确定 PD 方向。

`enrollment_context_decision_id` 必须解析为 `EnrollmentContextDecisionRef`，其 query_context、source events、effective time、decision rule/version、lineage 和完整 scope 与 Query 精确相等；页面标志、当前 tab 或模型推测无权设置该字段。

每个 source event 还必须解析到内容寻址的 `EnrollmentSourceEvent`。`enrollment_not_occurred` 只能绑定 screening status，`enrolled_or_post_enrollment` 只能绑定 enrollment，`enrollment_state_unresolved` 只能绑定 enrollment conflict；event role、effective time 与 query context 任一不一致即 fail closed。variant matrix 的 decision ID 按 canonical context 顺序确定，active 单 context 使用其唯一 canonical decision ID。

decision rule ID/version 由独立 `EnrollmentDecisionRule` 冻结；decision、active/variant outcome 和 Query lineage 必须一致引用该 registry。rule/version 仅“非空”不合格，同步修改 decision 与 expected outcome 但不匹配 registry 仍须 fail closed。

这里“完整 scope”逐字段指 project/run/monitoring mode/source revision/accepted snapshot/scope binding/cutoff/subject/site/episode；任何缺失或不等都使 Query audience payload 不可生成。D04/D05 producer 可以共享同一业务事件，但不得省略这些消费时冻结的 scope 字段。

not_evaluable 只显示资料缺口，不伪装成 Query。一个 evaluation root 至多一个 D06 Query；不发送、不跟踪回复、不建立待办。

## 10. Patient Journey 疗效轨道

D06 输出 renderer-neutral `EfficacyJourneyProjection`，不声称 R5 UI 已完成：

- 与 D05 顶部共享访视轴对齐，同时显示名义访视、实际评估时间和 cutoff；不把时间点吸附到错误名义访视；
- 每个 endpoint/量表可独立折叠，默认优先显示主要/关键次要终点及中高风险；
- 趋势线显示实际观察点、基线标记、允许范围/反应阈值、变化方向、部分日期、缺项和截止日后记录；
- PRO、观察者报告、研究者评估、功能测试和客观指标使用不同形状与中文短标签，不只靠颜色；
- 整体评估缺失/超窗显示 D05 producer marker，计分/基线/反应/趋势问题显示 D06 marker，identity 不合并；
- 干扰事件、AE、CM、IP、PD 等仅以 typed context marker 并列；未经验证不画因果连线；
- 点击风险一跳到方案/SAP/量表原文、原始 item、派生步骤、支持/排除依据、Query 和该受试者 Profile/Timeline；
- 日期缺失、算法未定或归属未定进入独立“资料待补充”区，不伪造点位；cutoff 后事件进入“截止日后记录”；
- 缩放、筛选、折叠和页面跳转只改变显示，不改变 L1/L3、分母或风险身份。

界面禁止出现研发、判定机与运行日志词。冻结词典 `d06-audience-zh-v1` 的 phrase 集按列出顺序为：`positive|negative|boundary|not_applicable|not_evaluable|candidate|formal fact|model confidence|backend|debug|log|classifier|payload|lineage|hash|QC|正式事实|候选信号|只读投影|规则命中|后端|模型置信度|算法异常|模型判断`；display-key 集按列出顺序为：`id|*_id|hash|*_hash|ref|*_ref|classifier|payload|lineage|backend|debug|log|confidence`。`forbidden_lexicon_hash=SHA-256(canonical_json({display_keys:[...],phrases:[...]}))=d73a3da6fb9e5643c17673273bff042af5df75259979dcc59cb8adff917e5a75`。新增或删改词必须升 lexicon version 并改变内容 hash，不能在 validator 中另藏黑名单。

匹配算法固定：所有可见字符串先 Unicode NFKC、Unicode casefold、连续空白折叠为单空格、首尾去空白；中文 phrase 做 normalized substring；ASCII phrase 先把非字母数字下划线转为空格后按完整 token sequence 匹配，因此 `backend-qc-positive` 会命中三项，而“阳性结果”不会因英文 `positive` 被误伤。display-key 先同样 NFKC/casefold，再对完整键或 `_*` suffix 规则匹配。只检查 schema 明示的可见文本叶节点；结构性 `query_id/risk_id` 可存在但绝不进入 `validated_display_string_paths` 或可见标签。

payload conditional schema 固定：`query` 恰为 `QueryAudiencePayload`，所有列出的字段必填且 basis/finding/action 分别以“依据：/发现：/行动项：”开头，三段不得合并或为空；`journey` 恰为 `JourneyAudiencePayload`，主轴、至少一个 endpoint lane、marker label 和 source jump target 必填，after-cutoff/data-gap 区仅在有对应记录时出现；`risk_label` 恰为 `RiskLabelAudiencePayload`，风险类别、优先级、精简发现和跳转目标必填。未知字段若带可见字符串、缺字段、空白字段、英文内部状态直出或可见路径未被列入 validation result 均 fail closed。

所有 Query/Journey/risk-label audience payload 必须先生成 `AudiencePayloadValidationResult(validation_state=passed)`：中文原生字段非空；Query 恰有“依据/发现/行动项”三段；PD 措辞严格服从 typed query_context；冻结词典命中数为零；禁止内部键直接变成标签。failed payload 不输出。payload schema version、validator version/hash、lexicon version/hash、可见路径和 validation result 写入 projection/query lineage，挑战 manifest 必须精确断言。`AudiencePayloadValidationResult.audience_payload_absent` 必须与 outcome 顶层同名字段完全相等；`passed` 不能携带 `payload_schema=false`，`failed` 必须抑制 payload。存在 payload 时按 kind 精确验证允许键：Journey 必须有中文访视轴、至少一个包含 endpoint label/marker label/source jump target 的 lane；Query 必须有 typed context 与分别以“依据：/发现：/行动项：”开头的三个中文字段；risk label 必须有中文风险类别、优先级、发现摘要和跳转目标。未知可见字段、空文本或错误 schema version 均 fail closed。

生成器不得信任 fixture 或 expected outcome 自报的命中结果。每个 `d06.audience_projection_validator` case 的 `required_audience_checks` 必须精确、按序等于 `payload_schema|payload_schema_version|validator_version|validator_hash|lexicon_version|forbidden_lexicon_hash|forbidden_fragment_hits|validated_display_string_paths|validation_state|audience_payload_absent`；少一项、多一项、改序或清空均 fail closed，非 audience entrypoint 禁止声明该集合。生成器必须从实际拟输出 payload；若 payload 被抑制，则从 typed `audience|projection|query` 输入中，递归提取可见字符串和键，按冻结 lexicon 的原始顺序独立重算 phrase hits 与 forbidden display-key hits。`validated_display_string_paths` 只列真实可见文本：Journey 的 display/axis/lane 文本、Query 的三段句和 risk label 的四项中文文本；不把 payload kind、schema version、query context 或 ID 当可见文案。expected `forbidden_fragment_hits` 与可见路径必须与独立复算结果逐项、顺序完全相等；存在 forbidden phrase 时必须 `failed + audience_payload_absent=true`，存在 forbidden visible key 时直接 fail closed。同步修改自报命中列表、DSL 和外层 hash 不能改变该结论。

## 11. 增量、修订与生命周期

1. 同一 accepted snapshot、expected-set、definition/algorithm/source lineage 和稳定事实重跑，unit/result/risk/projection hash 确定且不重复。
2. N+1 更正同一 assessment/item/result 保持 clinical identity，追加 lineage；普通 snapshot/revision 不改变 classifier。
3. 低/中风险仅在后续 accepted full snapshot、AcceptanceService 决定、expected-set/public identity 未变、当前 D06 全部 L0 scope 均为 `covered` 或有权威 applicability evidence 的 `not_applicable`、且无 `partial|truncated|failed|missing|not_evaluable`，五类 L1 等式闭合且 L1 `not_evaluable=0`、无 open gate、相同规则 lineage、目标 unit 精确 linked-negative 和显式 machine adjudication 下，才执行唯一公共 R2 转换：`risk_state=closed + adjudication=rejected_by_evidence + close_reason=resolved_by_data`。任一其他 required unit 缺口或 expected-set 漂移都阻断机器关闭。
4. high、用户确认/升级、关键终点、identity ambiguity 不机器关闭。
5. 算法/量表/SAP/基线/endpoint definition 的 semantic change 导致不可比时映射为 R2 `superseded` 或终态 `not_evaluable`；不得以新算法重写旧 Run，也不得把 supersede 作为 resolved_by_data。
6. 基线更正导致多个下游变化值改变时保留因果 lineage，每个下游 result 生成新版本，不复制为多个根风险。
7. 本次 not_evaluable 只 carry-forward 既有风险并显示 gap，不产生新确定风险。
8. late-arriving 旧 cutoff 前记录只影响新 Run，不回写旧 Run。
9. 用户新增自然语言规则经拆解、适用性/来源/版本确认后形成新 rule lineage，只作用于新 Run。

## 12. 覆盖、计数与不变量

- `expected_units = positive + negative + boundary + not_applicable + not_evaluable`，每个 unit 恰好一次；未来 timepoint 不进入该式。
- `EfficacyGate` 不进入医学等式；`current_run_gates = closed_resolved + open_boundary + open_not_evaluable`，任一 open gate 阻断 D06 完整性。
- L0 与 L1 正交；L0 partial/truncated/failed/missing 或任一 L1 not_evaluable 时不得声明 D06 完整。
- definitions、assessments、items、baseline decisions、derived results、comparisons、units、risks、Queries、coverage notices、trend points 和 Journey markers 分别计数。
- 每个 positive 至少一个 D06 candidate/risk；negative 不建 candidate；boundary 至多一条保留不确定性的 clue。
- 每个 result 可双向追溯到算法、输入 item、baseline、timepoint、定义和 source locator；每个 item 只能按显式规则被消费。
- D05/D07/D08/D10 producer claim 不进入 D06 expected-set；typed ref 的 subject/site/project/run/episode 必须一致，wrong binding fail closed。
- accepted result 与 deterministic recalculation 分别保留；comparison 不覆盖任一结果。
- 每个 assessment/result/scope decision/unit/risk/query/projection 必须解析到同一 `EfficacyRunScopeBinding`；project/run/mode/source revision/accepted snapshot/cutoff 任一错绑即 fail closed。
- 每个 `BaselineSelectionDecision` 的完整 scope/cutoff/site、所有 candidate/selected assessments、baseline rule 和其下游 result 必须精确相等；跨 Run/snapshot/source revision 的 baseline 决定不得复用。
- 每个 `TimeToEventResult` 的 subject/site/project/run/mode/source revision/snapshot/scope/cutoff/episode/endpoint/timepoint 必须与 parent `DerivedEfficacyResult` 精确相等。
- 每个 `EndpointComparisonDecision` 两侧 result 必须同 scope/endpoint/timepoint/episode，并引用可解析的 `ToleranceRuleDefinition`；unknown tolerance 或 opaque comparison 打开 algorithm gate。
- `accepted_source` 必须来自 accepted analysis artifact；模型输出、外部自由文本或未接受汇总不能成为 accepted source 或 deterministic engine 输入。
- 每个 timepoint-dependent D06 unit 和每个有日期锚点的 D06 Journey marker 必须绑定同一 scope/episode 的 D05 occurrence/timing/assignment ref 与 shared temporal spine hash。
- D05 binding、shared spine、D06 scope/unit/result/projection 的 project/run/mode/source revision/accepted snapshot/scope binding/cutoff/subject/site/episode 必须全部精确相等；axis version/hash 不一致即 fail closed。
- numeric/temporal canonical serialization 冻结键序、Unicode NFC、十进制、null、布尔、时区、部分日期区间和集合排序；NaN/Infinity 拒绝，`-0` 按 policy 规范化。
- 趋势排序按真实时间区间和稳定 timepoint identity，不按输入行、VISITNUM、显示名或值大小。
- 聚合只消费稳定个体结果和明确分母，不复制风险 identity、不隐藏 high/gap。
- Query 导出不等于发送，Journey 投影不等于风险建立，筛选不改变 lifecycle。
- D06 复用公共 `contracts.py`、`lifecycle.py` 和 R2 状态机，不复制关闭逻辑。

L0 `not_applicable` 若有权威 applicability evidence、对应 L1 `not_applicable` 且不属于目标风险 identity，是可解释的非阻断状态；阻断完整性的是 L0 `partial|truncated|failed|missing`，以及不具权威依据的 `not_evaluable`。因此 §11 机器关闭所称“全部 L0 scope 完整”精确定义为 `covered` 或有权威、可追溯的 `not_applicable`，不得要求所有 unit 字面值均为 covered。

### 12.1 挑战用例执行合同

第 13 节每行不是文字检查表，而必须实例化一个 `D06ChallengeCase`：

```text
D06ChallengeCase:
  number/name/input_scope/fixture_builder/evaluator_or_projection_entrypoint
  assertion_callback/required_assertion_manifest
  expected_l0_status/expected_gate_state?
  expected_l1_disposition/expected_primary_subtype?
  expected_l2_counts/expected_l3_state_or_transition
  expected_hash_or_hash_relation/required_trace_edges
  expected_audience_fragments/forbidden_audience_fragments

D06ChallengeOutcome:
  invoked_entrypoint/input_scope_hash/output_kind=result|gate|projection|definition_binding|error
  coverage_status/gate_state?/gate_disposition?
  l1_disposition?/primary_subtype?/secondary_reason_codes
  l2_counts/l3_state?/l3_transition?/object_ids/object_hashes
  trace_edges/audience_payload?/audience_payload_absent?/audience_validation_result?
  error_type?/error_stage?

RequiredAssertionManifest:
  manifest_id/manifest_hash/contract_semantic_hash/challenge_number
  fixture_hash/entrypoint_id
  required_outcome_fields/required_exact_values/required_hash_relations
  required_trace_edge_types/required_audience_checks/expected_error_stage?

ChallengeManifestRegistry:
  registry_id/version/contract_semantic_hash
  catalog_id/catalog_version/catalog_hash/outcome_oracle_hash
  ordered_manifest_ids/row_to_manifest/test_to_row
  challenge_count/registry_hash/frozen_at

D06TypedFixtureCatalog:
  catalog_id/version/case_count/catalog_hash
  cases[challenge_number,fixture_id,fixture,expected_outcome,
        entrypoint_id,required_outcome_fields,required_hash_relations,
        required_trace_edge_types,required_audience_checks,
        assertion_dsl_version,assertion_dsl,test_id]

D06TypedFixture:
  fixture_schema_version=d06-typed-fixture-v2/challenge_number/synthetic_only=true
  scope/definitions/records/bindings/policies/case_inputs

D06AssertionClause:
  clause_id/outcome_path/operator=equals|is_null
  typed_expected_value/canonicalization_rule=d06-canonical-v1

D06ExpectedOutcomeOracle:
  oracle_id/version/case_count/oracle_hash
  cases[challenge_number,fixture_hash,expected_outcome]
```

`contract_semantic_hash=SHA-256(UTF-8 NFC、LF-normalized 的本文件从首个字节 `## 1.` 起、到 `\n## 15.` 前一字节止)`；Date/Status/§15 不参与。canonical JSON 递归把全部字符串/键转换为 Unicode NFC，object keys Unicode 升序，array 保序，UTF-8、`ensure_ascii=false`、无多余空白、分隔符 `,`/`:`；禁止 NaN/Infinity。

fixture catalog 的顶层键集合必须精确为 `catalog_id|version|case_count|catalog_hash|cases`；每个 case 的键集合必须精确为 §12.1 `D06TypedFixtureCatalog.cases[...]` 列出的十二项，未知或缺失字段均 fail closed。`catalog_id/version` 必须精确为 `medical-monitoring-r4-d06-typed-fixtures/8.0.3`，缺失、未知或同步升级均 fail closed；两字段与 catalog hash 同时显式写入每个 manifest 和 registry。fixture catalog core 是除 `catalog_hash` 外的完整 catalog object，`catalog_hash=SHA-256(canonical_json(catalog_core))`，且本冻结快照的该 hash 固定为 §15 记录值并硬绑定生成器；任何内容修改即使重算 catalog/manifest/registry hash 也不得冒充本快照。catalog 中每个 `fixture` 都是完整物化的 typed object：固定合成 scope、定义版本、accepted source records、D05/D07/D08/TTE/ICE/enrollment bindings、numeric/priority/audience policies 和该 challenge 的具体输入值均在 fixture 内；不得用场景描述、expected text、关键词、正则或运行结果替代输入。fixture hash 精确为 `SHA-256(canonical_json(fixture))`。本冻结快照的 scope 必须逐字段等于 canonical synthetic scope：`SYN-D06-PROJECT/SYN-D06-RUN-001/full/SYN-D06-SUBJECT-001/SYN-D06-SITE-001/EPISODE-001/SYN-REV-001/SYN-SNAPSHOT-001/SYN-D06-SCOPE-001/2026-01-31T23:59:59+08:00`，且 snapshot-as-of 同为该 cutoff；不能把整套 fixture 与消费对象一起迁移到另一个 subject、cutoff 或 snapshot 后重封存。

`challenge_number`、`fixture_id`、`test_id` 与说明性 annotation 只用于验证工件定位，绝不能成为 evaluator 的 typed input。生成器必须对移除 `fixture.challenge_number` 后的完整 fixture 做 canonical substantive-input 分组：同组用例的 `entrypoint_id`、全部非 case-bound expected outcome 叶和 `required_trace_edge_types` 必须完全一致。仅允许不同的 case-bound 叶为 `domain_assertions.challenge_assertion_code`、`domain_assertions.evaluated_fixture_hash` 与 `object_hashes.fixture_hash`；其他任何 L0/L1/L2/L3、临床文字、trace、audience、identity、count 或 error 差异均 fail closed。不得通过 case 编号、expected text、oracle、manifest 或测试注释使相同 typed input 产生不同 runtime outcome。

相同并不等于正确。对当前唯一 substantive duplicate group 17/173，生成器还必须使用独立 `DefinitionBoundaryClinicalOutcomeResolver`，不能从 expected outcome、oracle、DSL、manifest 或 implementation table 读值。resolver 的 typed 前提精确为：entrypoint=`d06.gate_evaluator`；`case_inputs.typed_parameters` 仅含 canonical-sorted unique `applicable_instrument_ids=[INST-001,INST-002]`；instrument definition 的完整键集合精确为 `admin_mode|content_hash|definition_scope|id|object_type|recall_period|reporter_type|source_locator_ids|stable_key|version`，endpoint definition 的完整键集合精确为 `content_hash|definition_scope|directionality|id|object_type|role|source_locator_ids|stable_key|version`；两者的 `definition_scope` 键集合必须精确为 `project_ref|run_ref|monitoring_mode|subject_ref|site_ref|episode_key|source_revision|accepted_snapshot_ref|scope_binding_id|cutoff` 并逐字段等于 fixture scope。instrument ID/stable key/version=`INST-001/SYN-SCALE/1.0`，endpoint ID/stable key/version=`EP-001/SYN-ENDPOINT/1.0`；两者 content hash 均须由除 `content_hash` 外的完整 typed definition 重算相等，source locators 非空。满足时唯一 semantic code=`definition_boundary_gate`，唯一 `clinical_outcome_contract="definition boundary gate"`；字段缺失/未知、候选集合/顺序/唯一性漂移、版本/定义/scope/content hash 不能解析时 fail closed。catalog、oracle、DSL 和生成的 manifest 必须逐一等于该独立推导值。即使把两个用例、oracle 与外层 hash 同步重封成同一个错误文本，也必须在 manifest 构建前失败。

fixture 的条件对象也必须可执行：`d05_binding_state=required` 时 accepted D05 inventory、每个 `D05AssessmentBindingRef`、对应 foreign-key registry、完整 required set、唯一 `SharedTemporalSpineBinding`、axis version/hash 和正反 consumer link 全量物化；每个被消费的 `ActualAssessmentRecord` 还必须是完整同 scope/cutoff/episode 的 `accepted_current` 当前记录，assessment/stable key、instrument、assessment time、item IDs、D05 unit/activity/disposition/assignment、scope decision 与 correction/supersession 状态均解析到冻结来源。每个 assessment 必须按冻结顺序解析恰 6 个 typed `AssessmentItemRecord`；item identity 全局唯一，反向指向 parent assessment，定义 ID、原始/规范值、单位、accepted-current 与 correction 状态、source locator 和可重算 content hash 完整。当前评估项还必须与 evaluator 的 item input 一一相等。不存在的 item、空 source locator、错 parent、wrong order、withdrawn、superseded、跨 subject/site/run/snapshot 或未解析 correction 的记录，即使同步重算 lineage/catalog hash 也不得进入 accepted inventory。`maturity_binding_state=required` 时 decision、typed consumer、全部 typed anchors、candidate set、selected/tie 状态、D05 source identity/time 与 spine hash 必须互相解析。ICE 的 `not_required|missing_required` 禁止在任何 nested input 夹带可消费 estimator binding；`active` 才允许恰一个 active ID 指向完整同 scope `EstimatorBinding`。Query 用例的每个 active/variant context 必须有独立 `EnrollmentContextDecisionRef` 并绑定 closed-role source event、冻结 enrollment rule/version、effective time 与 lineage。每个 TTE binding 必须解析 `TTESourceRegistry`、`TTEPrecedenceRule` 和 typed event source 的 endpoint/timepoint/rule/source times/event identity；event/censor time还必须解析冻结 timepoint，boundary 的每个 feasible ID 必须解析为完整同 scope `TimeToEventInterpretationRef`，不产生单一 duration。每个 fixture 必须携带 canonical full `D06PriorityPolicy`；resolver、decision 与 outcome 只能解析该完整 policy。risk case 还必须通过 typed `D06UnitStableCore` 绑定 priority/risk/public identity。控制面 definition no-match 不得携带 medical-unit D05/maturity binding、priority resolver 或 priority decision。

manifest core 是除 `manifest_id` 与 `manifest_hash` 外的完整 manifest object，`manifest_hash=SHA-256(canonical_json(manifest_core))`，`manifest_id="d06m-" + 三位 challenge number + "-" + manifest_hash 前 16 个十六进制字符`。registry core 恰含 `registry_id/version/contract_semantic_hash/catalog_id/catalog_version/catalog_hash/outcome_oracle_hash/challenge_count/manifests/ordered_manifest_ids/row_to_manifest/test_to_row`，`registry_hash=SHA-256(canonical_json(registry_core))`；`frozen_at` 和 `registry_hash` 自身不参与 registry hash。冻结时生成只读 typed fixture catalog、独立 immutable expected-outcome oracle 与 `ChallengeManifestRegistry`，registry 必须恰有 challenge_count 个 manifest、challenge number 连续唯一、row↔catalog case↔oracle case↔manifest↔test 双向无孤儿。oracle core 为除 `oracle_hash` 外的完整 object；其固定 hash 必须同时硬绑定于生成器、每个 manifest 与 registry。每个 oracle case 精确绑定 challenge number、fixture hash 和完整 expected outcome；catalog/DSL/manifest/registry 即使一起重封存，也不能改写 coverage、L1/L2/L3、counts、clinical outcome 或任何 expected leaf。每个 manifest 直接复制经 oracle 验证的 exact typed expected outcome 和 assertion DSL；生成器只能验证/哈希/装配，不得从 Markdown prose 或 fixture 内容推断 entrypoint、L0/gate/L1/L2/L3/hash/trace/audience/error-stage 期望，不得提供默认 expected fallback。不存在 `positive or not_evaluable` 这种未由 fixture 决定的运行时分支。

fixture builder 只能返回与 frozen catalog object 和 `fixture_hash` 相同的 typed input；runner 必须调用 frozen entrypoint并生成 `D06ChallengeOutcome`。v1 使用冻结 `assertion_dsl_version=d06-assert-v1`，不依赖可替换 callback source：interpreter 只能读取 outcome 与 manifest clauses，逐 clause 解析 typed path；每个 clause 的键集合必须精确为 `canonicalization_rule|clause_id|operator|outcome_path|typed_expected_value`，不得缺字段或夹带未知字段。持久 fixture 仅允许 `equals|is_null` 两个 operator，且 `is_null` 的 `typed_expected_value` 必须严格为 null，`equals` 的 `typed_expected_value` 必须严格非 null。clause IDs 必须从 `assert-001` 连续编号，canonicalization rule 必须恒为 `d06-canonical-v1`。DSL 与 expected outcome 的全部叶路径必须构成精确一一映射：每个 leaf 恰一 clause、不得多出未知或重复 path，不得加入额外 clause、恒真比较或未消费 outcome；任一违反均在 pre-evaluator coverage validation 失败。`required_trace_edge_types` 自身必须等于 canonical sorted-unique list，outcome `trace_edges` 与之逐项完全相等，不能用 set 化隐藏重复或改序。每个 outcome 必须把 `invoked_entrypoint`、`input_scope_hash`、`object_hashes` 与 canonical-sorted `trace_edges` 作为 exact typed expected fields；audience 用例还必须精确断言 `AudiencePayloadValidationResult` 与 `audience_payload_absent`，后者为 true 时禁止出现 payload，为 false 时 payload 必填。manifest/test 不能根据实际 outcome 动态生成、替换或修改期望，runner 执行前重算 catalog hash、DSL hash、manifest_hash、manifest_id、fixture hash、registry hash。每行精确断言真实输出和 structure/identity/hash/trace/audience 不变量；schema/QC fail 用例断言具体 error_type + error_stage 且 L1/L2 未创建。缺任一 manifest 字段 coverage 即该行未覆盖。

## 13. 最小合成挑战矩阵

每一行须成为具名 fixture/test 或经接受的一对多映射，并按 §12.1 断言该用例适用的 L0/gate/L1/L2/L3/hash/trace/audience 字段；schema/QC fail 用例须断言在建立医学输出前 fail closed，不能虚构 L1/L2/L3。

| # | 挑战 | 预期 |
|---:|---|---|
| 1 | 6 项完整，总分与重算一致 | negative |
| 2 | 总分与重算不一致 | `score_inconsistent` positive |
| 3 | 必需 item 缺失且算法不允许缺项 | `required_component_missing` positive |
| 4 | 6 项量表已答 `[1,2,3,4,5]`、第 6 项缺失；规则为 after-reverse prorate_mean、minimum_answered_count=5，记录总分 18 | recalculated score=18、comparison=consistent、L1=negative |
| 5 | 最少已答题数规则缺失 | algorithm gate not_evaluable |
| 6 | 反向计分 item 正确 | negative |
| 7 | 反向计分遗漏 | score positive |
| 8 | item 权重错误 | score positive |
| 9 | 变换公式版本错误 | score positive |
| 10 | 仅舍入差异且在冻结容差内 | negative |
| 11 | 容差规则缺失且差异会改变分类 | not_evaluable |
| 12 | raw value 超理论范围 | component positive |
| 13 | normalized value 有效但 raw value 保留 | 可追溯，不覆盖 raw |
| 14 | 原始单位可按冻结换算 | negative |
| 15 | 单位缺失且量纲不可唯一推断 | unit gate not_evaluable |
| 16 | 同名量表两个版本，适用版本唯一 | 选唯一版本 |
| 17 | 两个量表版本均有完整适用依据且计分不同 | definition boundary gate |
| 18 | 默认选最新量表版本 | QC fail |
| 19 | 量表名称相同但 item 集不同 | 身份分离 |
| 20 | 来源角色完整且明确把 ClinRO 值填入只允许 PRO 的评估 | `rater_or_mode_inconsistent` positive |
| 21 | 允许代理报告且角色/条件匹配 | negative |
| 22 | 代理仅猜测患者感受，定义不允许 | rater positive |
| 23 | 纸笔转电子且有 accepted equivalence rule | negative |
| 24 | 实施方式改变且无可比规则 | not_evaluable |
| 25 | recall period 不符且记录完整 | rater/mode positive |
| 26 | 整个计划评估缺失 | 路由 D05，不建 D06 duplicate risk |
| 27 | D05 已确认评估发生但 item coverage 表缺失 | D06 not_evaluable |
| 28 | D05 评估按时但 D06 总分错误 | D05 negative、D06 positive |
| 29 | D05 评估超窗但分数正确 | D05 positive、D06 negative，identity 分离 |
| 30 | 计划访视未来未到期 | 不进 D06 expected-set |
| 31 | cutoff 后评估 | 仅 Journey 截止日后记录 |
| 32 | 部分日期跨 cutoff | cutoff boundary gate |
| 33 | date role 缺失 | not_evaluable，不伪造时间 |
| 34 | 唯一合格干预前基线 | baseline negative |
| 35 | 首次给药前第 7 天和第 1 天各有一次合格评估；policy=chronological_last | CandidateSelectionDecision=unique、selected=第 1 天 assessment、baseline L1=negative |
| 36 | 无规则却默认最近首次给药 | QC fail |
| 37 | 两个完整基线候选且 tie-break 未定义 | baseline boundary |
| 38 | 基线候选时间冲突 | baseline not_evaluable |
| 39 | postbaseline 值被当作基线 | baseline positive |
| 40 | 重筛 episode 的旧基线被复用且 episode 证据完整 | `baseline_inconsistent` positive；新旧 episode unit identity 分离 |
| 41 | 不同治疗周期各有基线 | episode 身份分离 |
| 42 | baseline 更正 | 新 lineage，旧结果 superseded |
| 43 | change 重算一致 | negative |
| 44 | change 符号错误 | change positive |
| 45 | lower-better 被显示为更差 | trend/projection QC fail |
| 46 | higher-better 被显示为改善 | 正确方向投影 |
| 47 | directionality 未定义 | 不显示改善/恶化，只显示数值 |
| 48 | percent change 基线为零且无规则 | not_evaluable |
| 49 | percent change 与冻结公式一致 | negative |
| 50 | unit conversion 后 change 一致 | negative |
| 51 | response 规则为改善比例 `>=30%`，确定性值恰为 30%，source class=responder | comparison=consistent、response L1=negative |
| 52 | response 规则为改善比例 `>30%`，确定性值恰为 30%，source class=non_responder | comparison=consistent、response L1=negative |
| 53 | 阈值端点包含性缺失 | not_evaluable |
| 54 | 部分精度跨 response 阈值 | boundary |
| 55 | responder 需连续两次确认且仅一次 | response positive |
| 56 | 确认时间窗内两次满足 | negative |
| 57 | progression 组成项方向错误 | response positive |
| 58 | source response class 与完整原始值/冻结阈值冲突，无外部报告 | `response_class_inconsistent` positive；response root、组成值和阈值 trace 完整 |
| 59 | `any_component` 复合终点：一个组件 event，其他组件 non_event 且全部可评价 | composition negative；逐组件 trace 完整、总体 event |
| 60 | 复合终点漏掉一个发生组件 | composition positive |
| 61 | multi-component 要求全部满足却用 any | composition positive |
| 62 | component identity 不唯一 | not_evaluable |
| 63 | hierarchical endpoint 顺序错误 | composition positive |
| 64 | time-to-event 事件日和删失日一致且 event precedence 明确 | negative；status=event、origin/event/competing rule trace 完整 |
| 65 | time-to-event 事件/删失规则缺失 | not_evaluable |
| 66 | D06 生成 KM/HR/p 值 | scope QC fail |
| 67 | primary endpoint role 唯一，single + recoverable + actionable | impact=primary_endpoint、priority=medium、precedence_step=3 |
| 68 | endpoint role undefined | priority unknown，不默认 low |
| 69 | SAP 明确低影响 exploratory，single + recoverable + actionable 且四项输入完整 | impact=administrative、priority=low、匹配 precedence step 5 |
| 70 | key secondary、repeated_subject、recoverable、actionable | impact=key_secondary_endpoint、priority=medium、precedence_step=4 |
| 71 | 主要终点数据问题 | high + machine-close-forbidden |
| 72 | accepted result 与重算一致 | comparison negative |
| 73 | accepted result 与重算不一致 | reported result positive |
| 74 | 只有 accepted result、无算法/原始项 | not_evaluable，不把 accepted 值当完整证据 |
| 75 | 只有原始项、无 accepted result，但算法完整 | 可生成 deterministic result |
| 76 | 模型自由补算权威分数 | QC fail |
| 77 | 模型对缺项做均值填充 | QC fail |
| 78 | SAP 冻结规则对缺失 item 使用 after-reverse explicit_constant=0；重算与 accepted result 一致 | result=complete、comparison=consistent、L1=negative，并保留 strategy/input lineage |
| 79 | 未预设 LOCF | 禁止 LOCF |
| 80 | treatment discontinuation 被当作 missing | ICE/missing QC fail |
| 81 | rescue therapy typed event 且 strategy 明确 | 趋势显示上下文 |
| 82 | rescue therapy 同日但 wrong subject | fail closed |
| 83 | death 后不存在的测量被标普通缺失 | QC fail |
| 84 | withdrawal 后观察值按冻结 treatment-policy strategy 纳入，typed ICE 与 estimator 状态完整 | result=complete、ICE context=applicable、L1=negative |
| 85 | hypothetical strategy 无 estimator | ICE context/L1=not_evaluable；不生成假设值或正常 derived result |
| 86 | ICE 规则有两个完整合法解释且结论不同 | boundary |
| 87 | 缺 ICE 来源角色 | dependency not_evaluable |
| 88 | 同一 timepoint 重复测量，规则选首次 | 唯一选择 |
| 89 | lower-better endpoint 同一时点候选值 8 与 12，policy=worst_value | CandidateSelectionDecision=unique、selected=value 12 assessment、repeat L1=negative |
| 90 | 无规则默认最后一条 | QC fail |
| 91 | 重复记录实为更正且 lineage 完整 | 使用当前 accepted，保留旧值 |
| 92 | 两条冲突值均无更正 lineage | not_evaluable |
| 93 | 中央评审是终点权威，本地值不同 | 使用中央；本地作上下文 |
| 94 | 未指定中央/本地优先级 | not_evaluable |
| 95 | 短时大幅改善命中冻结阈值 | trend positive，标签“个体趋势待核实” |
| 96 | 短时大幅变化但无冻结阈值 | 只显示数值，不建风险 |
| 97 | 相邻点方向反转命中复核规则 | trend positive |
| 98 | 三点持平且 item 组合一致 | negative |
| 99 | 总分持平但 item 组合互换且规则要求复核 | trend positive |
| 100 | 只有模型认为“不符合药物机制” | 不建风险 |
| 101 | D08 已验证暴露—疗效关系 | 可显示 typed relation，不复制 D08 risk |
| 102 | 仅相同日期的 IP 与疗效变化 | 不建立关系 |
| 103 | D07 实验室值作为明确替代终点输入 | 仅消费 typed endpoint value |
| 104 | D07 安全异常与疗效同日 | 不复制安全风险 |
| 105 | 外部监查报告趋势与个体值一致 | report consistency negative |
| 106 | 报告说改善但个体数据明确恶化 | reported result positive |
| 107 | 报告无分母/来源 | not_evaluable，不直接判错 |
| 108 | 同 snapshot 重跑 | 全部 hash 稳定、不重复风险 |
| 109 | item 输入顺序交换 | score/result/hash 不变 |
| 110 | endpoint 定义输入顺序交换 | expected-set/hash 不变 |
| 111 | 算法 hash 变更且以内容寻址证明语义等价 | classifier 稳定、旧执行 lineage superseded |
| 112 | endpoint 逻辑义务无法跨版本证明延续 | identity_ambiguous |
| 113 | N+1 补充精确 linked-negative | 低/中风险可按公共 gate 关闭 |
| 114 | N+1 coverage partial | carry-forward，不关闭 |
| 115 | high 后续已更正 | 保留人工关闭要求 |
| 116 | late-arriving 旧 cutoff 前数据 | 只影响新 Run |
| 117 | wrong project binding | dependency gate not_evaluable，join fail closed |
| 118 | owner routing 竞争 | 单一 routing gate，不重复单元 |
| 119 | 一个 gate 影响 20 个 timepoints | 只计一个 control-plane gate |
| 120 | open+resolved、closed+boundary 或 open+blocks=false gate | schema fail closed；合法 open boundary/not_evaluable 必须 blocks=true |
| 121 | Query 缺依据/发现/行动项 | audience QC fail |
| 122 | not_evaluable 生成 Query | QC fail，只能 coverage notice |
| 123 | 投影把 PRO/ClinRO/PerfO 都标“已记录事项” | audience QC fail |
| 124 | 投影泄漏 positive/candidate/正式事实/候选信号 | audience QC fail |
| 125 | 基线、阈值、实际点和风险 marker 可辨 | projection pass |
| 126 | 无日期点被放在伪造日期 | projection fail，进入资料待补充区 |
| 127 | 筛选/缩放改变风险数量或生命周期 | projection QC fail |
| 128 | 中高风险折叠后身份/数量丢失 | projection QC fail |
| 129 | 点击风险无法回到原始 item/算法/定义 | traceability fail |
| 130 | 全部 L0 covered、五类 L1 闭合、not_evaluable=0 且无 open gate | 才可声明 D06 域完整 |
| 131 | L0 partial 但 L1 全 negative | 不得声明完整 |
| 132 | fixture 含真实项目/受试者/固定量表硬编码 | isolation QC fail |
| 133 | wrong site binding | dependency gate not_evaluable，join fail closed |
| 134 | wrong Run binding | dependency gate not_evaluable，join fail closed |
| 135 | wrong phase/episode binding | dependency gate not_evaluable，join fail closed |
| 136 | wrong source revision/accepted snapshot binding | scope gate not_evaluable |
| 137 | model output 包装为 accepted_source | schema/QC fail closed |
| 138 | 模型选择最大改善值作为基线 | baseline QC fail，不得执行 |
| 139 | 模型输出“具有统计学显著性/研究有效” | audience QC fail |
| 140 | 未预设零填充、最佳值填充或最差值填充 | algorithm gate，不得计算 |
| 141 | decimal 2.345 在 half-up 与 half-even 边界 | 严格按冻结 numeric policy，分类/hash 可重放 |
| 142 | 同值 `1`/`1.0`/`1.00` | canonical result/hash 相同 |
| 143 | `-0` 与 `0` 且 normalize_zero | canonical result/hash 相同 |
| 144 | NaN/Infinity 输入 | schema/algorithm fail closed |
| 145 | Unicode 等价标签 NFC 前后 | identity/hash 相同；原始显示保留 |
| 146 | 同一 instant 的不同时区表示 | temporal canonical hash 相同 |
| 147 | month precision 跨分析窗口 | boundary，不取月初/月末 |
| 148 | month precision 跨基线窗口 | baseline boundary |
| 149 | month precision 跨 responder 确认窗口 | response boundary |
| 150 | 成熟时点规则缺失 | gate not_evaluable，不生成 future/missing 结论 |
| 151 | unknown scoring operation | algorithm gate not_evaluable |
| 152 | prorate 在 reverse 前/后会得不同值而 stage 未定义 | algorithm gate not_evaluable |
| 153 | composite component 缺失且 rule=propagate_missing | composition not_evaluable；逐组件 trace 保留 |
| 154 | composite 一项 event、一项 missing，combination=all_components 且 missing policy=not_event | overall=non_event、composition L1=negative，逐组件 trace 保留 |
| 155 | responder 两次确认 refs 之一 wrong episode | fail closed |
| 156 | time-to-event 缺 time origin | not_evaluable |
| 157 | semantic algorithm change 但个体数值偶然相同 | 新 lineage，旧结果 superseded，不用于 auto-close |
| 158 | 阈值 `>=` 改 `>` 且值在边界 | semantic change，分类按新 lineage 重算 |
| 159 | D05 occurrence ref 缺失 | dependency gate；不投影到访视轴 |
| 160 | D05 ref 同名但 wrong axis hash | fail closed，不按名称吸附 |
| 161 | shared spine wrong cutoff | projection QC fail closed |
| 162 | 三种 query_context | 仅 enrolled_or_post_enrollment 可出现 PD 评估措辞 |
| 163 | primary endpoint、single、recoverable、actionable | impact=primary_endpoint、priority=medium、precedence_step=3、policy hash 可重算 |
| 164 | primary endpoint actionability unknown | priority unknown，不默认 high/low |
| 165 | repeated-site key secondary 且 actionable | high，保存 recurrence evidence |
| 166 | open boundary gate 且其余 L1 全 negative | D06 域仍不完整 |
| 167 | open not_evaluable gate 且其余 L1 全 negative | D06 域仍不完整 |
| 168 | item 缺失同时总分和报告不一致 | item root positive；下游 not_evaluable，差异只作 secondary evidence |
| 169 | 两个独立 clinical actions 同时异常 | 保留两个 unit roots；风险/Query 不按别名重复 |
| 170 | challenge callback 为 lambda/pass/assert True/字面量恒真 | challenge validator 拒绝 |
| 171 | challenge 只断言 fixture 输入未断言 outcome | challenge validator 拒绝 |
| 172 | 一个 challenge 拆成多个测试 | 双向映射、L0/L1/L2/L3/hash/trace 总覆盖完整 |
| 173 | 同一 endpoint 有两个合法 instrument 定义 | definition boundary gate |
| 174 | 同一 endpoint 有两个合法 timepoint/ICE 定义 | 单一 definition boundary gate，全部 feasible IDs 入 hash |
| 175 | baseline decision 来自 wrong Run/source revision | fail closed，不产生 change/response result |
| 176 | accepted/recalculated 差值恰在 absolute tolerance inclusive 边界 | 按 `ToleranceRuleDefinition` negative |
| 177 | comparison 缺 tolerance definition | algorithm gate not_evaluable |
| 178 | maturity/cutoff 使用 opaque expression | schema/QC fail；只允许关闭 temporal rule |
| 179 | hypothetical ICE 无 estimator binding | ICE context not_evaluable，不构造反事实值 |
| 180 | TTE ref 来自 wrong subject/scope | fail closed |
| 181 | 实验室值无 validated D07 endpoint ref | 只显示 context，不作为 endpoint input |
| 182 | 同日 IP/疗效但无 validated D08 relationship ref | 不画关系、不建 D06 risk |
| 183 | 低风险 linked-negative 满足关闭条件 | 精确 R2 closed/rejected_by_evidence/resolved_by_data 转换 |
| 184 | D06 尝试输出中心/项目/治疗组聚合趋势 | owner/QC fail，必须路由 D10 |
| 185 | analysis artifact 未经 AcceptanceService 接受 | coverage gap，不得成为 accepted_source |
| 186 | actual recall period 与 instrument 明确不同、来源完整且无 equivalence rule | `rater_or_mode_inconsistent` positive |
| 187 | D05 binding 与 D06 source revision/snapshot 不同 | dependency fail closed，不投影共享轴 |
| 188 | 页面 flag 设置 enrolled，但 typed enrollment decision unresolved | Query 禁止 PD 措辞 |
| 189 | challenge callback 读取 outcome 但只断言无关字段 | manifest coverage fail，challenge 不计覆盖 |
| 190 | `all_components` 中一项正确、一项缺失且 propagate_missing | composition not_evaluable，逐组件 trace 完整 |
| 191 | 外部监查报告写改善，但 accepted source-backed 个体值明确恶化 | `reported_result_inconsistent` positive；report root 与 source/result trace 分离 |
| 192 | arm/phase applicability unresolved 且两套定义可行 | 单一 applicability boundary gate，不选定义 |
| 193 | 一个 definition decision 影响 20 个 timepoint | 一个 gate、canonical affected-set hash、零正常 units |
| 194 | relative tolerance 的 accepted/recalculated denominator 结果不同 | 严格按 reference_role；缺角色则 algorithm gate |
| 195 | 1 月 31 日加 1 calendar month，end_of_month_policy=clamp_to_last_day | 结果为同年 2 月最后一日，不按 30 天 |
| 196 | event/censor/competing event 同刻且 rule=first_in_order、competing_event 排首位 | TTE status=competing_event，typed ref/precedence trace 完整 |
| 197 | 一个 item 原记录分叉为两个 accepted_current correction | identity/algorithm gate，不按录入时间选值 |
| 198 | negative unit 有中央确认和本地差异 | counterevidence + context 两类 L1b refs 均保留 |
| 199 | actual assessment 更正但 obligation 未变 | unit_id 不变、lineage/result hash 更新 |
| 200 | public impact=rights_safety 且 recoverability unknown | high + machine-close-forbidden，另列 coverage context |
| 201 | 目标 unit linked-negative 但另一 required unit not_evaluable | 阻断 R2 resolved_by_data |
| 202 | ICE estimator_availability=available 但无 estimator binding | schema/QC fail closed |
| 203 | applicability `any` 全 no_match 且 rule=no_match:not_applicable | control-plane definition binding=not_applicable；不建 medical expected unit，L1 为空 |
| 204 | gate 缺 required gate_binding_ref_id | error_type=SchemaContractError、error_stage=gate_binding_validation，且不创建 L1/L2 |
| 205 | denominator=other_explicit 但无 input key/unit | algorithm gate not_evaluable |
| 206 | zero denominator policy=explicit_constant 但无 constant/unit | algorithm gate not_evaluable |
| 207 | maturity anchor candidates 两个且无唯一 tie-break | MaturityAnchorSelectionDecision boundary |
| 208 | responder 规则要求 consecutive 两次但中间一次不满足 | not_confirmed，不以任意两次替代 |
| 209 | competing event 同刻 precedence 胜出 | TTE status=competing_event + typed ref |
| 210 | 两个 accepted_current assessments 共享 stable key | identity gate，不进入 item/score selection |
| 211 | D07 value 与 consuming operation endpoint 不同 | D07ConsumptionBinding fail closed |
| 212 | equivalence rule 用于未绑定的另一量表 | rater/mode fail closed |
| 213 | absolute_jump trend rule 缺 threshold | rule validation=not_evaluable、L1=not_evaluable、L2 risk/query=0 |
| 214 | manifest registry 少一行或任一 fixture hash 变化 | error_type=ChallengeRegistryIntegrityError、error_stage=pre_fixture_integrity，runner 不调用 evaluator |
| 215 | 已唯一绑定并已生成的 unit 有权威 unit-level applicability rule/effective interval 与 applicability evidence | L0=not_applicable、L1=not_applicable，可满足域完整且不阻断其他目标 risk close |
| 216 | Query 含 `backend QC positive` 或 Journey 含 `candidate` | AudiencePayloadValidationResult=failed、命中冻结 lexicon，audience payload 不输出 |
| 217 | lower-better endpoint 使用 worst_value | 选择 maximum；decision/hash 可重放 |
| 218 | selection 无 candidate 且 policy=no_candidate:not_evaluable | decision not_evaluable，不默认最后/最近 |
| 219 | event/censor 同刻且 `tie_policy=boundary` | TTE status=boundary、至少两个同 scope feasible interpretation refs、无单一 duration |

## 14. 实现与验收边界

### 14.1 合同接受后的允许实现面

只允许在 `poc/medical_monitoring_ai_native_r4` 新增 D06 领域对象、确定性 evaluator、合成 fixtures、Journey projection 和测试；公共文件只做复用 identity/lifecycle/typed join 的最小适配，并跑 D01-D05、R2、R3 相邻回归。

禁止启动 8911、运行真实项目、调用真实 provider、修改 R1-R3 冻结语义、R5 产品 UI、医学写作子系统或安全实现/测试；禁止引入统计推断和正式 PD workflow。

### 14.2 完成证据

1. 合同经隔离新上下文反证审阅并由 Codex 冻结；
2. 219 行挑战矩阵全部具名覆盖或有经接受的拆分映射；
3. D06 聚焦、R4 全量、R2、R3、compileall、确定性重跑、root export 与 audience payload QC 通过；
4. definition/algorithm/baseline/result/comparison/L1/L2/L3/Query/Journey join 不变量通过；
5. D05 typed occurrence/timing surface 被真实消费且不重复风险；D07/D08/D10 只保留 typed boundary；
6. 8911 仍停止，未运行真实项目，医学写作文件无改动；
7. 独立 verifier 以冻结 hash 接受，Codex 写 acceptance record、R0-R8 与 LOOP ledger。

### 14.3 非完成声明

D06 合成纵切通过不等于 R4 总体、R5 Patient Journey UI、真实项目、真实模型、统计分析、项目级疗效结论、产品或商业化接受。

## 15. 纠偏与冻结记录

冻结状态：`FROZEN_R4_D06_CONTRACT_V1_18`。v1.17 已关闭用例 106/191 的同输入异 trace 与 expected/manifest 循环注入问题，但随后的 raw-runtime 实现纠偏对账又发现用例 17 与 173：两者移除 `fixture.challenge_number` 后的完整 typed fixture 相同，entrypoint、trace 及所有执行性结果也相同，唯一矛盾是 `clinical_outcome_contract` 文本不同。运行时若满足两个文本只能按 challenge/test identity 分支，违反合同。因此 v1.17 验证工件不再作为实现接受依据，v1.17 实现也仍未被接受。

本次 v1.18 只做最小验证工件勘误：把用例 173 的 `clinical_outcome_contract` 统一为与同一 typed input 的用例 17 相同的 `definition boundary gate`，并新增生成器强制不变量——相同 substantive typed fixture 必须具有相同 entrypoint、trace 和除三个 case-bound hash/定位叶外的全部 expected outcome；独立 typed resolver 另从精确 definition schema/scope/version/content hash 推导唯一临床结果文本，防止两个用例一起重封为同一错误答案。本段不参与 contract semantic hash。

同一独立合同审阅 session `019ff62a-6f59-75f2-b80f-95f917d53a4b` 在 pass 27 接受完整 v1.18 候选草稿文件 SHA-256 `663ca94a3166fea08080a0611e3831a21396fe3a8783c646a434e2e537b8bef7`、§1–§14 语义 SHA-256 `247eb0bc4a4c97428714f069639161ac832bed05cfcb7dfc4c01240a7ef84642` 及下列固定 catalog/oracle/registry。顶部标题、状态、范围与本段是接受后由 Codex 写入的冻结元数据；§1–§14 语义和 219 个验证用例未变。pass 25/26 的拒绝 findings 已在 pass 27 的协调重封负变异中关闭。

已冻结 validation artifact reference：

- typed fixture catalog artifact: `reviews/medical_monitoring_r4_d06_typed_fixture_catalog_v1_20260812.json`
- typed fixture catalog version: `8.0.3`
- typed fixture catalog hash: `44287f1277790ad0bbbd21045565c50049a67d5451c6eefcb30e68f12d64b774`
- typed fixture catalog file SHA-256: `d4774a82e3d34dae28d6f25145f672cb62b28c506453d1bcc49ce0d60021a8e9`
- independent expected-outcome oracle artifact: `reviews/medical_monitoring_r4_d06_expected_outcome_oracle_v1_20260813.json`
- independent expected-outcome oracle hash: `16b8b9648670adcae14fa16b1fe03c2570a2449e3835671bab00345f6fe9244a`
- independent expected-outcome oracle file SHA-256: `772bca08198b7e6279915c22077f74e328f97d2563f95a0f49db1f9d4d63e26b`
- registry artifact: `reviews/medical_monitoring_r4_d06_challenge_manifest_registry_v1_20260812.json`
- contract semantic hash: `247eb0bc4a4c97428714f069639161ac832bed05cfcb7dfc4c01240a7ef84642`
- registry hash: `f7a7733b00c1367d95e66d7f8b5e1a12793d51ab0f7585367dcad664922be1b4`
- registry file SHA-256: `a02c4f8b7969e7b86673fc32903929f333adbf2f68fac401551056b23b7e0aba`
- challenge count: `219`

v1.18 冻结只授权 `poc/medical_monitoring_ai_native_r4` 内的合成/离线 D06 有界实现纠偏，不等于实现、R4 总体、R5 UI、真实项目、统计分析、产品、医学写作或生产接受。最终冻结文件 SHA-256 记录在合同接受记录中，并须由同一审阅会话进行一次 metadata-only 确认。
