# R6 外部报告审阅与模式化输出合同 v0.1

状态：`CANDIDATE_FOR_INDEPENDENT_ACCEPTANCE`

本文件是 R6 合同候选稿，供后续独立会商、machine-readable contract 校验和
synthetic/offline runtime 规划使用。它不是产品实现、医学结论、真实项目报告或
用户确认记录。只有 prose、`contract.json`、`challenge_matrix.json` 字段/枚举/
计数/错误语义一致，并且独立会商在稳定字节上返回接受后，才可规划 R6 第一条
synthetic/offline runtime 纵切。

## 1. 权威来源、范围与术语

合同以以下来源为准：

1. `reviews/medical_monitoring_ai_native_system_design_v1_20260809.md`（文件路径
   保留 `v1` 作为恢复锚点，正文为 System Design v1.1），重点为 §§5、5.1、5.2、
   6.1–6.4、8.2、10.1–10.4、12、13、14、15.2–15.4、17.1、18；
2. `context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md`，
   重点为 §§2、3、5、10、11 的 R0–R8 边界、R1/R2 接口约束和 R6 完成证据；
3. `context/medical_monitoring_r6_contract_freeze_20260827.md`，作为本轮合同冻结
   的任务边界、输出路径、禁止事项和完成门；
4. 已存在的 R1/R2 合成合同实现只用于接口相容性核对：
   `poc/medical_monitoring_ai_native_r1/src/mm_r1/report_review.py`、
   `poc/medical_monitoring_ai_native_r1/src/mm_r1/modes.py`、
   `poc/medical_monitoring_ai_native_r2/src/mm_r2/modes.py`。它们不是 R6 的
   医学事实来源，也不解除 R6 的独立接受门。

本合同只冻结外部报告审阅、三件套、`ClaimCoverageLedger` 和三模式输出语义。
不修改产品/runtime/医学写作，不启动服务、模型、OCR、真实 provider 或真实项目。

规范性用语：`MUST` 表示实现必须满足；`MUST NOT` 表示禁止；`MAY` 表示明确
允许但必须保留身份、来源和状态。

## 2. 权威边界与对象所有权

对象不因出现在同一报告中而共享医学权威。以下边界不可合并：

| 对象/来源 | 权威含义 | R6 可做的事 | R6 不可做的事 |
|---|---|---|---|
| 外部报告原始字节 | 仅证明外部报告实际写了什么 | 冻结、定位、抽取、逐条比较 | 覆盖、修订原件，或把它当作医学真值 |
| R1–R5 source/fact/risk/Profile/Timeline authority | 项目事实、风险、时间轴和既有决定的来源链 | 作为报告 claim 的证据引用 | 由报告文字反向提升为 `CanonicalFact`、正式风险或用户决定 |
| `ReportReviewMatrix` | R6 报告审阅的结构化权威 artifact | 保存 claim、issue、coverage、证据和 diff | 代替原始来源、用户确认或外部回复 |
| 批注副本 | 矩阵的格式化投影 | 在原版副本上叠加可验证批注 | 改写原始内容或隐藏未决 issue |
| 清洁修订稿 | 可选的用户按需草稿 | 根据矩阵生成，并显式标记 `DRAFT` | 冒充最终版、签署版、用户确认版或对外发送件 |
| `QueryDraft` | 依据＋发现＋行动项的草稿 | 生成、编辑、导出 | 发送、跟踪外部回复、关闭 Query/PD |

所有输出必须来自同一个 `project_id × run_id × data_cutoff × source_revision_id`
及同一 facts/risk/decision authority。外部报告审阅三件套与系统自产报告必须有
不同的 `producer_kind`，不能通过文件名、页面标题或用户界面位置隐式区分。

## 3. 身份合同

### 3.1 公共运行身份

每一个 R6 artifact、issue、coverage ledger 和 mode output MUST 携带下列共同绑定：

```text
project_id
run_id
mode
execution_basis
data_cutoff
source_revision_id
knowledge_pack_version
rule_activation_version
mapping_version
identity_algorithm_version
identity_algorithm_digest
schema_version
```

其中：

- `project_id` 是 `StudyProject` 的隔离主键；不同研究不得复用业务主键或静默
  共享 issue/claim/coverage；
- `run_id` 是一次不可变 `MonitoringRun` 的主键。模式、cutoff、源修订、执行基线
  或明确的 carry-forward 关系变化 MUST 产生新 `run_id`；重试不是新医学 run；
- `data_cutoff` 是数据截止的规范化标识，不得只依赖显示文案或文件修改时间；
- `source_revision_id` 是 Run 所绑定数据/快照的通用不可变 `SourceRevision` 身份；
  外部报告还必须带 `report_source_revision_id`（报告自身通用 `SourceRevision` 的
  显式链接）、`report_lineage_id`、`report_revision_id` 和 `report_artifact_id`。
  Run 的 `source_revision_id` 与报告的 `report_source_revision_id` 不得互换；
- `identity_algorithm_version` 和 `identity_algorithm_digest` 必须被 Run 冻结，
  不能在修订比较中隐式升级；
