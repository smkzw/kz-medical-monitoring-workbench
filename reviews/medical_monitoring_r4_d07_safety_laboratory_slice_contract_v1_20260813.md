# R4-D07 临床安全性、实验室与检查纵切合同 v0.4

Date: 2026-08-13  
Status: `REVISED_DRAFT_V0_4_FOR_INDEPENDENT_REVIEW`  
Scope: 仅限 synthetic/offline R4-D07 合同与后续有界 POC；不代表实现、R4 总体、R5 UI、真实项目、正式安全性评价、监管报告、产品或生产接受。

## 1. 目标、用户问题与禁区

D07 面向中文医学监察员回答：

1. 每项 LB/VS/EG/PE/影像或其他安全检查是否有可解释的原值、单位、范围、时间、访视、基线与来源；
2. 治疗后是新发异常、基线异常加重、持续/复发、恢复，还是仅由单位/范围/样本/时间变化造成；
3. CTCAE 或项目分级、CS/NCS、AE 记录、复测、CM/IP 处置和方案/IB 要求是否彼此一致；
4. 哪些异常需要优先查看，缺少哪一环，能否一跳回原始结果、适用规则和相邻事件。

D07 产生具体的“检验结果待核实”“检查变化待核实”“复测或处置记录待核实”“临床意义判断待核实”风险、三段式 Query 草稿和 renderer-neutral Journey 标记。禁止：

- 把任何超范围值自动认定为 AE、SAE、AESI、DILI、心律失常或药物相关反应；
- 把 CTCAE/检查等级、严重性、CS/NCS 和监察优先级互相替代；
- 由模型补单位、范围、基线、等级、临床意义、处置或因果关系；
- 在通用内核硬编码项目名、药物名、检查项、表/字段、Hy's law、QTc、停药或复测阈值；
- 在 D07 形成中心/项目/治疗组聚合、发生率、正式安全结论或监管报告。

## 2. 依据与来源权威

### 2.1 外部依据

- ICH E2A：异常实验室发现可构成 AE 的一种表现，但 AE、因果、严重性和严重程度分离。
- ICH E3：按时间和个体变化评价实验室安全性，阈值及 shift 定义需预先说明。
- ICH E19：安全资料收集范围必须由研究文件明确，不能把未收集误作阴性。
- NCI CTCAE：版本化术语/等级；运行时只使用项目绑定版本。
- FDA DILI 与 ICH E14：肝损伤/QT 风险需组合证据和项目化规则，不能变成全局硬编码诊断器。
- NMPA/CDE：受试者保护与安全风险管理属于申办方/研究者/DMC 正式职责；本系统仅提供可追溯监查看板与 Query 草稿。

完整链接与取舍见 `context/medical_monitoring_r4_d07_external_pattern_decision_20260813.md`。

### 2.2 项目内 claim authority

1. **收集/处置权威**：事件时适用的方案、修订、IB/RSI、实验室手册、检查章程、监查计划及项目激活规则；
2. **原始观察权威**：accepted full snapshot 中原值/字符结果、单位、范围、采集/检查时间、方法、样本状态、读片/复核与更正 lineage；
3. **参考与分级权威**：事件时适用且版本明确的中心/本地范围、单位转换、CTCAE/项目分级、器官风险与处置 RuleSet；
4. **相邻域权威**：D01 AE/MH、D02 CM、D03 IP、D04 方案、D05 访视/活动、D06 疗效及住院/操作 producer 的 accepted typed refs；
5. **辅助来源**：自由文本、外部报告、历史看板和模型输出只帮助定位或形成候选，不覆盖 1–4。

冲突不得用“最新”、多数票或模型置信度解决。无法唯一绑定适用版本/范围/单位/时间/方法时为 `boundary` 或 `not_evaluable`。

## 3. 唯一 owner 与相邻域边界

| Claim | 唯一 owner | D07 行为 |
|---|---|---|
| AE/MH 是否已记录、是否疑似漏报、严重性判据 | D01 | 仅输出 typed abnormality/seriousness clue；不复制 AE/MH 风险或 Query |
| CM 禁限用/适应证/处置 | D02 | 消费 accepted CM ref，输出检查—用药一致性证据给 D08 |
| IP 暂停/减量/停药及暴露 | D03 | 消费 accepted IP action/exposure ref；不重新判 PD |
| 方案阈值/处置要求是否执行、潜在 PD | D04 | D07 评价医学检查链；方案执行问题只形成 D04 handoff |
| 访视/检查是否到期、缺失或超窗 | D05 | 消费 occurrence/timing/assignment；不重复缺失/超窗风险 |
| 检查作为疗效终点的计分/反应 | D06 | D07 只拥有安全性解释；疗效算法由 D06 |
| 跨域因果/一致性关系 | D08 | D07 只产 typed link clue，不自行建立因果关系 |
| 中心/项目聚合 | D09/D10 | 仅提供稳定受试者结果与 coverage inputs |

Owner routing 必须先于 expected-set。一个问题只能有一个 risk/query owner；其他域使用 `producer_ref + consumption_binding`。

### 3.1 Typed owner gate

```text
D07OwnerRoutingDecision:
  decision_id/scope_binding_id/subject_ref/episode_key
  candidate_problem_kind/producer_domain/producer_object_refs
  owner_domain=D01|D02|D03|D04|D07|D08
  d07_action=evaluate_and_own|handoff_only|context_only|not_applicable
  risk_owner/query_owner/handoff_target_domain?
  decision_rule_id/decision_rule_version/reason_codes
  source_locator_ids/hash

D07ProducerConsumptionBinding:
  binding_id/scope_binding_id/producer_domain/producer_object_type
  producer_object_id/producer_content_hash/producer_version
  consumer_domain=D07/consumer_unit_id?/consumption_purpose
  permitted_outputs=evidence_only|handoff_only|risk_and_query
  source_locator_ids/lineage_hash

D07Handoff:
  handoff_id/from_unit_id/target_domain/target_problem_kind
  evidence_refs/reason_codes/query_creation_permitted=false
  risk_creation_permitted=false/grade_comparison_assessment_id?
  clinical_significance_assessment_id?/seriousness_clue_state
  priority_decision_id?/producer_content_hash/source_locator_ids/hash
```

Owner gate 不是建议。`risk_owner != D07` 或 `query_owner != D07` 时，D07 只能产生 handoff/context，不得建立风险或 Query。D01/D04 回传的最终风险也不得复制回 D07。

## 4. 正交语义

每项观察同时但独立保存：

- `reference_range_state=low|within_range|high|not_classifiable`；
- `grade_state=graded|not_graded|not_applicable|not_evaluable` 与 `grade`；
- `clinical_significance=CS|NCS|unknown|not_collected`；
- `seriousness_clue=present|absent|unknown`，不是正式 SAE 判定；
- `monitoring_priority=low|medium|high|unknown`。

任何一个维度不得推导或覆盖另一个。`NCS` 不能自动清除持续加重、项目阈值、缺处置或跨域矛盾；高等级不自动等于 serious；监察优先级不显示成 CTCAE grade。

## 5. 领域对象与内容寻址

所有对象 immutable、内容寻址、带 scope/cutoff/source locators；修改产生新版本和 lineage。

