# R5-S4 Risk Inspector 运行时薄切合同 v0.1

日期：2026-08-19  
状态：`R5_S4_RUNTIME_CONTRACT_READY_FOR_REVIEW`  
上位权威：System Design v1.1、R0–R8 实施计划 v1.1、R5 阶段合同 v0.3、
`ACCEPT_R5_S4_CONTRACT`、已接受 R4 ensemble/D10 及 R5 S1–S3 public authority。

唯一审阅结论：`ACCEPT_R5_S4_RUNTIME_CONTRACT` 或
`REVISE_R5_S4_RUNTIME_CONTRACT`。本合同不索取 runtime、UI、浏览器、真实项目/模型、
产品、生产、医学写作或 S5+ 接受。

## 1. 目标与边界

本片只实现 synthetic/offline、renderer-neutral Risk Inspector 运行时：

1. 从调用方注入的 typed external authority anchor、R4/R5 public typed objects 和 raw bytes
   组装 `R5S4AuthorityPacket`；
2. 独立重建 worker/baseline/verification/conflict/adjudication/Query/Journey/history、
   audience/audit 与六节点 hash DAG；
3. 以结构先行、fail-closed 的 validator 拒绝身份、权威、数据、历史、
   投影或哈希漂移；
4. 生成可供后续 UI 使用的中文 audience projection，但本片不接入前端。

R5 不重算医学风险、严重度、分子/分母或裁决。R4 的风险、Query、ensemble、
verification、conflict 和 adjudication 仍是权威；R5 只做精确绑定、核对与投影。

## 2. 运行时输入、测试 oracle 与禁止输入

### 2.1 唯一合法运行时输入

`R5S4RuntimeInput` 必须包含：

- typed `S4AcceptedAuthorityAnchor`（由调用方注入，运行时不打开 JSON 路径）；
- `R5AuthorityReceipt`、上游 `R5RiskInspectorProjection`、`R5ChangeBand`、
  `R5DeepLinkState` 与 runtime-only typed `R5S4SourceInput`；
- R4 `AnalysisAttempt`、`WorkerAnalysisOutput`、`ReferenceBaselineItem`、
  `EvidenceDigestContext`；
- 可选 R4 `AdjudicationBinding`、D10 `ModelEvidence`、`D10QueryDraft`；
- `R5S4RawOutputInput` 形式的 raw bytes；
- 外部已接受 history log；
- 仅用于离线投影的 `R5S4SyntheticAudienceLabels`。

合法 R4 `AnalysisAttempt.claimed_rule_id/version` 是七维权威声明，不属于测试意图。

### 2.2 仅测试/oracle 可读

以下文件只可由 tests/gates 读取，`src/mm_r5/s4_*` 不得导入或打开：

- `artifacts/medical_monitoring_r5_s4_contract_v0_1/accepted_authority_anchor.json`；
- 同目录 `packet_schema.json`、`exact_overlay.json`、`challenge_registry.json`、
  `source_pins.json`、`manifest.json`；
- `tools/generate_medical_monitoring_r5_s4_contract_v0_1.py`；
- `tools/verify_medical_monitoring_r5_s4_contract_v0_1.py`。

### 2.3 禁止的语义决策输入

运行时不得根据 challenge `case_id/category/expected outcome/expected projection/test_locator/
stage_oracle_contract/mutation`、variant/index、oracle 结果、文件名、fixture 身份、synthetic
sentinel、hash 命名约定或测试路径分支。不得调用合同 verifier 或其 sample-packet
builder 代替 runtime。

## 3. 最小模块与责任

### 3.1 `s4_contracts.py`

- 定义不可变 dataclass、closed vocabularies、canonical/hash recipes、精确引用 grammar。
- 只处理局部结构与哈希不变量；不访问文件、不调用 R4 evaluator。
- 定义 `S4RuntimeContractError`、`S4RuntimeImplementationError`、
  `R5S4ValidationIssue`、`R5S4ValidationResult`。

### 3.2 `s4_authority_builder.py`

- 接受 typed runtime input，按稳定身份 join R4/R5 对象，构建内部 `R5S4BuildState`。
- 重算 parsed hash、verification 与全量 conflict set，组装 packet。
- 不接受声明的 audience/audit/hash 作为权威输入。

