# R4-D05 访视、评估、样本与时序符合性纵切合同 v1.2

Date: 2026-08-12  
Status: `FROZEN_R4_D05_CONTRACT_V1_2`  
Scope: 仅限合成/离线 R4 纵切；合同冻结前不得据此实现产品代码。

## 1. 目标与边界

D05 把版本化方案计划与已接受的实际记录拆成可追溯、可重复计算的“计划—实际”评价单元，回答以下问题：

1. 截至本次数据截止日，哪些访视、评估或样本要求已经适用且已到可评价时点；
2. 哪些实际就诊、操作、评估或采样记录可以唯一归入哪个计划单元；
3. 发生与否、发生时间、先后次序、计划归属是否与适用方案一致；
4. 哪些问题需要医学监察员核实，并如何在共享访视轴上定位到方案和原始数据。

D05 只产生“访视超窗待核实”“评估记录待核实”“样本采集时间待核实”等具体问题、风险标记和三段式 Query 草稿。它不正式判定、分级、报送、登记或关闭方案偏离（PD），不建立 PD 待办或外部回复闭环，不替代研究者、申办方或其他有权责任方。

本合同不运行 OCR/VLM、真实项目、真实 provider 或产品服务；不启动 8911；不改 R1-R3、R5 UI 或医学写作子系统；不把任何项目名、固定访视号、固定窗口、固定表名/字段名、固定药物或固定检查写入通用内核。本阶段不新增系统安全设计或安全测试。

## 2. 依据、来源权威与责任边界

### 2.1 规范依据

1. CDISC SDTMIG v3.3：TV 表达计划访视，SV 表达受试者实际经历的访视；TV/SV 比较可发现计划偏离，但一个方案访视可跨多日或多次实体接触，一次住院也可包含多个方案访视；触发型访视的 VISITNUM 不必按时间递增，实际 SV 日期可能由多域记录推导。
2. ICH E6(R3) Step 4 Final Guideline（2025-01-06，2025-10-24 errata）：方案应可操作地描述评估方法、范围和时点，并保留可靠的数据采集、复核和缺失/错误处理路径。
3. NMPA《药物临床试验数据递交指导原则（试行）》：研究/受试者标识与适用数据集中的 VISIT/VISITNUM 等时间变量应一致、可追溯；原始缺失不得填补。
4. FDA 2024 年 protocol deviation 文件仍为 draft/nonbinding，本合同只借鉴其“检测、分类、记录、报告责任分离”原则，不把它当作中国项目强制规则或 D05 正式判定 PD 的授权。

证据等级（检索日 2026-08-12）：CDISC 官方标准与 NMPA/ICH 官方文件均为 A 级（权威 5/5、直接性 4-5/5、可查询性 5/5）；FDA draft 为 B-级（权威 4/5、直接性 3/5、约束力 1/5），只作责任边界反例。主要来源、版本状态与可查询链接保存在 `context/medical_monitoring_r4_d05_visit_schedule_discovery_20260812.md`。

### 2.2 项目内来源权威

来源按 claim scope 分层，不能用多数票解决冲突：

- **计划权威**：适用方案正文、Schedule of Activities、表格脚注、正式修订及中心/队列/受试者过渡条款；
- **实际权威**：当前 Run 接受的全量快照中的实际就诊、评估、采样、处置、状态和可定位说明；派生日期必须保留输入行、算法与精度；
- **例外权威**：方案预定义例外、在事件时点已生效且适用的正式变更，以及可定位的改期/远程/住院/合并访视记录；
- **辅助来源**：访视标签、汇总状态、DV/说明、外部报告和模型输出，只能帮助定位，不能覆盖方案或 accepted source record。

计划与实际来源冲突时分别保留。无法唯一解释适用版本、归属或时点时进入 `boundary` 或 `not_evaluable`，不得由模型投票、输入顺序或“离得最近”裁决。

### 2.3 域责任边界

| Claim | 唯一 owner | D05 可做 | D05 禁止做 |
|---|---|---|---|
| 计划访视/评估/样本发生、时间窗、次序、计划归属 | D05 | 建 expected-set、匹配、时序评价、风险/Query/Journey marker | 正式判 PD |
| 研究药计划/实际暴露、剂量和处置医学评价 | D03 | 引用稳定的给药事件作为访视锚点 | 复制给药风险或 Query |
| 入排、知情/随机/入组、非计划型前置要求 | D04 | 引用稳定事件作时间锚点 | 复制资格或方案执行风险 |
| 疗效终点/量表结果的医学含义 | D06 | 核对是否完成及完成时点 | 判断疗效趋势、反应或终点值 |
| 实验室/检查结果、单位、分级和医学意义 | D07 | 核对是否采集/检查及完成时点 | 判断异常、CTCAE 或临床意义 |
| 跨表关系本身 | D08 | 消费已验证 `CrossDomainEvidenceRef` | 以相同日期/文本自行建立跨域医学关系 |

方案解构器可抽取全部计划要求，但 owner 路由必须先于 D05 expected-set。非 D05 claim 不进入 D05 L1 分母，不生成 D05 candidate/risk/Query；总览只能以 typed reference 投影 producer 的单一结果。owner 无法唯一确定时只生成一个 `ScheduleGate(gate_kind=routing)`，在 coverage/control plane 计量并阻断完整性，不在多个域重复建单元。

## 3. 领域对象与内容寻址

所有对象均为 immutable record；修改产生新版本与 lineage，不原地改写既往接受结果。自由文本不得进入稳定身份核心。

### 3.1 计划对象

```text
VisitScheduleApplicabilityDecision:
  decision_id/project_ref/subject_ref/site_ref
  protocol_version/arm/cohort/phase/transition_rule
  cutoff/decision_status/reason_codes/feasible_schedule_ids
  source_locator_ids/rule_version/hash

PlannedVisitDefinition:
  planned_visit_id/planned_visit_key/schedule_id/protocol_version
  official_visit_code/audience_visit_name/planned_order
  visit_kind=scheduled|triggered|contingent|repeat_allowed
  applicability_expression/anchor_rule/window_rule
  phase/allowed_modalities/merge_or_split_rule
  source_locator_ids/definition_hash

PlannedActivityDefinition:
  planned_activity_id/planned_activity_key/planned_visit_id
  activity_kind=assessment|sample|procedure|contact
  clinical_domain/official_activity_code/audience_name
  applicability_expression/occurrence_rule/timing_rule
  repeat_rule/specimen_or_method_role
  owner_domain/source_locator_ids/definition_hash

EvaluationMaturityRule:
  maturity_rule_id/unit_kind
  anchor_kind/anchor_source_role
  maturity_expression/cutoff_precision/timezone
  missing_anchor_effect=gate
  rule_version/source_locator_ids/hash
```

