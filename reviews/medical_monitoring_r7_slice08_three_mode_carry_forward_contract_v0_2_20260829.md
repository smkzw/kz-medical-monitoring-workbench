# R7 Slice-08 三模式跨 Run 连续性合同 v0.2 纠偏附录

日期：2026-08-29  
状态：`FROZEN_ACCEPTED_R7_SLICE_08_CONTRACT_V0_2`

本附录与 v0.1 合并构成完整合同；冲突时本附录优先。它关闭独立会商 Round 1 的七类缺口，且不新增平行医学风险生命周期。

## 9. 数据缺失不等于风险消除

1. 继承现有 R1 规则：上一已发布结果中的高危/严重风险在本轮完整 listing 中未出现关联记录时，不得自动关闭，必须继续可见并显示“需重新判断”或按既有 R1 高危沿用规则保持开放。
2. 当覆盖不完整、当前快照不具备基线资格、稳定业务键不可用、身份/映射/规则谱系变化时，任何严重度的既往风险都不得因“本轮未出现”而关闭。
3. 低危/中危风险只有在当前完整、可比较、基线合格的全量 listing 与冻结域规则明确支持数据性消除时，才可进入既有 R1 `resolved_by_data` 路径；R7 不自行推导临床转归，也不把 `resolved_by_data` 改写为已获得人工结案。
4. `close_with_evidence` 必须引用当前运行的明确纠正、转归、排除或结案证据，并通过 R2 既有 adjudication/transition 门；单纯缺行、窗口外或文字相似均不是结案证据。

## 10. 不建立第二套风险状态机

R2 `RiskLifecycleState / RiskTransitionType` 及其合法转移矩阵继续是唯一机器权威。Slice-08 不新增 `continued` 等平行生命周期状态，也不把中文变化词写回 R2 状态。

R7 只新增只读 `RiskChangeKind` 投影：

| 公开中文 | `RiskChangeKind` | R2/前后事实约束 |
|---|---|---|
| 新增 | `new` | 本轮新建立稳定风险身份 |
| 升级 | `upgraded` | 合法 R2 escalated transition 或严重度上升证据 |
| 持续 | `continued` | 同一稳定身份仍开放且未发生升级/降级；不追加虚构 R2 transition |
| 降级 | `downgraded` | 合法 R2 deescalated transition |
| 关闭 | `closed` | 合法 R2 closed transition 与当前证据 |
| 重开 | `reopened` | 既往 closed 后发生合法 R2 reopened transition |
| 需重新判断 | `needs_rejudgment` | identity_ambiguous、not_evaluable、谱系变化或数据缺失阻断 |

`closed` 不得直接投影为升级/降级/持续；只有先发生 R2 `reopened` 才可在后续事实中重新分级。每个投影必须携带前后 R2 状态、前后严重度、原因类别和当前/比较来源定位。

## 11. CarryForwardPlan 粒度与规则作用域

允许的 `object_type` 仅为：

- `risk_instance`：稳定风险身份；
- `mode_output_item`：R6 ModeOutput 中具备独立内容摘要的子项；
- `query_draft`：与单一风险/受试者/中心身份绑定的结构化 Query 草稿；
- `evidence_binding`：当前对象可复核的来源绑定。

完整 data listing 行是 diff 输入而非可沿用产物；Subject Journey/Timeline 必须从当前 R5 authority packet 与当前事件事实重新投影，不得整块沿用上一轮页面或 SVG。

规则变化只影响显式属于该 `rule_revision_id` 适用范围的对象。计划条目必须记录 `governing_rule_revision_ids` 和 `changed_applicable_rule_ids`；若无法证明规则不适用，则该对象进入 `re_evaluate_rule_change`，不得全项目静默沿用，也不得因一条规则变化强制重算所有无关对象。

## 12. 沿用产物校验

`reuse_unchanged` 条目必须绑定内部来源运行、来源 publication、来源 artifact ID/SHA-256、对象身份、当前适用规则和当前目标身份。发布前逐项核对：

1. 来源 publication 为同项目、同模式、`available`；
2. 来源 artifact 在该 publication/R5-R6 权威包的允许成员中；
3. 重新读取的字节 SHA-256 与冻结值一致；
4. 当前对象身份、数据关联、规则适用性和输出合同版本兼容；
5. Query 草稿仍只是草稿，不沿用“已发送、已关闭、已确认”等状态。

任一项失败时，对象转为重新评估；跨项目、摘要篡改或来源包成员不一致时整次 publication `blocked`，结果入口保持关闭。

## 13. 最小 additive schema 与原子提交

不复制 R2 风险 transition 表，也不建立第二个结果发布器。`launch_registry.sqlite3` 从 v2 向后兼容升级，仅新增：