### 3.3 `s4_projection.py`

- 从 typed build state 纯函数重建 audience、audit 与 hash DAG。
- 中文词汇与排序确定；不做新的医学判定。
- 不接受调用方预制的 audience 结果来决定输出。

### 3.4 `s4_validator.py`

- 结构/类型/exact-key 检查必须先于排序、算术、dataclass 构造和语义 join。
- 从 typed authority 独立重建 receipt、worker、baseline、verification、conflict、
  adjudication、Query、Journey、history、audience、audit 和全部 hash。
- 稳定排序并去重 `s4.*` issues；R4/dataclass 异常映射为稳定合同错误。
- trusted source/schema/implementation 故障单独抛出 `S4RuntimeImplementationError`，不伪装成 packet 拒绝。

### 3.5 唯一公开 API

四个子模块只冻结以下公开入口；其他 helper 以前导下划线命名：

- `build_s4_authority_state(runtime_input: R5S4RuntimeInput) -> R5S4BuildState`；
- `project_s4_authority_packet(build_state: R5S4BuildState) -> R5S4AuthorityPacket`；
- `build_s4_authority_packet(runtime_input: R5S4RuntimeInput) -> R5S4AuthorityPacket`
  （严格等于前两步串联）；
- `validate_s4_authority_packet(candidate: Mapping[str, object] | R5S4AuthorityPacket,
  runtime_input: R5S4RuntimeInput) -> R5S4ValidationResult`。

`R5S4ValidationIssue` exact fields 为 `code: str`、`path: str`、
`message_zh: str`；`R5S4ValidationResult` exact fields 为 `ok: bool`、
`issues: tuple[R5S4ValidationIssue, ...]`、`expected_packet: R5S4AuthorityPacket | None`。
issues 按 `(code,path,message_zh)` 排序去重。结构无法安全解析时
`expected_packet=None`；否则 validator 必须从 runtime input 重建 expected packet 后比较，
不得以 candidate 自证 candidate。Mapping 先做 exact-key/primitive/container/type 检查，
全部通过后才构造 dataclass；未知键、缺键、错误 primitive 不得先触发 dataclass 异常。
每个 issue 的 `message_zh` 不允许自由生成，唯一公式为
`核对未通过：{path}（{code}）`。公开 dataclass 全部 `frozen=True`。

`src/mm_r5/__init__.py` 不修改。后续使用直接子模块导入，保护已接受 S1–S3
根包 SHA。

## 4. Typed 对象

### 4.1 必须精确对齐已接受 machine schema 的对象

- packet/core：`R5S4AuthorityPacket`、`R5S4RiskIdentity`、`R5S4WorkerView`、
  `R5S4RawOutputArtifact`、`R5S4BaselineRow`、`R5S4ConflictRow`、
  `R5S4VerificationRow`、`R5S4AdjudicationRow`、`R5S4QueryDraftRow`、
  `R5S4JourneyLink`、`R5S4HistoryEntry`、`R5S4HistoryLog`；
- audience/audit：`R5S4AudienceInspector`、`R5S4AudienceBaselineRow`、
  `R5S4AudienceWorkerSummary`、`R5S4AuditInspector`、`R5S4AuditWorkerRow`、
  `R5S4VerificationAuditRow`、`R5S4DigestContextView`、`R5S4ModelEvidenceRef`；
- external anchor：`S4AcceptedAuthorityAnchor`、`S4AcceptedRiskIdentity`、
  `S4AcceptedAdjudicatorBinding`、`S4AcceptedBaselineItem`、`S4AcceptedHistoryState`、
  `S4AcceptedQueryDraft`、`S4AttemptAuthorityRow`、`S4JourneyTargetIdentity`、
  `S4ModelEvidencePermit`、`S4SourceRevisionPair`。

上述对象的 exact keys/type/cardinality/nullability/closed enum/constraint 以已接受
`packet_schema.json` 为测试参考权威；runtime source 不在运行时读该 JSON。

两项冻结 errata 优先于旧 machine schema 的矛盾叶，且只适用于 runtime：

