# R4-D08 多表医学逻辑与数据质量纵切合同 v0.6

日期：2026-08-14  
状态：`REVISED_DRAFT_FOR_TYPED_INPUT_KEY_REVIEW_ROUND6`  
范围：仅隔离、合成、离线 R4 POC；未冻结，禁止据此进入实现。

## 1. 目的与用户价值

D08 不再重复判断 AE、MH、CM、IP、方案、访视、疗效或检查本身是否构成风险；它只检查这些已由 D01-D07 解释的记录之间是否存在可定位的显式关系缺口、关系 cardinality/反向守恒、跨表身份错配、无人拥有的确定性时间矛盾或来源修订消费版本断裂。用户看到的必须是具体中文问题，例如“跨表引用无法反向定位”“同一来源身份出现在不同受试者”“记录修订后派生结果未同步”，并能一跳查看可见的参与记录和同一受试者访视轴。“用药适应证未找到对应 AE/MH”等医学匹配仍由 D02/D01 owner 处理，D08 不重复生成风险或 Query。

## 2. 来源与方法决定

### 2.1 本地权威

- `reviews/medical_monitoring_r4_risk_coverage_matrix_v1_20260810.md` D08 及共同风险合同；
- 已接受 D01-D07 合同、coverage、public risk identity、Query、Journey/source-jump 和 shared temporal spine；
- R2 accepted snapshot/source revision/lifecycle/adjudication binding；
- R3 active mapping、data specification、rule/knowledge lineage 与部分日期合同。

### 2.2 外部一手参照

