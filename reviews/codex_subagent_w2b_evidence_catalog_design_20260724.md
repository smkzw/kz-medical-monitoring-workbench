# 医学写作 AI-first W2b：证据目录与完整 PICOS 组合候选只读技术审阅

**审阅日期：** 2026-07-24  
**范围：** 仅医学写作 AI-first W2b。目标是让产品独立 AI
`deepseek/deepseek-v4-pro` 在生成完整 PICOS 组合候选时，使用并返回可逐项
核验的“事实 - 原文摘录 - 来源 ID - 定位”绑定。本文不修改生产代码、测试、运行数据或
前端。

## 结论

当前系统已经有足够的原始载体来实施 W2b，但这些载体尚未被收敛成一次生成所使用的、
不可变且有界的证据目录。现有 prefill AI 只接收 `registered_source_ids`；服务端随后只
检查该 ID 是否在集合中，并不能证明引用的来源实际支持某个剂量、盲法、给药途径、机制、
终点或统计结论。因此，W2b 不应继续增强“来源 ID 白名单”提示词，而应在服务端先构造
证据目录，再要求模型按目录条目返回 claim 绑定，并由服务端重新绑定原文。

本切片应保持如下边界：

1. 产品 AI 仍只由工作台配置的 `deepseek/deepseek-v4-pro` 运行；Codex、subAgent 或
   执行模型只用于开发和验收，不产生系统中的医学候选。
2. 当前项目的明确原文可支持“有来源的项目事实”；竞品 ClinicalTrials.gov 快照只能支持
   “可供选择的设计参照”，不能反向证明当前项目采用相同设计。
3. 无直接证据时可生成中文的待决定卡和待补资料清单，但不得生成可直接采用的精确事实。
4. 每一个组合候选内的每一项精确主张都必须能追溯到目录条目；不能以候选级别的一个泛化
   `source_id` 覆盖整个 population、intervention、comparator、outcomes 或 statistics 包。

## 1. 当前可用的真实证据载体和字段

| 载体 | 当前可用字段 | W2b 可用性与限制 |
| --- | --- | --- |
| 项目最小事实 | `framing.investigational_product`、`framing.indication`、`framing.study_phase`、以及已生效的 `StudyDefinition.framing/picos` | 可作为项目身份和已由用户确认值的证据。仅凭三项最小事实不可推出成人、随机、盲法、对照、剂量、途径、靶点、终点或统计假设。 |
| 导入方案摘要 | `MedicalWritingSynopsisImport.evidence_spans` 包含 `span_id/source_id/locator/source_text/source_text_sha256`；`field_evidence_span_ids` 将字段映射到 span；`field_extracted_value_sha256` 约束已提取值 | 是最接近 W2b 需求的现成载体。只应纳入未失效且已经过用户确认的摘要；其字段映射可用于精确项目事实。 |
| 研究者手册/上传方案/下载 Protocol/SAP 的注册表和解析结果 | `SourceRegistryEntry`、`SourceRegistrySpan`，以及 `WritingReferenceDocumentArtifact`、`WritingReferenceExtractedSpan` 的文档 hash、解析版本、页码、block、`source_locator`、`source_text`、`source_text_sha256` | 可用于 IB、正式方案、公开 Protocol/SAP 的明确摘录。应要求文档处于当前版本、内容校验允许使用、解析成功且 span 有可读原文。 |
| 已批准竞品中文证据简报 | `WritingReferenceEvidenceBrief` 有 `artifact_id/span_id/translation_id/translation_revision/approved_zh_text/source_locator/source_text_sha256/document_sha256/medical_review_id` | 最适合在中文候选中引用已审阅的竞品章节；它仍是竞品证据，不能升级为当前项目事实。 |
| ClinicalTrials.gov 不可变检索快照 | `WritingReferenceSearchSnapshot` 及 candidate 的 NCT、标题、Brief Summary、疾病、分期、研究类型、干预名称/类型、allocation、intervention model、masking、入组数、申办方、状态、首次/最近发布日期、公开文件元数据 | 可为竞品设计差异、候选表述和“需用户决定”的比较提供证据。不得把其中一个研究的随机/双盲/安慰剂/成人/途径/剂量/终点当作当前项目事实。 |
| 已有 AI task 原文校验基础设施 | `AiTaskSourceRef`、`AiTaskEvidenceEntry`，以及 `ai_task_runner.py` 的 exact quote、normalized substring、source/locator 绑定逻辑 | 可复用其“服务端重绑原文”思想和规范化规则，但 prefill 目前没有 `AiTaskRun` 审计记录，也没有把 catalog 条目传给模型。 |

