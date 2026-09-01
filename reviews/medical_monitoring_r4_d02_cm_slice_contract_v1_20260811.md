# R4-D02 CM 用药合理性、适应证与禁限用药切片合同 v1.1

日期：2026-08-11  
状态：`FROZEN_R4_D02_CONTRACT_V1`  
适用范围：医学监查 AI-native 隔离 R4-D02；仅合成/离线输入；不代表产品、真实项目、真实词典或临床结论就绪。

## 1. 目标与边界

本切片把 CM 记录、方案禁限用药条款、版本化药物身份依据、AE/MH/诊断和研究阶段连接为可覆盖、可追溯、可增量重算的医学监查单元，形成：

- “用药依据待核实”“禁限用药待核实”“用药信息与方案要求不一致”等具体风险；
- 支持依据、排除依据、原始 CM、方案条款和药物身份依据的一跳关联；
- “依据＋发现＋行动项”三段式 Query 草稿；
- 受试者医学旅程中的 CM 区间事件和风险锚点；
- N→N+1 的持续、补充信息后解决、规则版本变化和身份歧义处理。

本切片不把 CM 当作 IP/EX/EC/DA，不正式判定或报送 PD，不从商品名猜成分/类别，不把模型解释当作药物身份或方案条款，不调用真实项目、真实 provider 或产品服务。

## 2. 来源权威与方法决定

1. 上游权威为 `FROZEN_R4_CONTRACT_V1` 的共同合同和 D02 行，以及已接受 R1 coverage、R2 source/identity/lifecycle/acceptance、R3 mapping/rule/knowledge 公共合同。
2. accepted listing 只说明“记录了什么”；active protocol/rule pack 说明“要求是什么”；受控词典绑定说明“药物身份和类别依据是什么”；模型只能提供待核实语义线索。
3. 不引入外部运行库或项目特异字典。药物词典、方案条款、类别和时间窗都作为版本化输入；通用内核不硬编码项目药名、禁限用清单或阈值。
4. D02 复用 D01 已接受的 CoverageLedger、EvaluationUnit、R2 identity/lifecycle、Query/journey join；不复制第二套生命周期或关闭规则。
5. 为避免 D01 专用类型扩散，生命周期仅依赖结构化 `RiskDomainUnitResult` 公共协议；候选身份读取函数移到中性公共面，`lifecycle.py` 不再导入 `AEMHUnitResult` 或 D01 身份函数。D01 只增加兼容属性与中性函数重导出，行为不得改变；D02 实现同一协议。

`RiskDomainUnitResult` 冻结字段为：

```text
unit_id: str
subject_ref: str
l1_disposition: str
monitoring_priority: str
r2_candidates: Sequence[RiskCandidate]
risk_candidate_refs: Sequence[RiskCandidateRef]
risk_instance_refs: Sequence[RiskInstanceRef]
not_evaluable_reason: str
```

`evidence/source_record_refs/query_refs/boundary_reason/journey_markers` 是域结果及 ledger/投影使用字段，不参与生命周期的候选身份预检。每个可注册候选的 `detail` 必须带 `risk_identity_id/scope/classifier/stable_core/lineage_fingerprint/domain/full_locator_id`；中性身份函数必须在任何 `register_candidate`、adjudication 或 establish 副作用前，以公共 R2 `make_risk_identity` 重新计算并逐项验证。`stable_core == classifier`、candidate/ref 一一对应、ref 身份和 locator 精确一致等 D01 已接受约束不得弱化。

D01 `AEMHUnitResult` 保留 `medical_grading`，只增加：

```text
monitoring_priority -> medical_grading.monitoring_priority
```

D02 不需要伪造 AE/MH 的 `MedicalGrading`。生命周期对 positive 建立、boundary 仅登记、linked-negative 关闭、重开、supersede、identity_ambiguous 和 not-evaluable carry-forward 的行为保持不变。

以上八字段是 lifecycle input Protocol，不是完整 ledger 对象。每个域的 concrete result 还必须能物化完整 `UnitEvaluation`，包括 evidence、source/candidate/risk/Query refs、snapshot provenance 和 rule lineage，才能进入 `CoverageLedger`；D02 concrete result 必须同时满足两者。