```text
D07RunScopeBinding:
  scope_binding_id/project_ref/run_ref/monitoring_mode
  source_revision/accepted_snapshot_ref/snapshot_as_of/clinical_event_cutoff
  protocol_version/ib_rsi_version/lab_manual_version/mapping_version
  unit_dictionary_version/rule_set_versions/source_locator_ids/lineage_hash

D07RecordScopeEnvelope:
  envelope_id/project_ref/run_ref/monitoring_mode/scope_type/scope_key
  subject_ref/site_ref/domain_id
  episode_key/source_revision/accepted_snapshot_ref/scope_binding_id
  observed_time_ref/cutoff/source_locator_ids/record_id/record_content_hash
  record_status=accepted_current|superseded|withdrawn|pending|out_of_cutoff
  prior_record_id?/supersedes_record_id?/correction_reason?
  authority_binding_id/lineage_hash

D07RecordScopeDecision:
  decision_id/envelope_id/scope_binding_id
  project_equal/run_equal/mode_equal/scope_equal/subject_equal/site_equal
  snapshot_equal/source_revision_equal/domain_equal/episode_equal
  cutoff_relation=before|at|after|overlaps|precision_insufficient
  cutoff_decision_id
  decision=in_scope|out_of_cutoff|boundary|not_evaluable
  reason_codes/source_locator_ids/hash

D07CutoffDecision:
  cutoff_decision_id/record_time_ref_id/run_cutoff_time_ref_id
  d05_cutoff_policy_id/d05_cutoff_policy_version/d05_cutoff_policy_hash
  normalized_record_interval/normalized_cutoff_instant
  comparison=before|at|after|overlaps|precision_insufficient
  admitted/decision=within_cutoff|out_of_cutoff|boundary|not_evaluable
  reason_codes/source_locator_ids/hash

D07TimeRef:
  time_ref_id/value/precision=datetime|date|month|year|unknown
  timezone?/timezone_state=provided|required_missing|not_applicable
  interval_start?/interval_end?/source_locator_ids/hash

D07AuthorityBinding:
  authority_binding_id/claim_kind
  selected_authority_id/selected_version/effective_interval
  candidate_authority_ids/decision_status=unique|boundary|not_evaluable
  scope_predicate_results/source_locator_ids/hash

D07CorrectionChainDecision:
  decision_id/stable_source_record_id/candidate_record_ids
  accepted_current_record_id?/branch_state=linear|forked|broken|ambiguous
  supersession_edges/cutoff_decision/source_locator_ids/hash

SafetyMeasureDefinition:
  definition_id/stable_measure_key/version/domain=LB|VS|EG|PE|IMAGING|OTHER
  audience_name/result_kind=numeric|ordinal|categorical|text|interval
  specimen_kind?/method_kind?/body_site_kind?/lead_kind?/position_kind?
  fasting_state_kind?/reader_role_kind?/laterality_kind?
  expected_unit_dimension?/allowed_result_kinds
  applicability_rule_id/source_locator_ids/definition_hash

ReferenceRangeDefinition:
  range_definition_id/stable_measure_key/version
  range_kind=lower_only|upper_only|closed_interval|categorical
  lower?/upper?/lower_inclusive?/upper_inclusive?/allowed_categories?/unit?
  sex=male|female|intersex|unknown|not_applicable
  age_interval?/pregnancy_state?/fasting_state?/method_kind?
  specimen_kind?/body_site_kind?/position_kind?/lab_or_site?
  effective_interval/source_locator_ids/hash

UnitConversionRule:
  conversion_rule_id/version/from_unit/to_unit/dimension
  formula=factor|affine/multiplier/addend?/numeric_policy_id
  applicability/source_locator_ids/hash

SafetyGradeRuleSet:
  rule_set_id/name/version/kind=CTCAE|protocol|ib|project
  stable_measure_key?/term_code?/ordered_grade_rule_ids
  grade_domain/endpoint_inclusivity/missing_input_outcome
  source_locator_ids/hash

SafetyMonitoringRule:
  rule_id/version/rule_kind=repeat|action|organ_pattern|clinical_significance
  applicable_measure_keys/temporal_window/exposure_context?
  ordered_predicate_ids/required_followup_roles/priority_floor?/owner_route
  source_locator_ids/hash

ObservedSafetyResult:
  result_id/stable_source_record_id/subject_ref/site_ref
  stable_measure_key/domain/raw_value/numeric_value?/character_value?
  original_unit?/reported_range_low?/reported_range_high?/reported_abnormal_flag?
  reported_cs_ncs?/reported_grade?/collection_or_exam_time
  visit_ref?/specimen_quality=acceptable|hemolysed|contaminated|clotted|
      insufficient|unknown|not_applicable
  method_kind?/body_site_kind?/lead_kind?/position_kind?/fasting_state_kind?
  lab_or_reader?/reader_role_kind?/laterality_kind?/correction_status
  scope_envelope_id/source_locator_ids/record_status/accepted_snapshot_ref/lineage_hash

SafetyContextBindingDecision:
  decision_id/result_id/scope_binding_id
  candidate_measure_definition_ids/selected_measure_definition_id?
  candidate_range_definition_ids/selected_range_definition_id?
  candidate_conversion_rule_ids/selected_conversion_rule_id?
  candidate_grade_rule_set_ids/selected_grade_rule_set_id?
  selected_monitoring_rule_ids/decision_status
  predicate_results/rejected_candidates/source_locator_ids/hash

SafetyGradeRule:
  grade_rule_id/sequence/grade
  comparator=lt|le|eq|ge|gt|between|outside|categorical_equals
  left_operand=value|ratio_to_uln|ratio_to_lln|change_from_baseline|category
  lower?/upper?/lower_inclusive?/upper_inclusive?/categorical_value?
  required_context_fields/source_locator_ids/hash

SafetyMonitoringPredicate:
  predicate_id/sequence/left_operand
  comparator=lt|le|eq|ne|ge|gt|between|outside|in_enum|not_in_enum|
      exists|absent|before|after|overlaps|within_window|same_interval
  right_typed_value?/right_ref_id?/temporal_relation?
  missing_outcome=not_evaluable|boundary|no_match
  source_locator_ids/hash

D07BaselineRule:
  rule_id/version/candidate_window/allowed_record_statuses
  ordering_fields/tie_break_fields/minimum_required_candidates
  no_candidate_outcome=not_evaluable|not_applicable
  tie_outcome=boundary|not_evaluable/source_locator_ids/hash

D07TrendRule:
  rule_id/version/minimum_comparable_points/confirmation_point_count
  confirmation_window/recovery_window/recurrent_gap_window
  required_same_context_fields
  missing_point_policy=break_series|boundary|not_evaluable
  source_locator_ids/hash

NormalizedSafetyResult:
  normalized_result_id/result_id/stable_measure_key
  normalized_value?/normalized_unit?/range_low?/range_high?
  range_state/range_ratio_to_uln_or_lln?/normalization_status
  definition_binding_id/source_locator_ids/content_hash

D07BaselineSelectionDecision:
  decision_id/stable_measure_key/subject_ref/scope_binding_id
  candidate_result_ids/selected_result_id?/selection_rule_id
  selected_time_ref?/decision_status=selected|tie|no_candidate|not_applicable|
      not_evaluable/rejected_reasons
  d05_binding_ref_ids/source_locator_ids/hash

SafetyGradeAssessment:
  assessment_id/normalized_result_id/rule_set_id/rule_set_version
  matched_rule_id?/grade?/grade_state/endpoint_equality_state
  input_refs/source_locator_ids/hash

SafetyGradeComparisonAssessment:
  assessment_id/result_id/reported_grade?/recomputed_grade?
  comparison_state=match|mismatch|reported_only|recomputed_only|
      both_not_applicable|not_evaluable
  rule_set_id/rule_set_version/source_locator_ids/hash

ClinicalSignificanceAssessment:
  assessment_id/result_id/reported_token?
  controlled_value=CS|NCS|unknown|not_collected|unmapped
  vocabulary_id/version/mapping_rule_id?/reason_ref_ids
  consistency_state=consistent|inconsistent|boundary|not_evaluable
  source_locator_ids/hash

SafetyTrendAssessment:
  assessment_id/stable_measure_key/baseline_decision_id/trend_rule_id
  ordered_normalized_result_ids
  trend_kind=new_abnormality|baseline_abnormal_worsening|persistent|
      recurrent|recovered|stable_abnormal|stable_normal|fluctuating|
      insufficient_points|boundary|not_evaluable
  new_abnormality/baseline_abnormal_worsening/persistent/recurrent/recovered
  magnitude_change?/grade_change?/analysis_window
  source_locator_ids/hash

SafetyFollowupAssessment:
  assessment_id/trigger_result_ids/monitoring_rule_ids
  expected_followup_roles/observed_followup_refs
  repeat_state/action_state/explanation_state/ae_record_state
  temporal_match_state/source_locator_ids/hash

D07ActionObligationDefinition:
  obligation_definition_id/version/obligation_kind=repeat|clinical_review|
      treatment_action|ae_assessment|protocol_execution_check
  trigger_rule_id/required_action_role/temporal_window
  owner_domain/query_owner/merge_key_fields/source_locator_ids/hash

D07ActionObligationBinding:
  obligation_binding_id/obligation_definition_id/trigger_result_ids
  subject_ref/site_ref/episode_key/scope_binding_id
  required_action_role/temporal_window/owner_routing_decision_id
  stable_obligation_core_hash/source_locator_ids/hash

SafetyOrganPatternComponentBinding:
  binding_id/pattern_rule_id/component_role/stable_measure_key
  candidate_result_ids/selected_result_id?/selection_state
  temporal_relation_to_anchor/lineage_state/source_locator_ids/hash

SafetyOrganPatternAssessment:
  assessment_id/pattern_rule_id/pattern_rule_version
  project_ref/run_ref/monitoring_mode/scope_type/scope_key
  subject_ref/site_ref/accepted_snapshot_ref/source_revision/cutoff/episode_key
  required_component_roles/component_binding_ids/missing_component_roles
  temporal_window/temporal_cooccurrence_state=matched|outside_window|
      precision_insufficient|conflicted|not_evaluable
  exposure_context_binding_ids/alternative_explanation_refs
  pattern_state=matched|not_matched|boundary|not_evaluable
  seriousness_clue_state/owner_routing_decision_id/source_locator_ids/hash

SafetyExaminationContextAssessment:
  assessment_id/result_id/domain=VS|EG|PE|IMAGING|OTHER
  required_context_roles/observed_context_bindings/missing_context_roles
  ecg_correction_formula?/ecg_lead_set?/repeat_series_ref?
  vital_sign_position?/device_or_method_ref?
  physical_exam_body_site?/laterality?
  imaging_reader_role?/central_local_review_state?/adjudication_ref?
  interpretation_state=consistent|inconsistent|boundary|not_evaluable
  owner_routing_decision_id/source_locator_ids/hash

SafetyExaminationRequirementSet:
  requirement_set_id/version/domain
  required_context_roles/conditional_requirement_predicates
  allowed_interpretation_states/source_locator_ids/hash

D07EvaluationUnit:
  unit_id/unit_kind=observation_interpretation|followup_obligation|organ_pattern
  project_ref/run_ref/monitoring_mode/scope_type/scope_key/domain_id
  subject_ref/site_ref/accepted_snapshot_ref/source_revision/cutoff
  episode_key/temporal_window
  unit_algorithm_version/stable_source_event_keys
  stable_measure_key_or_pattern_key/record_scope_decision_ids
  definition_binding_id?/result_ids/baseline_decision_id?
  grade_assessment_ids/trend_assessment_id?/followup_assessment_id?
  organ_pattern_assessment_id?/examination_context_assessment_id?
  action_obligation_binding_id?
  cross_domain_consumption_binding_ids/source_locator_ids/hash

D07UnitResult:
  unit_id/project_ref/run_ref/monitoring_mode/scope_type/scope_key/domain_id
  subject_ref/site_ref/accepted_snapshot_ref/source_revision/cutoff/episode_key
  eval_disposition/positive_subtype?/monitoring_priority
  supporting_evidence_refs/counterevidence_refs/context_refs
  risk_candidate_ref?/query_draft_ref?/downstream_handoff_refs
  grade_comparison_assessment_id?/clinical_significance_assessment_id?
  seriousness_clue_state/priority_decision_id?/owner_routing_decision_id
  source_locator_ids/content_hash
```