- 所有机器可寻址 artifact 使用内容寻址 `sha256`。哈希覆盖 canonical payload，
  不覆盖提交时才产生的时间戳/存储位置字段；原始报告的 `report_artifact_id` 必须
  能回溯到原始字节哈希。

### 3.2 外部报告来源和修订身份

`ReportSourceRevision` 至少包含：

```text
report_lineage_id          # 同一报告系列跨修订保持不变
report_revision_id         # 每个不可变文件/版本唯一
source_revision_id         # 通用来源版本身份
report_source_revision_id  # 报告自身 SourceRevision 的显式链接，避免与 Run 来源混淆
report_artifact_id         # 原始字节内容哈希
project_id
media_type                 # docx | pdf | html | other
source_name
reported_version_label     # 报告中声明的版本，可为空但必须记录缺失
reported_data_cutoff       # 报告声明的截止，可为空但必须显式缺失
reported_cutoff_status     # declared | missing | ambiguous
received_at
parent_report_revision_id  # 首版为空；修订版指向前一版
source_scope
immutable                  # MUST be true after registration
```

在该对象中，`report_source_revision_id` 必须等于报告自身通用
`SourceRevision.source_revision_id` 的显式链接；它与 Run 绑定的
`source_revision_id` 是两个不同字段，即使底层类型相同也不得省略报告前缀。

注册规则：

1. 原始文件注册后冻结；同一 `report_artifact_id` 的重复导入只能去重或返回已有
   身份，不得伪造新的临床修订；
2. 报告声明的新版本、内容哈希变化或受控修订必须创建新
   `report_revision_id`/`report_source_revision_id`（以及其对应的通用
   `SourceRevision`），并保留父修订；旧报告、旧矩阵、旧批注副本和旧草稿不覆盖；
3. `report_lineage_id` 仅表示版本家族，不表示内容相同；跨修订是否为同一 claim
   或 issue 必须经过稳定身份算法和证据核对；
4. 报告缺少版本或 cutoff 不是“当前版本”的默认值，而是显式
   `missing_report_version`/`missing_report_cutoff`（分别通过版本缺失标记和
   `reported_cutoff_status` 表达），需要 `not_evaluable` 或对应 issue；
5. 文件路径、页码、表号等展示定位不是来源身份。它们只属于
   `ReportLocator`，且必须和来源哈希、revision 一起使用。

### 3.3 claim、issue 和跨修订稳定身份

`ReportClaim` 是某一报告修订中可独立比较的原子主张；`claim_id` 只在一个
`report_revision_id` 内唯一。跨修订使用：

```text
claim_identity_key = hash(
  project_id,
  report_lineage_id,
  scope,
  normalized_claim_concept,
  normalized_subject_or_site_scope,
  normalized_temporal_window,
  identity_algorithm_version,
  identity_algorithm_digest
)
```

原子主张必须保留原文、规范化概念、scope、时间窗、报告截止、来源定位和
`claim_identity_key`。模型只能产生候选；确定性解析和证据核对决定是否进入正式
`ReportClaim` artifact。

`ReviewIssue` 是报告审阅发现的问题，不是风险事实。其稳定身份不得由页码、段落
序号或模型生成的标题单独决定：

```text
issue_identity_key = hash(
  project_id,
  report_lineage_id,
  normalized_clinical_concept,
  normalized_subject_or_site_scope,
  normalized_temporal_window,
  identity_algorithm_version,
  identity_algorithm_digest
)
```

Issue 必须保存当前 claim/报告修订引用，并可保存跨修订的
`related_issue_ids`。若确实发生 merge/split，必须追加可重建的 transition，不能
悄悄把一个 issue 改成另一个 issue。Issue 的稳定身份也不能把 `unsupported`、
`outdated_wrong_cutoff` 等审阅状态提升为事实状态。
`claim_kind`、`issue_kind` 与 `evidence_relation` 都是当前 occurrence 的分类，不进入
跨修订稳定 key；分类变化必须保存 `reclassified` transition，merge/split 同理保存
来源和目标 issue IDs。这样同一临床命题的重新分类不会伪装成旧问题消失和新问题
出现。

### 3.4 Locator 和 evidence reference

`ReportLocator` 至少含：`report_revision_id`、`unit_id`、`unit_type`、页/节/表/
图/脚注/段落等结构定位、可选字符/单元格范围、锚点摘要、提取方法和
`report_artifact_id`。页码或 offset 不可用时，必须使用可解释的结构锚点；无法验证
锚点则为 `anchor_status=broken|unverified`，不能被写成已验证批注。

`EvidenceRef` 至少含：`evidence_id`、`authority_class`、`source_revision_id` 或
`authority_artifact_id`（二者至少一个）、`snapshot_id`、`data_cutoff`、locator、content hash 和
`relation`（`supports|contradicts|qualifies|context_only`）。证据 cutoff 与目标
Run 不一致时不能支持 `supported`。报告声明的 cutoff 与目标 Run 不一致时不能支持
`supported`；报告未声明或声明不明确时，`reported_cutoff_status` 必须保持
`missing`/`ambiguous`，不能填充当前 Run cutoff。

### 3.5 Canonical enum registry