### 当前缺口

- `AuthoringPrefillEvidenceRef` 已有 `source_id/locator/source_text/quote_sha256`，但不含
  catalog 条目身份、目录版本或 claim 对应关系；只要模型猜中一个已登记 ID，就可能让一个
  无关来源看起来像证据。
- `_collect_registered_source_ids()` 只收集 `StudyDefinition.source_artifact_ids` 加三个最小
  framing ID；它没有加载任何来源的具体 span、文本、版本或定位。
- `DeepSeekPrefillAdapter._build_bulk_request()` 传入的是来源 ID 列表和精简竞品 hints，解析
  仅读 `source_ids`。现有 prompt 中虽写“可引用来源”，但服务端并无语义验证条件。
- 当前 prefill 独立调用 DeepSeek 并把候选合并入 package；`AuthoringPrefillCandidate.ai_run_id`
  已存在但该调用链没有持久化一个与候选相连的 AI run/输入 catalog 证据快照。

## 2. 最小、向后兼容的数据合同、服务和 API 改动

### 2.1 合同

保持既有 `AuthoringPrefillEvidenceRef` 和所有既有 package JSON 可读。新增字段均为可选，
旧候选继续按照现有路径显示，但不能被 W2b 视为“证据绑定候选”。建议新增：

```text
AuthoringPrefillEvidenceCatalogEntry
  catalog_entry_id            # sha256(catalog_id, source_id, locator, quote_sha256)
  catalog_id
  source_kind                 # project_fact | synopsis | ib | registry | ctgov_snapshot
  source_id
  source_revision             # extraction/translation/snapshot revision or content hash
  locator
  quote                       # 服务端保留的原文；可为英文
  quote_sha256
  title
  support_scope               # current_project_fact | competitor_observation
  supported_target_paths      # 可被该条目直接支持的字段集合
  provenance                  # artifact_id/span_id/nct_id/snapshot_id 等最小可追溯元数据

AuthoringPrefillClaimBinding
  target_path                 # 例如 picos.primary_endpoint
  value_pointer               # 组合 structured_value 内的 JSON pointer；标量用 ""
  catalog_entry_id
  source_id
  locator
  quote_sha256
  support_kind                # exact_fact | normalized_enum | competitor_option

AuthoringPrefillCandidate (optional additions)
  evidence_catalog_id
  evidence_catalog_sha256
  claim_bindings: List[AuthoringPrefillClaimBinding]
  evidence_status             # supported | partially_supported | insufficient
```

`AuthoringPrefillEvidenceRef` 继续作为 UI 展示和旧候选兼容投影。W2b 新候选必须由
`claim_bindings` 反向生成其 `evidence_refs`；不得允许客户端直接把任意 `source_text` 写入
最终 package。

### 2.2 服务

新增一个纯服务层 `AuthoringPrefillEvidenceCatalogService`，输入为有效的 authoring journey、
当前检索快照、writing reference repository/source registry。它只做以下事情：

1. 读取当前且可用的 span/快照事实；
2. 生成稳定排序、大小受限、带哈希的 catalog；
3. 将 catalog 投影为 DeepSeek 输入；
4. 校验并重新绑定 DeepSeek 输出；
5. 为成功调用持久化 `AiTaskRun` 或等价 prefill-run 审计对象，记录 provider、model、
   prompt version、catalog hash、输出 validation 结果及候选 `ai_run_id`。

`DeepSeekPrefillAdapter` 只接收这个 catalog，不再接收裸 `registered_source_ids`。可在现有
`enrich_package()` 内部改造，避免扩大 journey service 的职责。不得把 catalog 构建交给
前端或模型。

### 2.3 API

现有 `POST /prefill-package/generate` 请求体无需改变，响应的 package 通过新增可选字段带回
catalog ID、run ID 和候选 claim bindings。这样旧前端、旧项目和调用方保持兼容。

不建议在 W2b 新增“客户端提交 source_id/source_text”的 API。若 UI 需要查看来源，复用现有
文档/摘要/快照读取端点，或在后续只读 `GET .../prefill-package/evidence-catalog/{catalog_id}`
中返回经过脱敏的目录条目。该 GET 不是 W2b 功能正确性的前置条件。

## 3. 有界 source catalog 的构建规则

### 3.1 纳入规则

