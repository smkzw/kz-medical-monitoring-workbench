# R5-S4 Risk Inspector 与多模型证据归并实施合同 v0.1

日期：2026-08-19
状态：`R5_S4_CONTRACT_READY_FOR_REVIEW`（独立审阅接受前不得写 S4 runtime）
上位权威：System Design v1.1（§9.2–9.4、§10.2、§11.3、§12、§17）、R0–R8 实施计划 v1.1、已接受 R5 v0.3 exact contract、`ACCEPT_R5_S2`、`ACCEPT_R5_S3`、R4 ensemble/D10 只读 public authority、R5-S4 会商证据（grok46 与 pi/qwen 独立对抗输出）。
唯一可接受结论：`ACCEPT_R5_S4_CONTRACT` 或 `REVISE_R5_S4_CONTRACT`；本合同不索取 runtime 完成、产品/UI/浏览器/真实项目/模型/生产或 S5+ 接受。

本合同只完成 S4 **synthetic/offline、renderer-neutral 的 Risk Inspector 与多模型证据归并数据投影合同**。唯一机器权威为
`artifacts/medical_monitoring_r5_s4_contract_v0_1/`（packet_schema.json、exact_overlay.json、source_pins.json、manifest.json；challenge_registry.json 由 worker_03 按 overlay 冻结的 challenge_spec 落盘），
由授权生成器 `tools/generate_medical_monitoring_r5_s4_contract_v0_1.py` 确定性生成，并由
`tools/verify_medical_monitoring_r5_s4_contract_v0_1.py`（worker_02）在普通与 `PYTHONOPTIMIZE=2` 下独立验证。
**语义硬引脚（semantic hard-pins）位于 verifier 自身代码中（artifact 之外），协调重签名无法削弱判定语义。**

### 外部接受权威锚（external accepted-authority anchor）与信任边界

S4 的关键真值来自**独立的外部接受权威锚**，而不是 packet 自我证明：

- 外部锚（`accepted_authority_anchor.json`）是**单独的输入**，位于 generator 产出的 artifact 集合之外。
  授权生成器**不得创建、改写或签名**该锚；manifest 不包含它。验证器通过显式 `--anchor <path>` 输入接收它，
  锚缺失时**fail-closed**；验证器**绝不信任 in-band packet 副本**（packet 只能 `authority_anchor_ref`/`anchor_identity_hash`
  引用其不可变身份，不得定义或改写其真值）。
- 外部锚绑定：project/run/snapshot/cutoff/site/subject/risk/spine 身份、接受的 R5 authority receipt 身份与内容哈希、
  每个 attempt 的 input hash / artifact ref / raw-byte SHA / parsed-output hash / date window / unit contract /
  source revision / rule id+version / model id+version、per-state 接受的 history head/seq/hash、
  接受的 Journey target 身份、permitted ModelEvidence id/role/leaf/model_id/version/ensemble/context、
  per-risk monitoring priority 与 severity authority、接受的 risk identity hash、接受的 baseline 条目
  （item_id/source_kind/source_locator_ids/source_revision_id/snapshot_id/claimed_identity/temporal_window/
  claimed_content_hash/origin_artifact_hash/project/run/snapshot/cutoff/source 关系）、接受的 Query draft
  （query_draft_id/risk_ref/basis_zh/finding_zh/action_zh/source_locator_refs/pd_wording_state/content_hash/draft_only）。
  逐 worker baseline 行与 audience Query 三句均为上述外部锚接受的**精确投影**：packet 侧任何改写必须拒绝
  （`s4.baseline_projection_drift` / `s4.query_projection_drift`）。
- **接受的 R5 风险身份实例（`accepted_risk_identity`，D 修复）**：外部锚携带完整风险身份
  （risk_ref/risk_identity_hash/domain/domain_zh/monitoring_priority/severity/severity_zh/change_kind/change_cause/
  project/run/snapshot/cutoff/site/subject/spine_ref）。packet `risk_identity` 与 audience 均为其**精确投影**；
  `domain_zh`/`severity_zh` 是 `domain`/`severity` 的确定性闭投影。任何 domain→mh/MH、change_kind→continued、
  change_cause→model 等改写必须拒绝（`s4.anchor_claim_drift`）。
- **接受的裁决绑定（`accepted_adjudicator_binding`，D 修复）**：完整 AdjudicationBinding 身份
  （binding_id/session_id/model_id/model_version/independent_context_hash/outcome）外部固定；N 态
  `reviewed_artifact_refs` 必须等于每个活跃 worker raw artifact 的**精确排序集**（无子集/超集/重复）。
  改 adjudicator model_id/version/legal outcome/binding/session/context 或 reviewed 集合必须拒绝
  （`s4.anchor_claim_drift`；worker-self/context-collision/off-enum/unresolved-authority 为更具体单一码）。
- **完整 ModelEvidence 绑定（C 修复）**：`S4ModelEvidencePermit` 覆盖全部 18 个 R4 `d10.ModelEvidence`
  dataclass 字段（含 `adjudication_state`、`evaluation_content_identity`、`input_content_hash`、
  `source_revision_content_pairs`、`source_refs`、`ensemble_size`、`member_analysis_refs`、
  `member_analysis_ref_set_hash`、`output_identity`、`model_binding_hash` 等）。验证器比对完整 dataclass 投影
  （`dataclasses.asdict`），非手选子集；任一字段（含 adjudication_state pending→accepted）单叶改写必须拒绝
  （`s4.model_evidence_not_permitted`）；上游 dataclass 新增字段若无绑定则 coverage 断言失败。