所有 schema 为 exact-key typed schema；未知 key、缺必需 key、枚举外值、错误对象类型或嵌入 hash 不匹配均在医学求值前 fail-closed。哈希统一为 `sha256(canonical_json(all typed fields except own hash))`；canonical JSON 固定 UTF-8、对象 key 排序、数组保序、Decimal 字符串、禁止 NaN/Infinity、禁止隐式时区/浮点转换。

`precision=datetime` 必须 `timezone_state=provided` 且 timezone 为 IANA zone 或明确 UTC offset；date/month/year 只能 `timezone_state=not_applicable`，unknown 必须无 value/interval。区间端点必须使用同一 precision/timezone 且 start≤end。cutoff 不在 D07 另造语义，必须唯一绑定 D05 已接受的 cutoff policy/version/hash：datetime 先按 policy 归一为 UTC，end≤cutoff 为 within，start>cutoff 为 out，start≤cutoff<end 为 overlaps；date/month/year 先按 D05 policy 展开闭区间再应用同一真值表；unknown 或无法唯一归一为 precision_insufficient。`before|at` admitted=true/within，`after` admitted=false/out，`overlaps|precision_insufficient` admitted=false 且分别 boundary/not_evaluable。`accepted_current` 必须来自唯一 `D07CorrectionChainDecision`；fork/broken/ambiguous、wrong project/run/mode/scope/site/subject/domain/episode/snapshot/source_revision/cutoff、pending/out-of-cutoff/superseded 不得进入医学结果。每个输入先产生 `D07CutoffDecision` 与 `D07RecordScopeDecision`；仅 `in_scope` 可进入确定性医学求值，`boundary/not_evaluable` 只产生控制面缺口，`out_of_cutoff` 仅供下一 Run 比较。