catalog 必须是一次 generate 调用的服务端不可变输入，且只包含下列明确来源：

1. **项目最小事实：** 每个非空的药物、适应症、分期各形成一个 `project_fact` 条目，
   locator 为对应 framing path。仅 `supported_target_paths` 中的身份、标题、检索词和研究
   分期相关字段可以使用它们。
2. **已确认的方案摘要：** 仅 `synopsis_import.status == confirmed` 的 field evidence spans；
   以 `field_evidence_span_ids` 作为可支持字段白名单。不得把同一摘要任意段落扩展为全方案
   的通用证据。
3. **IB/已登记项目文件：** 仅 `source_current`、解析成功、内容校验允许使用的 artifact 的
   明确 extracted span。IB 的 `ib_status`、validation 状态和 source ID 必须一致。若只知道
   IB 文件 ID 但没有解析 span，则它不是可供 AI 主张事实的目录项。
4. **ClinicalTrials.gov 快照：** 每个显式字段单独形成条目，而非用整个研究作一个来源。例如
   `ctgov:{snapshot}:{nct}:design.masking`、`...:intervention[0].type`、
   `...:brief_summary`。quote 是快照原始字段文本；`source_kind=ctgov_snapshot`，
   `support_scope=competitor_observation`。
5. **已医学审阅的竞品中文证据简报：** 只纳入 `approved_current` 简报，并保留其原文 hash、
   翻译 revision、医学审核 ID 和 M11 anchor。它也必须是 `competitor_observation`。

不纳入：模型以往输出、未确认摘要提取、旧快照、已失效文档、仅文件名/标题推断、无 span 的
artifact ID、泛化语料、未医学审核的翻译、或用户未确认的“AI inferred”产品事实。

### 3.2 有界性与可重复性

- 每类资料设置显式上限，例如项目事实最多 30、摘要/IB/项目文件最多 120 个经字段相关性
  排序的 span、CT.gov 每个候选最多 12 个指定字段、已审阅竞品简报最多 80 个。超出时以
  当前项目字段相关性、文档版本、证据状态和稳定排序截断，并记录 `catalog_truncation`。
- `catalog_id` 由 project、journey revision、snapshot ID、入选条目 ID、每条
  `quote_sha256` 和来源 revision 计算；任何摘要确认、文档失效、快照切换或 span 内容变化都
  产生新 catalog。
- catalog 内引用的原文在调用后仍由服务端保存；AI 输出不能重新定义 quote。响应只输出需要
  给用户看的短摘录和 locator，完整原文继续在其权威文档/注册表中读取。
- CT.gov 英文原文可作为 quote；候选 `preview/rationale` 必须是监管中文。翻译本身不是原文
  事实，而是基于相同 catalog 条目的中文显示层。

## 4. AI 输出与服务端验证

### 4.1 要求 DeepSeek 返回的结构

在现有结构化 JSON 中增加 `catalog_id`、`catalog_sha256` 和 package-level candidates。每个
可主张的 atomic value 必须带 binding：

```json
{
  "field_path": "package.intervention",
  "target_paths": ["picos.intervention_summary", "picos.intervention_dose_regimen"],
  "structured_value": {
    "picos.intervention_summary": "CMS-D017按方案规定给药",
    "picos.intervention_dose_regimen": ""
  },
  "recommendation_role": "pending_decision",
  "claim_bindings": [
    {
      "target_path": "picos.intervention_summary",
      "value_pointer": "",
      "catalog_entry_id": "...",
      "source_id": "framing.investigational_product",
      "locator": "framing.investigational_product",
      "quote_sha256": "...",
      "support_kind": "exact_fact"
    }
  ],
  "evidence_gaps": ["推荐剂量、给药频次和给药途径需IB或已确认摘要明确支持。"]
}
```

模型只需提交 `catalog_entry_id` 及冗余校验字段；`quote` 应被视为可选回显，不能作为可信
输入。模型不能通过一个 source ID 支持未列出 target path 的主张。

### 4.2 服务端验证顺序

1. `catalog_id/catalog_sha256` 必须等于本次请求的不可变 catalog。
2. 每个 binding 的 `catalog_entry_id` 必须存在，且 `source_id/locator/quote_sha256` 与 catalog
   完全一致；只传 source ID、未知 entry、跨项目 entry、过期 entry 或错 locator 一律拒绝。
3. 若模型回显 quote，先逐字相等；仅允许现有 `ai_task_runner` 已采用的保守规范化：NFKC、
   空白折叠和有限中英文标点等价。规范化命中后由服务端写回 catalog 中的原始连续摘录，
   不能保留模型提供的文本。