`official_visit_code`、VISITNUM 或显示顺序是标识/排序证据，不是通用时间权威。`planned_order`、触发事件和 anchor lineage 必须显式保存。

`planned_visit_key` 与 `planned_activity_key` 表示跨普通修订可追踪的逻辑 obligation；版本化 definition id 与 definition hash 进入 lineage。若修订无法证明旧新 obligation 的延续关系，必须 supersede 或标记 identity ambiguity，不能只因中文名称相同而沿用身份。

### 3.2 实际对象

```text
ActualEncounterRecord:
  encounter_id/stable_actual_object_key/subject_ref/site_ref
  source_record_keys/recorded_visit_code/recorded_visit_name
  encounter_kind=onsite|remote|hospital|home|unscheduled|unknown
  start/end/date_precision/timezone
  date_origin=recorded|derived
  derivation_algorithm_id/input_locator_ids
  source_locator_ids/content_hash

ActualActivityRecord:
  actual_activity_id/stable_actual_object_key/subject_ref/site_ref
  activity_kind/clinical_domain/recorded_activity_code
  start/end/date_precision/timezone
  encounter_refs/source_locator_ids/content_hash

ActualEncounterBundle:
  bundle_id/stable_actual_object_key/subject_ref/site_ref
  member_encounter_ids/episode_kind
  merge_or_split_rule_id/assignment_scope
  derived_start/derived_end/date_precision/timezone
  completion_evidence_locator_ids/lineage_hash

ActualRecordScopeDecision:
  scope_decision_id/actual_object_id
  snapshot_as_of/clinical_event_cutoff
  event_effective_start/event_effective_end/date_precision/timezone
  scope_status=in_scope|out_of_cutoff|boundary|not_evaluable
  reason_codes/source_locator_ids/lineage_hash
```

每个 encounter/activity 在参与 bundle 或 assignment 前必须恰有一个 `ActualRecordScopeDecision`；只有 `in_scope` 进入正常 inventory，`out_of_cutoff` 仅可投影 future context，`boundary|not_evaluable` 生成单一 cutoff-scope gate。`ActualEncounterBundle` 是计划访视 assignment 唯一可引用的实际访视 episode；单次接触也形成一个单成员 bundle。成员排序按稳定 key canonicalize，不能按输入行序决定。一个 encounter 只有在显式 split rule 允许时才能进入多个 bundle；一个 bundle 只有在显式 merge rule 允许时才能支持多个计划访视。`stable_actual_object_key` 来自冻结的来源身份算法和不可变业务键，不含可修订的日期、访视名称或自由文本；无法稳定识别时进入 identity ambiguity。派生的实际访视起止日期必须可回到输入行；推导失败或候选日期冲突不得伪装成原始日期。

### 3.3 分配、评价与投影对象

```text
VisitAssignmentDecision:
  assignment_id/subject_ref/actual_bundle_id
  candidate_planned_visit_ids/selected_planned_visit_id
  decision_status=unique|multi_feasible_boundary|unplanned_supported|
                  unassigned_inconsistent|not_evaluable
  evidence_predicate_ids/rejected_candidate_reasons
  algorithm_version/hash/source_locator_ids

ActivityAssignmentDecision:
  assignment_id/subject_ref/actual_activity_id
  candidate_planned_activity_ids/selected_planned_activity_ids
  decision_status=unique|multi_feasible_boundary|unplanned_supported|
                  duplicate_consumption|not_evaluable
  repeat_or_resample_parent_id/repeat_rule_id
  evidence_predicate_ids/algorithm_version/hash/source_locator_ids

ActualActivityConsumptionLedger:
  ledger_id/subject_ref/site_ref
  actual_activity_id/consuming_planned_activity_ids
  allowed_multiplicity/repeat_rule_id/assignment_ids
  reverse_coverage_status/lineage_hash

TypedScheduleAnchorRef:
  anchor_ref_id/producer_domain/producer_unit_id
  stable_source_event_key/content_hash
  subject_ref/site_ref/phase/episode_id
  anchor_start/anchor_end/date_precision/timezone
  relation_type=fixed_reference|prior_actual_visit|first_ip_dose|
                randomization|consent|other_verified_protocol_anchor
  source_locator_ids/lineage_hash

ScheduleGate:
  gate_id/gate_kind=applicability|routing|anchor|cutoff_scope
  subject_ref/site_ref/gate_state=open|closed
  decision_status=boundary|not_evaluable|resolved
  feasible_schedule_ids/feasible_owner_domains/feasible_anchor_ref_ids
  affected_planned_visit_keys/affected_planned_activity_keys
  missing_evidence_roles/reason_codes/source_locator_ids/lineage_hash
  prior_gate_id/resolved_by_decision_id
  counts_in_medical_expected_set=false/blocks_domain_complete

ScheduleInterpretationLedger:
  ledger_id/decision_scope
  interpretation_ids/accepted_interpretation_ids/rejected_interpretation_ids
  predicate_results/rejection_reason_codes
  merge_split_repeat_reschedule_trigger_rule_ids
  source_locator_ids/algorithm_version/lineage_hash

ScheduleEvaluationUnit:
  unit_id/subject_ref/site_ref/unit_kind
  planned_visit_id/planned_activity_id/actual_bundle_id/actual_activity_id
  evaluation_window_id/applicability_decision_id
  visit_assignment_id/activity_assignment_id
  rule_id/rule_version/classifier/stable_core
  lineage_hash/source_locator_ids

VisitCoverageGapNotice:
  notice_id/unit_id/reason_code/missing_evidence_roles
  plan_locator_ids/reachable_source_locator_ids/audience_text

VisitJourneyProjection:
  projection_id/subject_ref/site_ref
  planned_visit_markers/actual_encounter_markers/activity_markers
  assignment_edges/risk_markers/pending_time_markers/out_of_cutoff_markers
  source_locator_ids/payload_hash
```

`unit_kind` 是关闭集合：

1. `visit_occurrence`：已到期的计划访视是否发生；
2. `visit_timing`：唯一实际访视是否命中计划窗口；
3. `visit_order`：实际先后是否满足显式次序/触发规则；
4. `activity_occurrence`：应进行的评估/样本/操作是否完成；
5. `activity_timing`：实际评估/样本/操作是否命中独立窗口；
6. `actual_assignment`：实际对象是否被错误归入计划访视、重复或无法合理归属；
7. `schedule_consistency`：方案计划自身存在不可同时满足的时序规则。