条件 schema 固定如下：

- `ReferenceRangeDefinition`：lower_only 只允许 lower+lower_inclusive；upper_only 只允许 upper+upper_inclusive；closed_interval 必须 lower/upper 及两个 inclusivity 且 lower≤upper；categorical 必须非空 allowed_categories 且不得有数值边界。numeric 范围必须有 unit；categorical 不得有 unit conversion。
- `UnitConversionRule`：factor 必须 multiplier 且不得 addend；affine 必须 multiplier+addend；from/to dimension 必须相同，multiplier 不得为 0。所有参数为 Decimal string。
- `SafetyGradeRule`：lt/le/eq/ge/gt 只允许单一标量；between/outside 必须 lower/upper 且 lower≤upper；categorical_equals 只允许 categorical_value。operand 所需 context 必须与 required_context_fields 完全一致。
- `SafetyMonitoringPredicate`：exists/absent 不得有 right operand；between/outside 必须 typed lower+upper；其他 comparator 必须 right_typed_value 与 right_ref_id 恰有一个。仅 before/after/overlaps/within_window/same_interval 可有同名 temporal_relation，其他 comparator 禁止该字段。lt/le/eq/ne/ge/gt 用 Decimal 或同类型 ordinal；in_enum/not_in_enum 用非空同枚举集合，类型不一致为 not_evaluable。
- baseline 必须使用唯一 `D07BaselineRule`；无候选/并列分别严格执行规则 outcome。trend 必须使用唯一 `D07TrendRule`：少于 minimum comparable points=`insufficient_points`；break_series 在缺点处分段且各段独立满足最少点数，boundary/not_evaluable 直接给同名 trend kind；正常→异常=`new_abnormality`，异常基线进一步越过冻结 magnitude/grade rule=`baseline_abnormal_worsening`，连续确认异常=`persistent`，恢复后在 recurrent gap 内再异常=`recurrent`，异常后满足确认点数正常=`recovered`，全异常但无恶化=`stable_abnormal`，全正常=`stable_normal`，其余可比升降交替=`fluctuating`。阈值仍来自项目规则，不写入通用内核。
- `SafetyOrganPatternComponentBinding` 的 component role 在一个 pattern rule 内唯一；每个 component 必须有线性 accepted-current lineage、同 subject/site/scope/episode 和明确 anchor temporal relation。
- 每项检查必须唯一绑定 `SafetyExaminationRequirementSet`；条件 predicate 命中的 required context 缺失时为 `not_evaluable`，多个冲突上下文为 `boundary`。不得由实现自行决定 ECG/VS/PE/IMAGING 所需字段。

### 5.1 稳定身份

```text
unit stable core = project + site + subject + domain + scope_type/scope_key
                 + unit_kind + unit_algorithm_version
                 + stable_source_event_identity + stable_measure_or_pattern_key
                 + specimen/method/body-site/lead/position role
                 + clinical episode + protocol-defined temporal window + rule lineage
risk stable core = unit stable core + positive_subtype + normalized concept
```

`stable_source_event_identity` 由来源系统稳定记录键加 accepted correction root 组成，不含可变行号；没有稳定键时使用内容寻址的 source-locator tuple 并标记不可跨 Run 自动迁移。原值、等级、风险级别、模型措辞、Query、当前 locator 和本次 Run ID 不进入稳定核心。Run 不进入 identity，但所有 unit/result/binding/organ-pattern assessment 消费前必须验证 project/run/mode/scope/site/subject/domain/episode/snapshot/source_revision/cutoff 全等；身份所需字段缺失/冲突时 fail-closed，不生成可迁移风险身份。

D07 的 `scope_type` 固定为 `subject`，`scope_key=sha256(project_ref + site_ref + subject_ref)`；其他 scope_type 不进入 D07。`D07EvaluationUnit` 条件键固定：observation 必须 definition/result/baseline/grade/trend refs，禁止 obligation/pattern ref；followup 必须 action obligation + followup assessment，禁止 pattern ref；organ_pattern 必须 organ pattern assessment，禁止 action obligation。检查类 observation 在适用域必须带 examination context assessment。`D07UnitResult` 的 scope tuple 必须与 unit 逐字段全等，否则 integrity fail-closed。

## 6. 适用性与 expected-set

顺序固定：

1. 冻结 scope/cutoff/source revisions；
2. 解析项目是否收集该安全域及选择性收集范围；
3. 唯一绑定 measure/range/unit/grade/monitoring 规则；
4. 消费 D05 已接受的到期/活动/采样绑定；
5. 从计划要求与 accepted 实际记录双向生成 expected units；
6. 冻结 ordered expected-set 与 hash；
7. 每个 unit 恰有一个 L1 disposition；
8. 最后才生成 risk/priority/Query/Journey。

未计划且无实际记录只有在“项目明确不收集/明确选择性排除”的适用性 authority 可定位时才为 `not_applicable`；仅为空表、缺域、缺 mapping 或未运行均为 L0 gap，不得生成 L1 `not_applicable`。已计划但缺记录由 D05 owner；D07 对已有结果缺关键解释可 `not_evaluable`。选择性收集必须有版本化项目依据，不能从空表推断。

### 6.1 Coverage ledger 与 D05 gate

```text
D07ApplicabilityEvidence:
  applicability_evidence_id/scope_binding_id/unit_candidate_key
  authority_binding_id/applicability_rule_id
  applicability=applicable|not_applicable|boundary|not_evaluable
  predicate_results/control_plane_no_match
  source_locator_ids/hash

D07GateBlockedObservation:
  blocked_observation_id/source_record_id/d05_gate_binding_id
  project_ref/run_ref/subject_ref/site_ref/scope_binding_id
  blocked_stage=expected_set_expansion|evaluation_admission|
      obligation_assessment|pattern_assessment
  control_plane_state=boundary|not_evaluable
  reason_codes/source_locator_ids/hash

D07CoverageLedger:
  ledger_id/scope_binding_id/domain=D07
  required_source_roles/provided_source_roles
  role_status_by_name: CoverageUnitStatus
  expected_unit_ids/expected_set_hash
  evaluated_unit_ids/missing_unit_ids/unexpected_unit_ids/duplicate_unit_ids
  disposition_counts/applicability_evidence_ids
  d05_gate_binding_ids/open_gate_ids
  source_locator_coverage/mapping_coverage/authority_coverage
  ledger_hash

D07DomainCompletionDecision:
  decision_id/ledger_id
  l0_complete/expected_set_reconciled/all_units_disposed
  not_evaluable_count/open_d05_gate_count/unresolved_identity_count
  join_invariants_passed/qc_passed
  domain_complete/reason_codes/hash
```

复用 R1 `CoverageUnitStatus` 与 R4 L0 语义。对有序集合按 stable unit ID 精确求值：`missing=expected−evaluated`、`unexpected=evaluated−expected`、`duplicate=count(id)>1`；`expected_set_reconciled=true` 当且仅当三者均为空且 expected/evaluated 一一对应。`all_units_disposed=true` 当且仅当每个 expected unit 恰有一个闭合 disposition；`l0_complete` 要求所有 required roles 为 satisfied/not_applicable-with-authority，且无 open D05 gate、scope/identity/authority gap；`domain_complete` 当且仅当 `l0_complete && expected_set_reconciled && all_units_disposed && not_evaluable_count=0 && open_d05_gate_count=0 && unresolved_identity_count=0 && join_invariants_passed && qc_passed`。

