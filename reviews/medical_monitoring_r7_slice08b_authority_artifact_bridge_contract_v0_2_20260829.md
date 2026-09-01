# R7 Slice-08B 权威与产物桥接合同 v0.2 纠偏附录

日期：2026-08-29  
状态：`FROZEN_ACCEPTED_R7_SLICE_08B_CONTRACT_V0_2`

本附录与 v0.1 合并构成完整合同；冲突时本附录优先。它关闭独立会商 Round 1 提出的输出集摘要孤悬、对象身份/canonical 不明确、publication 生命周期与跨库事务边界不明确等缺口。

## 9. R6 输出集摘要必须进入 Continuity 权威链

v4 additive migration 不仅扩展 `r7_result_publications`，还须给 `r7_continuity_plans` 增加：

- `r6_output_set_digest TEXT NOT NULL DEFAULT ''`。

08B 新建 `CarryForwardPlan` 时必须提供 64 位小写 SHA-256 的 `r6_output_set_digest`，并将其纳入 `CarryForwardPlan.canonical_payload` 与 `plan_digest`。v3 旧 plan 回读时允许空值，但不得转为 `verified/published`，必须按当前来源 publication 重建为 v4 plan。

`r6_publication_digest` 保持既有语义：来源 `ResultPublication.publication_fingerprint`，不改名、不复用为输出内容摘要。最终 CAS 分别核对：

1. `plan.r5_authority_digest == publication.r5_authority_packet_digest`；
2. `plan.r6_publication_digest == publication.publication_fingerprint`；
3. `plan.r6_receipt_digest == publication.receipt_set_digest`；
4. `plan.r6_output_set_digest == publication.r6_output_set_digest`。

任何一项漂移均为 `continuity_publication_conflict`，不得以另一个摘要替代。

## 10. v4 字段、状态与原子边界

完整 v4 additive 字段为：

- `r7_result_publications.r6_output_set_digest TEXT`；
- `r7_result_publications.artifact_member_ids_json TEXT NOT NULL DEFAULT '[]'`；
- `r7_result_publications.artifact_member_set_digest TEXT`；
- `r7_continuity_plans.r6_output_set_digest TEXT NOT NULL DEFAULT ''`。

`publishing` 与 v3 历史行允许空输出集/成员集；只有 `finalize_publication` 才强制四个 ModeOutput、非空成员闭集及三个新摘要完整。`available` 行必须满足：

- `r6_output_set_digest` 为合法 SHA-256；
- `artifact_member_ids` 排序、去重、非空；
- `artifact_member_set_digest == content_digest(artifact_member_ids)`；
- 每个成员均由调用 `finalize_publication` 前的 08B verifier 证明属于同一 run、类型为 `r6_mode_output` 且 `R1 Store.verify_artifact` 为真。

同值 available 重放返回原记录；输出集或成员集任一值不同均冲突。迁移故障注入至少覆盖每个 `ALTER` 后、版本更新前和 commit 前，全部回滚并可重试，旧 publication、公开 token 与 v3 continuity 行不变。

R1 Store 与 LaunchRegistry 是两套 SQLite，08B 不声称分布式事务。R1 artifact 先按既有协议提交；其只读验证结果作为 LaunchRegistry `BEGIN IMMEDIATE` 的输入。publication 字段、launch 结果入口与 continuity `published` 仍必须在 LaunchRegistry 的同一事务内推进；验证失败时不得进入该推进事务或须完整回滚。

## 11. Canonical 与对象身份闭集

08B 自身的 `r6_output_set_digest`、`item_digest`、`artifact_member_set_digest` 统一复用 R7 `launch_registry.content_digest/canonical_json`；不另写 JSON/hash helper。R1 artifact ID 仍只由 R1 `ArtifactEnvelope.canonical_hash` 产生，R5/R6 各自身份仍由其原模块产生，四个哈希域不得混用。

抽取对象身份固定为源字段，不在 R7 重算上游业务 ID：

| object_type | 输出路径 | object_id |
|---|---|---|
| `risk_instance` | `current_full_risk/full_risk.payload.risks[]` | 非空 `risk_id`，且必须存在于来源 R5 packet 的 risk ref 集合 |
| `query_draft` | `affected_query_draft.payload.query_drafts[]` | 非空 `query_draft_id`；R6 validator 已重算并校验其算法 |
| `mode_output_item` | `site_materials.payload.materials[]` | 非空 `site_material_id`；R6 validator 已规范化并校验 |
| `mode_output_item` | `subject_materials.payload.materials[]` | 非空 `subject_material_id`；R6 validator 已规范化并校验 |

缺 ID、重复 ID、risk ID 不在 R5 权威成员集、材料中的 subject/site/risk 引用不在 R5 成员闭包，均拒绝该输出集。R7 不猜测 `risk_ref/risk_id` 映射、不按文本相似度补身份。