中性 identity accessors 与 `MONITORING_PRIORITY_*` 常量统一放在 `mm_r4.contracts`，`aemh.py` 只为兼容既有公共导出而重导出；共享面改造后 `lifecycle.py` 不得再从 `aemh.py` 导入这些对象。

## 3. 核心输入合同

### 3.1 listing 语义角色

| 类别 | 语义角色 | 规则 |
|---|---|---|
| 最小必需 | `recorded_cm`, `subject_identity`, `site_identity`, `temporal_anchor` | 角色来自 active mapping，不依赖表名；角色缺失与“已覆盖但零行”必须区分 |
| 适应证关联 | `reported_ae`, `reported_mh`, `diagnosis`, `symptom_event` | 只有已接受来源记录可证明存在对应事件；D02 不把自身线索写回 AE/MH 计数 |
| 治疗边界 | `ip_exposure` | 仅用于证明某记录属于 IP/EX 而非 CM，或解释阶段关系；不得混并成 CM |
| 访视/阶段 | `visit`, `study_phase` | 用于解析基线、筛选、治疗、随访及条款适用窗口 |

只映射为 `ip_exposure` 的行生成零个 D02 `MedicationEpisode` 和零个 D02 `EvaluationUnit`；同一来源行同时被互斥地映射为 CM 与 IP/EX 时为 not_evaluable，不得在两边各生成一个 positive。

### 3.2 版本化非 listing 输入

- `MedicationIdentityBinding`：原始药名、规范名称、成分列表、类别列表、剂型/产品类型、词典名称/版本、证据定位、确认状态。
- `ProtocolMedicationRule`：规则 id/版本、条款定位、规则类型、目标成分或类别、适用阶段、时间窗口及起止端点是否包含、允许条件、稳定治疗/抢救/预防例外、确认命中时的版本化监察优先级及理由、规则 lineage。
- `MedicationMatchStrategy`：成分精确匹配、类别包含关系、复方拆分、时间区间比较、适应证概念等同性及各自版本。
- `MedicationEpisode`：CM 来源记录、稳定 CM source/event key、成分、剂量、单位、途径、频次、开始/结束/持续、治疗角色及其确认状态、适应证及其可映射状态和来源定位。
- `D02PriorityPolicy`：非具体禁限用条款风险（如用药依据、记录矛盾）的版本化优先级策略、影响依据和内容哈希；通用内核不凭风险名称暗定高/中/低。

### 3.3 跨域证据引用

`CrossDomainEvidenceRef` 是中性、不可变、只读的来源引用，不是 candidate/risk/Query：

```text
evidence_ref_id
producer_domain / consumer_domain / evidence_role
source_locator / producer_unit_id / content_hash / claim_scope
context_payload  # 仅治疗角色、适应证文本/概念、成分确认状态等来源上下文
```

它不得携带 consumer candidate/risk/Query id、consumer L1 结论或任何生命周期状态。D02 通过它输出 `cm_indication`；D01 仍只在自己的 EvaluationUnit、coverage、规则与身份边界内建立 D01 对象。

`content_hash` 固定为 `stable source event key + evidence_role + claim_scope + 按键排序的 context_payload` 的 canonical JSON SHA-256，排除 snapshot/revision id；完整 locator 仍单独保留作来源追溯。同一 D01 run/snapshot 内 dedup key 固定为 `(table_semantic, record_id, evidence_role, content_hash)`；临床 claim 内容变化必须产生新 hash。

任一需要受控词典或权威条款的单元未绑定名称、版本、内容哈希和 locator 时，不得由模型或常识补成 positive/negative。

## 4. EvaluationUnit 与身份

### 4.1 单元拆分

D02 `EvaluationUnit` 为：

```text
subject + medication episode + ingredient(or unresolved component)
+ activated protocol rule item(or indication check) + temporal window
+ rule/knowledge/mapping/dictionary/algorithm lineage
```

- 复方药逐成分、逐规则项建立单元；已证明命中的禁用成分可以 positive，未知成分另建 not_evaluable 单元，不用一个总状态掩盖二者。
- 一个 CM episode 同时触发“禁限用药”和“适应证待核实”时建立不同单元、不同风险 identity；共享来源但不互相覆盖。
- 同一来源记录的 snapshot/revision 变化不改变稳定事件 identity；成分、规则项、临床概念或 lineage 变化按 R2 身份规则处理。