- **证据/来源中文精确投影（E 修复）**：`support_evidence_zh`/`counterevidence_zh`/`source_one_hop_zh`
  是 typed findings/gaps 与精确 source locator 的确定性投影（`来源 {loc} 已定位` / 一跳内定位句）。
  仅含允许 locator 的**不同医学句子**必须拒绝（`s4.cross_plane_projection_drift`）；不得只检查允许
  locator 是否出现。
- **异常包含（B 修复）**：所有 R4 typed reconstruction/validator/`derive_conflicts`/`ModelEvidence`/
  `AdjudicationBinding` 路由在合同边界被包裹；schema 形状合法但值非法的 packet（如 baseline
  `claimed_content_hash`=f*64）必须返回稳定具名 `s4.*` 码（`s4.baseline_projection_drift`），绝不泄漏
  R4/dataclass/KeyError/TypeError/ValueError/assertion；实现故障（trusted generator/artifact 加载）与
  packet 校验失败显式区分。
- **结构失败短路（B 修复，第六轮）**：递归结构/类型/schema 校验在任何语义校验之前运行；一旦产出任何
  packet 形状/类型/schema 错误（如 `ensemble_size="2"`、import 未知键/错误类型），立即返回稳定的归一化
  （确定性排序 + 去重）错误列表，绝不进入算术、排序、dataclass 构造或跨平面语义代码（`'2' < 2` 型
  TypeError 不可能泄漏）。registry 单 mutation 仍恰一码。trusted-artifact 失败边界保留：缺失/损坏的
  机器 schema 或未解析 import 是 artifact 实现故障（`VerificationError`），绝不误标为普通 packet 拒绝。
- 接受的 R5 权威 pin 为 **R5 exact-contract JSON 原始字节 SHA**：
  `3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949`
  （`artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json` 的 `shasum -a 256`）。
  该值**不是** stage-contract Markdown SHA，也不是 packet 声明的值；外部锚的 `accepted_receipt_identity`
  必须以其为后缀。
- 测试用确定性 synthetic 锚是**独立钉住的测试输入**：其原始字节 SHA 冻结在测试
  `poc/medical_monitoring_ai_native_r5/tests/test_s4_contract_artifacts.py` 中
  （`ANCHOR_SHA256`），生成器不能创建/更新它；篡改需同时破坏该独立冻结 SHA。
- 外部锚固定时，对 packet 的 project/receipt/journey/anchor-hash 与全部 authority claim 的联合改写必须失败
  （`s4.anchor_identity_mismatch` / `s4.anchor_claim_drift` / `s4.receipt_hash_mismatch`）。
- **critical severity**：本 scope 无已接受的独立外部 critical authority；`critical_severity_authority`
  为具名 deferred（`critical-severity-authority-public-v1`）。任何 critical packet 必须拒绝
  （`s4.critical_severity_authority_missing`），不得以 generic enum mismatch 拒绝，也不得声明合法 critical fixture。

---

## 1. 目标、边界与接受边界

S4 只完成一组精确 typed packet 与三平面（audience / audit / packet-integrity）投影合同，
回答 Risk Inspector 的确定性核对与多模型证据归并：
0/1/N、raw-byte 与 parsed hash 分离、逐 worker baseline 原文回查、七维验证先于裁决、
全冲突关系与不可隐藏、独立裁决上下文、正反证/来源解析、三分句 draft-only Query、
append-only 历史与 Journey fallback=none、普通中文 audience 与 audit 隔离。

- 不启动 8911；不接前端/浏览器/真实项目/真实模型/产品/生产/安全专项/医学写作。
- 不实现 S4 runtime：不调用 `run_ensemble`、`verify_attempt`、`derive_conflicts`、`_adjudicate`、D10 Query builder；
  这些 R4 函数仅在本合同的 **join recipe / 语义重推导** 中被 verifier 用作非 LLM oracle，机器工件本身不执行它们。
- 不修改 R4、既有 R1–R4、frontend、services、current R5 source/runtime、S2/S3 合同/工件、根 `__init__.py`、医学写作或真实项目。
- 不重算医学风险、严重度、分子/分母或裁决；D10 `ModelEvidence` 仅为 packet/audit provenance，绝不提升为 audience 真值。
- 不存在上游 leaf 只能具名 `deferred`（如 AE/MH match history 仍在 S5），不得用空串/占位词/synthetic sentinel 伪造 authority。
- 本合同只能产出 `R5_S4_CONTRACT_READY_FOR_REVIEW`；`ACCEPT_R5_S4_CONTRACT`、`ACCEPT_R5_S4` 与 S5+ 由 Codex 与 fresh independent reviewer 拥有。

### 接受摘要（acceptance digest）——外部不可变，非 generator 所有

最终 Codex/reviewer 接受时创建外部不可变接受摘要，钉住本合同的 human contract / generator / verifier /
artifact / contract test 的 SHA-256。该摘要不属于 generator；generator 每次运行只写四项 artifact 与 manifest，
绝不写接受摘要；后续任意协调重签名都会使已钉住 SHA 漂移并使接受无效。v0.1 当前不拥有也不伪造接受记录。

---

## 2. 语义权威与 R4/R5 只读 authority

