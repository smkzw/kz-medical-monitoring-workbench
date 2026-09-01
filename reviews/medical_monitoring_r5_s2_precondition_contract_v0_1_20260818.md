# 医学监查 R5 S2 supplemental precondition authority packet 合同 v0.1

日期：2026-08-18  
状态：`R5_S2_PRECONDITION_CONTRACT_READY_FOR_INDEPENDENT_REVIEW`  
上游：`ACCEPT_R5_CONTRACT`、`ACCEPT_R5_S1`、`ACCEPT_R4_STAGE`

## 1. 权限边界

本合同只为 R5 S2 第一条 synthetic/offline 薄纵切提供补充测试权威：一个项目风险 → 一个中心模式 → Risk Inspector → 同一受试者的单一 visit/event/risk anchor → 一跳来源。它不是 S2 runtime，不是临床事实、正式医学结论、真实项目资格、产品 UI、生产或安全专项授权；不允许写回 R4、风险生命周期、分子分母、裁决、Query 状态或用户决定。

唯一机器权威为：

- `artifacts/medical_monitoring_r5_s2_authority_packet_contract_v0_1/exact_overlay.json`
- `artifacts/medical_monitoring_r5_s2_authority_packet_contract_v0_1/authority_packet_schema.json`
- `artifacts/medical_monitoring_r5_s2_authority_packet_contract_v0_1/manifest.json`

## 2. Supplemental overlay

S0 exact contract 的 86 个 deferred leaf 不被修改。S1 已独立激活 `R5AuthorityReceipt.public_projection_kind`；S2 只激活机器 overlay 中精确列出的 40 个 leaf：

- center cell：`domain`、`individual_risk_refs`、`pattern_refs`、`severity`；`measure_refs` 继续为空并延后至 S3。
- deep link：`event_ref`、`risk_anchor_ref`、`spine_ref`、`visit_ref`。
- single temporal chain：`R5JourneyEvent`、`R5RiskAnchor`、`R5VisitNode` 的全部字段，以及 `R5TemporalSpineProjection` 的 `content_hash/cutoff_ref/event_refs/spine_ref/subject_ref/visit_refs`；`pending_date_refs/phase_band_refs` 继续为空并延后至 S5。
- Inspector：`authority_receipt_ref`、`domain`、`severity`、`source_locator_refs`；`query_draft_ref/worker_output_refs/support_evidence_refs/counterevidence_refs` 继续为空或 null，并延后至 S4。

其余 45 个 deferred leaf 必须与 overlay 的 sorted exact set 完全一致，任何遗漏、额外激活或重叠都 fail closed。

## 3. Packet exactness

`R5S2AuthorityPacket` 只接受 exact keys、closed enums、NFC 字符串、sorted-unique 无序引用、显式 cardinality/nullability 和 canonical SHA-256。packet 的权威常量必须严格等于 planner 冻结值 `synthetic_offline_test_only`，且顶层固定为一个 S1 receipt、一个 project-risk binding、一个 center binding、一个 temporal binding、一个 source binding、一个 `ReferenceBaselineItem`、恰好两个 `BaselineAssessment`、一个 Inspector binding、两个隔离 worker attempts、两个对应 worker outputs、两个 deterministic verifications、一个可见冲突、一个独立 adjudicator 和一个 packet-only D10 `ModelEvidence`。

任何 extra/missing key、错类型、错 cardinality、未闭合 enum、非 NFC、重复/未排序引用、hash 不一致或跨对象绑定不一致均拒绝。`packet_content_hash` 严格计算 canonical packet JSON 并仅排除顶层 `packet_id` 与 `packet_content_hash`；`packet_id` 必须等于 `r5-s2-auth:` + `packet_content_hash`，避免循环哈希。排序语义只适用于 schema 明示的 unordered references。

## 4. R4/S1 authority invariants