复方 expected-set 必须按以下顺序展开：

1. identity binding 拆出“已确认成分”和“未确认 component slot”；
2. 每个适用的 active 规则对每个已确认成分建立 `ingredient × rule item` 单元；
3. episode 只要存在未确认 component，且存在任一 active 用药规则或任一 D02 检查需要药物分类，就必须为每个未确认 component 建立 `ingredient_resolution:<component_slot>` 的 not_evaluable 单元；即使没有规则能被当前身份明确激活，也不得让未知成分从 expected-set 消失；
4. episode 汇总只是只读视图，可同时显示 `has_positive/has_boundary/has_not_evaluable`，不得用一个 episode disposition 替换子单元；任一 not_evaluable 子单元继续阻断域医学完整；
5. 同一 CM 行在 L2 source record 只计一次，候选/风险/Query 按其实际单元分别计量。

`ingredient_resolution` 单元的规范 token 固定为：`risk_family=ingredient_resolution`、`signal_type=ingredient_unresolved`、`activated_rule_item_or_indication_concept=ingredient_resolution:<component_slot>`、`l1_disposition=not_evaluable`，不创建 R2 candidate 或 Query；固定合成输入必须有稳定 unit_id/expected-set hash 金标测试。

八个 `EvaluationUnit` 哈希维度固定映射为：

```text
domain_id = D02_cm
scope_type = subject
scope_key = subject_ref
normalized_concept_or_rule_item =
  stable_cm_event_key | ingredient_or_unresolved_component |
  rule_item_or_indication_concept | risk_family
temporal_window = versioned CM interval ∩ rule/check window descriptor
rule_or_knowledge_lineage = dictionary | rule | mapping | knowledge lineage
unit_algorithm_version = d02_unit_v1
```

`stable_cm_event_key` 只能由稳定语义角色＋record/event id 构成，不得使用包含 snapshot/revision 的完整 locator id。

### 4.2 风险身份：稳定临床事件与版本 lineage 分层

D02 必须使用公共 R2 `make_risk_identity`，并把稳定临床事件与评估版本分开：

```text
domain = D02_cm

classifier / stable_core =
  d02 | risk_family | stable_cm_source_event_key |
  ingredient_or_unresolved_component | activated_rule_item_or_indication_concept |
  signal_type

scope / lineage_fingerprint 至少包含：
  site | relevant temporal window | date precision |
  dictionary name/version/hash | protocol rule id/version/hash |
  match strategy version | mapping/rule/knowledge lineage |
  unit algorithm version
```

classifier 禁止包含 snapshot id、source revision id、词典/规则/mapping/算法版本或可修改的剂量/途径自由文本；完整 locator 只用于来源追溯。scope 排序并参与公共 R2 identity；`lineage_fingerprint` 必须等于公共 scope 的精确连接结果。

- 同 classifier＋同 scope：同一身份，N→N+1 可持续或在精确 linked-negative 下关闭；
- 同 classifier＋不同 lineage：`superseded`，不得伪装为 `resolved_by_data`；
- 同 classifier 在 N+1 出现多个互斥 identity：`identity_ambiguous`，阻断自动合并/关闭；
- 不同 CM event、成分、规则项或风险族：不同风险，不得用“同一受试者/同一药名”维持旧风险。

- 全量快照中正式补录/更正 CM 后保留“原待核实风险—后续记录”的匹配历史。
- 无法确认同一 CM/成分/规则单元时使用 `identity_ambiguous`，阻断自动合并/关闭。
- 词典、mapping、规则或算法版本变化导致不再命中时使用 `superseded/not_evaluable`，不得伪装为 `resolved_by_data`。

L1 `eval_disposition=not_evaluable` 本身只使活动风险 carry-forward，绝不终止 L3。只有 risk identity 本身无法继续时，才通过公共 `terminate_not_evaluable` 显式进入 L3 终态 `risk_state=not_evaluable`；它与 supersede 是不同路径。

## 5. L1 医学评价合同