- R4 只读 public authority（前两个为本合同核心新 authority）：`mm_r4.ensemble_contracts.py`、
  `mm_r4.ensemble.py`、`mm_r4.d10_contracts.py`（ModelEvidence、EVIDENCE_SOURCES、ADJUDICATION_STATES、
  PD_WORDING_STATES）、`mm_r4.d10_projection.py`（D10QueryDraft、D10RiskMarker、build_d10_query_draft 语义）、
  `mm_r4.contracts.py`（MONITORING_PRIORITIES）、`mm_r2.risk.py`（AdjudicationOutcome）。
- 已接受 R5 只读 authority：`s2_contracts.py`（R5S2InspectorBinding、S2_DOMAINS、S2_SEVERITIES、
  FALLBACK_POLICIES、MODEL_EVIDENCE_VISIBILITIES）、`s2_thin_slice.py`、`s3_contracts.py`、`s3_projection.py`、
  `contracts.py`（R5AuthorityReceipt、R5DeepLinkState、R5RiskInspectorProjection、R5SeverityLexiconItem）、
  `canonical.py`、`authority_adapter.py`。
- R5 v0.3 exact contract：`artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json`
  （contract_sha256 = `1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6`）。
- S4 只适配 R4 已接受事实/风险/Query/ensemble/D10 ModelEvidence；S4 不得在 R5 新算医学风险/严重度/分子分母/裁决。

---

## 3. 精确 typed 对象（packet_schema.json）

所有对象 exact keys、type、cardinality、nullability 与 closed enums 冻结在 `packet_schema.json`。
根对象为 `R5S4AuthorityPacket`，引用下列 typed 对象与三个 import（`import:R5AuthorityReceipt`、
`import:ReferenceBaselineItem`，以及嵌套在 receipt 内的 `SourceRevisionContentPair`）。

**Import 递归执行（A 修复）**：每个 `import:<Name>` 令牌统一归一化一次并解析到生成
`import_schemas` 的 `<Name>`（键无前缀）；imported 对象递归执行 exact keys、类型、cardinality、
nullability、closed enums、嵌套 list/object/import 约束与全部声明叶约束。packet 内 import 实例的
未知键/缺失必需键/错误 primitive 类型/错误嵌套类型/nullability 违反/约束违反均返回稳定
`s4.*` 码（缺省 `s4.schema_key_mismatch`）；未解析的 import schema 是合同/artifact 实现故障
（artifact 验证期失败），不是合法 packet 条件，也绝不静默跳过。`baseline_items` 的五个 S4 投影
扩展字段（project_ref/run_ref/snapshot_ref/cutoff_ref/source_revision）由**精确 typed 描述符**
（`import_extensions`，含 type/cardinality/nullability/非空/ref 约束；cutoff_ref 可空、其余必填）
声明并合并进基础 import schema 递归校验（C 修复）；未知扩展键仍拒绝，基础 import 字段不可被
扩展覆盖。schema 验证断言每个 `import:` 引用恰解析一次、无孤儿 import_schema、扩展描述符键恰为
批准五字段集且只用受支持约束令牌。
**扩展字段结构 ref grammar（A 修复，第八轮）**：五个扩展字段冻结精确结构 grammar（前缀对齐接受锚
身份示例，绝不宽于/窄于既有权威）：`project_ref`→`^project\.[A-Za-z0-9_.-]+$`、`run_ref`→`^run\.[…]$`、
`snapshot_ref`→`^snap\.[…]$`、`cutoff_ref`→`^cutoff\.[…]$`、`source_revision`→`^rev\.[…]$`；
在递归 import 校验中于语义/hash 层之前执行。畸形字符串/空串返回恰 `s4.schema_key_mismatch`；
`cutoff_ref=None` 因可空保持结构允许、随后由非空外部锚语义拒绝
（`s4.baseline_projection_drift`）。
**弃用 untyped 形状拒绝（B 修复，第八轮）**：`import_extra_keys` 名字形状在描述符校验中彻底移除；
schema 中任何 `import_extra_keys` 键 → trusted-artifact `VerificationError`（`deprecated_import_extra_keys`）；
生成器永不输出该键；machine schema 硬性要求 `baseline_items` 使用精确五描述符 typed
`import_extensions`。

**对象数组 sorted_unique_by 通用执行（A 修复）**：一个通用递归执行器对每个声明的
`sorted_unique_by:<key>` 对象数组约束（根/audience/audit/import 嵌套数组全覆盖）同时强制
**规范序与唯一性**；排序用冻结规范比较器（str/int 类型标签，绝不直接比较混合类型，杜绝 TypeError），
缺失/null/错型键为结构错误（`s4.schema_key_mismatch`）。reverse/duplicate/missing-key/
same-key-different-row 各返回稳定声明码：root/audit 数组 → `s4.cardinality_not_0_1_n`、
worker summaries → `s4.ordinal_mapping_drift`、audience baseline rows → `s4.baseline_projection_drift`、
history → `s4.history_append_only_violation`。覆盖断言枚举每个 packet 可达的 sorted_unique_by 字段
并证明执行器访问过。
**history 顺序先于链检查（C 修复，第八轮）**：执行器在结构类型校验之后、`_check_history` 链检查与
锚 history-prefix 交叉检查之前运行；反转/重复 history entries 恰返回
`s4.history_append_only_violation`（无 `history_chain_break`/`history_prefix_rewrite` 级联）。
`first_entry_genesis` 移入 dedicated-oracle bucket（由 `_check_history` 在排序检查后执行）；锚
history-prefix 比较在既有排序错误时门控跳过。非排序类链破坏（prior-hash 断裂）仍报
`s4.history_chain_break`（不回归）。history_log.entries 纳入生成覆盖与 reverse/duplicate 参数化矩阵
（无手工省略表）。