`ScheduleGate` 属于 coverage/control plane，不属于 D05 医学 expected-set，也不使用五类 L1 分母；open gate 单独计入并阻断域完整性，不创建 candidate/risk/Query。状态组合是关闭集合：`open + boundary|not_evaluable + blocks_domain_complete=true`，或 `closed + resolved + blocks_domain_complete=false`；其他组合 schema/QC fail。`applicability`、`routing`、`anchor` 每个稳定 decision 在一个 Run 只允许一个 gate。对象不可变：新 Run 以 `prior_gate_id + resolved_by_decision_id` 追加 closed/resolved gate，旧 open gate 保留；只有当前 Run 的 gate 已关闭，才展开相应正常 obligation。不得在 open gate 下预生成 N 份潜在医学单元。

### 3.4 稳定身份

`stable_core` 至少包含：

```text
(project_scope, subject_ref, site_ref, owner_domain=D05,
 unit_kind, planned_visit_key?, planned_activity_key?, stable_actual_object_key?,
 evaluation_window_id, rule_id, anchor_episode_id?)
```

不得包含 Run/snapshot/revision、方案显示版本、自由文本、Query、severity 或实际评价结果。方案/规则/mapping/算法/来源版本进入 lineage。相同 clinical obligation 在 N→N+1 保持 classifier；规则或算法变化产生 superseded/not_evaluable lineage，不伪装为数据已解决。不同重筛周期、治疗周期或触发 episode 必须有不同 `evaluation_window_id`，不能互相关闭。

## 4. 适用性与 expected-set

### 4.1 适用性先行

`VisitScheduleApplicabilityDecision.decision_status` 只允许：

- `unique_active`：可唯一确定方案版本、研究臂/队列、阶段、中心启用及受试者过渡规则；
- `multi_feasible_boundary`：完整证据支持两个及以上可行计划解释；
- `not_evaluable`：决定所需版本、中心启用、治疗阶段、队列、触发或关键日期缺失/冲突。

只有 `unique_active` 可生成正常医学 expected-set。其余状态每个稳定 applicability decision 只生成一个 `ScheduleGate(gate_kind=applicability)`，不进入医学 expected-set，不生成“版本×访视×活动”的大量伪分母，不按最新版本或输入顺序选一个。gate 以 decision、排序后的可行 schedule、缺失角色、来源与 lineage 做 canonical hash。

方案修订可以是：仅新入组、既有受试者继续旧版、全部在组切换、下一访视后切换、重新知情后切换或其他显式规则。中心启用日不是自动覆盖全部受试者的充分条件；不得默认最新版本、全项目统一生效或选择离事件最近的版本。

### 4.2 到期判定

每个 Run 必须同时冻结两条不可混用的时间边界：

- `snapshot_as_of`：本次 accepted full snapshot 的接受/形成时点和 source revision；决定“本次实际读到了哪些记录”；
- `clinical_event_cutoff`：本次医学监查允许评价的事件/采集有效时点；决定“哪些实际事件可进入 assignment、L1、风险和关闭逻辑”。

实际记录只有同时属于 accepted snapshot，且其可比较 `event/collection effective interval` 完全不晚于 clinical_event_cutoff，才进入本 Run 的正常 actual inventory。事件完全在 cutoff 后，只能进入 Journey 的 `out_of_cutoff` 上下文，不得参与 expected-set、assignment、L1、风险、Query 或关闭。部分日期/跨午夜区间跨越 cutoff 且来源精度完整时形成 `cutoff_scope` boundary gate；有效时点或所需时间角色缺失/冲突时形成 not_evaluable gate。后续 snapshot 补入“事件发生于旧 cutoff 前、但此前未录入”的 late-arriving record，只影响新的 Run，并按 §11 的 linked-negative/supersede 规则处理，不能回写旧 Run。

expected-set 只纳入在 cutoff 时已经达到适用性评价成熟时点的原子 obligation：正常医学评价单元须满足以下全部条件；若唯一、权威的适用性表达式明确为假，则为保持五类 L1 审计闭合，可生成相应 `not_applicable` audit unit，但不得继续生成 occurrence/timing/assignment 医学单元。

1. 对该受试者/中心/臂/队列/阶段/episode 适用，或已有充分权威依据唯一证明不适用；
2. 触发条件已经发生且可定位，或固定计划锚点已确定；
3. 该 `unit_kind` 的 `EvaluationMaturityRule` 已冻结，且按其 anchor、窗口最晚端点、显式宽限期、精度和时区计算的成熟时点不晚于 clinical_event_cutoff；
4. 规则、端点包含性、日历算法和所需来源角色已冻结；
5. owner 为 D05。

未来未到期项目保留在计划轴并标记“尚未到计划时间”，但不进入 L1 expected-set、风险分母或 coverage 缺口。窗口仍开放时也不生成“访视缺失”；如已发生记录需要评估，可仅生成适用的 timing/assignment 单元。

早退、死亡、失访、撤回同意、治疗结束、阶段不适用等只有在权威状态及其生效时点可定位时，才把已达到适用性评价时点的相应 obligation 生成 `not_applicable` audit unit。单纯“未见后续数据”不能推断早退或死亡。cutoff 后才可能发生的 obligation 仍是未来计划，不生成 not_applicable unit。

### 4.3 expected-set 生成顺序

固定顺序：

```text
冻结 Run/source snapshot_as_of/clinical_event_cutoff
→ 构建 accepted actual identity inventory（不做问题分类）
→ 构建 typed anchor candidate index 与 ActualEncounterBundle candidates
→ 冻结方案计划适用性、owner routing 和 ScheduleGate
→ 唯一解析 fixed/chained/producer typed anchor
→ 展开适用且到期的 planned obligations；未决 anchor 只留单一 gate
→ 冻结 expected-set/hash
→ 生成 visit/activity assignment 与 consumption ledger
→ 逐 unit 评价
→ 生成 L2/L3/Journey 投影
```

前置 actual identity/anchor index 只能使用 accepted record identity、时间、阶段、producer typed binding 和冻结 mapping 谓词，不得读取医学异常结论、风险或 Query，也不得根据“看起来异常”选择性创造计划分母。链式 anchor 唯一时才能展开正常 obligation；anchor 缺失或存在多个完整可行解释时只生成一个 `anchor` gate，受影响下游 obligation 不进入正常 L1 分母。expected-set 按 canonical key 排序并内容寻址；输入行序、字典顺序或模型输出顺序不得改变 hash。

## 5. 分配与访视语义

### 5.1 唯一分配算法

分配使用版本化、关闭集合的证据谓词，按以下顺序收窄可行集合：