- `R5S4HistoryLog.entries` 为 `min_items:0`；仅 `no_ensemble` 允许空 entries，且必须
  `head_seq=0`、`head_hash="genesis"`；single/multi 仍为 `min_items:1`；
- `S4AcceptedHistoryState.hash` 为 `genesis_or_sha`，仅 `seq=0 && head="genesis"`
  时允许 `hash="genesis"`，其他状态必须是 SHA-256。

旧 JSON、anchor 和 verifier 保持原字节不动；新 runtime tests 必须显式覆盖这两项条件规则，
不得把 errata 扩张为通用 schema 改写权。

### 4.2 runtime-only wrappers

- `R5S4RawOutputInput(attempt_id: str, artifact_id: str, raw_format: str,
  raw_bytes: bytes)`；
- `R5S4AdjudicatorInput(binding: AdjudicationBinding,
  independent_context_hash: str)`；
- `R5S4SyntheticAudienceLabels(risk_title_zh: str, project_display_zh: str,
  center_display_zh: str, subject_display_zh: str, cutoff_display_zh: str)`；
- `R5S4SourceInput(availability_state: Literal["locatable", "unavailable"],
  resolution: R5S2SourceResolution | None,
  unavailable_reason: Literal["target_not_projectable", "source_locator_missing"] | None)`；
  `locatable` 必须 resolution 非空且 reason 为空；`unavailable` 必须 resolution 为空且
  reason 非空；不允许第三种组合；
- `R5S4RuntimeInput(anchor: S4AcceptedAuthorityAnchor,
  authority_receipt: R5AuthorityReceipt,
  upstream_inspector: R5RiskInspectorProjection, change_band: R5ChangeBand,
  deep_link_state: R5DeepLinkState, source_input: R5S4SourceInput,
  attempts: tuple[AnalysisAttempt, ...],
  worker_outputs: tuple[WorkerAnalysisOutput, ...],
  raw_outputs: tuple[R5S4RawOutputInput, ...],
  baseline_items: tuple[ReferenceBaselineItem, ...],
  digest_context: EvidenceDigestContext | None,
  adjudicator: R5S4AdjudicatorInput | None,
  model_evidence: ModelEvidence | None, query_draft: D10QueryDraft | None,
  history_log: R5S4HistoryLog, audience_labels: R5S4SyntheticAudienceLabels)`；
- 内部 immutable `R5S4BuildState(anchor, authority_receipt, upstream_inspector,
  change_band, deep_link_state, source_input, risk_identity, ensemble_id,
  ensemble_projection_state, input_content_hash, attempts, worker_outputs,
  worker_views, raw_artifacts, baseline_items, baseline_rows, verification_rows,
  conflict_rows, adjudication_row, query_draft_row, journey_link, history_log,
  digest_context, model_evidence, audience_labels)`；`attempts` 与 `worker_outputs`
  保留完整 R4 typed objects，供 projection 从 supported/unsupported finding、gap 与
  source locators 独立重建文案；每一复数字段均为 tuple，不保存 candidate audience、
  audit 或 candidate hash。

synthetic audience labels 仅能影响展示文本，不得影响风险身份/域/等级、verification、
conflict、adjudication、Query、authority 或哈希以外的医学语义。

### 4.3 上游 Inspector 与来源的精确信任边界

`upstream_inspector` 是 S2 交叉声明，不是 S4 worker/evidence/Query 权威：

- 必须逐字段等于独立重建值：`risk_ref`、`authority_receipt_ref`、`domain`、
  `severity`、`analysis_attempt_refs`、`baseline_item_refs`、
  `baseline_assessment_refs`、`conflict_refs`、`verification_refs`、
  `adjudication_ref`、`source_locator_refs`；任一漂移唯一返回
  已接受码 `s4.cross_plane_projection_drift`；
- S2 冻结的 `worker_output_refs`、`support_evidence_refs`、
  `counterevidence_refs` 必须为空，`query_draft_ref` 必须为空；任一非空唯一返回
  已接受码 `s4.imported_object_drift`；S4 对这些字段只从 R4
  `WorkerAnalysisOutput`、外部 anchor 和可选 `D10QueryDraft` 重建；