### 3.1 `R5S4AuthorityPacket`（根，无 root content_hash，hash DAG 无环）

- `packet_id`：`r5-s4-contract:<audience_content_hash>`（单冒号 grammar）
- `schema` = `medical-monitoring-r5-s4-packet-schema-v0.1`
- `status` = `R5_S4_CONTRACT_READY_FOR_REVIEW`；`authority_mode` = `synthetic_offline_test_only`
- `ensemble_projection_state`：closed `no_ensemble | single_analysis | multi_analysis`
- `ensemble_id`（str）、`ensemble_size`（int，约束按 state：no_ensemble→0 / single_analysis→1 / multi_analysis→≥2）
- `input_content_hash`（sha256，nullable；required_when state≠no_ensemble，forbidden_when no_ensemble）
- `risk_identity`（R5S4RiskIdentity）、`authority_receipt`（import:R5AuthorityReceipt）、
  `receipt_content_hash`（canonical_sha256_of:authority_receipt）
- `baseline_items`（import:ReferenceBaselineItem 多，sorted_unique_by:item_id，min 0）
- `baseline_rows`（R5S4BaselineRow 多，sorted_unique_by:row_ref，min 0）
- `worker_views`（R5S4WorkerView 多，sorted_unique_by:attempt_id，exact_count:ensemble_size）
- `raw_artifacts`（R5S4RawOutputArtifact 多，sorted_unique_by:artifact_id，exact_count:ensemble_size）
- `verification_rows`（R5S4VerificationRow 多，sorted_unique_by:verification_id，exact_count:ensemble_size）
- `conflict_rows`（R5S4ConflictRow 多，sorted_unique_by:conflict_id，min 0）
- `adjudication_row`（R5S4AdjudicationRow 必填）
- `query_draft_row`（R5S4QueryDraftRow，nullable）
- `journey_link`（R5S4JourneyLink 必填）
- `history_log`（R5S4HistoryLog 必填，append-only）
- `audience_inspector`（R5S4AudienceInspector 必填）
- `audit_inspector`（R5S4AuditInspector 必填）
- `audience_content_hash`（canonical_sha256_of:audience_inspector）
- `audit_content_hash`（canonical_sha256_of:audit_inspector_excluding:packet_fingerprints —— 无环排除）
- `packet_integrity_hash`（canonical_sha256_of_all_leaves_excluding_packet_id_and_hash_fields_dependencies）

**唯一无环 hash DAG（六节点，A 修复）**：`audience_content_hash`（覆盖 audience_inspector，
无依赖）、`audit_content_hash`（覆盖 audit_inspector 但排除 `packet_fingerprints` 叶子，无依赖）、
`receipt_content_hash`（覆盖 authority_receipt，无依赖）、`packet_id`（`<prefix>:<audience_content_hash>`，
依赖 audience）、`packet_fingerprints`（audit 内叶子，精确 recipe：
`sorted([audience:<audience_content_hash>, receipt:<receipt_content_hash>, packet:<packet_id>, risk_identity:<risk_identity_hash>])`，
依赖 audience/receipt/packet_id/risk_identity，并从 audit hash 排除）、`packet_integrity_hash`
（覆盖 packet 全部叶子，排除 packet_id 与全部依赖 hash 字段/schema/status/authority_mode）。
无任何节点直接或间接包含自身；schema 的 hash_dag 节点自描述（recipe/depends_on/excluded_leaves/
excluded_root_keys），独立测试只读 schema 即可逐字节重建全部 hash（zero/single/N 三态）。

### 3.2 `R5S4RiskIdentity`

`risk_ref`(marker grammar)、`risk_identity_hash`(canonical of R4 public risk identity)、
`domain`(8 域 closed)、`domain_zh`、`severity`(critical/high/medium/low closed)、`severity_zh`(紧急/高/中/低)、
`change_kind`(10 closed, import R5)、`change_cause`(12 closed, import R5)、
`project_ref`、`run_ref`、`snapshot_ref`、`cutoff_ref`(nullable)、`site_ref`(nullable)、`subject_ref`(nullable)。

### 3.3 `R5S4WorkerView`（一条 worker attempt 的 audit 视图）

`attempt_id`、`ordinal`(1..N)、`ordinal_zh`(分析一/分析二/…按 attempt_id 排序)、
`binding_id`、`session_id`、`model_id`、`model_version`、`role`(worker)、
`independent_context_hash`(sha)、`input_content_hash`(sha)、`output_artifact_ref`、
`declared_output_hash`(sha, = parsed hash)、`claimed_date_window`、`claimed_unit_contract`、
`claimed_source_revision`、`claimed_rule_id`、`claimed_rule_version`、
`assessment_row_refs`(多)、`finding_ids`(多)、`gap_ids`(多)、`raw_artifact_ref`、`verification_ref`。

### 3.4 `R5S4RawOutputArtifact`（raw-byte artifact；与 parsed hash 严格分离）

`artifact_id`、`attempt_id`、`raw_format`(closed `utf8_text`)、`raw_bytes_b64`、
`raw_bytes_sha256`(canonical sha of raw bytes)、`parsed_output_hash`(canonical of `WorkerAnalysisOutput`)、
`declared_output_hash`(attempt.output_hash；必须等于 parsed_output_hash)。

### 3.5 `R5S4BaselineRow`（item × attempt 六态回查行）