1. 已验证的稳定 explicit mapping 或 source-maintained parent key；
2. 适用方案版本内的官方访视/活动 code 与经过验证的别名映射；
3. 研究臂、阶段、触发 episode、访视类型和允许 modality；
4. 计划活动组合、实体就诊范围和显式 merge/split/repeat 规则；
5. 时间窗只作为排除不可能候选的一个证据，不能单独用“最近日期”选择赢家。

结果解释：

- 唯一 planned candidate 且 bundle membership、全部决定性谓词通过：`unique`；
- 两个及以上候选仍有完整依据：`multi_feasible_boundary`；
- 方案明确允许且记录明确为非计划/追加：`unplanned_supported`；
- 证据完整且记录自称某计划访视但与唯一可适用计划矛盾，或无任何允许归属：`unassigned_inconsistent`；
- 访视 code/mapping/阶段/日期/来源覆盖不足或冲突：`not_evaluable`。

不能仅因日期落在窗口内就吸附；不能用文件行序、VISITNUM 大小、同名、相同日或文本相似替代稳定映射。`multi_feasible_boundary` 和 `not_evaluable` 均阻断依赖该分配的确定 positive/negative，除非 issue expression 在所有可行分配下恒真或恒假。

### 5.2 多次接触、住院与合并/拆分

- 一个方案访视可由多次实体接触或多日记录共同完成，但必须由明确 merge rule 与 source lineage 证明；
- 一次住院可承载多个方案访视，但每个计划 obligation 保持独立身份和各自完成证据；
- 远程/电话/居家完成只有在适用计划或已生效规则允许该 modality 时才可作为 negative counterevidence；
- 重复测量、补采、重做或改期记录不自动形成第二个计划访视；由 repeat/reschedule rule 决定其是同一 obligation 的补充、允许的非计划事件或独立问题；
- 取消记录只说明计划动作未实施，不自动使 obligation `not_applicable`。

### 5.3 typed anchor 绑定

固定基准、D03 给药、D04 随机/入组/知情或其他 producer 事件作为计划锚点时，必须先形成 `TypedScheduleAnchorRef`。有效 binding 要求 producer domain、producer unit/event id、stable source event key/content hash、subject、site、phase/episode、可比较时间区间、日期精度、时区和 `relation_type` 全部一致；任一 wrong/missing/conflicting 均形成 `ScheduleGate(gate_kind=anchor)`，不得仅凭同日、相邻日期、同一访视名或普通 locator 选锚点。

D05 可以消费 producer 的稳定事件与时间，不复制 producer 的 L1、candidate/risk/Query 或医学裁决。producer 本身为 boundary/not_evaluable 时，D05 不升级其确定性；依赖该锚点的 obligation 不进入正常 expected-set，直到新 Run 提供唯一 typed anchor。

## 6. 时间窗与次序算法

每个 `window_rule` 必须版本化并可定位，至少冻结：

- anchor 类型与稳定 anchor id；
- 固定锚点（如 Day 1）或链式锚点（如前次实际访视）的明确选择；
- calendar date、elapsed duration 或 study day 语义；
- Study Day 0 是否存在；若无 Day 0，跨基准日前后如何换算；
- lower/upper offset、端点包含/排除、允许宽限期；
- date/datetime 精度、时区与跨午夜处理；
- 部分日期比较和范围传播算法；
- 触发、改期、重排、提前/延后传播规则。

内核不得默认 ±N 天、默认 Day 0、默认本地时区、默认端点包含、默认固定 Day 1 或默认“以上一次实际访视为锚点”。固定计划的某次延迟不能无依据地把后续全部窗口顺延；链式计划则必须按显式规则传播。

部分日期保留原值、规范化区间和精度。若 accepted source 的允许精度本身导致所有可能值都在窗内或都在窗外，可得 determinate negative/positive；若区间跨越窗口边界且来源覆盖完整，为 `boundary`。关键日期角色缺失、冲突、无法建立锚点或算法未冻结时为 `not_evaluable`。不得静默补日或用月首/月末伪造精确日期。

次序只依据显式 `planned_order`、触发依赖或 phase transition rule；触发型/contingent/非计划访视的 VISITNUM 可能不按时间排序，不得据此判错序。

merge/split/repeat、改期、触发、窗口端点和链式 anchor 的所有可行解释必须进入 `ScheduleInterpretationLedger`。`boundary` 要保留至少两个 accepted interpretations 及各自结果；“所有解释下恒真/恒假”须能由 ledger 重放；被排除解释必须有版本化 predicate 和 reason code。输入顺序、模型措辞或未记录的临床常识不得增删解释。

## 7. 评估、样本与双向核对

### 7.1 计划到实际

对每个到期的 `PlannedActivityDefinition`：

1. 先确定 applicability、occurrence rule、独立 timing rule 和允许 repeat/替代方式；
2. 再通过 `ActivityAssignmentDecision` 匹配一个或多个实际 activity record，并把消费关系写入 `ActualActivityConsumptionLedger`；
3. 分别评价“是否完成”和“何时完成”，不能因有任意结果行就同时判两者符合；
4. 记录 supporting、counterevidence 和 coverage gap。

### 7.2 实际到计划

每个实际 activity 也必须反向检查：

- 是否唯一归入计划 obligation；
- 是否为允许的非计划/重复/补采；
- 是否错误标记了名义访视；
- 是否重复计入两个计划 obligation；
- 是否存在计划表未展开或 mapping 漏失。

每条 actual activity 默认最多支持一个 planned obligation。只有冻结 repeat/resample rule、parent binding 和允许 multiplicity 均明确时，才允许同一 actual activity 或一组关联活动支持多个 obligation；否则 `duplicate_consumption` 为 positive。ledger 必须同时提供 `planned_activity → actual_activity[]` 与 `actual_activity → consuming_planned_activity[]` 两个可对账索引。一个方向“完整”不证明另一个方向无错配；两端都通过且 reverse coverage closed 后才可声明该活动链路完整。

D05 只判断发生、时间和归属。评估得分是否正确/具有疗效意义由 D06；样本结果、单位、异常或 CTCAE 由 D07；跨表临床关系由 D08。

## 8. L0/L1/L2/L3 合同

### 8.1 四层不得串层

- **L0**：输入、角色、行、来源、mapping 和执行 coverage，复用冻结 `CoverageUnitStatus`；
- **L1**：每个 `ScheduleEvaluationUnit` 恰有一个互斥 disposition：`positive|negative|boundary|not_applicable|not_evaluable`；
- **L2**：源记录、待核实线索、风险实例、Query 草稿和 coverage notice 分别计数，以稳定 ID 关联；
- **L3**：复用 R2 `RiskLifecycle`，D05 不新增第二套状态机。

L0“缺口已说明”不等于 L1 可评价；L1 `not_evaluable` 不自动改变既有风险的 L3 状态。

