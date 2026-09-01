# R5-S3 项目驾驶舱与中心图谱实施合同 v0.1

日期：2026-08-18  
状态：`R5_S3_CONTRACT_CANDIDATE`（独立审阅接受前不得写 S3 runtime）  
上位权威：System Design v1.1、R0-R8 实施计划 v1.1、已接受 R5 v0.3 exact contract、`ACCEPT_R5_S2`

## 1. 目标与边界

S3 只完成离线、合成、renderer-neutral 的项目驾驶舱与中心图谱数据投影。它让后续页面能够直接消费：当前风险集、变化带、分层定量度量和中心图谱；不实现页面，不启动 8911，不接真实项目/模型，不修改 R4，不触碰医学写作，也不进入 S4–S8。

本阶段不把不足的上游字段伪称为既有 R4 public authority。R4 D10 已能提供 count surface、typed numerator/denominator、coverage、cutoff、evaluation limits、change section、center distribution、risk marker 与 visibility；多中心组合和 low-risk cluster 则由本合同定义的 synthetic supplemental authority packet 明确承载，只用于离线工程验证，不代表临床事实或产品可用。

## 2. 唯一输入拓扑

`R5S3AuthorityPacket` 包含 1..N 个 `R5S3AuthorityUnit`，所有 unit 必须绑定同一 project/run/snapshot/cutoff 与同一 audience contract：

- 每个 unit 包含一个经过真实 R4 `evaluate` 与 `project_d10_run` 验证的 `D10TypedInput`、`D10RunResult`、`D10ProjectionBundle`；
- 每个 unit 包含对应 `R5AuthorityReceipt`，其 project/run/snapshot/cutoff/visibility/source pairs/evaluation identity/projection hash 必须与该 unit 精确一致；
- 每个 unit 的语义域只来自 `SignalDefinition.risk_or_outcome_domain`，且必须是 R5 八域之一；
- current-risk 成员只来自该 unit 的 projectable `Member` 与本 packet 的具名 `supplemental_member_authority`；补充成员本身必须是冻结的 R4 `Member` 对象，并有 exact source/visibility/parent-or-independent 绑定；
- unit 顺序不具有语义；重排不得改变 packet content identity 或任何 audience projection。

禁止从 fixture/case/test id、文件名、顺序、索引或字符串命名推断域、严重度、当前状态、中心归属或变化类型。

## 3. S3 typed 输出

除已冻结的 `R5CurrentRiskSet`、`R5ChangeBand`、`R5QuantitativeMeasure`、`R5CenterMapCell/Projection`、`R5ProjectCockpitProjection` 外，S3 仅新增以下 immutable supplemental objects：

### 3.1 `R5S3AuthorityUnit`

精确字段：

- `unit_ref: str`
- `authority_receipt: R5AuthorityReceipt`
- `typed_input_content_hash: sha256`
- `run_evaluation_content_identity: sha256`
- `projection_bundle_content_hash: sha256`
- `domain: closed R5 domain`
- `projectable_member_refs: tuple[str]`
- `hidden_member_refs: tuple[str]`
- `projectable_site_refs: tuple[str]`
- `hidden_site_refs: tuple[str]`
- `source_unit_refs: tuple[str]`

三个 content identity 分别由完整 typed input、run result 与完整 public bundle 的 canonical read-only representation 导出；它们只是防篡改 identity，不替代其中的逐叶 authority。

### 3.2 `R5S3SupplementalMemberAuthority`

精确字段：

- `member: R4 Member`
- `domain: closed R5 domain`
- `visibility_state: projectable|hidden`
- `parent_pattern_ref: Optional[str]`
- `source_locator_refs: tuple[str]`
- `authority_unit_ref: str`
- `content_hash: sha256`

它只允许补充 D10 numerator 不能同时携带的 pattern descendant，或独立 individual risk；不得改变 D10 count surface。hidden 补充成员只能用于泄漏门禁，不得进入 audience ref、cluster、cell、measure numerator 或深链。

### 3.3 `R5S3LowRiskCluster`

精确字段：