`row_ref`(=`baseline-row:<item_id>:<attempt_id>`)、`item_id`、`attempt_id`、`state`(6 closed, import R4)、
`reason_codes`(closed ASSESSMENT_REASON_CODES, import R4)、`source_recheck_locator_ids`(多)、
`source_revision_id`、`snapshot_id`、`recheck_complete`(state∈{confirmed,unsupported} ⇒ locators 非空)。

### 3.6 `R5S4ConflictRow`

`conflict_id`、`relation`(5 closed, import R4)、`display_state`(3 closed, import R4)、`hidden`(bool)、
`monitoring_priority`(4 closed, import R4)、`member_attempt_ids`(多)、`ordinal_labels_zh`(多, 按 ordinal 派生)。

### 3.7 `R5S4VerificationRow`

`verification_id`、`attempt_id`、`checked_dimensions`(恰七维, import R4)、`result`(3 closed, import R4)、
`failure_reason_codes`(closed, import R4)、`recomputed`(=true；recompute via R4 `verify_attempt` 语义)。

### 3.8 `R5S4AdjudicationRow`

`present`(bool)、`binding_id`、`session_id`、`model_id`、`model_version`、`independent_context_hash`(sha,
nullable when present=false)、`outcome`(5 closed, import R2)、`reviewed_artifact_refs`(多，present 时非空)、
`adds_explanation_only`(恒 true——裁决只能追加解释，不得改写 worker 输出/删除冲突)。

### 3.9 `R5S4QueryDraftRow`

`query_draft_id`、`risk_ref`、`basis_zh`、`finding_zh`、`action_zh`、`source_locator_refs`(多)、
`pd_wording_state`(2 closed, import D10)、`draft_only`(恒 true)。
**结构性缺失键**：`send_status`、`reply`、`closed_at`、`assignee`、`todo`、`unread`（schema forbidden keys）。

### 3.10 `R5S4JourneyLink`

`deep_link_identity`（project/run/snapshot/cutoff/site/subject/risk/event/visit/spine/anchor/source 全身份）、
`fallback_policy`(closed `none`)、`journey_available`(bool)、`unavailable_reason_zh`(nullable)。

### 3.11 `R5S4HistoryEntry` / `R5S4HistoryLog`（append-only）

Entry：`entry_id`、`seq`(1..N 严格递增)、`kind`(closed：attempt_bound|baseline_assessed|verification_recorded|
conflict_derived|adjudication_recorded|query_draft_generated|inspection_finalized)、
`payload_ref`、`prior_entry_hash`(根为 `"genesis"` 常量)、`entry_hash`(canonical sha 含 prior hash)。
Log：`history_ref`、`head_seq`、`head_hash`、`entries`(多，seq 严格递增，hash 链完整，append-only)。

### 3.12 `R5S4AudienceInspector`（普通中文平面，exact keys，禁 audit 叶）

风险区：`risk_title_zh`、`domain_zh`、`severity_zh`、`change_state_zh`、`subject_display_zh`、
`center_display_zh`、`project_display_zh`、`cutoff_display_zh`；
依据区：`basis_zh`(为什么提醒·依据/发现/建议核实)、`support_evidence_zh`(多)、`counterevidence_zh`(多)、
`source_one_hop_zh`；
基座区：`baseline_rows_zh`(多：{row_ref, item_anchor_zh, ordinal_zh, state_zh, recheck_zh}；
`row_ref` = `baseline-row:<item_id>:<attempt_id>` 为机器只读稳定身份，与用户展示文本 `item_anchor_zh`
分离，使同一基线条目的两次评估保持 distinct/deterministic/有序；`sorted_unique_by:row_ref`)；
分析区：`worker_ordinal_summaries`(多：{ordinal_zh, finding_summary_zh(多), verification_zh, gap_zh(多)})、
`consensus_zh`（门控短语）；
裁决区：`adjudication_status_zh`、`adjudication_explanation_zh`(nullable)；
Query 区：Query 三分句；历史区：`history_summary_zh`；旅程区：`journey_available`、`journey_link_zh`/`unavailable_reason_zh`。
**禁词**（verifier 强制）：provider/model/attempt/hash/backend/session/consensus/worker/adjudicator、
正式事实、候选信号、只读、待办、未读、金标准、已证实、权威结论、model_majority。

### 3.13 `R5S4AuditInspector`（audit 平面）

`authority_receipt_ref`、`receipt_content_hash`、`digest_context`(R5S4DigestContextView)、
`worker_audit_rows`(多：{attempt_id, binding_id, session_id, model_id, model_version, role,
independent_context_hash, input_content_hash, output_artifact_ref, declared_output_hash,
raw_bytes_sha256, parsed_output_hash})、
`verification_audit_rows`(多，recompute trace)、`adjudication_audit`、`conflict_audit`(member attempt ids, hidden)、
`history_audit`(entry hashes)、`packet_fingerprints`(audience_content_hash, receipt_content_hash,
packet_id, risk_identity_hash —— 精确无环 recipe，见 §3.1)、`model_evidence_ref`(packet-only provenance)。

### 3.14 `R5S4DigestContextView`（audit-plane EvidenceDigestContext 形状）

`input_content_hash`、`output_digests`、`evidence_digests`、`expected_ensemble_identity`、
`artifact_date_windows`、`artifact_unit_contracts`、`artifact_source_versions`、`artifact_model_versions`、
`artifact_rule_ids`、`artifact_rule_versions`、`artifact_finding_identities`、`artifact_authorized_source_locators`。

---

## 4. 三平面 hash DAG（audience / audit / packet-integrity）