### 8.2 `positive`

只有当适用性、到期、计划规则、决定性实际证据和分配关系足以在所有允许解释下确认 issue predicate 为真，才为 positive。关闭的 primary subtype：

| subtype | 用户标签 |
|---|---|
| `visit_overwindow` | 访视时间待核实 |
| `visit_missing` | 访视完成情况待核实 |
| `visit_order_inconsistent` | 访视先后顺序待核实 |
| `visit_duplicate` | 访视重复记录待核实 |
| `visit_assignment_inconsistent` | 访视归属待核实 |
| `required_assessment_missing` | 评估记录待核实 |
| `required_assessment_mistimed` | 评估时间待核实 |
| `required_sample_missing` | 样本采集记录待核实 |
| `required_sample_mistimed` | 样本采集时间待核实 |
| `schedule_rule_inconsistent` | 方案时序要求待核实 |

一个原子 unit 只有一个 primary subtype；相同 source event 被多个规则检查时保持各自 rule identity，但相同 `(subject, planned obligation, actual object, clinical action)` 不得因别名或 owner 重复建立 candidate/Query。

### 8.3 `negative`

negative 要求该 unit 的适用性、计划规则、所需 actual coverage、分配和允许例外均完整，且所有可行解释下 issue predicate 为假。`negative` 不是“没发现”，不能从零记录、空模型输出或局部表推断。允许窗、有效改期、允许远程、住院拆分、正式取消并转为不适用等必须作为可定位 counterevidence。

### 8.4 `boundary`

完整来源支持两个及以上允许解释，或已接受的合法日期精度跨越冻结窗口边界，而不同解释产生不同问题判断时为 boundary。它可生成一条明确保留不确定性的待核实线索；若优先级无法确定则为 `unknown`，不得默认 low。boundary 不得用来包装缺表、缺字段、缺锚点、算法未冻结或 mapping 未完成。

### 8.5 `not_evaluable`

单元适用或适用性未知，但缺少/冲突的计划锚点、实际日期、访视 mapping、阶段、适用窗口、必要来源角色或规则算法使问题无法判断时为 not_evaluable。它生成 `VisitCoverageGapNotice`，不创建新的确定风险或 Query，不显示“未知风险等级”。已有活动风险只 carry-forward 并显示资料缺口。

### 8.6 `not_applicable`

只有权威适用性证明该 obligation 对该受试者/阶段/episode 不适用时使用。尚未到期不是 not_applicable；未来项目不进入本次 expected-set。无法证明早退/死亡/撤回的有效时点时不得把后续计划批量标为 not_applicable。

## 9. 优先级、风险与 Query

### 9.1 监察优先级

优先级来自版本化、内容寻址的 `D05PriorityPolicy`，不是正式 PD 重要性等级，也不得由模型自由打分。策略输入必须是经方案解构和人工/确定性 QC 验证的关闭枚举：`impact_class=rights_safety|critical_treatment|primary_endpoint|key_secondary_endpoint|mandatory_critical_sample|other_required|administrative`、`recurrence_class=single|repeated_subject|repeated_site`、`recoverability=recoverable|time_critical|irrecoverable|unknown` 和 `actionability=actionable|context_only|unknown`。

v1 决策严格按以下 precedence 执行，命中即停止：

1. `impact_class=rights_safety|critical_treatment`：始终 high 且 machine-close-forbidden；`actionability/recoverability` 为 unknown 或 context_only 只形成 coverage/context 提示，不得把已确定的安全/权益优先级降为 unknown；
2. 其他 impact class 若任一必需输入未冻结、`recoverability=unknown` 或 `actionability=context_only|unknown`：优先级为 unknown，不生成确定低/中/高，也不得默认 low；
3. `primary_endpoint|mandatory_critical_sample`：`time_critical|irrecoverable` 为 high，其余为 medium；
4. `key_secondary_endpoint|other_required`：基线 medium，`repeated_site` 或 `irrecoverable` 升为 high；
5. `administrative + single + recoverable + actionable`：low；其他 administrative 组合基线 low，`repeated_subject` 升 medium，`repeated_site|irrecoverable|time_critical` 升 high。

升阶以 low→medium→high 封顶。所有决定保存 policy id/version/hash、输入枚举、命中的 precedence step 和 reason code。

- 可能影响受试者安全/权益、关键治疗决策或关键时点的确定问题按上述映射优先显示；
- 关键终点/样本和反复出现问题按冻结枚举升阶，不由自然语言自由判断；
- 影响有限且满足唯一 low 组合的问题才可为低；
- not_evaluable 不投影风险等级；boundary 无法定级时保留 unknown。

高优先级仍只是待核实问题。`rights_or_safety_critical` 或其他 `machine_close_forbidden` 冻结布尔键沿用公共 R4 lifecycle adapter：建立时强制高优先级，既有 high、用户确认/升级、身份歧义和关键权益问题不允许机器关闭。

### 9.2 三段式 Query 草稿

每条 Query 必须绑定 subject/site、适用方案版本、计划访视/活动原文定位、决定性 actual records、EvaluationUnit 和 candidate/risk。生成行动项前必须冻结 `query_context=enrollment_not_occurred|enrolled_or_post_enrollment|enrollment_state_unresolved`，由可定位的随机、入组、首次给药和处置记录决定，不能由当前页面或模型猜测：

- `enrollment_not_occurred`：只请核实访视/评估/样本完成情况、筛选结论或数据记录，不写“评估是否构成方案偏离”；
- `enrolled_or_post_enrollment`：已明确随机、入组或接受研究干预后，才可追加 PD 评估措辞；
- `enrollment_state_unresolved`：先核实是否已随机/入组/接受研究干预及事件时序，明确当前资料不足，不写确定 PD 方向。

格式固定为：

```text
依据：写明适用方案版本、访视/评估/采样要求、计划锚点和允许窗口。
发现：写明具体名义访视、实际日期或缺失记录、支持依据、排除依据及仍存在的不确定性。
行动项：请核实、说明、补充或更正；只有 query_context=enrolled_or_post_enrollment 时，才可追加“如确认不符合方案，请评估是否构成方案偏离并按相应流程处理”。
```

合成示例（假设 `query_context=enrolled_or_post_enrollment`）：

```text
依据：方案 V2.0 规定第 4 周访视应在计划日 ±3 天完成，并在该访视采集样本 X。
发现：参与者 SYN-001 第 4 周访视实际记录为计划日后第 5 天，当前未见适用的改期或允许例外记录；样本 X 是否完成由独立活动单元评价。
行动项：请核实访视日期及改期记录；如确认不符合方案，请评估是否构成方案偏离并按相应流程处理。
```