- `cluster_ref: str`
- `authority_receipt_ref: str`
- `domain: closed R5 domain`
- `site_ref: str`
- `member_refs: tuple[str]`（非空、sorted unique、全部 current/projectable/low）
- `content_hash: sha256`

cluster 是展示聚合而非新医学风险；展开必须无损恢复全部 low-risk member identity。

### 3.4 `R5S3ProjectionBundle`

精确字段：

- `packet_ref: str`
- `authority_unit_refs: tuple[str]`
- `current_risk_set: R5CurrentRiskSet`
- `low_risk_clusters: tuple[R5S3LowRiskCluster]`
- `change_bands: tuple[R5ChangeBand]`
- `measures: tuple[R5QuantitativeMeasure]`
- `center_map: R5CenterMapProjection`
- `cockpit: R5ProjectCockpitProjection`
- `content_hash: sha256`

## 4. 当前风险集规则

- `accepted_current_state == accepted_current` 且 projectable 的 high/medium 成员逐个进入 `high_risk_refs` / `medium_risk_refs`，不得截断为 3–5 项。
- low 成员按 `(domain, site_ref, authority_receipt_ref)` 分组为 `R5S3LowRiskCluster`；cluster refs 进入 `low_risk_cluster_refs`，但成员 identity 全部保留在 cluster。
- hidden 成员不得出现在任何 current/cluster audience ref。
- `resolved_history_refs` 在 S3 维持空，除非输入存在独立、明确、逐 identity 的 R2 lifecycle authority；不得仅凭 D10 `change_kind=resolved` 推断风险已关闭。
- 同一 risk/member ref 不得跨 high/medium/low/resolved 重复。

## 5. 变化带规则

- 每个具有可投影 risk marker 的 unit 产生一个 change band；`change_kind` 与 `change_cause` 逐值复制 D10 `D10ChangeSection`，不从两次数值差计算。
- `initial_current` 的 `prior_snapshot_ref` 必须为 `None`；其他变化仅在 D10 `ChangeDecision.prior_snapshot_ref_or_none` 存在时引用。
- `not_comparable` 或非数据 cause 不得被改写为新增、加重、减轻或关闭。
- D10 `mixed` 不是 R5 closed cause；遇到 mixed 必须 fail-closed，不得任取第一个原因。
- resolved change band 可以进入变化历史，但不自动把相同 risk 从 current set 移除。

## 6. 定量度量规则

每个 unit 按 D10 separated count layers 独立生成可用的 `R5QuantitativeMeasure`：`individual_risk`、`center_pattern`、`affected_subject`、`event`、`affected_site`、`project_signal`、`clue`、`query`。禁止相加为“总风险数”。

- `numerator_value` 逐值复制 `D10ProjectionCountSurface` 对应字段；`authoritative_value_ref` 绑定该 unit 的 `count_surface_ref` 加 closed layer kind，不由 UI 行数产生。
- `numerator_member_refs` 必须从 D10 projectable member/source projections 按该 layer 的 closed membership recipe 重建；无法逐成员归属的 layer 使用空 tuple，并显式保留 evaluation-limit ref，不能编造 refs。
- `denominator_*` 逐值复制 `D10TypedInput.denominator`；值、state、kind、unit 与 member/exclusion refs 不得重算。`recomputed_value` 只用于验证上游自洽，不进入 R5 audience value。
- `coverage_state` 只接受同 unit D10 center rows 的唯一 closed coverage state；无公开 row、多个冲突 state 或 hidden-only unit 时为 `not_evaluable`，不得当 complete/0。
- `cutoff_ref` 来自唯一 closed analysis window；缺失或多窗不唯一时 fail-closed。
- `evaluation_limit_refs` 使用该 unit `EvaluationLimits` 完整 canonical content identity；不把限制值当医学结论。
- `closed_zero` 只允许 denominator value 0 且 rate state `not_evaluable`；unknown/unclosed 不显示 0%。

## 7. 中心图谱规则