- `audience_content_hash` = canonical SHA-256(audience_inspector 仅 audience 叶)。
  forbidden leaves：任何 audit-only 字段（binding/session/model/context/hash/raw_bytes/verification trace/
  conflict hidden 标志外的 audit 字段/ModelEvidence）。改 consensus 短语、隐藏不可隐藏冲突、替换支持证据为
  hidden locator 都会改变 audience hash → verifier fail。
- `audit_content_hash` = canonical SHA-256(audit_inspector 全部 audit 叶)。
- `receipt_content_hash` = canonical SHA-256(完整 R5AuthorityReceipt)；`receipt:` 前缀。
- `packet_integrity_hash` = canonical SHA-256(除 packet_id 与各 hash 字段与依赖外的全部叶)；
  同时覆盖 audience 与 audit 平面；hidden-only 私有变更只改 packet_integrity_hash，不得改 audience/audit hash。
- canonical 规则同 R5 family：UTF-8 NFC、sorted keys、compact、`ensure_ascii=False`、`allow_nan=False`；
  many-cardinality 集合排序后序列化；`datetime.date`→`YYYY-MM-DD`。

---

## 5. 不变量（exact_overlay.json `invariants` 逐条冻结）

1. `cardinality_0_1_n`：state 与 ensemble_size 双向一致；no_ensemble 时 worker/raw/verification 全空
   （`s4.ensemble_zero_must_be_empty`）、无 adjudicator（`present=false`）、consensus_zh=“尚无独立分析”；
   single_analysis 恰一 worker、禁任何 consensus/“多个分析结果一致”（`s4.single_model_consensus_forbidden`）。
2. `same_input_version`：state≠no_ensemble 时全部 attempt 共享同一 `input_content_hash`
   （`s4.authority_drift`）。
3. `worker_isolation`：N≥2 时 `len(set(binding_id))==N`、`len(set(session_id))==N`、
   `len(set(independent_context_hash))==N`（`s4.duplicate_worker_binding/session/context`）。
4. `raw_vs_parsed_hash`：`raw_bytes_sha256 != parsed_output_hash`；`sha256(raw_bytes)==raw_bytes_sha256`；
   `parsed_output_hash == declared_output_hash == R4 worker_output_content_hash(recompute)`
   （`s4.raw_parsed_hash_confusion`、`s4.parsed_output_hash_mismatch`、`s4.raw_output_rewritten`）。
5. `baseline_recheck`：state∈{confirmed,unsupported} ⇒ `source_recheck_locator_ids` 非空且 ⊆ 授权
   （`s4.baseline_recheck_missing`、`s4.verification_unresolved_authority`）；baseline 行恒为 item×attempt；
   未评估 item 只能出现为 baseline_miss 冲突，不得显示“基座成立”（`s4.baseline_as_gold`）。
6. `verification_before_adjudication`：verification 在裁决前重推导；`result` 必须等于 R4 `verify_attempt`
   重算值；`checked_dimensions` 恰为七维；passed 无 failure codes；任何失败 ⇒ 无支持性 outcome
   （`s4.verification_label_only`、`s4.verification_unresolved_authority`）。
7. `conflict_full_set_and_non_hideable`：`conflict_rows` 恰等于由 `derive_conflicts` 语义重推导的**全量**集合
   （不增不删；任何一 relation 缺失 ⇒ `s4.conflict_set_incomplete`）；`hidden=True` 拒绝于
   high priority 或 `mutual_negation`/`baseline_miss`（`s4.high_risk_hidden`、`s4.mutual_negation_hidden`、
   `s4.baseline_miss_hidden`）；HIGH `single_model_new` 与互斥 negation 不得被 consensus/裁决隐藏
   （`s4.single_addition_omitted`）；裁决不得删除任何 conflict ref（`s4.adjudication_deleted_conflict`）。
   mutual_negation⇒visible_conflict；baseline_miss⇒visible_baseline_miss。
8. `adjudicator_independence`：present 时 binding_id/session_id/independent_context_hash 与每个 worker
   **互斥**（`s4.worker_self_adjudication`、`s4.adjudicator_context_collision`）；absent 时 audience 只能显示
   “尚未独立核对”（不得显示“独立核对”）；outcome 用 R2 五态 closed（`s4.off_enum_s2_adjudication_state` 拒绝
   S2 的 `"adjudicated"` 冒充 D10 `accepted|divergent|pending`）。
9. `support_counter_source_resolution`：`support_evidence_refs ∪ counterevidence_refs ∪ source_locator_refs`
   ⊆ projectable locator 集；与 `hidden_member_refs`/`hidden_site_refs` 相交 ⇒ fail（`s4.hidden_source_leak`）；
   未解析 locator 显示中文修复路径且绝不 nearest fallback（`s4.nearest_fallback_forbidden`）。
10. `query_draft_three_part_draft_only`：三分句齐全；结构缺失键存在 ⇒
    `s4.query_task_semantics`；partial/无依据 ⇒ `s4.query_draft_partial`；`draft_only=true`。
11. `history_append_only`：seq 严格递增 1..N；entry_hash 链式（含 prior hash）；任何删除/改写/重排/断链 ⇒
    `s4.history_append_only_violation` / `s4.history_chain_break`。
12. `journey_fallback_none`：`fallback_policy=="none"`；任一 deep-link 身份缺失 ⇒ `journey_available=false`
    + 中文修复路径，绝不降级/邻近替代（`s4.journey_fallback_not_none`）。
