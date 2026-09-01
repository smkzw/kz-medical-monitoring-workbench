# R7 Slice-08B 权威与产物桥接合同 v0.1

日期：2026-08-29  
状态：`PROPOSED_FOR_INDEPENDENT_REVIEW`

## 1. 目标与范围

本切片只关闭 Slice-08A 的三项真实证据缺口：

1. 来源 R5 权威必须来自既有 `mm_r5.r5_publication_authority.R5AuthorityPacket`；
2. 来源 R6 产物必须先通过既有 `validate_mode_output`，再按固定路径提取原子子项；
3. 允许沿用的来源产物必须是既有 R1 `Store` 已提交、属于来源 publication 成员集且真实文件字节可复核的 `ArtifactEnvelope`。

08B 仍是 synthetic/offline 后端纵切。不改 UI，不启动 8911/5174，不运行真实项目或模型，不修改 R1-R6 医学事实、风险分级、Journey/Timeline 或医学写作。

## 2. 唯一权威边界

### 2.1 R5

- R7 不新增第二套 authority packet、assembler 或医学成员闭包。
- `DecisionBaseline.r5_authority_digest` 与 `CarryForwardPlan.r5_authority_digest` 必须等于来源 `R5AuthorityPacket.packet_digest`。
- 接入时必须重新实例化/校验现有 typed packet；同时核对 `packet_identity == "r5-publication-authority:" + packet_digest`、`authority_hash == packet_digest`、项目、运行、公开 token、快照、截止点和中心覆盖。
- S4 packet ID/digest 只证明 R5 包内成员身份，不冒充磁盘产物字节摘要。

### 2.2 R6

- R6 `ModeOutput` 仍由 `mm_r6.mode_output` 定义；R7 不复制 envelope validator。
- 每个来源输出必须对来源 `run_binding + mode_contract` 调用 `validate_mode_output`，返回任何失败码即拒绝该输出。
- `output_id` 是 R6 canonical envelope 身份；它不等于 R1 artifact ID，也不等于 publication digest。
- `r6_output_set_digest` 定义为对按 `(output_kind, output_id)` 排序的完整已验证四输出集合进行 canonical JSON SHA-256；三种模式均须恰好覆盖各自四个默认 output kind，不接受缺项、重复或额外系统输出。

### 2.3 R1 产物

- 真实文件与成员权威复用现有 R1 `Store.stage_artifact/commit_artifact/get_artifact/verify_artifact`；不新增平行文件仓库、路径 manifest 或自制原子写入器。
- 每个已验证 R6 ModeOutput 以一个 `ArtifactEnvelope` 持久化，payload 保存完整 ModeOutput，`artifact_type="r6_mode_output"`，版本固定，`run_id` 与来源 run 一致。
- R1 `artifact_id == content_hash`，且 `verify_artifact` 同时校验数据库成员、content-addressed 文件真实字节、envelope canonical hash 与 raw-output evidence 引用。
- R7 禁止接受调用方传入的 `artifact_verified=True` 或 `artifact_member_verified=True` 作为事实；这两个值只能由 08B verifier 根据 R1 Store 与 publication 成员集计算。

## 3. Publication 最小 additive 扩展

`launch_registry.sqlite3` 从 v3 向后兼容升级为 v4，只给 `r7_result_publications` 增加：

- `r6_output_set_digest TEXT`；
- `artifact_member_ids_json TEXT NOT NULL DEFAULT '[]'`；
- `artifact_member_set_digest TEXT`。

`artifact_member_ids` 是本 publication 允许被连续性计划引用的 R1 artifact ID 闭集。集合必须排序、去重、非空；每个成员均须属于同一来源 run 且 `Store.verify_artifact(id)` 为真。`artifact_member_set_digest` 为 canonical 排序 ID 列表的 SHA-256。

不得把成员清单塞入 `runtime_manifest_identity_json`：该字段属于已冻结运行 manifest 身份，混入完成后产物会破坏职责与重放语义。不得以“该 run 的全部 artifacts”隐式代替 publication 成员闭集。

最终发布 CAS 必须在同一事务中核对并写入 R5 packet 身份、R6 output-set digest、artifact member IDs/set digest、receipt set，以及 continuity plan 的三个摘要；任何漂移均回滚，结果入口保持关闭。已 available 的同值重放返回原记录，不同值重放冲突。

## 4. R6 子项抽取闭集