系统只生成、编辑、可选用户确认和导出草稿；不发送、不跟踪回复/关闭，不创建强制待办。not_evaluable 只显示资料缺口提示，不伪装成 Query；一个 evaluation root 至多一个 D05 Query。

界面不得显示 `positive`、`candidate`、`formal fact`、`候选信号`、`正式事实`、`只读投影`、`规则引擎命中`、`后端`、`模型置信度` 等研发语言。

## 10. Patient Journey 共享访视轴投影

D05 提供 renderer-neutral 的 `VisitJourneyProjection`，不声称 R5 UI 已完成：

- 顶部固定访视轴同时显示阶段、cutoff、名义计划访视、实际接触、非计划/触发型访视和待定归属；
- 计划访视 marker 与实际 encounter marker 是不同对象，以 assignment edge 连接，不能压成一个“已记录事项”；
- 评估、样本、操作使用具体中文短标签；AE、MH、CM、IP、检验/检查等保持各自轨道与 producer identity；
- 一个计划访视跨多日/多次实体接触时显示一个计划节点和多个实际接触；一次住院承载多个计划访视时保留多个计划节点；
- 风险 marker 锚定实际日期/区间或名义计划窗口；日期缺失、冲突或归属未定进入独立待定区；cutoff 后事件进入独立 future/out-of-scope 区，不伪造时间点、不参与当前评价；
- 中高风险全部优先显示；形状、域名短标签和文字共同编码，不只靠颜色；重叠可聚类但点击后展开每个独立问题；
- 点击风险一跳到方案原文、计划规则、支持/排除依据、原始 listing、Query，以及共享时间窗中的 Profile/Timeline；筛选、缩放和页面跳转不得改变风险生命周期。

最小 marker：

```text
PlannedVisitMarker:
  marker_id/planned_visit_id/audience_name/phase
  nominal_anchor/window_start/window_end/date_precision
  status_hint=upcoming|due|evaluated|pending_assignment|pending_time
  source_locator_ids

ActualEncounterMarker:
  marker_id/encounter_id/encounter_kind/start/end/date_precision
  anchor_state=dated|partial|pending_time|out_of_cutoff
  assignment_id/audience_name/source_locator_ids

VisitRiskMarker:
  marker_id/audience_label/monitoring_priority
  anchor_kind/anchor_start?/anchor_end?/date_precision
  anchor_state=dated|partial|pending_time
  unit_id/candidate_or_risk_id/supporting_locator_ids
  counterevidence_locator_ids/query_ids/coverage_gap
```

所有双向 join 使用稳定 ID，不以相同日期、说明文字或访视名称替代。

## 11. 增量、修订与生命周期

1. 相同 accepted full snapshot、expected-set、规则/mapping/算法 lineage 和稳定事实重跑，unit/candidate/projection hash 确定且不重复建风险。
2. N+1 新增或修订实际记录仍命中同一稳定 obligation，风险持续并追加证据；普通 snapshot/revision 变化不改变 clinical identity。
3. 低/中风险只有在后续 accepted full snapshot、完整 closed coverage、相同身份与规则 lineage、精确 linked-negative 和显式 machine adjudication 下，才可 `resolved_by_data`。
4. high、用户确认/升级、rights/safety critical、身份歧义、关键冲突和 `machine_close_forbidden` 不机器关闭。
5. 方案修订、schedule/mapping/window/identity 算法或来源范围变化导致旧评价不可直接比较时使用 `superseded` 或终态 L3 `not_evaluable`，不得伪装为数据已解决。
6. 同一 actual object 或 planned obligation 的 identity 无法唯一延续时使用 `identity_ambiguous`，阻断自动 merge/close。
7. 本次 L1 not_evaluable 只 carry-forward 既有风险并显示 coverage gap，不产生新确定风险。
8. 用户后续新增自然语言特殊规则经受控拆解、来源/适用性/版本确认形成新 lineage 后，只影响新 Run；不回写旧结果。

## 12. 覆盖、计数与不变量

- `expected_units = positive + negative + boundary + not_applicable + not_evaluable`，每个 unit id 恰好一次；未来未到期计划不在该式中；
- `ScheduleGate` 不进入上述等式，当前 Run 单独满足 `current_run_gates = closed_resolved_gates + open_boundary_gates + open_not_evaluable_gates`；任一 open gate 阻断域完整性；
- L0 与 L1 正交；L0 partial/truncated/failed/missing 或任一 L1 not_evaluable 时不得声明 D05 医学完整；
- plan definitions、actual records、encounter bundles、visit/activity assignments、consumption ledgers、gates、evaluation units、candidates、risk instances、Query drafts、coverage notices 和 Journey markers 分别计数，不互相推导；
- 每个 positive 至少关联一个 D05 candidate/risk；negative 不创建新 candidate；boundary 至多创建一个明确保留不确定性的 clue；
- 每个 evaluation root 至多一个 candidate/risk/Query；activity occurrence 和 timing 是不同原子 root，不能以一条结果相互覆盖；
- 计划→实际与实际→计划 coverage 分别保存；任一方向缺失时不得声明活动链路完整；
- 每个 bundle member、actual activity consumption、typed anchor 和 interpretation 均可双向追溯且 canonicalized；未被允许的多重消费为 positive，未决多重解释为 gate/boundary；
- snapshot_as_of 与 clinical_event_cutoff 分别冻结并进入 Run lineage；out-of-cutoff actual 不进入 assignment/L1/L2/L3；
- producer-owned claim 不进入 D05 expected-set，且必须有一个 owner typed ref 或 routing gap；
- assignment、unit、risk、Query、Journey、bundle、ledger、typed anchor 的 subject/site/project/run binding 必须一致；wrong-subject、wrong-site、wrong-project、wrong-run/phase/episode 一律 fail closed；
- 中心/项目聚合只聚合个体结果与明确分母，不复制/改写风险 identity，不隐藏 high 或 coverage gap；
- Query 导出不等于发送，Journey 投影不等于风险建立，风险筛选不改变 L3；
- D05 复用公共 `contracts.py`、`lifecycle.py` 和 R2 状态机，不复制关闭逻辑。

## 13. 最小合成挑战矩阵

每一行须成为具名测试或确定性 fixture；除明确写“投影”外，均需断言 L0/L1/L2/L3 分层和稳定 hash。