- `source_input.availability_state="locatable"` 时，`R5S2SourceResolution` 的十个字段
  全部参与校验：`locator_id/locator_kind/source_file/
  row_or_cell_ref/lineage_ref/revision_id/revision_content_hash/fallback_policy/
  resolution_state/content_hash`。其 locator 必须等于 deep link、anchor Journey target、
  digest/baseline 授权 locator；revision pair 必须等于 receipt 的唯一对应 pair；
  `fallback_policy="none"`、`resolution_state="locatable"`，且 `content_hash` 按 S2
  recipe 重算。身份/版本/哈希不符唯一返回已接受码 `s4.source_path_unresolvable`；任何邻近回退
  唯一返回 `s4.nearest_fallback_forbidden`。
- `source_input.availability_state="unavailable"` 是唯一合法不可定位态：deep link 与
  anchor 已知的 project/run/snapshot/cutoff/site/subject/risk/spine/anchor/event/visit
  身份仍必须一致；仅 source locator 可以因 `target_not_projectable` 或
  `source_locator_missing` 缺席。其他任何身份不符仍拒绝并返回
  `s4.source_path_unresolvable`，不得伪装成 unavailable。

## 5. 运行时不变量

### 5.1 0/1/N 与隔离

- `no_ensemble`：N=0，attempt/output/raw/verification/conflict/ModelEvidence 全空，
  adjudicator/Query 为空，audience 只能显示“尚无独立分析”。
- `single_analysis`：N=1，verification 必须运行，不得产生 consensus；本薄切
  adjudicator 必须缺席。
- `multi_analysis`：2≤N≤10（冻结词汇仅含“分析一”至“分析十”）；全部 attempt
  共用同一 input hash，binding/session/context 各自唯一，必须有外部已接受的独立 adjudicator。
- attempt 按 `attempt_id` 排序；ordinal 与所有 refs 由该序列派生；输入换序不得改变 packet identity/hash。
- N=0 时 canonical conflict set 固定为空，且不得调用 R4 `derive_conflicts`；这是避免
  “零 attempt + 非空 baseline”产生无成员 `baseline_miss` 的冻结短路。N≥1 才调用
  `derive_conflicts`，并继续服从完整集合/不可隐藏规则。

### 5.2 Raw、baseline 与 verification

- `raw_bytes_sha256` 从注入 bytes 重算；parsed hash 从 `WorkerAnalysisOutput`
  使用 R4 `worker_output_content_hash` 重算；raw/parsed domain 相等必须拒绝。
- baseline rows 必须是真实 `item × attempt`。`confirmed/unsupported` 必须重查授权原始
  locator；未评估 item 产生可见 `baseline_miss`，不得默认“基座成立”。
- 使用 R4 `verify_attempt` 重算七维：identity/version/date/unit/source/rule/
  artifact_integrity；verification 必须先于 adjudication。
- failed/not_evaluable authority 阻断任何支持性 adjudication outcome。

### 5.3 Conflict、adjudication 与 ModelEvidence

- `derive_conflicts` 重算的完整集合与 packet 精确相等；不增、不减、不仅保留多数结论。
- high、`mutual_negation`、`baseline_miss` 及 high `single_model_new` 始终可见。
- 不调用 R4 private `_adjudicate`。输入 `AdjudicationBinding` 是权威；R5 只校验与投影。
- adjudicator binding/session/context 与全部 worker 互斥；`reviewed_artifact_refs`
  等于活跃 raw artifact 的精确排序集。
- `ModelEvidence` 使用 `dataclasses.asdict` 绑定当前全部 18 个上游字段；任一
  新增/漂移字段在 coverage 补齐前 fail-closed。它只进 packet/audit，不进 audience。

### 5.4 Query、Journey 与 history

- Query 可空；存在时必须与外部已接受 R4 投影完全一致，三分句非空、
  locator 非空、`draft_only=True`、PD wording closed，结构中无发送/回复/关闭/负责人/待办/未读。
- Journey 必须绑定 exact `R5DeepLinkState` 与外部 target，`fallback_policy="none"`。
  只有 §4.2/§4.3 的 typed `unavailable` 可投影不可定位及中文修复理由；其他身份或来源
  不符一律拒绝，不得降级成 unavailable，不得 nearest fallback。