13. `audience_audit_split`：audience_inspector 无任何 audit-only 叶；改 audit 叶不得改 audience hash；禁词/禁 token
    （`s4.audience_audit_leak`、`s4.model_evidence_on_audience`）。
14. `synthetic_offline_test_only`、`receipt_content_hash_recipe`、`packet_id_grammar`（单冒号）、
    `hash_dag_acyclic`、`schema_key_mismatch`、`source_path_resolution`、`join_recipe_resolution`：
    机器合同不变量（`s4.packet_id_grammar_mismatch`、`s4.receipt_hash_mismatch`、`s4.hash_recipe_cycle`、
    `s4.source_path_unresolvable`、`s4.join_recipe_unresolvable`）。

---

## 6. Closed enums（exact_overlay.json `enums`）

| enum | values | 来源 |
|---|---|---|
| ensemble_projection_state | no_ensemble / single_analysis / multi_analysis | S4 冻结 |
| baseline_state | confirmed/partially_supported/unsupported/outdated/insufficient_evidence/not_applicable | import R4 BASELINE_STATES |
| verification_dimension | identity/version/date/unit/source/rule/artifact_integrity | import R4 |
| verification_result | passed/failed/not_evaluable | import R4 |
| verification_failure_code | 8 项 R4 | import R4 |
| conflict_relation | shared_finding/single_model_new/graded_conflict/mutual_negation/baseline_miss | import R4 |
| conflict_display_state | needs_attention/visible_conflict/visible_baseline_miss | import R4 |
| non_hideable_relation | mutual_negation/baseline_miss | import R4 |
| adjudication_outcome | 5 项 R2 | import R2 AdjudicationOutcome |
| attempt_role | worker/adjudicator | import R4 |
| raw_output_format | utf8_text | S4 冻结 |
| fallback_policy | none | import S2 FALLBACK_POLICIES（closed 单值） |
| pd_wording_state | not_pd/verify_whether_pd | import D10 |
| monitoring_priority | high/medium/low/unknown | import R4 |
| severity | critical/high/medium/low | import R5 exact |
| severity_zh | 紧急/高/中/低 | import R5 exact |
| domain | 八域 | import R5 exact / S2_DOMAINS |
| change_kind | 10 项 | import R5 exact |
| change_cause | 12 项 | import R5 exact |
| history_entry_kind | attempt_bound/baseline_assessed/verification_recorded/conflict_derived/adjudication_recorded/query_draft_generated/inspection_finalized | S4 冻结 |
| projection_kind | d09_audience/d10_project/ensemble/subject_temporal/aemh_history | import R5 exact |
| severity_source | r4_priority_mapped/r4_explicit_critical/fail_closed | S4 冻结（severity 只从冻结映射） |

`severity_mapping` 冻结表：R4 monitoring_priority high→high、medium→medium、low→low、unknown→fail_closed；
`critical` 仅当 R4 权威显式给出时才投影，S4 不得把 high 升级为 critical。

---

## 7. Field mappings / join recipes（exact_overlay.json `source_matrix` + `join_recipes`）

每条 audience/audit 叶必须能逐段解析到真实 R4/R5 dataclass 字段或具名 synthetic supplemental；
`module:Class.field[.nested]` 逐段真实存在（verifier AST 解析 + allowlist/denylist）。关键 join recipes（唯一）：

1. `worker_view ← mm_r4.ensemble:WorkerAnalysisOutput ⋈ mm_r4.ensemble_contracts:AnalysisAttempt` on `attempt_id`
   （audit 叶；raw artifact 另见 recipe 4）。
2. `baseline_row ← mm_r4.ensemble_contracts:BaselineAssessment ⋈ ReferenceBaselineItem` on `item_id` ⋈ attempt
   on `attempt_id`。
3. `conflict_row ← mm_r4.ensemble_contracts:ConflictVisibility`（member_attempt_ids ⊆ attempt ids；
   语义重推导= R4 derive_conflicts 全量集合）。
4. `raw_artifact parsed_output_hash ← mm_r4.ensemble:worker_output_content_hash（重算，非赋值）`;
   `raw_bytes_sha256 ← sha256(raw_bytes_b64 解码字节)`。
5. `verification_row ← R4 verify_attempt 重算（attempt × WorkerAnalysisOutput × digest context）`,
   不信任存储标签。
6. `adjudication_row ← AdjudicationBinding + independent_context_hash（S4 包装，R4 Adjudicator 缺 context hash 的封口）`。
7. `query_draft_row ← mm_r4.d10_projection:D10QueryDraft 公开三句与 pd_wording_state`（draft-only 语义。
   本合同只冻结 schema 与语义源，不调用 builder）。
8. `severity ← severity_mapping(R4 monitoring_priority)` 冻结表；`severity_zh ← R5SeverityLexiconItem`。
9. `journey deep-link 身份 ← 引用的 R5DeepLinkState 身份字段 + 本项目/run/snapshot/site/subject/risk 唯一投影`（fallback=none）。
10. `ModelEvidence ← packet/audit only；model_evidence_visibility=packet_only；adjudication_state 用 D10 closed enum`。

synthetic supplemental（具名，绝不冒充 R4）：`R5S4RiskIdentity.domain/severity`（域/严重度属于 R5 audience
词表层，不提升为 R4 authority）、`change_kind/change_cause` 来自 R5 exact；凡无 R4/dataclass 真实来源的
Inspector 叶（如 raw bytes 语义文本）标记 `synthetic_offline_test_only`。

---