### 5.1 `positive`

至少一种权威闭环成立：

1. `medication_indication_unexplained`：CM 明确记录了可映射到具体医学概念的适应证/治疗目的，治疗角色与适用且完整的 AE/MH/诊断/症状/病史来源均可核实，但没有可解释对应或记录相互矛盾；明确预防/抢救且符合相应依据时不因缺 AE/MH 自动命中；
2. `treatment_without_event_record`：CM 明确用于治疗研究期新发/恶化医学事件，而完整的 AE/MH/诊断中无相应记录；同时向 D01 提供 `cm_indication` 跨域证据引用，不在 D02 建立任何 D01 candidate/risk/Query；
3. `prohibited_medication_match`：权威成分/产品类型或精确类别明确命中 active 禁用规则且区间落入适用窗口；
4. `restricted_medication_condition_mismatch`：明确命中限制规则，但稳定剂量、抢救、预防、阶段、剂量/途径/频次等允许条件不满足；
5. `medication_record_inconsistency`：剂量、途径、频次、起止或治疗角色与权威规则/适应证形成明确矛盾；
6. `treatment_action_relationship_inconsistent`：CM 与 AE/MH/IP 处置关系在同一身份与时间窗内明确冲突。

每个单元只有一个 primary positive subtype。对同一 indication-check，若“明确治疗角色＋可映射概念＋可确定为研究期新发/恶化＋完整来源无对应”同时满足 1 和 2，以 `treatment_without_event_record` 为 primary；其他有明确适应证但无法解释者使用 `medication_indication_unexplained`。两类均可输出一个 `cm_indication` 引用供 D01 独立评价，但不得因这个引用在 D02 重复创建第二个 positive 单元。

“适应证已记录”必须同时满足非空和可映射。`对症治疗/其他/遵医嘱` 等笼统文本、未知编码或冲突概念不是明确适应证，按 not_evaluable/coverage gap 显示“适应证记录不具体”，不反向推断 AE/MH 漏报。

### 5.2 `negative`

仅在本单元所需的药物身份、成分/类别、治疗角色、适应证、阶段、时间窗、active 规则和来源 coverage 全部可核实时使用，并且明确未命中目标、位于窗口外、满足允许条件或适应证与已记录医学事件一致，且不存在已知矛盾。

风险数为零、模型未发现、商品名不同、上位类别不同均不足以判 negative。

### 5.3 `boundary`

- 同一 component 有两个或以上各具版本化支持、但不能唯一选择的成分/产品类型 binding；已确认成分与完全无依据的未知 component 不合并为 boundary，而是分别评价、后者 not_evaluable；
- 商品名可对应多个成分/剂型/产品类型；
- 开始或结束恰在禁限用窗口端点，协议未说明包含关系；
- 部分日期与规则窗口发生可能重叠；
- 预防与治疗、长期稳定与新启用、抢救与常规治疗存在两个或以上各有来源支持的可行解释，且当前证据不能唯一选择；
- 同一药名存在不同产品类型，现有证据不足以确认具体制剂。

`boundary` 可以形成待核实风险线索，但必须显示不确定性，不得作为确定 PD 或确定禁用药结论。

`boundary` 只用于“关键输入存在且支持两个以上临界/可行解释”；关键输入单纯缺失、角色未记录或无法确认规则所需允许条件时为 not_evaluable。同一单元同时存在 boundary 条件和阻断评价的 coverage 缺口时，not_evaluable 优先。

### 5.4 `not_evaluable`

- 药物成分/类别、治疗角色、关键日期/阶段、适应证或 active 方案条款缺失/冲突；
- 需要词典分类却无版本化词典绑定；
- 规则要求“活/减毒活疫苗”等具体产品类型，但只有 J07 等上位分类码；
- CM 与 IP/EX 角色无法区分；
- 受试者/中心身份或 required role coverage 不可确认。

缺失适应证字段本身不得被自动解释为“无适应证”；缺失、笼统不可映射或冲突时为 not_evaluable/coverage gap。只有 active 数据规范明确要求收集、来源角色已完整覆盖且 accepted CM 行的该字段被确定记录为空，系统才可显示“适应证信息缺失”的确定数据缺口；它仍不等于“无适应证”，也不自动生成“无用药依据”的医学 positive。