抽取器只返回冻结 DTO：`object_type`、`object_id`、`output_kind`、`output_id`、`artifact_id`、`item_digest`、`payload`。`item_digest` 是原子子项完整 mapping 的 canonical JSON SHA-256；不删除或改写 run/source 字段，不制造“跨轮等价”。是否变化仍由 08A 的稳定业务身份与当前事实比较决定。

允许路径：

| 模式 | 输出 | 原子路径 | object_type | 备注 |
|---|---|---|---|---|
| daily | `current_full_risk` | `payload.risks[]` | `risk_instance` | 必须有稳定 risk ID |
| daily | `affected_query_draft` | `payload.query_drafts[]` | `query_draft` | 必须保持 draft、未发送、未关闭、未确认 |
| pre_lock | `full_risk` | `payload.risks[]` | `risk_instance` | 只读风险项，不复制 R2 生命周期 |
| post_lock_pre_cfdi | `site_materials` | `payload.materials[]` | `mode_output_item` | 以 `site_material_id` 为对象身份 |
| post_lock_pre_cfdi | `subject_materials` | `payload.materials[]` | `mode_output_item` | 以 `subject_material_id` 为对象身份 |

`change_summary`、两类 revision/impact/package、`check_package`、`checklist`、`full_project_report`、整份 ModeOutput、listing、页面、SVG、Profile、Journey、Timeline 均不得作为 `reuse_unchanged` 子项；它们必须从当前运行事实重新生成。证据绑定只可作为上述原子对象的引用证据，不作为可独立复制的医学结论。

## 5. 沿用校验算法

对每个拟 `reuse_unchanged` 的来源条目，按顺序执行：

1. 来源 publication 为同项目、同模式、`available`，且其 R5/R6/receipt 摘要与基线一致；
2. `source_artifact_id` 位于 publication 的显式 `artifact_member_ids`；
3. R1 `get_artifact` 返回的 envelope 属于来源 run、类型为 `r6_mode_output`，其 `artifact_id/content_hash` 与条目 SHA 一致；
4. `Store.verify_artifact(source_artifact_id)` 为真，从而复核真实 content-addressed 文件字节；
5. envelope 内 ModeOutput 再次通过 R6 validator，`output_id/output_kind` 与抽取记录一致；
6. 重新抽取同一 `object_id`，其 `item_digest` 与计划证据一致；
7. 08A 的同项目、同模式、身份兼容、规则适用、数据未变化和 Query 草稿边界全部通过。

文件缺失、成员缺失、字节或 envelope/子项摘要篡改、跨项目、跨模式、错误 run、错误 output set 均为完整性冲突：阻断 publication，不把它静默降级成普通“重新评估”。当前数据或规则正常变化才进入 08A 单项重新评估处置。

## 6. 实现边界

优先新增单一 R7 模块 `continuity_bridge.py`，只做：

- 复用 R5 typed packet 校验；
- 调用 R6 validator、计算 output-set digest、抽取固定原子路径；
- 复用 R1 Store 提交/读取/验证 ModeOutput artifact；
- 由真实验证结果构造 08A `CarryForwardItem` 输入。

`continuity.py` 不增加第二套验证器；`launch_registry.py` 只做 v4 additive 字段、迁移、序列化与 CAS。产品路由只接线现有 provider/bridge/store，不在路由层重写上述规则。

## 7. 验收矩阵

必须覆盖：

1. 三模式各四个 ModeOutput 正常集合，以及缺项、重复、额外、错误模式、错误 run、篡改 output ID；
2. 五类允许子项的提取、稳定排序/摘要、重复对象 ID、缺对象 ID、Query 终态污染；
3. R5 packet 身份/摘要/项目/run/快照/截止/中心漂移；
4. R1 artifact 未提交、非成员、错误 run/type、文件丢失、单字节篡改、envelope 篡改；
5. v3→v4 迁移各故障点完整回滚并可重试，旧行与公开 token 不变；
6. publication/continuity CAS、available 同值重放、异值冲突、迟到回调；
7. 3 个 hash seed × normal/`-O`/`-OO` 的 output-set/item/member-set digest 一致；
8. 聚焦、完整 R7、相邻 R1/R5/R6 与产品医学监查回归；8911/5174 停止，医学写作边界不变。

## 8. 本切片不证明

08B 不证明真实项目医学质量、真实模型调用、UI/中文投影、Patient Journey、项目/中心看板、视觉质量、三模式真实端到端、R7 总体或 R8 完成。视觉专项要求继续留在 08C 及后续 UI Phase。