为防止 prose、machine contract 和挑战矩阵漂移，v0.1 的 canonical 枚举集中如下；
同名字段不得另造同义值：

```text
mode: daily | pre_lock | post_lock_pre_cfdi
execution_basis: full | incremental
source_state: registered | immutable_frozen | structurally_parsed | reviewable | superseded | blocked
report_review_state: not_started | running | coverage_open | coverage_closed | evidence_reviewed | qc_passed | blocked | failed
report_media_type: docx | pdf | html | other
reported_cutoff_status: declared | missing | ambiguous
report_unit_type: document | page | section | body | table | figure | footnote | denominator | cutoff
claim_kind: numeric | categorical | temporal | trend | comparison | risk_statement | scope_qualifier | conclusion | other
claim_status: supported | partially_supported | unsupported | outdated_wrong_cutoff | overstated | understated | internally_inconsistent | not_evaluable
issue_kind: unsupported | partially_supported | outdated_wrong_cutoff | overstated | understated | internally_inconsistent | omitted | not_evaluable | anchor_invalid | coverage_gap | source_revision_mismatch | identity_mismatch | unresolved_conflict
issue_lifecycle_state: open | partially_resolved | resolved | superseded | not_evaluable | reopened
issue_revision_diff_state: new | unchanged | unresolved | partially_resolved | resolved | reopened | superseded | not_evaluable
issue_transition_kind: reclassified | merge | split
issue_severity: info | low | medium | high | critical | unknown
coverage_status: claimed | no_claim | not_evaluable | partial | truncated
extractability: text | table | vector | image | ocr | unextractable | unknown
anchor_status: verified | unverified | broken | not_applicable
annotation_mode: in_place_copy | sidecar
bundle_state: assembled | qc_blocked | qc_passed
producer_kind: system_monitoring_output | external_report_review
output_kind: change_summary | current_full_risk | affected_query_draft | data_knowledge_rule_model_change_note | full_risk | revision_impact | check_package | query_revision_package | full_project_report | site_materials | subject_materials | checklist | external_report_review_bundle | report_review_matrix | report_annotated_copy | report_clean_draft
```

本合同结构计数（不含 worker_02 的挑战案例计数）固定为：`mode=3`、三件套
`piece=3`、`report_unit_type=9`、`claim_status=8`、`coverage_status=5`、
`output_kind=16`、合同级确定性 validator `=11`、禁止边界 `=16`。枚举或禁止项
新增/删减必须提升合同版本并重新走独立接受，不能只改计数。

## 4. 对象合同

### 4.1 `MonitoringRun`

Run 顶层身份为：

```text
StudyProject
× ModeContract
× data_cutoff
× source_revision(s)
× execution_basis(full | incremental)
× frozen knowledge/rule/mapping/identity/schema/profile versions
```

Run 必须记录：`run_id`、`project_id`、`mode`、`execution_basis`、`data_cutoff`、
`source_revision_id`、当前报告修订引用（如有）、快照/接受证据引用、
`carry_forward_run_ids`、版本哈希、actor 和创建时间。受试者、中心、风险域和
报告 claim 是 Run 内 work unit，不是新顶层 Run。

### 4.2 `ReportUnit`

`ReportUnit` 是 coverage 的最小期望单位。v0.1 的标准 `unit_type` 为：

```text
document | page | section | body | table | figure | footnote | denominator | cutoff
```

实现可以为表格、正文或脚注建立更细的子单元，但不得把子单元从期望集合中静默
删除。每个 unit 具有 revision 内唯一 `unit_id`、结构定位、父 unit、提取方法、
是否必需、可选 `declared_cutoff`/`computed_cutoff` 和 anchor digest。
根 `document` 的 `parent_unit_id=null`；其他 unit 必须指向可解析父 unit。六类内容
单元（body/table/figure/footnote/denominator/cutoff）必须进入挑战矩阵；document、
page、section 是结构容器，只要解析器生成，就同样进入冻结 expected set，不得被
运行时从覆盖分母中删除。

### 4.3 `ReportClaim`

`ReportClaim` 最少字段：

```text
claim_id
claim_identity_key
report_lineage_id
report_revision_id
report_source_revision_id
project_id
run_id
unit_ids[]
claim_kind
source_text
normalized_claim_concept
scope { project | site | subject | risk_domain | other }
temporal_window
report_cutoff
report_cutoff_status
status
evidence_refs[]
issue_ids[]
locator
```

一个 claim 可以跨多个 unit；一个 unit 也可以承载多个 claim。R1 POC 的单元零/一
claim 结构只能作为兼容输入/输出投影，R6 canonical schema MUST 使用
`unit_ids[]` 和 `claim_ids[]` 的多对多关系，不能以 R1 限制实现 R6。
`claim_kind` 只能使用 3.5 节的闭集枚举。

### 4.4 `ReviewIssue`

`ReviewIssue` 最少字段：

```text
issue_id
issue_identity_key
project_id
run_id
report_lineage_id
report_revision_id
report_source_revision_id
issue_kind
claim_ids[]                  # 遗漏问题可为空
unit_ids[]
severity { info | low | medium | high | critical | unknown }
clinical_or_document_scope
evidence_refs[]
source_locators[]
lifecycle_state
revision_diff_state
related_issue_ids[]
transition_refs[]
current_note
```