### 5.5 `not_applicable`

只在权威方案/设计证明项目不收集 CM 且不存在任何禁用、限制、稳定治疗、抢救或预防规则，或某一规则项在当前阶段明确不适用时使用。零行或文件缺失不是不适用。

## 6. 药物身份与类别的 fail-closed 规则

1. 原始药名永远保留；规范化不覆盖原文。
2. 商品名、拼写相似、模型常识或自由文本不能独立证明成分/类别。
3. 成分精确命中优先；类别规则必须有词典中的显式 membership 证据和版本。
4. 复方药逐成分评价；不得因一个已知成分而假设其余成分。
5. 上位码只证明其对应的上位类别：当 active 规则目标本身就是该上位类别（如明确禁用全部 J07）时可以作为匹配依据；当规则要求更细产品类型（如活/减毒活疫苗）时，仅有 J07 不足以证明具体产品类型，必须 not_evaluable。
6. 多个各有版本化证据支持的 identity binding 未唯一化时，本次 L1 为 boundary；若它们竞争同一活动风险的 stable_core，则 L3 为 identity_ambiguous。无受控依据时为 not_evaluable。
7. 模型可生成 identity proposal，但不能把 proposal 直接变为 accepted binding。

## 7. 时间与阶段合同

- CM 采用区间：`start`, `end/ongoing`, 日期精度和来源状态；规则采用有效区间、阶段及端点包含关系。
- 全日精度且协议明示包含关系时可确定 inside/outside；端点包含关系未明时规范性默认是 boundary，绝不静默按 inside 处理。
- 月/年部分日期不得静默补为首日/末日；可能重叠为 boundary，无法比较为 not_evaluable。
- ongoing 不是缺失结束日期；必须以显式 ongoing 状态和 cutoff 共同解析。
- 长期稳定治疗需由开始时间、稳定期要求、剂量/频次未变证据共同证明；“开始很早”单独不足以判允许。
- CM 区间与规则区间确定重叠才可据此 positive，确定不相交才可据此 negative，可能重叠为 boundary；任一关键锚点无效、冲突或无法比较为 not_evaluable。

## 8. 适应证与 AE/MH 双向关联

- D02 从 CM 适应证反查 AE/MH/诊断，输出“用药依据待核实”及可供 D01 使用的 source-linked `CrossDomainEvidenceRef(evidence_role=cm_indication)`。
- D01 是否建立“疑似 AE/MH 漏报”仍由 D01 coverage、时间边界、匹配和反证合同决定；D02 不复制或直接关闭 D01 风险。
- 适应证概念匹配必须版本化；同义词 proposal 未经确认时只进入 boundary。
- 预防/抢救用药必须保留治疗角色，不能因缺 AE/MH 自动判漏报。

跨域所有权和去重固定为：

1. D02 只生产 CrossDomainEvidenceRef；D01 消费后才可转换为自己的 `SemanticRecord(role=cm_indication)`；
2. D02 不生产 D01 candidate/risk/Query，D01 也不得关闭或 supersede D02 风险；两域 identity 的 domain 必须不同；
3. 同一来源可支持两个医学含义不同的域风险，二者各自在域 ledger 中计量；D09/D10 可用 evidence_ref_id 分组显示关联，但不得仅因共享来源而把两个不同 risk identity 静默合并；
4. 同一 D01 run/snapshot 内 active mapping 已直接提供相同 `(table_semantic, record_id, evidence_role, content_hash)` 的 cm_indication 时，D02 handoff 不得再制造第二个 D01 SemanticRecord；
5. L2 source/candidate/risk/Query 计数保持分域且类型分离；跨域证据引用本身不是新的 CM 源记录或风险；
6. ref 中明确的 prophylaxis/rescue 角色作为 D01 反证/上下文，D01 不得仅凭“未找到 AE”自动 positive。

## 9. 风险分级、生命周期与 Query

### 9.1 监察优先级