| # | 挑战 | 预期 |
|---:|---|---|
| 1 | 唯一 active schedule、固定锚点、窗内访视 | negative |
| 2 | 唯一 active schedule、实际日期确定超窗 | `visit_overwindow` positive |
| 3 | 允许窗最晚端点早于 cutoff 且完整来源无访视 | `visit_missing` positive |
| 4 | 允许窗仍开放 | 不进入 missing expected-set；计划轴显示尚在窗口内 |
| 5 | 计划日期晚于 cutoff | 不进入 L1 分母，显示尚未到计划时间 |
| 6 | 适用方案版本缺失 | 单一 applicability gate not_evaluable |
| 7 | 两个修订版本均有完整适用依据 | 单一 applicability gate boundary |
| 8 | 最新修订仅适用于新入组，既有受试者继续旧版 | 选择旧版，不默认最新版本 |
| 9 | 下一访视后切换且该访视时点缺失 | applicability not_evaluable |
| 10 | 重新知情后切换且两种时点解释均有依据 | applicability boundary |
| 11 | 中心启用修订但既有受试者 grandfathered | 不自动切换 |
| 12 | 受试者研究臂/队列冲突 | applicability not_evaluable |
| 13 | phase 已明确结束，后续治疗期访视不适用 | not_applicable，保留依据 |
| 14 | 仅未见后续数据，未记录退出 | 不得推断 not_applicable |
| 15 | 死亡时点明确且后续 obligation 不适用 | not_applicable |
| 16 | 死亡日期冲突，后续计划是否适用未知 | not_evaluable |
| 17 | 撤回同意范围只禁止部分评估 | 仅相应活动 not_applicable，不批量关闭访视 |
| 18 | exact datetime 在 inclusive lower endpoint | 按冻结端点规则 negative |
| 19 | exact datetime 在 exclusive upper endpoint | 按冻结规则 positive |
| 20 | 端点包含性未定义 | not_evaluable，不默认包含 |
| 21 | 部分月日期区间全部在窗内 | negative |
| 22 | 部分月日期区间全部在窗外 | positive |
| 23 | 部分日期区间跨窗口边界且来源完整 | boundary |
| 24 | 实际日期角色完全缺失 | not_evaluable，不静默补日 |
| 25 | 两个权威实际日期冲突，且无已冻结的优先级或可行解释规则 | not_evaluable，不按最近日 |
| 26 | 跨午夜事件有完整时区 | 按 datetime 算法评价 |
| 27 | 跨午夜但时区缺失且可改变结论 | not_evaluable |
| 28 | Study Day 无 Day 0，基准日前一天 | 使用冻结换算，不产生 Day 0 |
| 29 | Study Day 0 语义未冻结 | not_evaluable |
| 30 | 固定 Day 1 计划中前访视延迟 | 后续窗口不自动顺延 |
| 31 | 明确链式“上次实际访视后 N 天” | 按前次唯一实际访视传播 |
| 32 | 链式锚点前次访视有两个完整、可行的 assignment | 依赖单元 boundary，不任选一个 |
| 33 | contingent visit VISITNUM 小于前访视但时间合法 | 不判错序 |
| 34 | 显式 planned_order 与实际次序确定矛盾 | `visit_order_inconsistent` positive |
| 35 | 只有文件行序不同 | 结果不变 |
| 36 | 只有字典/输入对象顺序不同 | expected-set/hash 不变 |
| 37 | explicit stable mapping 唯一 | assignment unique |
| 38 | 官方 code 唯一且版本/阶段一致 | assignment unique |
| 39 | 日期最近但 code/phase 不符 | 禁止最近日期吸附 |
| 40 | 两个计划访视均在日期窗且其他证据相同 | multi-feasible boundary |
| 41 | mapping 表缺失且仅名称相似 | not_evaluable |
| 42 | 实际明确为允许的非计划访视 | unplanned_supported，不建 positive |
| 43 | 实际自称计划访视但唯一可适用计划不一致 | assignment positive |
| 44 | 计划访视内发生额外非计划评估 | 按 activity rule，不强迫成计划活动 |
| 45 | 一个方案访视跨两天、两次实体接触且 merge rule 明确 | 一个计划节点、两个实际 marker、negative |
| 46 | 一个方案访视跨两次接触但 merge rule 缺失 | assignment not_evaluable |
| 47 | 一次住院承载两个方案访视且独立证据完整 | 两个 obligation 保持独立 |
| 48 | 一次住院被错误复用为两个访视的同一必需活动 | duplicate/assignment positive |
| 49 | 允许远程访视且记录完整 | negative，显示远程实际接触 |
| 50 | 方案要求现场但仅有远程记录，无已生效例外 | positive |
| 51 | 事后说明“已同意远程”但事件时未生效 | 不把问题改为 negative |
| 52 | 正式改期在事件前生效且范围匹配 | 作为 counterevidence |
| 53 | 改期记录 subject/site/rule 不匹配 | 不得作为 counterevidence |
| 54 | 取消访视但 obligation 仍适用 | occurrence positive，不自动 N/A |
| 55 | 方案正式取消该阶段访视且事件前生效 | not_applicable/superseded，保留 lineage |
| 56 | required assessment 完成且在独立窗口内 | occurrence/timing 两个 negative units |
| 57 | assessment 有结果但发生在错误访视窗 | occurrence negative、timing positive |
| 58 | assessment 未见记录且覆盖完整、已到期 | missing positive |
| 59 | assessment 表未提供 | not_evaluable，不判 missing |
| 60 | 实际 assessment 被两个 planned activities 同时使用 | assignment/duplicate positive |
| 61 | 允许 repeat assessment 且规则完整 | 不把重复判问题 |
| 62 | repeat rule 的必需方案来源角色缺失 | not_evaluable，不默认重复错误 |
| 63 | required sample 完成且采样时点窗内 | negative |
| 64 | sample accession date 与 collection date 不同 | 使用规则指定角色，不互换 |
| 65 | collection time 缺失但日级精度足以判窗内 | negative |
| 66 | 小时级窗口但 accepted source 只按日采集且该来源覆盖完整 | boundary |
| 67 | 样本补采被允许且明确绑定原 obligation | negative/counterevidence |
| 68 | 补采记录无 parent binding，仅日期相近 | 不得自动绑定 |
| 69 | 计划→实际通过，实际→计划发现额外错误标访视记录 | actual_assignment positive |
| 70 | 实际→计划通过，计划→实际发现另一个漏采 obligation | activity_missing positive |
| 71 | D06 疗效值异常但评估按时完成 | D05 negative；不得复制疗效风险 |
| 72 | D07 检验异常但采样按时完成 | D05 negative；不得复制检验风险 |
| 73 | D03 给药事件作为 visit anchor 且 typed ref 精确 | 可用于 D05 时间评价，不复制给药风险 |
| 74 | D03 anchor not_evaluable | 单一 anchor gate not_evaluable；依赖 obligation 不进正常 expected-set |
| 75 | D04 入排问题与同日访视问题 | 两个 owner identity，Journey 可并列，不重复 Query |
| 76 | D08 join 未验证，仅相同日期 | D05 不建立跨域关系 |
| 77 | owner routing 竞争 | 单一 routing gate，不在多域建 expected units |
| 78 | 方案计划自身两个确定的必需规则在所有允许解释下不可同时满足 | `schedule_rule_inconsistent` positive |
| 79 | 方案脚注缺失导致窗口算法不完整 | not_evaluable |
| 80 | window rule 版本改变，事实不变 | classifier 稳定、旧 lineage superseded |
| 81 | mapping algorithm 改变导致不同唯一归属 | identity_ambiguous/superseded，禁止 auto-close |
| 82 | N→N+1 补录同一访视，低/中风险有精确 linked-negative | 可按公共 gate resolved_by_data |
| 83 | N→N+1 本次来源不完整 | carry-forward + coverage gap，不关闭 |
| 84 | high 或用户确认风险后续补录 | 不机器关闭 |
| 85 | 同 snapshot 重跑 | unit/risk/projection hash 确定且不重复 |
| 86 | wrong subject/site/project/run typed join | fail closed |
| 87 | Query 缺依据/发现/行动项任一分句 | QC fail，不输出草稿 |
| 88 | not_evaluable 生成 Query | QC fail；只能 coverage notice |
| 89 | 界面 payload 泄漏 positive/candidate/正式事实/候选信号 | audience QC fail |
| 90 | Journey 把计划和实际压成单一“已记录事项” | projection QC fail |
| 91 | Journey 用 VISITNUM 作为触发型访视真实时间顺序 | projection QC fail |
| 92 | Journey 日期缺失事件被放到伪造日期 | projection QC fail，必须入待定区 |
| 93 | 中高风险重叠聚类 | 数量/身份不丢失，点击可展开 |
| 94 | 时间刷选/缩放 | 只改变显示，不改变 L1/L3 |
| 95 | 计划轴显示未来访视 | 可见但不污染 expected-set/风险分母 |
| 96 | 中心聚合复制个体风险 | join/QC fail |
| 97 | 单元 L1 数量与 candidate/risk/Query 数被互相推导 | accounting QC fail |
| 98 | L0 partial 但全部 L1 恰好 negative | 域仍不得声明医学完整 |
| 99 | 全部 L0 closed、五类 L1 完整且 not_evaluable=0 | 才可声明 D05 域完整 |
| 100 | fixture 含固定真实项目名/受试者/窗口或表字段 | isolation QC fail |
| 101 | 链式 anchor 缺失 | 单一 anchor gate；下游 obligation 不进正常 expected-set |
| 102 | 链式 anchor 有两种完整解释，一种在 cutoff 前成熟、一种未成熟 | anchor boundary gate，不生成 missing |
| 103 | accepted snapshot 含 cutoff 后实际访视 | 只进 Journey out-of-cutoff，不进 assignment/L1/风险 |
| 104 | 新 snapshot 晚录入一个 event-time 在旧 cutoff 前的访视 | 只影响新 Run，保留旧 Run，不回写 |
| 105 | routing gate 与 20 个受影响活动 | 只计一个 control-plane gate，医学 expected-set 为零 |
| 106 | applicability gate 有两个可行 schedule | 一个 canonical gate，输入顺序不改变 hash |
| 107 | 两个 encounter 合成一个 bundle，成员输入顺序交换 | bundle id/hash 和 L1 结果不变 |
| 108 | encounter 未经 split rule 同时进入两个 bundle | bundle/assignment QC fail closed |
| 109 | 同一 actual sample 被两个 obligations 消费且无 repeat rule | duplicate_consumption positive |
| 110 | repeat/resample parent 与允许 multiplicity 完整 | ledger 允许多重消费且可双向对账 |
| 111 | 三种 query_context | 只有 enrolled_or_post_enrollment 可出现 PD 评估措辞 |
| 112 | D03 typed anchor 同日但 wrong phase/episode | anchor gate，禁止日期近邻替代 |
| 113 | occurrence maturity rule 缺失 | gate/not_evaluable，不默认窗口最晚日 |
| 114 | merge/split/repeat 可行解释输入顺序交换 | interpretation ledger/hash 与结论不变 |
| 115 | rights_safety 且 actionability/recoverability 未知 | high + machine-close-forbidden；另列 coverage/context 提示 |
| 116 | open+resolved 或 closed+boundary gate 组合 | schema/QC fail closed |