遗漏问题可以没有 `claim_id`，但必须有可定位的 unit/报告范围或当前风险反向检测
证据；不能用空 claim 隐藏缺失抽取。高风险、重要结论、证据冲突和低置信度 issue
不得由多数票或模型裁决静默关闭。

### 4.5 `ReportReviewMatrix`

该 artifact 是三件套的唯一结构化权威，至少包含：报告来源身份、目标 Run 绑定、
全部 claims、全部 issues、evidence refs、`ClaimCoverageLedger` 引用、跨修订
diff（若有）、未决冲突列表、QC 状态和禁止正式输出的原因。矩阵的
`artifact_type` 固定为 `report_review_matrix`。历史输入中的 `payload_role=ledger`
与 `payload_role=report_review` 都只能投影为同一语义；本合同唯一 canonical 值为
`report_review`；R1 的 `ledger` 仅是兼容输入别名，不进入 R6 闭集枚举，也不得产生
第二种 artifact identity。R1 `post_lock` 的 `full_report` 同理，只能投影为 R6
canonical `full_project_report`。

## 5. 正交状态和错误语义

### 5.1 Run/artifact 的正交状态

R6 继续使用设计的正交状态，禁止用一个 `complete` 同时表达分析、证据、审阅和
输出：

| 维度 | 枚举 | 语义 |
|---|---|---|
| `analysis_state` | `not_started | running | complete | blocked | failed` | manifest 所声明的分析是否执行完成 |
| `evidence_state` | `complete | partial | truncated | not_evaluable | conflicted` | 输入/证据是否足以评价 |
| `review_state` | `not_required | deterministic_verified | independent_ai_reviewed | needs_user_attention | user_confirmed` | 审阅或用户动作的真实状态 |
| `output_state` | `not_published | dashboard_visible | draft_exportable | exported` | 投影/导出的实际状态 |
| `user_disposition` | `confirmed | edited | rejected | exported`，可空 | 只有实际用户动作才记录 |

`analysis_state=complete` 不等于医学结论已确认。R6 任何输出门还必须通过来源、
coverage、cutoff、revision、issue 和格式身份检查。

### 5.2 来源/报告审阅状态

来源和报告审阅可使用以下机器状态；它们是过程状态，不替代 5.1 的正交状态：

```text
source: registered | immutable_frozen | structurally_parsed | reviewable |
        superseded | blocked
report_review: not_started | running | coverage_open | coverage_closed |
               evidence_reviewed | qc_passed | blocked | failed
```

`superseded` 只表示来源/身份被新修订取代，不表示临床问题已解决。
`blocked`、`failed`、`partial` 和 `truncated` 必须带可定位 reason；不能降级成
`no_claim` 或 `supported`。

### 5.3 Claim evidence status

`ReportClaim.status` 的 canonical enum：

```text
supported
partially_supported
unsupported
outdated_wrong_cutoff
overstated
understated
internally_inconsistent
not_evaluable
```

状态仅描述该报告主张与冻结证据的关系。`unsupported` 不是“没有风险”；
`not_evaluable` 不是 negative；`outdated_wrong_cutoff` 不是问题已解决；
`overstated/understated` 不可通过改写 claim 原文消除。

### 5.4 Issue 生命周期和修订 diff

`lifecycle_state` 的 canonical enum：

```text
open | partially_resolved | resolved | superseded | not_evaluable | reopened
```

`revision_diff_state` 的 canonical enum：

```text
new | unchanged | unresolved | partially_resolved | resolved |
reopened | superseded | not_evaluable
```

规则：

- 首次出现的稳定 issue 为 `new` + `open`；
- 新报告中的同一稳定 issue，若命题、生命周期和支持/反证集合均无实质变化，记为
  `unchanged`；若问题仍未解决但措辞、locator、证据集合或周边报告语境发生变化，
  记为 `unresolved`；二者都不能自动清零；
- 新报告只修复部分证据/措辞为 `partially_resolved`；
- 证据和覆盖均证明问题已真正纠正才可为 `resolved`；
- source/rule/mapping/identity/cutoff 变化导致无法比较时为 `not_evaluable` 或
  `superseded`，不能伪装成 resolved；
- 后续修订重新暴露已 resolved 的同一稳定问题为 `reopened`；
- 每一个 diff 都必须保存前后 revision、前后 claim/unit 引用、判定理由和证据。

## 6. `ClaimCoverageLedger` 合同

### 6.1 期望集合和字段

ledger 必须先冻结 `expected_unit_set`，其 hash 和计数进入不可变 payload：

```text
ledger_id
run_id
project_id
report_lineage_id
report_revision_id
report_source_revision_id
report_artifact_id
expected_unit_set_hash
expected_unit_count
entries[]
claims[]
claim_unit_links[]
issue_unit_links[]
coverage_closed
coverage_counts
full_report_reviewed_eligible
blocking_reasons[]
```

每条 entry 至少包含：

```text
unit_id
unit_type
parent_unit_id
required
locator
extractability { text | table | vector | image | ocr | unextractable | unknown }
anchor_status { verified | unverified | broken | not_applicable }
coverage_status
claim_ids[]
issue_ids[]
reason
```