D05 open gate 的行为矩阵固定如下：

| D07 unit kind | 允许行为 | 禁止行为 |
|---|---|---|
| observation_interpretation 且已有 accepted actual record | 可保留原值并输出 `D07GateBlockedObservation` 供查看 | 不得生成 D07EvaluationUnit/L1 disposition、risk、Query、priority 或 lifecycle transition |
| planned observation 尚无 accepted actual record | 仅 D05 handoff/context | 不得扩展 D07 expected medical unit，不得声明 not_applicable/negative |
| followup_obligation | 仅保留未闭合 obligation binding 与 D05 handoff | 不得评价 missing/met，不得 risk/Query |
| organ_pattern | 仅保留已验证 components；pattern 为 not_evaluable | 不得命中 pattern、risk/Query |

`D07ApplicabilityEvidence` 是 L1 `not_applicable` 的唯一入口；`control_plane_no_match=true`、空表、未映射或未运行永远不是 L1 not_applicable。open gate 不阻断其他无关联 unit 的查看，但阻断对应 unit 的候选、risk、Query、priority 与域完整声明。

## 7. 确定性求值

### 7.1 单位、范围与边界

- 原值永远保留；只有唯一、维度一致且版本适用的转换规则可生成 normalized value。
- 范围按检查时年龄/性别/方法/中心或实验室/空腹等语境唯一选择；多个可行范围为 `boundary`，缺关键范围为 `not_evaluable`。
- 等于 ULN/LLN 或等级端点按规则的 inclusivity 求值，并显式记录 `endpoint_equality_state`。
- 单位或范围在纵向中改变时，比较前逐次归一；无法归一不得画连续趋势。
- numeric 求值只接受 Decimal policy；字符、ordinal、interval 与 numeric 走不同闭合 evaluator，禁止自动类型转换。

### 7.2 基线与趋势

- 基线选择复用 D05 typed 时间/活动 authority，并由版本化规则决定；不得默认“第一行”“最近一条”或“最正常值”。
- 区分：基线正常后异常、基线异常后进一步升/降级、持续、复发、恢复、波动和证据不足。
- 单点异常不能自动称趋势；趋势规则冻结最少点数、确认/复测窗与可比较性。

### 7.3 分级

- 只有项目绑定且 measure/term 可映射的版本化 RuleSet 可分级。
- CTCAE v5/v6 或其他版本不可混用；原报告 grade 与重算 grade 分别保留并比较。
- 没有适用分级规则可为 `not_graded/not_applicable`，不等于 `not_evaluable`；只有规则应适用但版本/映射/输入缺失时才 `not_evaluable`。

### 7.4 CS/NCS、复测与处置

- CS/NCS 先做受控枚举/词汇映射；禁止用中文/英文子串（如在 NCS 中命中 CS）。
- NCS 是一条可反证来源，不是自动阴性；理由、复测、趋势、方案/IB 阈值和实际处置需形成一致链。
- 复测必须按 measure、方法/样本、时间窗和身份匹配；任意后续正常值不能自动解释更早异常。
- action/repeat/explanation/AE-record 四个状态分别保存；缺一项只影响相应判断。

`SafetyFollowupAssessment` 的状态闭合为：

```text
repeat_state=not_required|required_met|required_missing|wrong_window|
             wrong_measure_or_method|not_evaluable
action_state=not_required|required_met|required_missing|discordant|not_evaluable
explanation_state=not_required|documented_consistent|documented_inconsistent|
                  missing|not_evaluable
ae_record_state=not_expected|matching_record_present|handoff_required|
                ambiguous|not_evaluable
temporal_match_state=matched|outside_window|precision_insufficient|conflicted
```

### 7.5 器官组合模式

- DILI、QT、电解质—心电、血象—感染/出血等组合只由版本化项目/知识 RuleSet 产生 `pattern clue`。
- clue 保留每个组成指标、同时窗、暴露/替代原因和缺失项；不得自动诊断或正式归因。
- 相邻域关系只通过 typed refs 输出给 D01/D08；D07 不因同日或文本相似建立因果。

`SafetyOrganPatternAssessment` 必须逐项物化 required/observed/missing components、同时窗、暴露语境与替代解释；组成不全或时间精度不足只能为 `boundary/not_evaluable`，不得命中模式。`SafetyExaminationContextAssessment` 必须按域验证心电校正公式与导联/重复序列、生命体征体位与方法、体检部位与侧别、影像读片角色与复核/裁决；缺关键上下文不得用通用文本补齐。

## 8. L0/L1/L1b/L2/L3

### 8.1 五类 L1 disposition

- `positive`：必需 authority 完整，且命中一个明确 subtype；
- `negative`：分母、范围、单位、基线、适用规则及所有必需反证链完成，未命中问题；
- `boundary`：端点相等、多个可行范围/基线、部分日期、样本/方法或临床判断边界；
- `not_evaluable`：缺必需单位/范围/版本/映射/时间/身份/CS 说明或关键关联；
- `not_applicable`：项目不收集/规则不适用且依据可定位。

### 8.2 positive subtype

1. `new_abnormality` — 新发异常；
2. `baseline_abnormal_worsening` — 基线异常进一步恶化；
3. `grade_or_magnitude_worsening` — 等级/幅度恶化；
4. `persistent_or_recurrent_abnormality` — 持续或复发；
5. `clinical_significance_inconsistency` — 数据链与 CS/NCS/说明矛盾；
6. `missing_repeat_or_followup` — 项目规则要求的复测/随访缺失；
7. `medical_action_inconsistency` — 异常与 CM/IP/停药/处置记录不一致；
8. `ae_recording_handoff_clue` — 可能需 D01 核查 AE 记录，仅 handoff、D07 不另建 AE 风险；
9. `protocol_or_ib_action_gap` — 命中项目阈值但缺规定动作，方案执行 owner 为 D04；
10. `organ_pattern_clue` — 版本化组合规则命中但尚未正式裁决；
11. `exam_interpretation_inconsistency` — 心电/体检/影像原结论、复核或临床动作矛盾；
12. `source_or_correction_inconsistency` — 原值/更正/读片/中心与本地结果 lineage 冲突。

同一 `unit_kind` unit 只选择一个 primary subtype；不同医学动作不得被压成同一 unit。异常解释属于 `observation_interpretation`，规定复测/处置缺口属于 `followup_obligation`，器官组合属于 `organ_pattern`。每个 followup unit 必须恰有一个 `D07ActionObligationBinding`，其 stable obligation core 为 `project+site+subject+episode+obligation_definition_id/version+trigger stable identities+required_action_role+temporal_window+owner_domain`。三者可共享来源但拥有不同稳定 unit/risk identity；owner gate 后每个 obligation 最多一个 risk/query。merge 仅限 unit stable core 与 stable obligation core 均完全相同；任一 obligation kind、action role、trigger、owner 或窗口不同必须 split，并保留 lineage 和 shared-evidence ref。重复 stable obligation core 在 pre-evaluator integrity 阶段 fail-closed。