- receipt 必须逐项匹配 S1 已接受的 project/run/snapshot/cutoff/projection/evaluation/visibility/source-revision authority；S2 不重算可见性或医学数字。
- project risk 必须绑定实际 D10 risk marker identity/content hash 和 projectable member/source refs；`projection_version_ref` 必须等于已绑定 `D10ProjectProjection.projection_version_ref`，同时 `public_projection_id/public_projection_content_hash` 必须与该 public projection 及 S1 receipt 逐项相同。
- center pattern 必须来自 `Member.member_kind=center_pattern`；individual refs 必须是该 pattern 的实际 `descendant_member_refs`，并解析到同一 site 的 `Member.member_kind=individual_risk`。domain 来自实际 `SignalDefinition.risk_or_outcome_domain` 与 member producer relation；severity 来自实际 member `monitoring_priority` 的 closed precedence。不得从 count surface、UI 行、文件名或测试 id 推断。
- temporal authority 是 S2 packet 内的 synthetic/offline supplemental test authority，不冒充现有 R4 public temporal authority。它只允许一条 exact-date visit/event/risk-anchor 链；project/run/snapshot/site/subject/cutoff/risk/member/source 必须与 receipt、center member 和 D10 deep-link target 逐项相同。不得伪造日期、吸附名义访视或 nearest fallback。
- source 必须是同一 projectable member 的一个 `locatable` D10 deep-link locator，并解析到实际 typed `EvidenceRef` 和 receipt 中已接受的 source revision-content pair；不可用即拒绝。

## 5. Inspector isolation boundary

两个 `AnalysisAttempt` 必须共享同一 input content hash，同时拥有不同 attempt/binding/session/independent-context identities；两个 `WorkerAnalysisOutput` 必须按 attempt id 精确归属；两个 `EvidenceVerification` 必须各自 `passed` 且覆盖 identity/version/date/unit/source/rule/artifact_integrity 七维。

顶层恰好一个实体 `ReferenceBaselineItem` 和恰好两个实体 `BaselineAssessment`。两个 assessment 必须指向该同一 item，同时按各自不同的 attempt 一对一绑定两个 worker，并用 `source_recheck_locator_ids` 重查 item 的原始 `source_locator_ids`，其中必须包含 packet 实际 `EvidenceRef.locator_id`；item 的 source revision/snapshot 必须与 source binding/receipt 一致。严格遵循 S0 冻结映射，公共 Inspector `baseline_assessment_refs` 只能投影两个 assessment 的 `item_id` 去重集；因两者绑定同一 item，v0.1 必须为 `exact_items:1` 且 `sorted_unique`，不得用 `attempt_id` 冒充 assessment ref。其他 Inspector attempt/conflict/adjudication/verification/source refs 亦必须从实际 packet 对象机械派生，不得是悬空引用。

冲突固定为可见且不可隐藏；adjudicator 的 binding/session 必须与两个 worker 均不同，并审阅两份原始 output artifact。D10 `ModelEvidence` 只存在于 supplemental packet，必须绑定同一 receipt/source/input/output/ensemble identities。公共 `R5RiskInspectorProjection.worker_output_refs/support_evidence_refs/counterevidence_refs` 必须恰为空，不能借 packet 偷渡成 R4 public authority；它们仍由 S4 解锁。

## 6. 禁止语义分支与完成门

不得按 project/case/fixture/test id、文件名、synthetic sentinel、oracle、index、mutation class 或 hash 命名约定决定语义；不得读取真实项目、真实模型或医学写作路径；不得修改既有 S0/S1/R1–R4/frontend/services/packages；不得启动 8911。

本工件只有在生成器 `--check`、独立 verifier 普通模式与 `PYTHONOPTIMIZE=2` 模式、内存 tamper probes、完整 artifact/source SHA 门均通过后，才可返回 `READY_FOR_INDEPENDENT_REVIEW`。worker 不拥有 `ACCEPT_R5_S2_PRECONDITION_CONTRACT`。

manifest 只 pin 稳定的 accepted S0/S1/R4 authority 与批准设计/计划源；持续更新的 S2 task context 仅作为本合同的决策输入记录，不得进入 `PINNED_SOURCE_SHA256` 或 manifest authority。