- history 是外部已接受的 append-only 输入。`N` 只选择 no/single/multi anchor，不表示
  history 长度。entries 的 `seq` 必须精确为 `1..len(entries)`，第一项
  `prior_entry_hash` 必须为所选 accepted state 的 `head`，后续 prior/hash chain 连续，
  `head_seq=len(entries)`，非空时 `head_hash=entries[-1].entry_hash`；空链按 §4.1 errata。
  accepted prefix 必须满足 `accepted.seq<=len(entries)`；`accepted.seq>0` 时
  `entries[accepted.seq-1].entry_hash==accepted.hash`；accepted.seq=0 时 accepted.hash
  必须为 `genesis`。不重写、不补造缺失历史。

## 6. 中文 audience、audit 与 hash

- 中文投影为纯模板函数；固定 domain/severity/baseline/change/adjudication/
  PD/verification/ordinal 词汇。
- 证据句为 `来源 {locator} 已定位`；一跳摘要为 `来源 {sorted locators} 已在一跳内定位`。
- baseline rows 按 `row_ref` 排序，保留每个 item×attempt；worker summaries 按 ordinal 排序。
- 所有 conflict relations 按冻结关系序完整投影。多模型仅在无任何冲突关系时可表达
  “多个分析结果一致”；N=0 为“尚无独立分析”，N=1 为“单一分析不形成一致性结论”。
- audience 禁止 model/provider/binding/session/hash/raw bytes/audit 叶、ModelEvidence 及已冻结禁词。
- 六节点 hash DAG 精确沿用已接受 S4 合同 recipe；audit-only 改动不改 audience hash，
  audience 改动不得通过改 audit 值修复。

### 6.1 中文模板与逐状态映射

除 `R5S4SyntheticAudienceLabels` 的五个展示值外，所有文案由以下闭集确定：

- `audience_contract_id` 固定为 `contract.s4.1`，不得从 receipt、label 或 candidate 推导；

- domain：`ae→AE`、`mh→MH`、`cm→合并用药`、`ip→试验药`、
  `lab_exam→检验/检查`、`hospital_procedure→住院/操作`、
  `symptom_efficacy→症状/疗效`、`protocol_compliance→方案符合`；
- severity：`critical/high/medium/low` → `紧急/高/中/低`；但本片 critical 按 deferred 拒绝；
- change：`initial_current/new/upgraded/continued/downgraded/resolved/reopened/
  superseded/not_evaluable/not_comparable` →
  `首次识别/新发/风险升高/持续存在/风险降低/已消失/再次出现/已被后续记录替代/
  暂无法评估/暂不可比较`；
- baseline state：`confirmed/partially_supported/unsupported/outdated/
  insufficient_evidence/not_applicable` →
  `已确认/部分支持/不支持/已过期/证据不足/不适用`；来源回查分别为
  `已回查来源`、`未回查来源`；
- ordinal 仅 `分析一` 至 `分析十`；verification 仅
  `七项核对均通过`、`核对未通过：{按错误码排序的中文项}`、`暂无法核对：{原因}`；
- verification failure：`identity_mismatch/version_mismatch/date_out_of_window/
  unit_mismatch/source_unresolvable/rule_version_mismatch/artifact_hash_mismatch/
  input_content_mismatch` →
  `身份不一致/版本不一致/日期超出范围/单位不一致/来源无法定位/规则版本不一致/
  文件内容不一致/输入内容不一致`；
- conflict relation 按固定顺序 `shared_finding/single_model_new/graded_conflict/
  mutual_negation/baseline_miss` →
  `共同发现/单一分析新增发现/风险分级不一致/结论相互矛盾/基线项目未被评估`；
- support 只取 supported findings 的 source locators；counter 只取 unsupported findings
  与 gap candidates 的 source locators；每项为 `来源 {locator} 已定位`，排序去重；
  一跳摘要为空时 `""`，否则 `来源 {locators，以顿号连接} 已在一跳内定位`；
- consensus：N=0 为 `尚无独立分析`；N=1 为 `单一分析不形成一致性结论`；N≥2 且
  conflict 为空为 `多个独立分析结果一致`；有 conflict 时为
  `独立分析存在{按冻结关系顺序连接的中文冲突类型}，请结合来源核实`；