根 `document` entry 的 `parent_unit_id=null`；非根 entry 必须有可解析父单元。
`reason` 仅在状态不需要说明时可空，`not_evaluable/partial/truncated` 必须有 reason。

`expected_unit_count` 是结构解析确定的分母；`entries` 不得通过只列出成功单元来
改变分母。所有 expected unit 必须恰好出现一次；多余、重复、孤儿 claim/link 或
未知 issue 都是阻断错误。

### 6.2 Coverage status

`coverage_status` 的 canonical enum：

```text
claimed | no_claim | not_evaluable | partial | truncated
```

- `claimed`：已抽取至少一个 claim，并且该 claim 与 comparison/evidence link 可追溯；
- `no_claim`：已完成该 unit 的抽取/检查，确实未发现报告主张。通常 `claim_ids=[]`；
  如当前风险反向检测到遗漏，可同时有 omission issue，但不得把 issue 当作 claim；
- `not_evaluable`：单元存在，但由于扫描、不可提取、损坏、缺失定位或证据条件不足
  无法评价；必须带 reason、extractability/anchor 状态和补救方向；
- `partial`：只处理了部分 unit/内容/claim；必须阻断 full-report claim；
- `truncated`：输入、提取或分析在终点前截断；必须阻断 full-report claim。

`missing` 不作为合法 entry status，而是 expected unit 没有 entry 的派生阻断错误。
报告单元不使用 `not_applicable` 掩盖缺页或未抽取；设计条款明确“不适用”只能
作为 reason/附加适用性字段，不能消除报告覆盖分母。

### 6.3 关闭和“全报告已审阅”资格

ledger 分成两个明确结果：

1. `coverage_closed=true`：期望集合非空、entry 一一对应、没有 missing/duplicate/
   orphan、所有 entry status 合法、`not_evaluable` 均有 reason、claim/issue/link
   均可解析；这只表示覆盖账已闭合；
2. `full_report_reviewed_eligible=true`：除 `coverage_closed` 外，还必须满足所有
   期望内容均可提取、anchor 已验证、没有 `partial`/`truncated`/`not_evaluable`、
   每个 claim 都有与目标 cutoff/revision 一致的 comparison、没有阻断性来源/版本
   冲突，且 `expected_review_surface` 非空、hash 已验证、`reverse_coverage_links`
   精确一一对应且无空映射，并且三件套 QC 通过。

因此，显式有理由的 `not_evaluable` 可以让 ledger 完成“账务闭合”，但不能让系统
声称“全报告已审阅”。这是对 R1 POC 允许显式 reason 的兼容性扩展：R1 的
`full_report_reviewed` 结果不能直接用作 R6 公共输出门。

### 6.4 Coverage 错误优先级

确定性 validator 按以下顺序保留所有阻断原因，不以第一个错误覆盖其余错误：

```text
expected_set_missing
expected_unit_missing
duplicate_unit_entry
unexpected_unit_entry
reverse_omission_uncovered
invalid_coverage_status
unreasoned_not_evaluable
partial_unit
truncated_unit
claim_without_unit
unit_claim_link_unknown
issue_without_unit_or_evidence
anchor_unverified
cutoff_mismatch
revision_mismatch
evidence_comparison_missing
```

空结果必须可区分：`no_claim`（已检查且无主张）、`not_evaluable`（存在但不能
评价）、`partial/truncated`（处理未完成）和 `failed`（节点/系统失败）不得互换。

### 6.5 风险/指标反向遗漏覆盖

`ReportReviewMatrix` 必须在比较报告前，从已接受的 risk/metric/protocol authority
冻结 `expected_review_surface[]`。每条 expectation 至少包含：

```text
expectation_id
expectation_kind { accepted_risk | accepted_metric | protocol_control_point }
authority_ref
scope
temporal_window
```

expected surface 在报告比较前冻结并生成 `expected_review_surface_hash`；比较结果不得
回写或改变该分母。每个 expectation 另有且仅有一个 `ReverseCoverageLink`：

```text
expectation_id
claim_ids[]
issue_ids[]
not_evaluable_exception
evidence_refs[]
```

`reverse_coverage_links[]` 必须与 expected surface 精确一一对应；每条至少映射一个
报告 claim、一个 omission/review issue，或一个带 reason、报告 scope 和证据的
`not_evaluable_exception`。空映射产生 canonical
`reverse_omission_uncovered`，阻断完整审阅和正式输出。外部报告没有写到某项内容
不能被解释为没有风险，也不能只因没有 claim 而从 expected surface 删除。

## 7. 三件套与修订 diff

### 7.1 Bundle 身份

`ReportReviewBundle` 必须保存：

```text
bundle_id
project_id
run_id
mode
data_cutoff
source_revision_id
report_lineage_id
report_revision_id
report_source_revision_id
report_artifact_id
matrix_artifact_id
annotated_artifact_id
clean_draft_artifact_id       # optional
matrix_content_hash
annotation_map_hash
issue_set_hash
coverage_ledger_id
bundle_state
```