### 8.3 L1b 与计数

支持、排除、背景证据可多选但必须 typed、可定位。可靠复测恢复、明确且一致的 NCS 理由、长期稳定基线、样本质量问题、方案允许变化可作为 counterevidence；不能删除原异常历史。

L2 分别计数 source records、evaluation units、risk candidates、risk instances、Query drafts 和 handoffs；不得互相替代。L3 生命周期复用 R2，D07 不复制状态机。

## 9. 监察优先级

按冻结 precedence 求值，未知输入保持 `unknown`：

1. 项目定义的受试者权益/安全关键阈值、潜在严重事件组合或需即时处置缺口 → `high`；
2. 等级/幅度快速恶化、持续异常、关键复测/处置缺失、重要 CS/NCS/AE/IP 矛盾 → 至少 `medium`，项目规则可提升；
3. 轻度孤立异常且复测恢复、解释链完整 → `low` 或 negative；
4. 关键 authority 缺失 → `unknown`，不得降为 low。

高优先级、严重性/AESI clue、身份冲突和低置信度不得机器自动关闭，也不得被多数票隐藏。

```text
D07PriorityPolicy:
  policy_id/version/ordered_precedence_rule_ids
  high_priority_clinical_flag_rules/machine_close_forbidden_rules
  source_locator_ids/policy_hash

D07PriorityResolverInput:
  resolver_input_id/unit_id/unit_kind/eval_disposition/positive_subtype?
  grade_state/grade?/grade_change?/magnitude_state?/persistence_state?
  seriousness_clue_state/clinical_significance_consistency?
  repeat_state?/action_state?/evidence_state/identity_state
  matched_project_rule_ids/source_locator_ids/hash

D07PriorityDecision:
  decision_id/unit_id/policy_id/policy_version/resolver_input_hash
  matched_precedence_rule_id/monitoring_priority/reason_codes
  machine_close_forbidden/source_locator_ids/lineage_hash
```

priority 必须由 policy + resolver input 唯一求值。pre-medical integrity failure 不得产生 priority decision、risk identity、Query 或 Journey risk marker。

## 10. 三段式 Query

```text
D07QueryDraft:
  query_draft_id/unit_id/risk_id?/owner_routing_decision_id
  query_owner=D07/basis_sentence/finding_sentence/action_sentence
  protocol_execution_context_ref?/d04_enrollment_or_pd_context_ref?
  evidence_refs/source_locator_ids/audience_payload_hash/content_hash

D07PDWordingPermissionDecision:
  decision_id/query_draft_id/d04_context_ref
  d04_decision_kind=protocol_deviation_candidate|eligibility_context|
      protocol_action_context
  context_scope_equal/context_accepted/content_hash_equal
  pd_wording_permitted/reason_codes/source_locator_ids/hash
```

每条仅含依据＋发现＋行动项，并引用来源：

- 依据：`方案要求 ALT 达到项目阈值后在规定时间内复测并评估临床意义；`
- 发现：`受试者 S-001 于研究第 29 天 ALT 由基线正常升高至 3.2×ULN，当前未定位到规定时间窗内复测或 AE 评估记录；`
- 行动项：`请核实该异常的临床意义、复测与 AE 判断，并补充或更正相关记录。`

不得写“系统判定 DILI/SAE/与研究药物相关”。潜在 PD 只在 accepted D04 方案执行或入排语境 ref 存在时写“请核实是否涉及 PD”；缺该 typed ref 时只能描述检查/处置不一致，不得自行加入 PD 措辞。Query 可查看、编辑、导出，不发送、不跟踪外部回复。

## 11. Patient Journey 检验与检查轨道

投影必须共享 Subject Temporal Spine/访视轴，并提供：

- 独立轨道/子轨道：实验室、生命体征、心电、体检、影像/其他检查；
- 点/区间标记包含域短标签、指标名、原值/单位、范围状态、grade（如适用）、CS/NCS、风险级别和 source jump；
- 趋势线仅连接可比、单位已验证的同一稳定指标；范围或方法变化显示断点；
- 风险锚定具体结果/区间/访视，支持跳到 AE/CM/IP/处置 ref，但不复制相邻事件；
- 中高风险优先显示，低风险折叠；不能用一个“已记录事项/通用风险点”代替临床域和类型；
- 部分日期、时间冲突、未分配访视进入待定区；筛选/缩放不改变风险身份或生命周期。

投影对象必须内容寻址且 source locators 完整；renderer 只消费 validated projection，不拥有医学状态。

```text
D07SharedSpineBinding:
  binding_id/scope_binding_id/project_ref/run_ref/monitoring_mode
  scope_type/scope_key/subject_ref/site_ref/accepted_snapshot_ref
  source_revision/episode_key
  d05_projection_id/spine_binding_id/axis_version/axis_hash/cutoff
  scope_equality_decision_id/source_locator_ids/hash

D07SharedSpineScopeEqualityDecision:
  decision_id/binding_id/d05_projection_id
  project_equal/run_equal/mode_equal/scope_type_equal/scope_key_equal
  subject_equal/site_equal/snapshot_equal/source_revision_equal
  episode_equal/cutoff_equal/axis_hash_valid
  all_equal/reason_codes/hash

D07JourneyEventMarker:
  marker_id/domain/event_kind=lab|vital_sign|ecg|physical_exam|imaging|other_exam
  stable_measure_key/event_time_ref/visit_or_pending_ref
  result_id/audience_label/value_label?/range_label?/grade_label?/cs_ncs_label?
  seriousness_clue_label?
  source_jump_ids/payload_hash

D07JourneyRiskMarker:
  marker_id/risk_id/unit_id/positive_subtype/monitoring_priority
  seriousness_clue_state/grade_comparison_assessment_id?
  clinical_significance_assessment_id?/priority_decision_id
  anchor_kind=result|interval|visit|pending_time/anchor_ref
  clinical_domain_label/risk_type_label/summary_label
  source_jump_ids/query_draft_ref?/payload_hash

D07SourceJump:
  jump_id/target_kind=listing_cell|listing_row|protocol_clause|ib_clause|
      lab_manual_rule|ae_record|cm_record|ip_action|visit|examination_report
  cardinality=one|many/target_ref?/ordered_target_refs?
  join_reason=direct_source|rule_authority|producer_binding|shared_identity|
      temporal_context
  temporal_relation_ref?/reverse_binding_ref
  hash


D07SourceJumpTargetRef:
  target_ref_id/target_object_id/target_schema_id/target_scope_binding_id
  target_content_hash/source_locator_ids/hash

D07SubjectJourneyProjection:
  projection_id/scope_binding_id/subject_ref/shared_spine_binding_id
  ordered_event_marker_ids/ordered_risk_marker_ids/source_jump_ids
  projection_hash

D07AudienceLexicon:
  lexicon_id/version/allowed_domain_labels/allowed_risk_type_labels
  forbidden_internal_tokens/required_sentence_patterns/content_hash

D07AudiencePayloadValidationResult:
  validation_id/payload_kind=query|event_marker|risk_marker|projection
  payload_object_id/payload_hash/lexicon_id/lexicon_version/lexicon_hash
  schema_valid/no_internal_tokens/domain_specific/risk_specific
  source_jump_valid/visible_path_valid/scope_equal
  validation_passed/reason_codes/hash

D07SourceJumpValidationResult:
  validation_id/jump_id/source_object_id/source_scope_binding_id
  target_schema_valid/target_hash_valid/scope_equal/cardinality_valid
  join_reason_valid/reverse_binding_valid/temporal_relation_valid
  validation_passed/reason_codes/hash
```