`item_digest = content_digest(原子子项完整 mapping)`；不剥离 run、source、cutoff 或状态字段。输出集摘要为：

```text
content_digest([
  {"output_kind": kind, "output_id": id, "artifact_id": artifact_id},
  ...按 output_kind、output_id 排序
])
```

这样输出内容身份与其已提交 R1 artifact 同时进入 output-set digest，任何一侧替换都会漂移。

## 12. Query 与跨对象依赖

Query 草稿除再次通过 R6 draft-only 门外，还必须满足关联 `risk_id`、`subject_id`、`site_id` 均能在来源 R5 packet 定位。若关联风险在当前计划中不是 `reuse_unchanged`，或未由当前事实重新建立为同一稳定身份，该 Query 草稿不得孤立沿用，改为既有 `re_evaluate_prior_uncertain`。

## 13. 失败分层

- 第 1-6 步证据完整性失败：来源 publication、R5/R6/receipt/output-set、显式成员集、R1 artifact、ModeOutput envelope 或子项摘要不一致，整次 publication `blocked`，结果入口关闭。
- 第 7 步业务适用性失败：当前数据、规则或对象关系发生正常变化，按 08A 的单项处置重评；不得把完整性冲突伪装成普通业务变化。
- `r6_mode_output` artifact 的 `evidence_refs` 不新造 `raw-output:` 引用；若上游明确提供该引用，则必须能被既有 R1 Store 验证，否则 artifact 校验失败。

## 14. 实现职责进一步冻结

`continuity_bridge.py` 只允许实现 R5 typed packet 边界核对、R6 四输出校验/摘要/固定抽取、R1 ModeOutput artifact 提交与复核，以及以机器计算的验证结果构造既有 08A `CarryForwardItem` 输入。不得重定义 `DecisionBaseline`、`CarryForwardPlan/Item`、`RiskChangeKind`、R2 状态或医学判断。

产品路由只负责取得既有 run binding、mode contract、R5 packet、R6 outputs 与 R1 Store，并调用桥接器；不得复制桥接规则。08B 若产品端尚无真实 R6 output provider，则以显式注入的 synthetic provider 完成产品接线测试，不伪造真实模型/项目已贯通。

## 15. 验收补充

除 v0.1 §7 外增加：

1. `r6_output_set_digest` 同时绑定 publication、plan canonical digest 与 finalize CAS；
2. publishing 空集、available 非空集、v3 旧 plan 不可直接 verify/publish；
3. risk ID 与 R5 member、Query 与风险/受试者/中心、site/subject material 与 R5 closure 穿透校验；
4. R1 文件单字节篡改、`raw-output:` 引用缺失、publication 成员 JSON 直接篡改均阻断；
5. v4 每个 ALTER 及 commit 前故障回滚；
6. 无任何代码从 `SELECT artifacts WHERE run_id` 推导隐式 publication 成员集，也不写 `runtime_manifest_identity_json`；
7. 聚焦测试后运行完整 R7、相邻 R1/R5/R6 和产品医学监查回归，保持 8911/5174 停止及医学写作聚合哈希不变。

## 16. 四项最终冻结补充

1. 每个 `r6_mode_output` 的 `ArtifactEnvelope` 固定为：`version = mm_r6.mode_output.CONTRACT_VERSION`、`node_id = ModeOutput.output_id`、`node_type = NodeType.DETERMINISTIC_SERVICE`、`payload_role = PAYLOAD_ROLE_INFERENCE`、`input_hashes = [mode_contract_digest]`、`coverage = None`、`completeness = COMPLETE`；`evidence_refs` 默认空，上游若显式提供已验证 `raw-output:` 引用则原样透传且必须通过 R1 Store 校验。任一字段偏离均产生不同 artifact 身份，不得与冻结成员混用。
2. 校验用 `mode_contract` 必须由 `mm_r6.mode_output.build_mode_contract(run_binding["mode"])` 现场取得，并先通过 `validate_mode_contract`；不得接受调用方自制或放宽的 contract。其 `mode_contract_digest` 同时写入 ArtifactEnvelope `input_hashes`。
3. `post_lock_pre_cfdi` 四输出除逐件 `validate_mode_output` 外，必须在计算 output-set digest 前通过 `validate_post_lock_output_set(full_project_report, site_materials, subject_materials, checklist) == ()`；任一跨输出总量、成员或身份不一致均阻断。
4. `object_type` 继承冻结 Slice-08 v0.2 的四类闭集，但本切片只开放 `risk_instance / query_draft / mode_output_item` 三类原子对象；`evidence_binding` 在 08B 仅作为这些对象的引用证据，不得独立进入 `reuse_unchanged`。