三件套共享 issue ID、evidence refs、source locator、Run/cutoff/revision 和
`issue_set_hash`。它们不能各自重新生成一套 issue identity。
`bundle_state` 只能为 `assembled | qc_blocked | qc_passed`；只有 `qc_passed` 才能
满足三件套输出资格。
三件套还必须共享 `execution_basis`、knowledge/rule/mapping 版本、
`identity_algorithm_digest` 与 `schema_version`，不能只凭同一个 `run_id` 推断这些
冻结版本一致。

### 7.2 结构化问题矩阵（必需）

`report_review_matrix` 是必需件，保存 claims、comparisons、issues、coverage、
revision diff、未决冲突、QC 结果和输出资格。矩阵可包含“支持/反驳/无法评价”三
类证据，但不得覆盖原报告文本或把未解决冲突删掉。

### 7.3 带批注副本（必需）

`report_annotated_copy` 是保留原文的批注投影：

- `source_bytes_hash` 必须等于原始报告 artifact hash，或在容器/sidecar 形式下
  明确记录原始文件 hash；
- 每条 annotation 必须引用 `issue_id`、matrix hash、原始 revision 和已验证 locator；
- 若 DOCX/PDF/HTML 无法原位批注，生成旁注/sidecar 副本，字段
  `annotation_mode=sidecar`，并明确“不是原位修改”；
- 只要无法以确定性检查证明原位批注无损且锚点保真，就必须使用 sidecar，而不是
  为追求视觉原位效果进行有损重打包；
- 锚点不能只依赖页码或显示顺序；页重排、表格跨页、图形和脚注都要能被
  `anchor_status` 验证；
- 批注副本不能删除、重排或润饰未被授权修改的原文。

### 7.4 清洁修订稿（可选）

`report_clean_draft` 只有用户按需请求才生成：

- `draft_label` 必须为可见、机器可检出的 `DRAFT`；`is_final=false`、
  `is_user_confirmed=false` 初始固定；
- 每个修改段/表/图/脚注必须关联一个或多个 `issue_id`，并保留 before/after
  provenance；
- 未决 issue、证据冲突、not_evaluable 单元和缺失 cutoff/版本不得从草稿删除；
  若不能安全改写，保留原文并添加明确的 unresolved note；
- 清洁稿是新 artifact，不覆盖原件或批注副本；导出它仍只表示导出草稿，不等于
  发送、签署、用户确认或正式医学结论；
- 若 matrix coverage 或 issue coverage 未通过，清洁稿可作为不可发布的内部草稿
  保存，但不得进入 `draft_exportable` 或 `exported` 的对外语义。

### 7.5 修订报告重审

新报告修订必须以新 `ReportSourceRevision` 重新建立 claims、coverage 和 evidence
comparison；旧 issue 不被删除。通过稳定 identity 和显式 transition 生成 diff：
`new/unchanged/unresolved/partially_resolved/resolved/reopened/superseded/
not_evaluable`。没有兼容身份或 cutoff/revision 对不上时，diff 为
`not_evaluable`，而不是 resolved。

## 8. 三模式 `ModeContract` 和输出资格

### 8.1 共同规则

三个 mode contract 均不可变；模式、cutoff 或 source revision 变化必须创建新 Run。
跨模式只允许显式 `carry_forward_run_ids`，并记录 source/target Run、原因和
可复用 artifact hash。模式变化不得伪装成临床数据变化。

每个 mode output MUST：

1. 绑定当前 `run_id`、`mode`、`data_cutoff`、`source_revision_id`、版本哈希和
   coverage/QC artifact；
2. 由同一 facts/risk/decision authority 投影，数字、风险状态、分母和 cutoff
   不能跨输出漂移；
3. 把数据变化、知识/规则/mapping/模型变化和用户决定分别标记；
4. 在输出内保留 `producer_kind`：`system_monitoring_output` 或
   `external_report_review`；不把外部报告三件套命名成系统自产报告；
5. 无用户主动动作不发送、不外发、不创建“已发送/已关闭”的伪状态。

数值一致性先比较 canonical raw value；存在分子/分母时以同一 population/cutoff
下的精确重算为准。没有精确有理数表示时使用
`abs(a-b) <= max(1e-12, 1e-9*max(abs(a),abs(b),1))`。展示值只有在声明 precision 与
rounding mode 后才比较，展示舍入不得改变 raw verdict。只有分子/分母同为同一
人群、时间窗和 cutoff 的 unique-subject count 时才允许用 `numerator <= denominator`；
事件数可大于受试者数。

若 `producer_kind=external_report_review`，该 output 还 MUST 携带
`report_source_revision_id`、`report_lineage_id`、`report_revision_id`、
`report_artifact_id` 和 `coverage_ledger_id`；这些字段不能由 Run 的
`source_revision_id` 代填。

### 8.2 `daily`

**进入条件**

- 当前全量 listing/snapshot 已按接受链通过，project/source/mapping/identity
  无歧义；
- 明确 `data_cutoff` 和 `source_revision_id`；
- `execution_basis=incremental` 时必须有同项目、兼容 identity/mapping/rule/
  knowledge、且 evidence-complete 的 prior baseline；否则使用 `full`；