4. `target_path` 和 JSON pointer 必须在候选声明的 target path 内，且在对应 catalog entry 的
   `supported_target_paths` 白名单内。一个包内的每个非空精确原子值都必须至少有一条有效
   binding；列表中的每个元素分别核验。
5. 对可确定性映射的枚举做字段级验证。例如 CT.gov `DesignAllocation=RANDOMIZED` 可产生
   “竞品研究采用随机分配”的观察；但不得产生“本项目采用随机设计”。机制、途径、剂量、
   终点、样本量、统计模型等非单值映射不得由自由文本语义相似性自动升级为项目事实。
6. 验证失败的单条候选整体降为 `pending_decision/manual_only` 并删除无效 claim，或在仍有
   未绑定精确值时完全丢弃；不能保留为“可手动选择的有证据候选”。服务端生成
   `evidence_validation_errors` 并持久化到 run。

关键原则是：**服务端验证来源身份和原文连续性，字段映射决定能否把主张写成项目事实；模型
不承担证据裁判角色。**

## 5. 无证据时的返回行为

无证据不是失败，也不是允许模型补全的空白。对每个没有足够绑定的模块，返回一个：

- `candidate_scope=module/design_package`
- `recommendation_role=pending_decision`
- `adoption_mode=manual_only`
- 空字符串/空数组作为未知精确字段值
- 仅包含项目身份的中性描述（如“诊断为 X 的目标人群，具体入选条件待确认”）
- 明确的 `evidence_gaps`、需用户最小补充信息和可选的竞品观察

用户明确选择或编辑后，该行为是用户确认，不应再显示“待医学批准”。但用户编辑产生的
项目事实必须与 AI 证据候选区分：记录 `value_origin=medical_manager_edit`、actor、时间、
旧值、catalog/run，并在后续重新生成时作为项目已确认事实，而不是倒灌为“AI 已证实”。

## 6. 完整 PICOS 组合包字段和禁止硬猜项

下表为 W2b 应支持的实际字段集合。字段可按当前 `MedicalWritingPicosDefinition` 和 structured
design 的路径投影，不要求这次重构领域对象。

| 包 | 至少包含的字段 | 绝对禁止由分期/竞品常见做法硬猜的项 |
| --- | --- | --- |
| `package.population` | 人群概述；诊断/表型；年龄/性别；病程与严重度及评估量表/时间点；既往治疗与治疗线；入选模块；排除模块；妊娠/避孕；洗脱期；地区/中心限制 | 成人、18-75 岁、疾病活动度阈值、既往失败线数、特定实验室阈值、感染/肿瘤/器官功能条款、洗脱时长。 |
| `package.intervention` | 试验药物身份；技术类型/机制；剂型/途径；剂量、频次、递增或滴定；给药时长；必需背景治疗；允许/限制/禁止合并用药；疗效评估前限制；剂量调整/中断/停药；依从性策略 | 单抗/小分子/RNA、口服/皮下/静脉/外用、任何剂量/剂量组/频次/间隔、SAD/MAD 队列、背景标准治疗、禁用药和限制窗口。 |
| `package.comparator` | 对照类型；对照药/安慰剂/无对照；对照给药方案；背景治疗平衡；随机比例；盲法及匹配；救援治疗与转组 | 安慰剂、阳性对照、随机比例、双盲/开放、平行/交叉、转组、救援治疗规则。 |
| `package.outcomes` | 主要/关键次要/其他次要/探索性目的和终点；终点定义、量表、时间点；安全性终点；AESI；PK/PD/免疫原性；影像/中心判读；终点层级 | 任何主要终点、关键次要终点、Week 时间点、AESI 清单、量表版本/版权、PK/PD 采样时间、临床意义阈值。 |
| `package.statistics` | 研究时期与访视策略；分析集；随机化/分层；estimand 与伴发事件；样本量策略及参数；假设检验；多重性；缺失值；模型/协变量；敏感性分析；期中分析/DMC/操作防火墙 | 样本量、效应量、变异性、alpha/beta、优效/非劣界值、统计模型、分层因素、缺失值策略、期中分析、DMC、提前终止和转组规则。 |