## 14. 实现与验收边界

### 14.1 允许实现面

合同冻结后只允许在 `poc/medical_monitoring_ai_native_r4` 的合成/离线 R4 包中新增 D05 领域对象、evaluator、fixtures、projection 和测试；公共文件只允许为复用既有 identity/lifecycle/typed join 做最小、行为保持的适配，并必须跑 D01-D04、R2、R3 相邻回归。

禁止：启动 8911；运行真实项目；调用真实 provider；修改 R1-R3 冻结语义、R5 UI、产品服务、医学写作子系统；建立正式 PD workflow；扩展系统安全设计/测试。

### 14.2 完成证据

1. 合同经隔离的新上下文反证审阅并由 Codex 冻结；
2. 116 行挑战矩阵全部有具名 fixture/测试或明确、经接受的拆分映射；
3. D05 聚焦测试、R4 全量、R2、R3、Ruff、compileall、确定性重跑和 audience payload QC 通过；
4. expected-set、assignment、L1、L2、L3、Query、Journey join 不变量通过；
5. D03/D04 producer stub 被真实 D05 typed producer surface 替换或明确保留兼容边界，不产生重复风险/Query；
6. 8911 仍停止，真实项目未运行，医学写作文件无改动；
7. 独立 verifier 以冻结 hash 接受，Codex 写入 acceptance record、R0-R8 与 LOOP ledger。

### 14.3 非完成声明

D05 合成纵切通过不等于 R4 总体、R5 Patient Journey UI、真实项目、真实模型、多中心聚合、产品或商业化接受。

## 15. 冻结记录

冻结状态：`FROZEN_R4_D05_CONTRACT_V1_2`。同一独立审阅 session `019ff2c3-128a-7471-bedd-2894201fdf32` 已接受 v1.1 临床/算法语义 SHA `7d20dadd...c4fa`，并对 v1.2 路径勘误 SHA `0c7eb9d5bd9e3fc9ab845715ba2121249ce99d56ee3c11edf7404fa2aae9c265` 给出 `ACCEPT_PATH_ERRATUM`。本行与顶部状态是接受后由 Codex 写入的冻结元数据；最终文件 SHA 记录在 acceptance record。接受仅限 synthetic/offline D05 合同语义及 R4 实现路径，不等于代码或产品接受。