- high：版本化规则/优先级策略明确标为关键的禁用/限制规则被确定命中，或与严重医学事件/关键处置形成有来源的强矛盾；不得由通用内核仅凭“禁用药”名称硬编码为 high。
- medium：版本化策略定义的用药依据缺少对应记录、确认的限制条件不满足或重要剂量/途径/时间矛盾。
- low：版本化策略确认影响有限、但仍需数据澄清的单一不一致。
- unknown：已形成 positive/boundary 线索，但规则/策略没有足够依据确定优先级；不得默认为 low。

priority 只投影到实际 candidate/risk；not_evaluable/coverage gap 即使结构协议字段为 `unknown`，界面也不得把它显示成“未知风险等级”。所有规则型 priority 来自 `ProtocolMedicationRule`，非规则型来自 `D02PriorityPolicy`，均需版本/哈希/理由。priority 与 L1 disposition 分层，不能用 priority 代替 not_evaluable。

只有系统建立的 low/medium 风险在下一已接受全量快照、相同身份算法、完整覆盖和精确 linked NEGATIVE 下可机器关闭；high、unknown、用户确认/升级、身份歧义和临床标记均延续。

该规则与共同合同 §3.6 一致：只有 low/medium 在满足全部条件时可机器关闭，其余均延续；D02 在此显式写明 unknown 的延续，不新增另一套生命周期。

### 9.2 中文受众标签

- `medication_indication_unexplained` → “用药依据待核实”
- `prohibited_medication_match` → “禁用药使用待核实”
- `restricted_medication_condition_mismatch` → “限制用药条件待核实”
- `medication_record_inconsistency` → “用药信息与方案要求不一致”
- `treatment_without_event_record` → “治疗用药与 AE/MH 记录待核实”
- `treatment_action_relationship_inconsistent` → “用药与处置记录关系待核实”

界面不得显示 `RiskCandidate`、`L1 positive`、`正式事实`、`候选信号`、`只读xx` 等内部对象名。

### 9.3 Query 草稿

每条 Query 必须为三段式并绑定最小可达来源。例如：

```text
依据：研究方案规定某成分/类别在指定阶段禁用或需满足特定条件。
发现：参与者在具体日期区间使用某药，版本化药物身份依据显示包含目标成分/类别。
行动项：请核实该用药是否符合方案要求以及是否构成方案偏离；如需，请按相应流程处理。
```

```text
依据：治疗用药通常应与相应医学事件或诊断记录一致。
发现：参与者使用某药治疗某症状/疾病，当前 AE/MH/诊断中未找到可对应记录。
行动项：请核实用药原因及 AE/MH/诊断记录是否完整，并按核实结果补充或更正。
```

系统只生成、编辑、确认和导出草稿；不发送、不跟踪外部回复。涉及 PD 只请求有权责任方核实，不由本系统正式判定/报送。

模板必须在实例化时写入受试者、CM episode/日期区间、规则 id/条款 locator、药物身份依据 locator 和最小原始记录 locator。例如合成实例：

```text
依据：方案规则 R-CM-007 规定治疗期不得使用目标成分（条款 P12-4）。
发现：参与者 SYN-001 在 2026-01-03 至 2026-01-05 使用合成药物 A；受控绑定 DICT-v1 显示其含目标成分，记录定位 CM#9。
行动项：请核实该用药是否符合方案要求以及是否构成方案偏离；如需，请按相应流程处理。
```

以上仅为合成格式示例，不是药物或项目规则。

## 10. 受试者医学旅程投影

- 每个 CM episode 投影为独立 CM 区间事件，显示药名、成分确认状态、剂量/途径/频次、适应证、开始/结束/持续及来源。
- 禁限用风险标记锚定 CM 区间与规则窗口交叠位置；用药依据风险锚定适应证/关联事件位置。
- 用药依据风险恰因“未找到对应事件”而成立时，不伪造一个事件位置；标记锚定 CM 区间，并显示“当前 AE/MH/诊断中未找到对应记录”。
- CM、AE、MH、IP 仍为不同轨道/形状/线型；风险标记显示具体类型和等级，不使用“已记录事项”“通用风险点”。
- 点击风险可双向到 CM 原始记录、药物身份依据、方案条款、关联 AE/MH/诊断和 Query；本切片只提供 projection payload，不宣称 R5 UI 已完成。