Query、event marker、risk marker 与 projection 各有闭合 exact-key audience schema；可选字段仅按对应 payload kind 的条件矩阵出现，缺必需 label/ref 或出现额外字段均失败。Shared spine 必须产生唯一 `D07SharedSpineScopeEqualityDecision`，其十二项 equality/hash 均为 true 才可投影。序列化器在输出前重算 projection、marker、jump/target-ref hash；每个 jump 必须恰有一个 reverse binding，`cardinality=one` 时必须恰有 target_ref 且禁止 ordered_target_refs，`many` 时必须恰有非空、无重复、保序的 ordered_target_refs 且禁止 target_ref；每个 target ref 逐一验 schema/scope/hash/locator。`temporal_context` 必须携带 typed `temporal_relation_ref`，其他 join reason 禁止该字段。每个 audience payload 必须产生 `D07AudiencePayloadValidationResult`，每个 jump 必须产生 `D07SourceJumpValidationResult`，两者通过才可见。

条件矩阵固定：Query 必须恰有依据/发现/行动项三句，只有 permission=true 才允许 PD token；event marker 必须 audience/domain/measure label，numeric/ordinal/categorical 结果必须 value label，grade/CS-NCS/seriousness 仅在对应 assessment 存在时出现；risk marker 必须 risk type、priority、summary、priority decision 与至少一个 source jump，grade/CS-NCS label 同样只能由对应 assessment 投影；projection 必须一个 shared-spine binding、非空 ordered event markers，risk markers 可空但不得引用 projection 外 event/source jump。

中文 validator 使用冻结 `D07AudienceLexicon`，拒绝内部对象名/枚举/“正式事实、候选信号、已记录事项、通用风险点”，要求具体域名、风险类型、指标与自然中文；visible path 只能暴露用户可理解的项目→中心→受试者→访视/待定区→域→原始记录层级。无有效 locator 的风险不得提供虚假跳转。PD 措辞必须有唯一 `D07PDWordingPermissionDecision` 且所有 scope/hash/accepted 条件为 true；否则 `pd_wording_permitted=false`。

## 12. 增量与生命周期

- 每次输入仍是 accepted full snapshot；incremental 只比较两个 accepted baselines。
- N→N+1 区分新结果、更正、删除/范围变化、新复测、新解释、新 AE/CM/IP/处置和规则版本变化。
- 风险关闭必须有精确 `close_reason`：如 `resolved_by_data`、`explained_by_verified_repeat`；后续再异常以同稳定 identity 重开并保留历史。
- 规则/范围/单位字典变化与数据变化分别标记，不能冒充新增临床风险。
- 后 cutoff 结果不回写当前 Run；新 revision/Run 显式处理。

```text
D07LifecycleBinding:
  binding_id/risk_id/unit_stable_core_hash/r2_lifecycle_ref
  current_transition_ref/previous_run_ref?/carry_forward_source_risk_id?
  superseded_by_risk_id?/identity_resolution_state
  close_proof_refs/reopen_trigger_refs/machine_close_forbidden
  adjudication_binding_ref/source_locator_ids/lineage_hash
```

只有稳定身份一致且 authority/correction chain 可比较时可 carry-forward。identity ambiguity、source deletion 未解释、high priority、seriousness/AESI clue 或 `machine_close_forbidden=true` 时禁止机器关闭。关闭必须有 accepted close proof；新数据再次命中时追加 reopen transition，不覆盖历史。

## 13. 覆盖与 fail-closed 不变量

1. expected-set hash、规则/定义/范围/单位版本、scope/cutoff、输入/输出 hash 全部冻结；
2. 每个 expected unit 恰有一个 L1 disposition；
3. `negative` 需要完整分母与必需反证链，空表/未运行/未命中不算 negative；
4. 任何 `not_evaluable` 阻断“D07 医学完整”声明；
5. runtime 不得读取 challenge number、fixture id、oracle 或 expected output；
6. stable identity、source locator、producer/consumer binding 必须双向解析；
7. 内容哈希在消费前从 typed fields 重算；同步改写若无外部 authority 必须明示边界，不硬编码 canonical fixture；
8. 相同实质 typed input 必须产生相同医学结果、trace 和 projection；
9. 所有异常结果保留原值，normalized/grade/trend 不覆盖来源；
10. D07 结果不得形成 D09/D10 聚合或 D01/D04 重复风险。

## 14. 合成挑战矩阵 v0.1

实现前须持久化 typed fixture catalog、独立 expected-outcome oracle、challenge registry 和生成器。初始最小矩阵 144 条：

| ID | 类别 | 数量 | 必含挑战 |
|---|---|---:|---|
| 001–012 | 五类 disposition/适用性 | 12 | 正/负/boundary/not_evaluable/not_applicable；选择性收集；空表非阴性 |
| 013–028 | 单位与范围 | 16 | 单位缺失/错维度/可转换；范围按性别年龄方法中心；ULN/LLN 等号；范围切换 |
| 029–044 | 基线与趋势 | 16 | 基线正常→异常；基线异常恶化/稳定；持续/复发/恢复；单点非趋势；部分日期 |
| 045–060 | CTCAE/项目分级 | 16 | 版本缺失/漂移；term 映射；端点 inclusivity；reported vs recomputed；不适用不等于不可评估 |
| 061–074 | CS/NCS 与样本质量 | 14 | NCS 子串陷阱；无理由 NCS；CS 缺动作；溶血/污染；可靠复测与错误复测匹配 |
| 075–092 | 复测、处置与跨域 handoff | 18 | repeat/action/explanation/AE 四状态；CM/IP 处置；D01/D04 owner 去重；同日非因果 |
| 093–106 | 器官组合/严重事件线索 | 14 | 肝脏组合、QT/电解质、血象、肾功能；组成缺失；替代原因；无自动 DILI/SAE |
| 107–118 | 检查类结果 | 12 | ECG lead/校正方式、VS 体位、PE body site、影像 reader/复核、字符/序数结果 |
| 119–128 | 身份/版本/内容哈希 | 10 | wrong scope/cutoff/source；stale hash；同步改写边界；duplicate/stable identity |
| 129–136 | Query/Journey | 8 | 三段式中文；source jump；域/风险标记；趋势断点；内部术语拦截 |
| 137–144 | 增量/lifecycle/聚合边界 | 8 | 新增/更正/删除/复测关闭/重开；规则变化；D10 输入但无聚合 |

每条必须具备：唯一编号与名称、typed input、entrypoint、expected L1/priority/subtype、expected trace/source locators、正/反变异、DSL assertion。禁止 `assert True`、静态 expected 回显、lambda/docstring 伪验证或用例号分支。