补充规则：一期的 SAD、MAD、首次患者、食物影响、物质平衡、肝/肾损伤、DDI 等应作为可多选
的 `phase1_parts` 待决定结构，而不是由“Ⅰ期”自动加入。对照、盲法、随机、期中分析、OLE、
交叉、转组和样本量再估计均是独立设计维度，只有得到项目明确事实或用户选择后才进入章节
计划、方案摘要、研究流程表和统计章节。

## 7. 测试矩阵

### 7.1 目录构建与版本

1. 只有药物/适应症/分期时，catalog 仅含三个项目身份条目；所有精确 PICOS 包为
   `pending_decision`。
2. 已确认摘要的多个 `field_evidence_span_ids` 形成对应字段条目；相同文本但不同 locator
   必须保留不同 catalog entry。
3. 未确认摘要、失效 artifact、解析失败 artifact、跨项目 source、旧 extraction revision 和
   无 span 的 IB source ID 均不得进入 catalog。
4. IB 有明确“口服、每日一次、剂量递增”摘录时，catalog 允许这些明确字段；删除或更新
   IB 后 catalog hash 改变，旧 package 标记 stale。
5. CT.gov snapshot 每个 NCT 的 Brief Summary、干预类型、allocation、masking、model、入组数
   分别进入；仅标题/文件名不能生成设计条目。
6. catalog 超上限时稳定截断，重复 generate 的 entry 顺序/hash 一致；任一 span text/hash 或
   snapshot ID 改变则 hash 改变。

### 7.2 模型输出/服务器验证

1. 正确 `catalog_entry_id + source_id + locator + quote_sha256` 通过，响应中的 quote 被服务端
   回填为原文。
2. source ID 正确但 locator 错、同一文本来自另一 locator、quote hash 错、跨项目 ID、目录
   hash 错、虚构 entry、非连续 substring、模型翻译后的 quote 都失败关闭。
3. 仅 `source_id`、仅 `evidence_refs`、或一个 binding 覆盖多个不相干 target paths 均不得使
   精确值进入推荐或批量采用。
4. 只允许无实质变化的 NFKC/空白/有限标点规范化；规范化成功后比较和持久化的仍是原始 quote。
5. 非空精确数组每个元素都需要 binding；空值可以留在 `pending_decision`。不支持路径或未知
   JSON pointer 必须被拒绝。
6. provider/model 必须保持 `deepseek/deepseek-v4-pro`，且生成 run 记录 catalog hash、prompt
   version、输入 source IDs、validation errors；任何非独立 provider/模型标识不匹配均失败关闭。

### 7.3 D017 专项反例

以 D017 干净项目、当前不可变 CT.gov 快照和无 IB 状态至少覆盖：

| 反例 | 期望结果 |
| --- | --- |
| CT.gov 英文标题 `Phase 2 Study of CMS-D017 in PNH` | UI 候选中文；不得把英文标题直接作为方案标题，且不得捏造随机、成人或研究目的。 |
| 竞品 `Allocation=RANDOMIZED` | 可显示“该竞品采用随机分配”的可追溯观察；当前项目的 `randomization_mode` 仍为待决定，候选为 `manual_only`。 |
| 竞品 masking/placebo | 同上；不能得到“本项目双盲/安慰剂对照”的推荐。 |
| 竞品成人入选 | 不得产生“D017 成人 PNH 患者”项目事实；只能形成带竞品来源的研究人群选项或待补项目资料卡。 |
| 竞品药物类型、给药途径、靶点/机制 | 不得填入 CMS-D017 机制、口服/注射或剂型。没有 IB/项目明示 span 时全部保持 unknown/pending。 |
| 剂量、频次、队列、洗脱、终点、Week 时间点 | 未有项目明确 span 时不得出现在可采用候选中；必须作为证据缺口。 |
| 样本量、alpha/beta、优效/非劣、分层、期中分析、DMC | 即使竞品有这些字段，当前项目的 statistics 包仍是 pending；不得按 II 期默认 RCT/DMC。 |

### 7.4 回归与用户流程

1. 现有无证据绿色建项仍能 `POST /prefill-package/generate` 并得到可编辑 pending packages，
   不破坏旧 package JSON。
2. 用户选中 pending 候选或填写自然语言后，保存为用户确认而非“待医学批准”；下一次 AI
   生成保留其来源和优先级。
3. 带确认摘要/IB的项目，AI 可生成 3-5 个实质不同的中文候选；每个直接事实均能在 UI 中
   展示原文、来源名称、locator 和版本。
4. 真实产品 AI 端到端验收必须用独立 DeepSeek，而不是测试模型：至少 D017 无 IB、一个
   有摘要、一个有 IB 的不同非肿瘤项目各跑一次，且逐候选人工核对目录条目。