`CMJourneyEvent` 最小字段为 `event_id/domain_track=cm/subject_ref/start/end/ongoing/date_precision/episode_id/display_label/source_locator_ids/unit_ids`；`CMRiskMarker` 最小字段为 `marker_id/risk_family/audience_label/monitoring_priority/anchor_kind/anchor_start/anchor_end/unit_id/candidate_or_risk_id/source_locator_ids/rule_locator_ids/query_ids/coverage_gap`。所有双向 join 用稳定 id 验证，不以说明文字代替。

## 11. 覆盖、计数与聚合不变量

- 每个 expected D02 单元恰有一个 L1 disposition；五类 disposition 总和等于 expected units。
- source CM、药物 identity evidence、risk candidate、risk instance、Query draft 分别计量，不相互推导。
- positive 至少关联一个具体 D02 candidate/risk；negative 不创建新风险；boundary 只创建带不确定性的线索。
- L1 not_evaluable > 0 或 L0 partial/truncated/failed/missing 时不得声明 D02 医学完整。
- 中心/项目汇总只聚合个体结果，不复制、改写或合并受试者风险身份；high/unknown 不得被多数票隐藏。

可执行不变量还包括：

- 非法 L1 值、同一单元尝试写入两个 disposition、positive 无 candidate/active risk、negative 新建开放 candidate，均在 ledger 前 fail closed；
- L1b supporting/counterevidence/context 可共存，但不产生第六种 L1；
- boundary 可登记 candidate，永不由机器 establish；not_applicable/not_evaluable 不登记新 candidate；
- Query 必须关联本单元、可达来源及 candidate/risk；Query count 永不进入 risk count；
- 同一 CM episode 的只读汇总必须保留全部 child unit ids 和 `has_positive/has_boundary/has_not_evaluable`，不得因存在 positive 隐藏 coverage gap；
- linked-negative 可以在 negative 单元关联历史 risk，但只有 exact risk_instance_id＋risk_identity_id、相同身份算法/lineage、闭合完整 ledger 和随后 accepted full snapshot 才能关闭；
- `lifecycle.py` 静态依赖不得包含 `AEMHUnitResult`；任一 identity tamper 必须在首次生命周期副作用前拒绝。

## 12. 合成挑战矩阵

至少覆盖：

1. 明确禁用成分且时间窗命中；
2. 明确不同成分/类别且窗口完整，negative；
3. 商品名/成分不明，not_evaluable；
4. 复方一个禁用成分＋一个未知成分，positive 与 not_evaluable 分单元共存；
5. 只有 J07 上位码却规则要求活/减毒活疫苗，not_evaluable；
6. 开始/结束恰在规则端点，boundary；
7. 月/年部分日期可能重叠，boundary；
8. 明确稳定治疗满足条件，counterevidence/negative；
9. 长期用药有两个来源支持的稳定/新启用解释时 boundary；稳定所需信息单纯缺失时 not_evaluable；
10. 抢救/预防角色明确，不因无 AE/MH 自动判漏报；
11. 明确治疗适应证但 AE/MH/诊断无对应，positive＋D01 evidence link；
12. 适应证缺失，not_evaluable，不伪装为无依据；
13. CM 与 IP/EX 无法区分，not_evaluable；
14. 同一受试者另一药物/另一规则不得维持或关闭旧风险；
15. N+1 正式更正后 low/medium 仅凭完整 linked-negative 关闭并保留历史；
16. 词典/规则 lineage 变化产生 superseded/not_evaluable，不使用 resolved_by_data；
17. 身份竞争产生 identity_ambiguous；
18. Query 三段式、最小来源、PD 仅核实、旅程区间与风险双向 join。
19. 同一 CM 同时满足 indication subtype 1/2，按优先规则恰有一个 primary positive、一个用户标签和一个 cm_indication ref；
20. 限制规则要求确认抢救角色，但 CM 未记录角色且无充分上下文，not_evaluable 而非 boundary；
21. 适应证为“对症治疗/其他/遵医嘱”等不可映射文本，not_evaluable/coverage gap，不反向判漏报；
22. 复方全部成分未确认且可能涉及 active 规则，所有 unresolved component 均进入 expected-set，域不得 complete；
23. 规则目标就是 J07 上位类且词典明确绑定时可匹配；规则目标为活/减毒活疫苗而只有 J07 时 not_evaluable；
24. 同一单元同时有端点 boundary 与关键角色缺失，not_evaluable 优先；
25. 同一稳定 CM event、相同成分/规则、普通数据更正且 lineage 不变时身份持续；词典/规则/mapping/算法 lineage 变化时 superseded；
26. 两个竞争 identity binding 对同一 stable_core 产生 identity_ambiguous，任何自动关闭均被拒绝；
27. D02 cm_indication handoff 与 active mapping 双路输入按稳定 event key＋content hash＋role 去重；snapshot/revision 改变而 claim 不变不重复，claim 变化产生新 hash；D01/D02 风险身份、Query 和生命周期互不写入；
28. compound episode 同时显示 positive 与 not_evaluable flags，L2 source 仍为 1，not_evaluable sibling 不产生 candidate/risk；
29. 仅映射为 ip_exposure 的 EX/IP 行不生成 D02 CM episode/unit；CM 与 IP 角色冲突时 not_evaluable；
30. 结构协议 duck-type D02 结果不含 MedicalGrading 仍可复用 lifecycle；identity/ref tamper 在任何副作用前失败，D01 224 项行为回归保持通过。