- adjudication status：N<2 为 `尚未进行独立裁决`；N≥2 且 binding 有效为
  `已完成独立裁决`；explanation 只投影上游 outcome 的冻结中文映射，不新增医学结论；
- adjudication outcome：`merged_supported/distinct_supported/rejected_by_evidence/
  version_mismatch/needs_user_attention` →
  `可合并为同一发现/应保留为不同发现/现有证据不支持/版本不一致，暂无法判断/
  需要医学监察员重点查看`；
- Query 不存在时四个 Query 中文叶全为 null；存在时前三句逐字取已接受草稿，PD
  仅 `not_pd→非方案偏离`、`verify_whether_pd→请核实是否为方案偏离`；
- Journey 可定位为 `查看该受试者历时记录`；不可定位时 link=null、原因固定为
  `无法定位到该受试者的对应记录，请核对项目、受试者和数据截止点`；
- history summary：N=0 `尚无独立分析记录`；N=1 `已记录一次独立分析及来源核对过程`；
  N≥2 `已记录多次独立分析、冲突核对及裁决过程`；
- basis：N=0 `当前仅展示已识别风险及其来源`；N=1
  `已完成一次独立分析，请结合来源核实`；N≥2
  `已完成多次独立分析，请结合基线、冲突与来源核实`。

`finding_summary_zh` 固定为 `发现 {finding_id}（来源 {排序 locator，以顿号连接}）`；
`gap_zh` 固定为 `待核实 {gap_id}（来源 {排序 locator，以顿号连接}）`。两者只允许由
finding/gap 的稳定 identity 与授权 locator 生成，不允许模型自由生成。所有词汇和 conflict/outcome/reason-code
中文映射以 `s4_contracts.py` 常量表一次定义，projection 与 validator 共享同一不可变表；
tests 对每个闭集成员逐项断言，不以快照整包代替。

## 7. 具名 deferred 边界

- `aemh-match-history-public-v1`：S4 只投影已接受通用 history，不重建补录匹配。
- `subject-workspace-temporal-spine-v1`：只绑定已接受 Journey target，不重建完整 spine/事件/访视。
- `critical-severity-authority-public-v1`：任何 `critical` 输入返回
  `s4.critical_severity_authority_missing`。
- 真实项目展示名/风险标题权威尚不存在；本 synthetic/offline 片只允许 typed
  projection labels，不得冒充临床权威。
- 当前 history anchor 只授权冻结的 per-state chain，不授权任意非 genesis continuation。
- single-analysis adjudication 未冻结；必须缺席。

## 8. 实现写入边界

合同接受后只可新建：

- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_authority_builder.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_projection.py`
- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_validator.py`
- `poc/medical_monitoring_ai_native_r5/tests/s4_runtime_fixtures.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_s4_contracts.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_s4_authority_builder.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_s4_projection.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_s4_validator.py`
- `poc/medical_monitoring_ai_native_r5/tests/test_s4_readonly_gate.py`
- `poc/medical_monitoring_ai_native_r5/tests/challenges/test_s4_runtime_challenges.py`
- `poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s4_readonly_sha256.json`

不允许修改任何现有文件，包括 `src/mm_r5/__init__.py`、S1–S3 source/tests/evidence、
R4、已接受 S4 合同/工件/generator/verifier、frontend/services、医学写作、真实项目与生产。

回滚只删除上述新建 S4 source/test/evidence；无 schema migration、无 R4/R5 恢复、
无风险/历史/用户数据回写。

## 9. 97-case 运行时挑战闭环

已接受 97 条 registry 按下列方式关闭：

| 类别 | 数量 | 关闭方式 |
|---|---:|---|
| ensemble_0_1_n | 9 | 真实 builder/validator |
| input_identity_isolation | 8 | 真实 builder/validator |
| raw_parsed_hash_separation | 6 | 真实 builder/validator |
| baseline_recheck | 10 | 真实 builder/validator |
| verification_before_adjudication | 8 | 真实 builder/validator |
| conflict_relations_hideability | 10 | 真实 builder/validator |
| adjudicator_independence | 6 | 真实 builder/validator |
| support_counter_source_resolution | 8 | 真实 builder/validator |
| query_draft_three_part | 6 | 真实 builder/validator |
| history_append_only | 6 | 真实 builder/validator |
| journey_fallback_none | 4 | 真实 builder/validator |
| audience_audit_split | 8 | 真实 builder/validator |
| artifact_governance | 8 | `R5S4C-090`–`R5S4C-097`；引用冻结时 acceptance record 与原始 SHA，不在 runtime 阶段重跑已完成的构建前门 |
| **合计** | **97** | **89 runtime + 8 adjacent governance** |