1. `r7_continuity_plans`：每个目标运行一行，保存目标 run、基线 publication/run 身份、决定版本、规则集合摘要、R5/R6 权威摘要、plan digest、状态、计数和时间；`UNIQUE(project_id, target_run_id)`。
2. `r7_continuity_items`：保存 plan、固定序号、对象类型/身份、处置、来源 artifact 身份、前后风险状态/严重度、规则作用域、归因和证据 JSON；`UNIQUE(plan_id, ordinal)`，并以外键绑定 plan。

DDL 必须使用现有显式 `BEGIN IMMEDIATE`、`busy_timeout`、版本标记最后推进和 failure injector 约定。旧 launch/publication 行保持不变；迁移中任一点失败必须完整回滚并可重试。

计划先写 `staging`，完整核对后转 `verified`。最终发布继续调用既有 `ResultPublication` CAS；只有当前 publication 仍为 `publishing`、continuity plan 为 `verified`、摘要与当前 R5/R6 身份一致时，才能在一个事务中把 plan 标为 `published` 并把 publication 推进为 `available`。CAS 冲突、迟到回调或摘要漂移全部回滚，不产生半发布。

## 14. 三模式和用户选择

- 日常监查支持 `full|incremental`；增量默认推荐最近一次兼容且已发布的日常结果，同时允许用户从其他兼容已发布结果中选择。`cannot_compare` 对象必须重新评估。
- 锁库前监查仍只允许 `full`。机器归因固定为 `query_driven|data_revision`；只有前者且证据完整时公开显示“Query 后修订影响”。
- 核查前监查强制 `full + fixed_total=true`。项目、快照、截止点、中心覆盖、规则集合和决定版本完全相同时才是同一请求重放；任一变化创建新运行，旧公开结果和数据库事实不变。
- 向导中新规则未确认、候选解释未选择或 option 已过期时，`prepare-and-start` 必须失败关闭，不回退到旧规则静默执行。
- Query 草稿按风险/受试者/中心身份单项绑定，同时由 R6 项目级 Query 输出包聚合展示；聚合包不得抹掉单项来源和风险身份。

## 15. 中文公开词表与页面字段

风险变化只显示：`新增、升级、持续、降级、关闭、重开、需重新判断`。

处置原因只显示：`沿用上次有效分析、因数据变化重新评估、因规则变化重新评估、因既往证据不足重新评估、已有证据支持结案、不满足沿用条件`。

归因只显示：`Query 后修订影响、本轮数据修订变化、本次固定数据范围`。

项目/中心摘要公开字段闭集为：本轮变化受试者数、中高风险新增/升级/持续/需重新判断计数、比较范围中文、数据截止中文。风险 Inspector 公开字段闭集为：上次结论、本次变化、判断依据、当前来源、比较来源。Journey 仅增加当前事件变化和风险变化标记，不增加第二条身份带。

公开 URL、响应和页面不得出现内部 `run_id/run_ref/digest/CAS/artifact/provider/model/sqlite/S4/R5/R6/R7`。既有 `public_run_token/result_context_token/response_digest` 可保留在协议内部字段，但 UI 文案不得显示；不得因词面 scrubber 删除合法医学文本，验证应针对 schema 字段和界面节点，而不是扫描所有来源正文。

## 16. 扩展验证矩阵

在 v0.1 十项基础上增加：

1. 高危/严重风险缺行、覆盖不全、基线不合格、谱系变化均不自动关闭；低/中危数据性消除只走冻结 R1 规则。
2. R2 所有合法/非法转移与七类公开变化映射；不产生平行生命周期记录。
3. 规则 A 改变仅影响适用对象；规则 B 无关对象仍可沿用；规则适用性不明则重新评估。
4. 来源 artifact 存在/丢失/篡改/跨项目/不在 publication 成员集；Query 禁止状态不得沿用。
5. v2→v3 additive migration 在建表、写版本、索引和提交前后故障注入；旧行与 publication token 不变。
6. plan staging/verified/published 与 publication publishing/available 的 CAS 冲突、迟到回调和重试。
7. 日常多基线推荐与用户改选、未确认规则阻断、锁库前归因、固定总量重放/新运行。
8. hash seed/优化级别、SQLite 关闭重开、相同请求重放的摘要一致性。
9. 公开 schema 字段和实际界面节点不泄漏内部词；医学来源正文不被错误 scrub。
10. ego(lite) 1280/1440/1920 验证项目→中心→风险→Journey→来源比较的身份和中文层级。

## 17. 实施顺序与冻结条件

1. 08A 只实现 continuity 领域对象、v3 additive migration、计划生成/校验、故障矩阵和确定性测试；不改 UI。
2. 08B 才连接 R6 ModeOutput、R5 authority bridge 和既有 ResultPublication CAS。
3. 08C 才增加中文跨轮投影和 ego(lite) 视觉验收。
4. 08D 完成三模式综合回归与独立接受。

v0.2 已由 Round 1 同一会话 Round 2 复核为 `ACCEPT_R7_SLICE_08_CONTRACT_V0_2`，现冻结为 08A 实施权威。任何后续修订必须形成新版本并重新会商，不得静默改写本冻结合同。