## 8. 错误码目录（closed `error_code`；verifier 判定使用，非自由文案）

`s4.ensemble_zero_must_be_empty`、`s4.single_model_consensus_forbidden`、`s4.duplicate_worker_binding`、
`s4.duplicate_worker_session`、`s4.duplicate_worker_context`、`s4.cardinality_not_0_1_n`、`s4.authority_drift`、
`s4.baseline_recheck_missing`、`s4.baseline_as_gold`、`s4.fabricated_consensus`、`s4.high_risk_hidden`、
`s4.mutual_negation_hidden`、`s4.baseline_miss_hidden`、`s4.single_addition_omitted`、`s4.conflict_set_incomplete`、
`s4.adjudication_deleted_conflict`、`s4.worker_self_adjudication`、`s4.adjudicator_context_collision`、
`s4.verification_label_only`、`s4.verification_unresolved_authority`、`s4.raw_output_rewritten`、
`s4.raw_parsed_hash_confusion`、`s4.parsed_output_hash_mismatch`、`s4.hidden_source_leak`、
`s4.nearest_fallback_forbidden`、`s4.query_task_semantics`、`s4.query_draft_partial`、`s4.audience_audit_leak`、
`s4.model_evidence_on_audience`、`s4.history_append_only_violation`、`s4.history_chain_break`、
`s4.journey_fallback_not_none`、`s4.packet_id_grammar_mismatch`、`s4.receipt_hash_mismatch`、
`s4.hash_algorithm_mismatch`、`s4.hash_recipe_cycle`、`s4.audience_hash_contains_audit_leaf`、
`s4.schema_key_mismatch`、`s4.enum_value_mismatch`、`s4.off_enum_s2_adjudication_state`、
`s4.ordinal_mapping_drift`、`s4.source_path_unresolvable`、`s4.join_recipe_unresolvable`。

---

## 9. 挑战矩阵 spec（exact_overlay.json `challenge_spec`；worker_03 落 challenge_registry.json）

最低独立 case 配额逐类满足，**恰 97 行**，一行一 mutation，非 LLM oracle：
| 类别 | 最低例数 | 必测问题 |
|---|---:|---|
| ensemble_0_1_n | 9 | 0/1/N；N=0 夹杂 attempt fail；1 不得 consensus；N≥2 同输入 |
| input_identity_isolation | 8 | 输入/source-pair 漂移；binding/session/context 重复；ensemble identity |
| raw_parsed_hash_separation | 6 | raw 改写、raw/parsed 混淆、parsed/digest 漂移、declared≠recompute |
| baseline_recheck | 10 | 六态；confirmed/unsupported 缺 locator；部分支持措辞；baseline miss |
| verification_before_adjudication | 8 | label-only、维度子集、失败阻断支持、unresolved authority |
| conflict_relations_hideability | 10 | 五关系 + HIGH/mutual/baseline/single 不可隐藏 + 全量集合 + 裁决删除 |
| adjudicator_independence | 6 | self binding/session/context、无裁决、S2 off-enum、adds-explanation-only |
| support_counter_source_resolution | 8 | hidden source leak、nearest fallback、正反证不相交、one-hop |
| query_draft_three_part | 6 | 三分句缺失、task 字段、partial、pd wording |
| history_append_only | 6 | 删除/改写/重排/断链/unmatched append |
| journey_fallback_none | 4 | identity 缺失、nearest subject/site 拒绝、unavailable 中文路径 |
| audience_audit_split | 8 | model/hash/attempt 叶泄漏、consensus 违规、禁词、ModelEvidence on audience |
| artifact_governance | 8 | packet id/receipt/hash 算法/环/schema keys/source path/join/pins |

每行 exact keys：`case_id/category/precondition/single_mutation/expected_typed_outcome_or_error/
forbidden_audience_output/stage_oracle_contract`；`single_mutation` exact keys `op/path/value`；
`stage_oracle_contract` exact keys `kind/planned_stage/rule_id/test_locator/expected_outcome/
expected_projection/required_non_llm_anchor`。challenge_spec 只冻结配额与 rule_id（error code）与
test_locator 前缀 `poc/medical_monitoring_ai_native_r5/tests/test_s4_contract_artifacts.py::test_challenge_case[<case_id>]`。

---

## 10. 接受边界与完成证据

`ACCEPT_R5_S4_CONTRACT` 需要：本合同 + exact schema/enum/mapping/join/invariant/source-pins + manifest +
challenge_spec 存在；packet/overlay 机械可解析；R4/R5 S1–S3 字节 SHA 完全不变；8911 停止；
generator write→`--check` 幂等字节稳定；verifier 普通与 `PYTHONOPTIMIZE=2` 逐字节一致（W2）；
挑战 registry 恰 97 行且每行真实可执行（W3）；fresh isolated reviewer 对唯一稳定 SHA 组返回
`ACCEPT_R5_S4_CONTRACT`。该状态只解锁 S4 runtime，不接受 R5 UI、真实项目/模型或生产。

---

## 11. 写入边界

合同接受前只允许写：本合同、`artifacts/medical_monitoring_r5_s4_contract_v0_1/**`、`tools/generate_...v0_1.py`、
`tools/verify_...v0_1.py`、`poc/medical_monitoring_ai_native_r5/tests/test_s4_contract_artifacts.py`
（均在执行上下文 Authorized Write Set）。禁止修改 R4、frontend/services、医学写作、真实项目、S2/S3 合同/工件、
既有 R5 source/runtime 与根 `__init__.py`。