## 13. 实现与验收边界

### 13.1 允许的实现面

- 新增 `src/mm_r4/cm.py`、`cm_projection.py`、`cm_fixtures.py` 及对应测试；
- 对 `contracts.py`/`lifecycle.py`/`aemh.py` 做最小、行为保持的公共 `RiskDomainUnitResult` 协议适配；
- 更新根导出和 README；不得改冻结 R1/R2/R3。

共享面必须先串行完成并验收：单一 owner 修改 `contracts.py/lifecycle.py/aemh.py`，先证明 D01 全量回归保持通过；其余 worker 才可并行新增 D02-owned 文件。任何两个 worker 不得同时写 `lifecycle.py`、`contracts.py`、根导出或 README；不得为 D02 复制第二个生命周期 adapter。

### 13.2 完成证据

- D02 五类 disposition、复方 expected-set、J07 粒度反例、时间端点、适应证反查、CM/IP 分层、跨域引用、Query/journey、N→N+1 和 lineage/identity challenge 全部有确定性测试；
- D01 全量 224 项保持通过；R2 risk/identity 与 R3 normalization/mapping/date 相邻回归保持通过；
- 无固定项目名、表名、药名、阈值、30 天窗口或 private R2 API；
- Ruff/compile/import/哈希/8911 通过；无 cache；
- 独立医学和工程复核接受。

## 14. 主会场冻结裁决

1. 缺失、笼统或不可映射适应证为 not_evaluable/coverage gap；只有明确可映射适应证、完整相关来源和可核实治疗角色才进入“用药依据待核实”。明确研究期治疗且缺事件记录时 subtype 2 优先。
2. 复方不仅逐成分/规则拆分，还必须为 unresolved component 生成 identity-resolution expected unit；episode rollup 不能替代单元。
3. 每条规则应显式给出端点包含关系；未给出时规范性默认 boundary。
4. `RiskDomainUnitResult` 使用 §2 的精确结构字段；lifecycle 使用中性 identity surface，D01 用兼容属性保持行为。
5. D02→D01 使用 §3.3/§8 的 CrossDomainEvidenceRef；共享来源引用，不共享 candidate/risk/Query/lifecycle。关联风险可分组显示，但不同 domain risk identity 不因同源而静默去重。
6. priority 来自版本化规则或 D02PriorityPolicy；not_evaluable 不显示成“未知风险”。

原医学 session `019fee42-0121-7000-8f86-d7ed22f72e7c` 差异复核为 `ACCEPT_WITH_GAPS`；原工程 session `ae34e41d-6171-48a3-9528-90c09081344d` 差异复核为 `ACCEPT_WITH_GAPS`。Codex 已把医学方唯一低级措辞建议和工程方 G1-G6 精度项逐项并入本文件，并对照冻结共同矩阵与当前 D01 公共面完成主会场裁决；本版本因此冻结为 `FROZEN_R4_D02_CONTRACT_V1`。