- 一个 cell 的 key 固定为 `(site_ref, domain)`；cell 中 `pattern_refs` 只含 `member_kind=center_pattern`，`individual_risk_refs` 只含 `member_kind=individual_risk`，两者不得互相推断。
- 单个 individual risk 不得升级成 pattern；pattern 必须有显式 R4 pattern member 或 pattern projection authority。
- severity 是该 cell 所有可见 current 成员的上游 monitoring priority 最大值；仅允许 high/medium/low，不能由数量升成 critical。
- `measure_refs` 只指向同 site/unit 的度量；无逐中心 denominator authority 时允许为空，不伪造中心率。
- hidden member/site 对 cell、stable order、measure membership 与 content hash 的 audience payload 都是零泄漏。
- `stable_site_order` 只按 NFC 后的 stable site identity 升序，重放稳定；schema、运行时和 audience 输出均不得出现 score、rank、top-N、红黑榜或惩罚性序号。

## 8. Projection identity 与引用闭合

- 所有输出引用必须在同一 bundle 内唯一解析；dangling ref、重复 ref、跨 packet ref 一律拒绝。
- `R5ProjectionInstance` 的 opaque run/snapshot 来自 receipt；replay content identity 由已排序的 authority-unit content identities 生成，unit 重排不变，任一 authority leaf 变化则改变。
- `center_map.content_hash`、`cockpit.content_hash` 与 S3 bundle hash 使用 R5 canonical recipe；调用者提供的旧 hash 必须拒绝。
- cockpit 默认 `selected_risk_ref=None`；S3 不替用户制造选择或写回。
- S3 public API 不暴露 raw hidden refs、fixture id、case id、test id、mutation class、后端日志字段或模型内部标识。

## 9. 挑战与非 LLM 验收矩阵

至少覆盖以下独立测试族；每项均用具体输入 mutation 与 exact error/output oracle：

1. authority identity/hash/project/run/snapshot/cutoff/visibility 漂移；
2. unit 重排 replay identity 不变、unit 内容改变 identity 改变；
3. high/medium 全量保留与超过 5 项不截断；
4. low cluster 无损展开、跨域/跨中心不错误合并；
5. hidden member/site 不进入 current/cluster/cell/measure/hash audience surface；
6. resolved 不自动移出 current；缺 R2 lifecycle 时 history 为空；
7. initial/new/upgraded/continued/downgraded/resolved/reopened/not_evaluable/not_comparable 与 cause plane 逐值适配；mixed fail-closed；
8. 八类 count layer 分别守恒且互不相加；query/clue/pattern/risk 不混算；
9. numerator member exact rebuild、重复成员拒绝、不可归属层不伪造；
10. denominator positive/zero/unknown/unclosed、exclusion、unit、rate state；
11. coverage complete/partial/truncated/unknown/not-applicable/hidden-only；
12. cutoff 缺失/多窗/错窗与 evaluation limit tamper；
13. pattern/individual 分层、单例不升级、domain/site 交叉污染拒绝；
14. stable site sorting、输入顺序无关、无 score/rank schema；
15. canonical hash、dangling/duplicate/cross-packet refs；
16. R4 全量 SHA 前后不变、R5 full tests、R4 adjacent/full tests、Ruff F、normal/optimized compile；
17. 8911 全程 `connect_ex != 0`，无浏览器/前端/真实项目访问。

## 10. 写入边界与阶段门

合同接受前只允许写本合同与 task context/review/metrics。接受后 S3 runtime 唯一写域：

- `poc/medical_monitoring_ai_native_r5/src/mm_r5/s3_*`
- `poc/medical_monitoring_ai_native_r5/tests/test_s3_*`
- `poc/medical_monitoring_ai_native_r5/tests/challenges/test_s3_*`
- `poc/medical_monitoring_ai_native_r5/evidence/r4_s3_readonly_sha256.json`
- 为公共导出所需的最小 `src/mm_r5/__init__.py` 修改
- 本任务 context/review/metrics/evidence

禁止修改 `poc/medical_monitoring_ai_native_r4/**`、`frontend/**`、任何医学写作路径、真实项目资料、服务/生产/安全专项。合同 reviewer 只可返回 `ACCEPT_R5_S3_CONTRACT` 或 `REVISE_R5_S3_CONTRACT`。合同接受只解锁 S3 runtime；最终必须由另一独立 reviewer 返回 `ACCEPT_R5_S3` 才能进入 S4。