- 外部报告输入是可选的，不能因没有报告阻断日常风险摘要。

**截止、修订和 carry-forward**

- cutoff 是当前 accepted full snapshot 的一部分；新全量快照或报告修订产生新
  source revision/new Run；
- 可按影响传播做增量，但输出仍必须说明当前全量风险视图与 coverage；
- 从其他模式承接必须显式声明 prior Run，不得原地转换。

**输出资格**

```text
change_summary
current_full_risk
affected_query_draft
data_knowledge_rule_model_change_note
```

有外部报告输入且 R6 coverage/QC 门通过时，允许按需附加
`external_report_review_bundle`；不得默认把日常摘要扩展成锁库/CFDI 全量报告。

### 8.3 `pre_lock`

**进入条件**

- accepted full listing/snapshot；
- 用户明确的锁库准备窗口和 cutoff；
- source scope、mapping、record/risk identity 无歧义；
- `execution_basis=full`。

**截止、修订和 carry-forward**

- Query 后的每个全量 listing 修订必须创建新 SourceRevision/new Run；
- 全量风险、修订影响、检查包、报告 coverage 必须绑定同一 cutoff/revision；
- carry-forward 只能引用可追溯的完整 prior evidence，不能把修订伪装为同一版本。

**输出资格**

```text
full_risk
revision_impact
check_package
query_revision_package
```

有外部报告输入并通过三件套门时，可附加 `external_report_review_bundle`。

### 8.4 `post_lock_pre_cfdi`

**进入条件**

- accepted 且 baseline-eligible 的全量 snapshot；
- 用户明确选择的数据/时间锁定版本，选择记录必须绑定本地 OS 用户、snapshot
  hash 和 acceptance evidence hash；
- cutoff、固定总量和 source scope/identity 无歧义；
- `execution_basis=full`。

**截止、修订和 carry-forward**

- 固定总量；运行内 cutoff、snapshot、manifest 不得漂移；
- 任何受控修订创建新 SourceRevision/new Run，旧输出永不覆盖；
- locked version 的后续审阅只能仍绑定同一锁定 snapshot 或经显式新 revision/new
  Run 处理；不能改写既往 `exported`/`draft` artifact；
- 跨模式 carry-forward 仅作为来源，不能改变固定版本身份。

**输出资格**

```text
full_project_report
site_materials
subject_materials
checklist
```

有外部报告输入并通过三件套门时，可附加 `external_report_review_bundle`。该
bundle 仍然是外部报告审阅产物，不得改名为固定版本正式报告。

### 8.5 输出门的最小谓词

任意 mode output 只有在以下全部为真时才可声明其资格；其中
`full_report_reviewed_eligible` 仅在本 Run 确实有外部报告输入时适用。没有外部
报告输入的系统自产报告使用同一 facts/risk/decision authority 的完整覆盖和 QC
门，不伪造一个外部报告 ledger：

```text
mode_contract_matches_run
entry_conditions_verified
cutoff_and_revision_match
required_snapshot_acceptance_verified
analysis_state == complete
evidence_state == complete
required_coverage_closed
full_report_reviewed_eligible   # 仅有外部报告输入时的外部报告审阅输出要求
issue_and_conflict_policy_passed
deterministic_qc_passed
format_identity_qc_passed
```

输出资格只表示“满足该合同的导出/投影门”，不表示用户已确认医学结论。用户
确认只能由真实用户动作追加 `review_state=user_confirmed` 或
`user_disposition=confirmed/edited`。

## 9. 禁止边界

R6 合同和后续实现 MUST NOT：

1. 覆盖、重命名、删除或原位改写外部报告原件；
2. 把外部报告 claim、模型输出、基座条目或既有交付物当作绝对医学真值；
3. 以模型多数票、模型置信度、空列表、页面命中或非空 artifact 代替来源证据；
4. 用 `no_claim` 隐藏缺页、不可提取、扫描件、损坏、截断或未运行；
5. 把 `not_evaluable`、`partial`、`truncated`、`failed` 互换，或无 reason 关闭
   coverage；
6. 在 coverage 不闭合、anchor 未验证、cutoff/revision 不一致、证据冲突或 issue
   未覆盖时声称“全报告已审阅”；
7. 缩小 expected unit/denominator、删除既有数字或重置覆盖分母来制造 full coverage；
8. 仅用页码、段落序号、文件名、UI 文案、目录位置或模型 session 名称充当稳定
   issue/source identity；
9. 静默把 daily/pre_lock/post_lock_pre_cfdi 互相转换，或用原 Run 表示模式变化；
10. 静默漂移 cutoff、source/report revision、knowledge/rule/mapping/model 或
    execution basis；
11. 生成没有可见、机器可检出 `DRAFT` 标记的清洁修订稿，或把草稿冒充
    final/approved/signed；
12. 从矩阵、批注副本或草稿中删除未决 issue、证据冲突或 not_evaluable 限制；
13. 把三件套、系统自产报告、Query、checklist、Profile/Timeline 等输出混成同一
    artifact 身份；