89 条 runtime tests 可在测试层读 registry 的 mutation/expected 元数据，但必须对每条：

1. 先通过真实 builder 构建并证明 base packet 有效；
2. 只施加一个 mutation；
3. 调用真实 runtime validator；
4. 精确得到冻结单一错误码；
5. 不得让 runtime 读取 registry row。

有效矩阵至少包含 0、1、N=2、N=10、输入换序、mutual negation、graded conflict、
high single-model addition、baseline miss、Journey unavailable、Query present/absent 和 audit-only mutation。

## 10. 机械门禁与完成标志

### 10.1 聚焦与相邻测试

- focused：本合同列出的 6 个 S4 runtime test modules（含 challenges）；
- adjacent R5：S1–S3 全部 unit/challenge tests；S4 contract-artifact tests 运行除下列
  5 个冻结时/构建前专用节点外的全部节点：`test_no_s4_runtime_imported`、
  `test_r4_r5_sources_unchanged_sha`、`test_generator_check_is_deterministic`、
  `test_verifier_normal_mode`、`test_verifier_optimized_mode`。排除原因不是失败豁免：前者
  与本片 create-only allowlist 逻辑互斥，后四者依赖包含后续合法任务记录的历史
  source-pins；不得修改或重签旧工件来让它们变绿；
- 8 个 artifact-governance case 的完成证据固定为
  `R5S4C-090`–`R5S4C-097`、`ACCEPT_R5_S4_CONTRACT` 记录及该记录列出的冻结 raw SHA；
  runtime 阶段只验证这些文件字节未变，不重新声称旧 verifier 对当前可变任务记录通过；
- “完整 runtime-compatible R5 suite”精确定义为新 S4 runtime tests + S1–S3 全部 tests +
  上述排除后的 S4 artifact tests；它在 normal 与 `PYTHONOPTIMIZE=2` 下均通过，
  collected/pass/deselected counts 一致。不得对其他失败新增排除；
- Ruff F/全规则、临时 bytecode 目录 compile、禁用 bytecode 的全新进程直接导入四个子模块。

### 10.2 反过拟合和边界门

- AST 检查新 runtime source：无 generator/verifier/registry 导入、无 runtime 文件读取、
  无 case/index/oracle/mutation/sentinel/test-locator 决策分支、无用 `assert` 实施运行时不变量。
- 实现前后 R4、R5 S1–S3、根 `__init__.py` 和已接受 S4 contract artifacts 的 raw SHA
  必须完全一致；证据写入唯一新 JSON。
- 8911 实现前后均无监听；无任何 service-start 命令。
- 不运行真实项目/模型，不修改 UI/医学写作/生产。

### 10.3 独立接受

fresh isolated reviewer 只获取固定 source/artifact SHA、本合同、验收标准与真实
test/command outputs，并只能返回：

- `ACCEPT_R5_S4`；或
- `REVISE_R5_S4`。

`ACCEPT_R5_S4` 只接受本 synthetic/offline、renderer-neutral runtime 薄切，不接受
UI/浏览器、真实项目/模型、产品、生产、临床真值、医学写作或 S5+。

## 11. 合同接受边界

`ACCEPT_R5_S4_RUNTIME_CONTRACT` 需要：

- 本合同的 runtime/test/oracle 输入边界、四模块责任、typed 对象、不变量、
  deferred、写入 allowlist、97-case 分配、门禁与回滚全部无歧义；
- 合同 raw SHA 冻结；
- 8911 停止；
- fresh isolated reviewer 对同一不变快照返回
  `ACCEPT_R5_S4_RUNTIME_CONTRACT`。

合同接受前不得创建任何 `s4_*` runtime source/test/evidence 文件。