### 14.1 冻结 validation artifacts

合同冻结前必须生成并分别哈希：

1. `typed_fixture_catalog`：144 条 immutable typed inputs；不含 expected outcome；
2. `independent_expected_outcome_oracle`：只含 case binding 与 exact output leaves；不得被 runtime import；
3. `challenge_manifest`：case → entrypoint → required trace/source/DSL；
4. `challenge_registry`：由冻结 generator 从前三者与合同 semantic hash 生成；
5. `assertion_dsl_schema`：闭合 predicate 类型，拒绝任意 callback/代码字符串；
6. `artifact_generator`：先验证合同/status/semantic hash、catalog/oracle/manifest hash、case bijection、duplicate substantive-input invariant，再输出 registry。

六类工件均为 exact-key canonical JSON；顶层固定如下（`schema_version/artifact_kind/contract_semantic_hash/content_hash` 为共同必需键）：

```text
typed_fixture_catalog:
  schema_version/artifact_kind/contract_semantic_hash/catalog_id
  ordered_cases[{case_id,case_name,fixture_id,entrypoint,typed_input,
                 substantive_input_hash,positive_mutation_ids,
                 negative_mutation_ids,input_source_locator_ids}]
  case_count/content_hash

independent_expected_outcome_oracle:
  schema_version/artifact_kind/contract_semantic_hash/oracle_id
  ordered_expectations[{case_id,fixture_id,expected_leaf_set,
                        expected_trace_leaf_set,expected_source_leaf_set,
                        expected_integrity_error?}]
  case_count/content_hash

challenge_manifest:
  schema_version/artifact_kind/contract_semantic_hash/manifest_id
  ordered_bindings[{case_id,fixture_id,oracle_case_id,entrypoint,
                    required_assertion_clause_ids,required_trace_paths,
                    required_source_paths,required_test_id}]
  case_count/content_hash

challenge_registry:
  schema_version/artifact_kind/contract_semantic_hash/registry_id
  catalog_hash/oracle_hash/manifest_hash/dsl_schema_hash/generator_hash
  ordered_registry_core[{case_id,fixture_id,oracle_case_id,manifest_case_id,
                         entrypoint,test_id,substantive_input_hash,
                         expected_leaf_set_hash,assertion_program_hash}]
  bijection_audit/content_hash

assertion_dsl_schema:
  schema_version/artifact_kind/contract_semantic_hash/dsl_schema_id
  allowed_operators/closed_clause_schemas/path_grammar/value_type_grammar
  forbidden_constructs/content_hash

artifact_generator_manifest:
  schema_version/artifact_kind/contract_semantic_hash/generator_id
  generator_source_hash/input_artifact_hashes/output_schema_hash
  semantic_hash_range/integrity_stage_order/content_hash
```

`contract_semantic_hash` 只覆盖本合同从标题后的 Status/Scope 至 §15 的 UTF-8 规范化文本，排除文件名、生成时间、工件哈希与审阅记录；范围起止字节与 normalization algorithm 固定写入 generator manifest。各 content hash 均为自身所有字段（排除 own content_hash）的 canonical JSON SHA-256。registry core 必须对 case_id、fixture_id、oracle_case_id、manifest_case_id、test_id 五列分别唯一并全双射；144 条一条不少、一条不多。

DSL 仅允许闭合 operators：`exists|absent|equals|not_equals|in_enum|decimal_equals|ordered_equals|set_equals|hash_equals|ref_resolves|scope_all_equal|one_to_one|count_equals|error_equals`。每个 clause exact keys 为 `clause_id/operator/actual_path/expected_typed_value?|expected_ref_path?|value_type/reason_code`，两个 expected 字段按 operator 恰选一个；path grammar 只允许从 runtime raw result root 出发的字段/数组索引，不允许 callback、lambda、import、eval、表达式字符串、fixture/oracle 反向读取。

`expected_leaf_set` 必须逐叶列出 disposition/subtype、五个正交维度、owner/query/handoff、obligation/pattern/examination、priority、lifecycle、Journey/audience validation 与 integrity outcome 中适用于该 case 的 exact typed leaves；`expected_trace_leaf_set` 至少含规则/authority/scope/correction/baseline/unit/range/grade/priority decision refs；`expected_source_leaf_set` 至少含 source locator、producer binding、source jump 及反向 binding。raw runtime 展平后的适用 leaves 与 oracle 做集合键全等和值全等，额外或缺失均失败。

pre-evaluator integrity 阶段顺序固定：`schema_parse → canonical_hash → artifact_hash → contract_semantic_hash → scope/cutoff → authority_version → correction_chain → identity/duplicate → foreign_key/bijection → D05_gate/applicability → evaluator_admission`。闭合错误类为 `schema_error|stale_hash|artifact_mismatch|semantic_hash_mismatch|scope_mismatch|out_of_cutoff|authority_mismatch|correction_ambiguous|identity_ambiguous|duplicate_identity|foreign_key_error|bijection_error|open_d05_gate|applicability_unresolved|evaluator_not_admitted`；首个失败阶段终止，且不得产生医学/priority/risk/Query/Journey 输出。

独立性要求：oracle authoring input 只允许合同、冻结 authority/rule definitions 与人工制定 expected leaves，不得调用 runtime evaluator、fixture generator 的医学分支或读取 runtime output；generator 只能装配、校验、哈希和建立双射，禁止生成或修改 expected values。oracle、catalog、manifest、registry 与 runtime source 的 import graph 必须由静态审计证明无反向依赖。

### 14.2 执行与反自证合同

- pre-evaluator integrity 必须在任何医学、priority、risk、Query、projection 前执行；
- 真实 entrypoint raw output 与 oracle 做 exact leaf bijection，额外/缺失 leaf 均失败；
- runtime source 禁止导入 catalog/oracle/manifest/registry，禁止读取 case number/name/fixture id/expected text；
- 去除 case binding 后相同 substantive typed input 必须产生相同 raw medical output、trace 与 projection；
- mutation suite 至少覆盖：每个 typed object stale/rehash、wrong scope/site/run/subject/cutoff、authority version、correction fork、open D05 gate、unit/range/grade/CS-NCS、owner/query、priority、lifecycle、Journey marker/jump/payload、同步改写且缺独立 authority；
- 对确无独立 authority 的 opaque locator/value，只能接受非空 typed/bidirectional/content-addressed 边界或走合同 erratum；禁止硬编码 fixture literal。

## 15. 实现与验收边界

合同独立接受后，才允许在 `poc/medical_monitoring_ai_native_r4` 新增 D07 专属模块/测试、最小 root export 与 README；不得修改冻结 D01-D06/R1-R3 语义。

实现完成证据至少包括：

- 144 条 raw runtime/oracle/DSL 全匹配且 deterministic；
- hash/identity/unit/range/version/CS-NCS/owner/Journey 变异全部 fail-closed；
- D07 focused、全 R4、R1-R3 相邻回归、Ruff、compile/import/export；
- 8911 停止且无任务缓存；
- 新鲜上下文独立临床/工程审阅无 P0-P4。

未运行真实项目、真实模型、浏览器/R5、中心/项目聚合或正式安全报告时，均不得宣称相应完成。