14. 建立 Query 外部回复跟踪、PD 正式登记/关闭、电子签名或企业级数据外发审批；
15. 让 Agent/LLM 直接提升 canonical facts、风险、snapshot baseline、publication
    或 user-confirmed 状态；
16. 在本轮合同阶段读取/运行 MG-K10、Ruxolitinib、MY008、MY009 等真实项目，启动
    8911/5174/浏览器/OCR/模型/provider/长任务，或修改 `frontend/**`、`services/**`、
    `packages/**`、`runtime/**`、`deploy/**`、R1–R5 已接受代码/工件或 medical-writing
    路径。

## 10. 合同级确定性验证器

以下验证器是 R6 合同的最小可执行检查名；worker_02 的挑战矩阵和 worker_03 的
独立审计设计可以增加用例，但不得改变这些基本语义：

| ID | 检查 | 失败结果 |
|---|---|---|
| `R6-C-ID-001` | project/run/mode/cutoff/source revision/schema/identity digest 完整且 cross-link 一致 | `identity_mismatch` |
| `R6-C-SRC-001` | 原始报告哈希、lineage/revision/parent、不可变来源完整 | `source_revision_mismatch | source_not_immutable` |
| `R6-C-CLAIM-001` | claim status 合法；每条 claim 有来源 unit 和 locator；evidence cutoff/revision 可核对 | `claim_not_evaluable | claim_without_unit | evidence_comparison_missing | cutoff_mismatch | revision_mismatch` |
| `R6-C-ISSUE-001` | issue stable key、claim/unit/evidence/transition 可重建；diff 不靠页码单独决定 | `issue_identity_invalid | issue_transition_invalid` |
| `R6-C-COV-001` | expected set 与 entries 精确一一对应；count/hash/links/状态一致 | `expected_set_missing | expected_unit_missing | duplicate_unit_entry | unexpected_unit_entry | reverse_omission_uncovered | unit_claim_link_unknown | issue_without_unit_or_evidence` |
| `R6-C-COV-002` | partial/truncated/missing/unreasoned not_evaluable/anchor 未验证均被保留且阻断 | `coverage_incomplete | coverage_blocked | invalid_coverage_status | unreasoned_not_evaluable | partial_unit | truncated_unit | anchor_unverified` |
| `R6-C-BUNDLE-001` | 三件套共享 Run/source/issue/coverage/hash；原件未改；批注 anchor verified | `bundle_identity_mismatch | annotation_anchor_invalid` |
| `R6-C-DRAFT-001` | 清洁稿可选、DRAFT 可见、before/after 与 issue 关联，未决冲突未消失 | `draft_identity_invalid | unresolved_issue_dropped` |
| `R6-C-MODE-001` | mode entry、execution basis、cutoff/revision/fixed-total/carry-forward 符合对应 contract | `mode_entry_blocked | silent_mode_conversion` |
| `R6-C-OUT-001` | 输出资格、producer_kind、facts/risk/decision authority 和数字/cutoff 一致 | `output_not_eligible | authority_mismatch` |
| `R6-C-BOUNDARY-001` | 仅合同工件路径，无 runtime/product/real-project/service 写入或执行 | `scope_violation` |

这些 validator 只定义合同所需的确定性信号，不表示当前已有 R6 runtime；在独立
接受前不得把本文件或 `contract.json` 当作已通过的实现证据。

上述小写 token 是唯一 canonical gate failure code。挑战矩阵中的大写
`REPORT_* | MODE_* | FORMAT_* | DRAFT_* | ORIGINAL_*` 仅是场景诊断别名；每个别名
必须在 `challenge_matrix.error_code_map` 中恰好出现一次，并绑定一个 validator、
一个 canonical failure code 和 `blocking` 布尔值。类别到 validator 的映射不能
替代该逐码映射。`R6-C-BOUNDARY-001` 由 governed execution audit 验收，故不伪装成
正文/表格等内容挑战类别。

## 11. 当前实现计划边界

本轮只交付：

- 本 prose 合同；
- 对应的 `artifacts/.../contract.json`；
- 由 worker_02 独立交付、随后由 Codex 合并核对的 `challenge_matrix.json`。

本轮不交付：产品/runtime、服务、真实项目、医学写作、浏览器/PDF/DOCX 实际
渲染接受、外部报告实例、正式临床结论或用户确认。Codex 必须在稳定字节上独立
核对 prose、machine contract、challenge matrix 的字段/枚举/计数，并保留未通过或
待补来源的证据；只有完成独立会商后，才可规划第一条 synthetic/offline runtime。
挑战矩阵在本轮是可执行语义的 metadata oracle，不是 runtime fixture/schema；其
fixture catalog、JSON Pointer 实例和实际执行器属于合同接受后的第一条
synthetic/offline runtime 纵切。本轮必须先冻结对象、单变异、预期结果、逐码映射和
非 LLM validator，后续 fixture 不得改变这些语义。

`contract.json.schema_version=r6-contract-v0.1` 标识领域合同 schema 平面；
`challenge_matrix.json.schema_version=2026-08-27.1` 标识挑战矩阵 metadata-oracle
平面。两者不是同一版本字段，均以共同的 `contract_id + contract_version=0.1`
绑定，不得互相替代或据此推断版本漂移。