- [CDISC SDTM v1.7 §4](https://www.cdisc.org/standards/foundational/sdtm/sdtm-v1-7/html)：记录关系必须由 subject、domain、identifying variable/value、relationship ID/type 等显式标识；RELREC 说明有关联，但不自动说明关系的医学性质。
- [CDISC SDTMIG v3.3](https://www.cdisc.org/standards/foundational/sdtmig/sdtmig-v3-3/html)：跨域关系、link/reference identifiers 与来源记录需要可追溯，不能只靠文本相等。
- [OpenLineage column lineage](https://openlineage.io/docs/spec/facets/dataset-facets/column_lineage_facet/)：派生字段应保留输入字段和 transformation lineage；本合同只借鉴 lineage 语义，不引入其运行库。
- [Great Expectations data integrity](https://docs.greatexpectations.io/docs/reference/learn/data_quality_use_cases/integrity/)：跨表完整性必须显式比较两个数据源/关系，而非把单表通过等同跨表一致；本合同不采用其执行依赖。

### 2.3 技术路线

不新增外部依赖。D08 使用 typed relationship graph：不可变 record nodes、版本化 relation rules、方向明确的 expected edges、实际 edges、时间比较证据和 modification lineage。图只组织确定性比较及证据，不把模型输出写成关系事实；模型只能提出需由 typed rule 和来源验证的候选关系。

## 3. Owner 边界

| Owner | 独占职责 | D08 允许消费 | D08 禁止 |
|---|---|---|---|
| D01-D07 | 各域记录医学解释、L1 disposition、域风险/Query/Journey marker | accepted/current record identity、coverage、evaluation unit、risk/issue refs、typed handoff | 重算 CTCAE、AE/MH 归类、禁用药、依从性、PD、访视、疗效或检查风险 |
| D08 | 跨表关系、时间逻辑、孤立引用、重复/错配、修订传播 | 上游 typed handoff 和 accepted source records | 以字符串/模型投票覆盖上游 owner；正式认定 PD；关闭上游风险 |
| D09-D10 | 中心/项目聚合 | D08 已验证个体关系风险和 coverage | D08 生成中心/项目分母或模式 |

D08 只继承本 rule `required_producer_domains` 的 L0 coverage/accepted-current 状态与 D08 自身实际消费的 identity、日期精度、单位/semantic normalization、mapping/lineage 完整性。参与记录的上游 L1 `not_evaluable/boundary` 不自动继承；只有该上游缺口与 D08 rule 的 operands/consumed fields 相交并足以改变 D08 判断时，D08 unit 才为 `not_evaluable/boundary`。本文“上游域不完整”仅指上述 L0 或 D08 实际消费缺口，不包括无关的上游医学评价缺口；不得把 coverage 未知误作“没有可比较记录”或 negative。

### 3.1 `D08OwnerRoutingDecision` 闭集

每个候选问题先产生 routing decision：`candidate_problem_kind`、left/right role、`clinical_claim_token`、`owner_domain`、`d08_action`（`evaluate_and_own/consume_only/handoff_only/context_only/routing_gate`）、risk/query owner、required producer domains、rule version/hash、locators。唯一 D08-owned 类别为：显式 link/RELREC-like resolve、反向/cardinality 守恒、跨文件/受试者身份碰撞、没有其他域 owner 的已识别记录确定性时间矛盾、source revision 与派生对象声明的 consumed revision 不一致。其余 D01-D07 医学 claim 一律 `consume_only`，生成零个 D08 医学 unit、风险和 Query。无法唯一路由时生成一个不计入医学 expected-set 的 routing gate，阻断域完整性。

`clinical_claim_token` 是规范性闭集：`d02_cm_indication_match`、`d02_treatment_without_event`、`d03_trigger_action`、`d03_assignment_exposure`、`d05_planned_actual`、`d06_score_baseline_timepoint`、`d04_criterion_waiver_pd`、`d01_seriousness_hospital_death`、`d08_explicit_link_resolve`、`d08_reverse_cardinality`、`d08_identity_collision`、`d08_unowned_temporal_impossibility`、`d08_propagation_lineage`、`d08_routing_or_coverage_gate`。只有 `d08_*` token 可设 `d08_action=evaluate_and_own`；“expected edge 缺失”只可在 `owner_domain=D08` 且 token 为 `d08_explicit_link_resolve/d08_reverse_cardinality` 时进入医学 expected-set。

涉及 authorized alternate/waiver 时，相关 owner 必须向 D08 提供 `D08WaiverAlternateHandoff`：`handoff_id/project_ref/run_ref/subject_ref/site_ref/scope_binding_id/cutoff/owner_domain/relation_rule_id/anchor_stable_identity/closure_state=full_set|explicit_empty|missing/authorized_object_refs/authority_locator_ids/producer_version/lineage_hash`。`full_set` 必须列全对象，`explicit_empty` 必须有 scope/rule locator 且 refs 为空，`missing` 不得带 refs；禁止第四状态。D08 只消费该 handoff，不读取或重判 owner L1 文本；`missing` 时相应 D08 unit 为 `not_evaluable`，不得假定“无 waiver”。

上述闭集中的 owner 映射为：CM indication↔AE/MH 由 D02/D01；IP action↔AE/检查由 D03；assignment↔exposure 由 D03；planned↔actual visit/activity 由 D05；efficacy score/baseline/timepoint 由 D06；criterion/waiver/PD-like claim 由 D04；hospitalization/death/seriousness↔AE 由 D01。D08 只可消费这些 owner 的 verified-link/assignment/handoff 对象，不得重判。

## 4. 冻结前必须定型的 typed 对象

### 4.1 `D08RecordNodeIdentity` 与 `D08RecordNodeEnvelope`

稳定 identity 只含 project/subject/site、domain、semantic role、上游已验证的 stable source record/event/treatment identity 与 correction-chain head；禁止 run/snapshot/revision/row/locator、L1/L3/risk/query/audience/model text 进入稳定 identity。Envelope 另存 run/snapshot/source revision、record status、time/visit refs、accepted source field values、unit/value/role、locators、cutoff scope decision、producer-consumption bindings 与 content hash。D08 不从文本重新推导事件/药物/治疗 identity。

`D08CutoffScopeDecision.decision` 闭集为 `in_cutoff/out_of_cutoff/spans_cutoff/time_missing_not_evaluable`，引用共享 D05 策略并区分 `snapshot_as_of` 与 `clinical_event_cutoff`。优先级固定为：rule 含时间 operand 且任一 required member 为 `time_missing_not_evaluable` 时，恰好一个 unit 为 L1 not-evaluable，不再生成 cutoff boundary gate；其余成员时间均可判定后，全体 out-of-cutoff 时不生成医学 unit，仅作不带风险的 Journey 上下文；单节点 spans-cutoff，或同一 explicit relation/anchor evidence set 同时含 in/out/spans 成员时，恰好生成一个 `routing_or_coverage_gate(signal_type=cutoff_boundary_gate, L1=boundary, counts_in_medical_expected_set=true)`，不得生成 positive/not-found。out-of-cutoff 节点不得作为 expected-set anchor、evidence member 或“当前可匹配节点”。只有 in-cutoff、L0 covered、operands 可比较且零 in-cutoff match 才能进入 not-found。expected-set admission 必须先执行该决定，跨 cutoff 本身不得产生医学 positive。

clinical cutoff 约束医学事件有效时间，不约束数据更正发生时间：一个 in-cutoff accepted node 在 snapshot-as-of 内形成的新 source revision，仍必须进行 consumed-revision 传播一致性检查；若同一 stable node 的 accepted correction 将事件有效时间从 in-cutoff 改为 out-of-cutoff，仍生成一个 propagation unit，用于验证下游对象已更新、退休或 superseded，不得静默消失；只有首次出现且全体医学事件有效时间 out-of-cutoff 的新节点不生成医学 propagation unit。不得把“修订发生在 cutoff 后”误作“事件有效时间 out-of-cutoff”。

节点只可来自 accepted-current source record 或显式历史/correction node。模型生成文本不是 record node。

### 4.2 `D08RelationRule`

字段至少包括：rule ID/version/hash、owner routing ref、clinical relationship type、left/right role constraints、`unit_anchor_role`、`evidence_set_role`、unit grain、typed cardinality、directionality、identity operands、time operands、shared precision、unit/semantic normalization preconditions、expected/forbidden/optional relation、required producer domains、applicability window、authority locator、fanout cap、duplicate policy、owner domain、algorithm version。

项目特异窗口、角色、允许重叠、expected link 和更新传播规则必须来自 active mapping/protocol/data specification/rule package，禁止内核硬编码。

### 4.3 `D08CardinalitySpec`、slot 与 expected unit

Cardinality 明确 left/right min/max、unbounded flag、unmatched/overmatch policy、bidirectional/reverse-required；其 `unit_grain` 必须与 unit grain 完全相等。`unmatched_required_policy` 闭集为 `positive_missing_required/not_evaluable_coverage/not_applicable`；`overmatch_policy` 闭集为 `positive_forbidden_edge/boundary_multi_model/allowed`。空 counterpart 是 typed `D08ExpectedSlotNode`，不是虚构 record。

允许 unit grain 仅为：`per_left_anchor_slot`、`per_right_anchor_slot`、`per_explicit_rel_instance`、`per_propagation_derived_object`、`routing_or_coverage_gate`。禁止笛卡尔 pair。`D08RelInstanceMembership` 保存一个 `rel_instance_id`、至少 2 个按 stable identity 规范排序的 member IDs、全部 raw link IDs 及其 bijection；N 元 RELID 恰好生成一个 `per_explicit_rel_instance` unit，pairwise observed edges 仅为证据，绝不另生成 units。“两端”只描述单条 directed observed edge，不描述 explicit relation unit。普通 one-to-many/many-to-many 以义务侧 stable identity 为 anchor 生成一个 unit，evidence side 为 set；若候选集合超过 rule package 的 `max_unidentified_fanout` 且 evidence side 无唯一 identity/RELID，只以该义务侧 stable identity 生成一个 `unit_grain=routing_or_coverage_gate, signal_type=identity_fanout_exceeded, L1=not_evaluable` gate。若义务侧 stable identity 本身缺失，则停在全局 identity admission gate，不生成 L1 unit；不得用行号、候选顺序或运行时字段补 identity。fanout 上限只决定证据可评价性，不改变 unmatched 医学语义；上限/规则版本变化按 superseded lineage 处理。内核只允许一个防资源耗尽的最大上限，项目规则只能更低，该上限不参与医学阈值判断。

```text
unit_id = hash(
  project_id,
  domain_id=D08_cross_domain_logic,
  scope_type=subject, scope_key,
  normalized_concept_or_rule_item=(relation_rule_id, unit_grain,
    anchor_stable_identity_or_explicit_rel_instance_id,
    relation_slot_kind, signal_type),
  temporal_window=(window_kind, rule_window_id_or_none),
  rule_or_knowledge_lineage,
  unit_algorithm_version=d08_unit_v1
)
```

`relation_rule_id` 与 `window_kind/rule_window_id` 均为版本无关的稳定身份；computed dates、interval endpoints、precision 和比较结果只进入 comparison/envelope，不进入 temporal-window identity。Evaluation `unit_id` 按冻结矩阵包含 lineage 与 algorithm version；另设版本无关 `D08UnitStableCore`，排除 lineage/version/computed dates/run/snapshot/revision，用于跨 run 对齐。规则/mapping/identity/algorithm 变更产生新 `unit_id`，旧 unit 在下一 expected-set 中 superseded，由 stable core 连接，绝不记为 `resolved_by_data`。每个 unit 恰好一个 L1 disposition；edge 数与 unit 数分别计量。

每个 positive unit 在建立风险前必须生成 `PublicR4RiskIdentity(domain_id=D08_cross_domain_logic, public_identity_version=d08_public_v1)`；其 stable source/event identity 为 explicit relation instance 或 obligation-side anchor，normalized concept 为 stable core 的 classifier/grain/rule/slot/signal，temporal window 仅含稳定 window kind/rule window ID。canonical tuple/hash 字段与公共 R4 合同一致，禁止与 D01-D07 identity 合并。数据值/日期修订保持 public stable classifier 并更新 envelope；规则 lineage 改变按 R2 supersession 连接，不得伪装为数据关闭。L2 分别计数 source records、relation units、clues、risks、queries、handoffs；positive unit 至少绑定一个 current clue 或 active risk。

### 4.4 关系证据

- `D08RawLinkRecord`：保存原始 subject/domain/IDVAR/IDVARVAL/RELID/RELTYPE、locator/hash；RELREC-like association 不等于医学性质。
- `D08ResolveDecision`：raw link 解析为 stable nodes 的 `unique/ambiguous/not_found/wrong_subject_or_site/not_evaluable`，保留 rejected candidates；raw↔materialized 显式 link 必须 bijection。若 counterpart role 属于 required producer domains 且其 L0 为 `missing/partial/truncated/not_evaluable/failed`，status 与 L1 必须为 `not_evaluable`，不得变成 not-found/positive。若唯一 counterpart candidates 为 out-of-cutoff，status 不得为 unique/not-found，且不应用 unmatched policy，而按全体 out-of-cutoff 或 mixed-membership cutoff 规则处理。仅当 counterpart in-cutoff、L0 covered、identifying operands 可比较且当前节点零匹配时才是 `not_found`。`not_found` 只有在 reverse-required/min≥1、typed owner handoff 已闭合证明无授权 alternate/waiver 且 unmatched policy 为 `positive_missing_required` 时为 positive；其余两种闭集 policy 分别落 not-evaluable 或经 locator 证明的 not-applicable。
- `D08ObservedEdgeIdentity`：rule、directionality、稳定两端、direction、explicit relationship instance 与 recorded operands；directed/bidirectional 不能 canonical-sort 后丢方向，undirected 才排序。Envelope/locators 与稳定 content hash 分离。
- `D08BidirectionalJoin`：显式 forward/reverse edge refs，守恒比较始终在完整 evaluation node/edge set 上执行；blinded/forbidden 节点仍参与内部 forward/reverse 计数和 identity 集合。audience projection 仅省略节点/边渲染，不改变 join 结果。
- `D08TemporalComparison`：两侧原始日期/区间、精度对、时区、端点开闭、共享精度、比较操作，先计算 active rule 下全部可行的规范关系集合。缺必须时区时 primary result/reason 固定为 `timezone_incomparable`；否则集合为空且原因是 operands/precision 缺口为 `precision_insufficient`。集合恰含一个关系时才可取 `before/equal/after/overlap/contains/contained_by`；集合含两个及以上可具体刻画的候选关系，或同日无时刻导致多个次序时为 `indeterminate`。range-end < point 或 range-start > point 可跨精度形成单一先后；不得以区间相交即直接判 determinate overlap。active rule 必须声明单一 `expected_relation` 或显式 `allowed_relation_set`；singleton result 属于允许集合才为 negative，否则为 positive。`contains` 与 `contained_by` 方向不同、不可互换，`overlap` 不自动满足包含要求；`indeterminate` 为 boundary；`precision_insufficient/timezone_incomparable` 为 not-evaluable。
- `D08IdentityComparison`：逐 operand 的 equal/different/unknown 和最终 `matched/distinct/ambiguous`。
- `D08ModificationPropagation`：source revision/correction chain、`change_cause=data/rule_or_mapping/algorithm`、changed fields、derived consumed fields/intersection、旧/新派生对象、声明/实际消费 revision、lineage fingerprint、结果 `in_sync/stale/derived_missing/producer_not_evaluable/ambiguous_chain`。可检查的 `derived_object_type` 闭集仅为 `producer_declared_derived_value/producer_declared_grade_ref/producer_declared_trend_ref/producer_declared_relationship_ref`，这些对象必须携带 declared consumed revision；严禁 Query draft、Journey marker、risk instance、L1/L3 disposition 进入传播检查。同一运行同时含数据和规则变化时拆成两个 propagation units：数据传播 unit 与 lineage supersede handoff；D08 不直接改变 R2 lifecycle。
- `D08RelationEvidence`：supporting/counterevidence/context，必须绑定 unit 与节点。
- `D08ProducerConsumptionBinding`：producer object ID/hash/version、purpose、permitted outputs、scope equality；producer L1/L3/risk/query 不进入 node/edge hash。
- `D08DuplicatePolicy`：versioned dedup keys、raw/materialized mirror exemption、stable-event collision semantics、modeling-rule ref。
- `D08VisibilityDecision`：分 evaluation/projectable sets；audience source nodes 只能来自 projectable set。projectable set 为空时省略 audience payload/edge，但保留 L1/clue/risk identity且不阻断 Subject Journey；义务节点不可投影而 counterpart 可见时，以首个可见 member 为 audience anchor，仅显示“跨表引用无法反向定位/数据更新待核实”，不得暗示隐藏治疗记录。
- `D08RelationshipRef` 精确字段为：`ref_id/producer_domain=D08/project_ref/run_ref/subject_ref/site_ref/episode_key/monitoring_mode/source_revision/accepted_snapshot_ref/scope_binding_id/cutoff/left_stable_identity/right_stable_identity/relationship_type/validation_state=validated/producer_version/source_locator_ids/lineage_hash`；scope/producer lineage 必须与 D06 consumer 精确相等。

## 5. Pre-evaluator fail-closed 顺序

1. run/snapshot/source revision/cutoff identity；
2. subject/site/shared-spine identity；
3. 本 rule `required_producer_domains` 的 L0 coverage 与 accepted-current status；不相关域不阻断；
4. active mapping/data specification/rule authority version/hash；
5. record node identity/hash/source locator；
6. rule applicability、role 与 cardinality；
7. time refs/precision/timezone 和单位/semantic normalization；
8. correction chain 与 lineage 完整性；
9. owner routing、raw/materialized resolve 与 expected-set generator admission/hash；
10. deterministic relation evaluation。

全局 schema/hash/scope/authority/identity/expected-set generator admission 失败只输出 integrity/coverage 缺口，不得输出任何 L1、风险、Query 或 Journey risk marker。已成功生成 expected set 后，单个 unit 的 applicability/cardinality/time/lineage 缺口进入该 unit 的 `not_evaluable`，仍参与守恒式。

## 6. 医学评价语义

### 6.1 `positive`

- 没有其他域 owner 的已识别记录明确不可能先后/重叠；
- 同一 upstream stable identity 在不同 subject/site/source role 间冲突；
- owner routing 已确认由 D08 拥有、required producer L0 covered 且 unmatched policy 明确要求的 expected edge 缺失，或 forbidden edge 存在；
- 显式引用无法反向找到当前节点，或双向关系不守恒；
- 内容相同且身份/时间/来源重复，或同一身份被错误分配至不同 subject/site/treatment role；
- accepted source 修订后，`changed_fields ∩ declared_consumed_fields` 非空，且允许的 producer-declared 派生对象为 `stale/derived_missing`。

### 6.2 `negative`

参与域 coverage 完整、身份/时间/单位/语义/修订 lineage 可评价，且全部 required/forbidden/cardinality/propagation 检查完成并一致。仅“未命中规则”不成立。

### 6.3 `boundary` 与合法多记录建模

同日无时刻或跨精度区间重叠、无权威 modelling rule 的拆分/合并、多记录、别名或修订身份迁移，但两侧仍有足够证据具体刻画两种候选关系时为 boundary。输入缺口无法刻画候选关系或缺必须时区时为 not-evaluable。若 active mapping/data specification 明确定义 split/merge/mirror/multi-record modelling 且记录符合，则为 `negative + counterevidence` 并绑定 `modeling_rule_ref`，不是 boundary。

### 6.4 `not_applicable`

active rule/data specification 明确证明该关系对当前设计/阶段/角色不适用，且给出适用性 locator。空表、无匹配或缺域不是不适用。

### 6.5 `not_evaluable`

本 rule required producer 的 L0 coverage、D08 实际消费的 identity/mapping、日期精度/时区、单位、关系规则或修改 lineage 不完整，且缺口足以改变判断。无关的上游 L1 医学评价缺口不继承。

## 7. D08-owned 关系族与 consume-only 邻接目录

1. explicit source links/RELREC-like raw resolve、reverse/cardinality conservation；
2. duplicate/identity collision across files, sheets, revisions and subjects/sites；
3. source/correction revision ↔ derived object declared consumed revision（只比较 lineage，不重算医学结果）；
4. 已识别 record 之间且 D01-D07 无 owner 的 deterministic temporal/state impossibility；
5. owner routing/coverage/visibility gate。

AE/MH↔CM、检查↔IP action、assignment↔exposure、planned↔actual、efficacy↔timepoint、criterion/waiver、hospitalization/death↔AE 仅为 consume-only adjacency catalog。D08 可验证其显式 refs 是否可解析/守恒，但医学 match/missing/action claim 仍由 D01-D07 owner；不得生成第二份风险或 Query。

每个 D08-owned 类必须有五类 disposition、counterevidence、hidden、false-positive、false-negative cases；consume-only 类必须断言零 D08 风险/Query。

## 8. 时间、单位与身份不变量

- 日期比较使用 R3 不确定区间；跨精度只有在区间完全可分离时才确定先后；区间重叠但可具体刻画候选次序为 `indeterminate→boundary`，输入缺口不能刻画候选次序才为 `precision_insufficient→not_evaluable`，不得截断或补日。
- 区间使用开闭端点、部分日期不确定区间和方案规则；同日无时间时不得判“先后错误”。
- 单位换算只使用版本化 authority；无法转换则 not-evaluable，不比较数值。
- 文本相等不是身份。匹配必须使用版本化 operands；别名/标准化结果是证据之一，不是唯一键。
- subject/site/project/run/snapshot/correction lineage 不相等时禁止合并。
- edge 是否排序取决于 directionality；stable identity/hash 排除 run/snapshot/revision/locator，envelope hash 另存；所有 edge 可反向定位。

## 9. 输出、Query 与 Patient Journey

- D08 只生成具体“跨表关系待核实/数据更新待核实”风险，不显示“正式事实”“候选信号”“关系图节点”等研发语言。
- 三段式 Query 固定为“依据＋发现＋行动项”，引用全部参与记录和规则；PD 语义仍仅为“请核实是否为 PD”。
- Journey 不新增通用事件。它高亮既有 AE/MH/CM/IP/检查/疗效/访视/住院等 marker 之间的关系线或风险锚；每端可一跳到来源。
- evaluation node set 可大于 projectable node set。只有两端均 projectable 才画 relation edge；单个 edge 被阻断不得清空 Subject Journey 的其他可见 marker。错误 subject/site/scope/hash 仍使该 relation payload fail-closed。
- blinded/forbidden 节点完全从 audience payload、Query 与可视化边中省略，不显示“存在隐藏记录”的占位；省略仅发生在 audience projection，不能改变内部 join/守恒结果。缺链风险只锚定义务侧可见节点，显示“未见对应记录/数据更新待核实”，不制造 phantom node。
- 义务侧不可见但至少一个 counterpart 可见时，audience anchor 取规范排序后的首个可见 member，文案只说明“跨表引用无法反向定位/数据更新待核实”；projectable set 为空时不生成 Query/Journey marker，但不删除内部 L1/clue/risk identity。
- D08 风险不能复制成多个上游域风险，也不能回写上游事实计数。

## 10. 增量与修订

- 当前全量 listing 与上次 accepted baseline 以 revision-free stable record/event identity 与 correction chain 比较；不得依赖行号。
- 新增、修改、删除/失效、拆分、合并分别记录；关系 unit lineage 必须可解释。
- 仅 changed fields 与 derived declared consumed fields 交集非空才产生数据传播义务；交集为空为 not-applicable。交集非空且 consumed revision 旧为 positive `propagation_stale`；producer not-evaluable 则 D08 not-evaluable。D08 禁止重算 grade、AE/MH class、adherence、PD、visit assignment 或 efficacy score。
- 规则/mapping/identity algorithm 改变使用 superseded lineage，不能伪装成数据修复。
- 规则版本改变时新旧 unit_id 不同但 `D08UnitStableCore` 相同；跨 run expected-set diff 必须以 stable core 识别 superseded lineage，旧 unit 的消失不得进入 resolved-by-data。
- 低/中风险关闭仍由 R2 lifecycle/adjudication owner 执行；D08 仅提供证据与建议。

## 11. 可执行守恒式

- `expected_units = positive + negative + boundary + not_applicable + not_evaluable`；
- 每个 positive 至少一个 supporting evidence 和两个以上参与 record/expected slots；
- 每个 negative 保存完整 checked edge set 与 counterevidence（若曾有候选）；
- typed cardinality 的 expected/observed 数量守恒；双向 link 的 forward/reverse 计数与 identity 集合相等；空 expected slot 可作为 positive 的第二参与 slot；
- 每个 propagation unit 的 source revision 必须等于派生对象消费 revision；
- Query、risk、Journey marker 的 source node 集合必须是 relation unit 的 projectable node set 子集；只有 audience payload 存在时才要求非空。projectable set 为空时允许内部 L1/clue/risk identity 无 audience source node；
- 只有 rule.required_producer_domains 中相关上游的 `partial/truncated/not_evaluable/failed/missing` 阻断该 unit；不得被 negative 覆盖，也不得全域连坐。

## 12. 合成挑战矩阵冻结要求

冻结前形成精确分区的独立 typed cases（目标不少于 200，而非只满足总数），且全部具备 exact-key immutable typed input、独立 expected-outcome oracle、可执行 assertion DSL 和 manifest registry。`D08TypedFixtureCatalog` 顶层 exact keys 为 `catalog_id/version/case_count/catalog_hash/cases`；每个 case exact keys 为 `case_id/family_id/grain/owner_route/clinical_claim_token/disposition/fixture_id/fixture_hash/oracle_case_id/manifest_case_id/expected_leaf_set/expected_trace_leaf_set/expected_source_leaf_set/mutation_class/audience_contract/typed_input`。`typed_input` 必须是完整、不可变、可独立哈希的对象；catalog 中三个 expected leaf-set keys 固定为 `null` 占位，真实 expected leaves 只存在于独立 oracle，generator/runtime 不得从 `disposition` 或 typed input 推导它们。registry bijection 列固定为 `case_id,fixture_id,oracle_case_id,manifest_case_id,test_id`。规范 synthetic scope 为 `SYN-D08-PROJECT/SYN-D08-RUN-001/SYN-D08-SUBJECT-001/SYN-D08-SITE-001`，cross-subject collision 另用 `SYN-D08-SUBJECT-002`：

- 5 个 D08-owned 类各至少 9 例：五类 disposition、counterevidence、hidden、FP、FN；
- D01-D07 owner-routing consume-only/zero-risk 至少 14 例；
- 时间精度/时区/区间端点至少 20 例；identity/duplicate/split/merge/cross-subject 至少 20 例；
- correction/propagation（含 data、rule、algorithm、同 run 拆分 units、consumed-field intersection、stale ref）至少 24 例；
- Query/Journey/source-jump/disclosure 至少 16 例；integrity/hash/scope/version/coverage 至少 20 例；
- raw↔materialized resolve/bijection 至少 12 例；double replay drift 至少 4 例；fanout gate 至少 4 例；
- cutoff 专项至少 4 例；covered-zero/not-found、uncovered/not-evaluable、N 元 RELID 单 unit、hidden obligation、日期修订保持 public stable classifier、规则变更 superseded 各至少 2 例；
- cutoff 必备 oracle：全体 out-of-cutoff→零医学 units；mixed membership→恰一个 cutoff boundary gate；单节点 spans-cutoff→同一 boundary gate；in-cutoff/covered/zero-match→保留 not-found 路径；time-missing 与 mixed 同时存在→恰一个 not-evaluable 且无 boundary gate；同一 stable event 从 in-cutoff 更正为 out-of-cutoff→保留 propagation unit。另含 in-cutoff event 在 cutoff 后发生 source revision 的 propagation 例，以及内部 blinded join 守恒但 audience 省略的例。
- 时间关系 oracle 必须覆盖 `expected contains × observed contained_by→positive`、显式双向 allowed set、overlap 不满足包含、时区与 precision 同时缺失时 primary reason=`timezone_incomparable`。
- 至少 12 个 hidden/anti-overfit cases 改变项目/表/字段名、顺序与非医学版本字段但保持 substantive relation semantic。

Substantive relation input 排除 run/snapshot/revision/version string/wall-clock，但包含 accepted source values、stable identities、rule semantic operands、cardinality；同 substantive input 不得对应不同医学结果。必须包含离开 fixture 的规则参数变异、raw/materialized 两种表示与 bijection、确定性双遍 `D08ReplayManifest`（排除 wall-clock/PID/mtime）、runtime 不得读取 oracle/registry 的静态闭包。禁止真实项目/药名、固定 listing/字段名、行号 join 和 oracle expected text 进入规则/fixture identity。

## 13. 冻结门

1. 合同、catalog、oracle、registry、generator 各自 file/content/semantic hash；
2. 全字段 schema、exact key set、交叉引用、hash、scope、cutoff、coverage、authority 验证；
3. 独立医学/工程 verifier 能以负向变异推翻错误关系、错误 negative、错误 propagation；
4. D01-D07/R1-R3 相邻回归；
5. 8911 停止、无真实项目、无产品/UI/医学写作改动；
6. 只有独立 verifier 对同一不可变快照 `ACCEPT_D08_CONTRACT` 后才改状态为 frozen 并允许实现。

## 14. 本轮独立审阅重点

- owner routing 是否确保 D01-D07 claim 零重复；关系 unit 是否严格 anchor/RELID grain、禁止多对多组合爆炸；
- “缺少预期关联”是否有可冻结分母，避免把空数据误报；
- 修改传播能否区分数据修改与规则/mapping/算法变更；
- Journey 关系线是否会泄漏不可见节点或产生跨 scope 链接；
- D08 是否越权重判 D01-D07 医学语义；
- 不少于 200 例的精确分区是否足以覆盖核心误报/漏报而不依赖项目名/固定表名。