## 建议的窄写集和实施顺序

为避免与 W2a、W3、前端并发写冲突，W2b 第一轮建议仅允许执行成员修改：

```text
packages/contracts/workbench_contracts/models.py
packages/contracts/workbench_contracts/__init__.py                 # 仅新增导出
services/api/app/medical_writing_authoring_prefill_ai.py
services/api/app/medical_writing_authoring_prefill.py              # 仅 catalog 投影/验证入口
services/api/app/medical_writing_authoring_journey.py              # 仅持久化 catalog/run 指针
services/api/app/main.py                                           # 仅注入 repository/run store
tests/test_medical_writing_authoring_prefill_evidence_catalog.py   # 新增
tests/test_medical_writing_authoring_prefill_ai_quality.py         # 仅新反例
tests/test_medical_writing_authoring_prefill.py                    # 仅必要兼容断言
```

不修改：前端、既有 writing-reference 数据、数据库历史快照、竞品分诊、DOCX 导出、W3 组合
采纳事务、用户确认语义。`writing_reference_repository.py` 只有在当前读取 API 无法返回项目
可用 spans 时才作为第二轮极窄补充；先复用其已有 `source_span()`/`source_spans()` 和
`evidence_briefs()` 查询能力。

推荐执行顺序：

1. 增加 catalog/claim binding 合同与纯服务端 catalog builder 单测；
2. 将 DeepSeek 输入切换为 catalog，新增输出 schema 和 fail-closed validator；
3. 持久化 prefill AI run 与 catalog hash，接入现有 generate 路径；
4. 用 D017 反例和两个带明确资料的真实项目进行产品独立 AI 验收；
5. W2b 通过后才进入 W3 的组合原子采纳和 W4 的推荐优先前端。

## 读取来源、证据与未决风险

### 读取来源

- `AGENTS.md`（项目规则与执行边界）
- `records/active_slices/medical_writing_production_rebaseline_20260722/TASK_RECORD.md`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/writing_reference.py`
- `services/api/app/writing_reference_repository.py`
- `services/api/app/ai_task_runner.py`
- `services/api/app/main.py`
- `packages/contracts/workbench_contracts/models.py` 与 `__init__.py`
- 相关 prefill、registered-source、AI citation 测试文件。

### 直接证据

- 当前合同已保存 source ID、locator、原文和 quote hash，但候选没有 catalog identity 或
  claim-level mapping。
- 已确认摘要能够按 `field_evidence_span_ids` 取得原文 span；writing reference 模块能够按
  artifact/revision 查询含页码和 block 的 extracted span；CT.gov 快照已保存显式设计字段。
- 当前 DeepSeek prefill payload 仅发送 `registered_source_ids`，解析阶段只过滤 ID 是否登记；
  代码自身已注明当前没有可核验的 source excerpts，因此对设计事实采取 fail-closed。
- `ai_task_runner` 已有可复用的原文连续摘录、规范化比较和 source+locator 绑定模式，但尚未
  应用于 prefill candidate generation。

### 未决风险

1. project source registry 和 writing-reference repository 的运行时装配关系需在实施前按当前
   `main.py` 真实实例确认，避免 W2b 再建一个平行存储。
2. 一些摘要/IB字段是自由文本，不能由 source quote 自动证明“医学等价”；第一版应仅对
   枚举/字段映射做确定性升级，其余保留为有来源但待决定的文本候选。
3. 竞品中文翻译的可读性与原文事实的权威性必须分层保存；不能用中文改写覆盖英文原文 hash。
4. catalog 大小、截断策略和 UI 展示原文长度需要在真实项目上测量；过大将损害产品 AI 输出，
   过小会遗漏关键 IB/摘要证据。
5. W2b 不能解决 W3 原子组合采纳、章节动态分支、前端入口和最终 DOCX；这些仍需后续切片。

## 审阅结论

W2b 可以在不引入新外部依赖、不替换产品 AI、且不改变现有 generate API 的前提下实施。最小
可靠路径是：**服务端构建不可变证据目录 -> 独立 DeepSeek 按 catalog 产生 PICOS 组合候选
和 claim binding -> 服务端重绑原文并逐项验证 -> 无证据降为 pending decision。** 这比继续
扩展 prompt 或允许 `source_id` 白名单更符合独立运行、科学可追溯和用户“AI 先填、用户修订”
的产品目标。
