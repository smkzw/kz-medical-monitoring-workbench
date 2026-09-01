# R7 Slice-07C-3 结果发布合同 v0.2 纠偏附录

日期：2026-08-29  
状态：`FROZEN_ACCEPTED_R7_SLICE_07C3_RESULT_PUBLICATION_V0_2`

本附录与 v0.1 合并阅读；冲突时以本附录为准。它吸收独立会商第一轮发现，不改变
Slice-07C v0.2 的上位业务目标。

## 1. R5 前置桥纳入本切

07C-3 采用完整方案，不降级为“只做 receipt 门禁”。实施第 0 步新增 **R5-owned** 两段桥：

1. `R5PublicationAuthorityInputAssembler`：只接受调用方注入的冻结 run identity、typed R4/R5
   accepted authority、raw bytes 与既有 `R5S4RuntimeInput` 所需 typed 对象；不从 R6 receipt marker、
   模型文本、前端 fixture 或测试 case 推断医学事实。它只做身份校验和 typed 输入装配。
2. `R5PublicationAuthorityBridge`：对每个风险调用既有
   `build_s4_authority_packet`，随后调用既有 `validate_s4_authority_packet`；再把已验证 S4 packet
   集合与已接受的 typed subject/site/event/visit/source authority 做确定性 member join，生成产品
   `R5AuthorityPacket`。它不得重算风险、严重度、Query、Journey、分子/分母或裁决。

R7 只注入并调用 R5 bridge/provider，核对返回 packet 的 project/run/snapshot/cutoff/site coverage
与 digest。其中注册表冻结的是公开 snapshot option token，产品 packet 使用 `snapshot_ref`；二者必须由
冻结 run options 中的确定性映射进行对账，synthetic 路径也使用同一映射，比对失败为 `blocked`。
桥不存在、输入不全或 validator 不通过时 fail closed。synthetic 测试可显式注入 accepted
synthetic authority provider，但禁止缺少 provider 时自动回退 fixture。

## 2. 双 manifest 身份

publication 同时冻结：

- setup manifest digest（launch registry 已存）；
- R1 runtime manifest revision 与按 canonical JSON 计算的 runtime manifest digest；
- 两者的 `work_unit_id → mandatory` 映射和 mandatory denominator。

setup 与 runtime 的 ID 集合、mandatory 标志或分母任一不一致均为 `blocked`。stage 中文化、scope
展示转换和 label 不参与跨 manifest 等同性判断，避免把展示差异误判为身份漂移。

## 3. Publication 唯一性与跨 key 重放

每个 run 只有一个 publication identity，唯一键为 `(project_id, run_id)`；当前 schema 的
`publication_revision` 固定为 1，预留字段不代表同一 run 可多版本覆盖。

请求级 canonical frozen-content fingerprint 由服务端计算，字段严格限定为：canonical project id、
public/internal run identity、公开 snapshot option token、source revision、data cutoff、排序后的 site coverage，
以及冻结 setup manifest 的 work-unit identity/mandatory 映射。runtime manifest 映射变化按 §2
判定 `blocked`，不参与请求级 fingerprint。fingerprint 明确不包含 receipt set、receipt-set
digest、publication attempt/state 等 completion-dependent 输入；receipt-set digest 只在 finalize 时绑定到
终态 publication row。idempotency key 只是请求重试句柄：

- 同 run 同 fingerprint，不论 key 是否相同，均返回同一 publication；
- reserve 后中断，可由原 key 或新 key 续接同一 publication；
- 同 run 冻结身份相同则 fingerprint 必须相同；冻结身份不同导致 fingerprint 不同则一律 409，不创建
  revision 2；
- key 在另一 run 使用按项目级 `(project,key)` 冲突规则拒绝。

## 4. 发布前状态校准与失败分类

发布入口先 reserve publication，再通过现有 `read_progress` 权威读取并校准 launch state，随后评估门禁。
只有在 reserve 本身失败、尚未产生 publication row 时才直接失败并允许管理员重试；reserve 后的 runtime、
authority 或临时 SQLite/I/O 读取失败必须记录到该 publication row：

- `running`、`waiting_start`、`stopping`、`interrupted_resumable`、`ended_incomplete`、`failed`
  均为 `blocked`，不得进入 R5 构建；
- 无法读取 runtime、临时 SQLite/I/O 故障：尚未形成内容判定，保留/转为
  `recoverable_failed`；
- 运行已 completed 后，receipt 缺失、partial/unparsed、覆盖缺口、身份漂移、manifest 不一致、
  site/member 不闭合属于 `blocked`；
- 门禁已通过后的进程中断、持久化临时故障、`S4RuntimeImplementationError` 或可信输入装配器
  的暂时实现故障属于 `recoverable_failed`；
- S4 validator 返回 packet 拒绝或 R5 member identity 不一致属于 `blocked`。

## 5. Site coverage 唯一派生

site coverage = 冻结 current snapshot 行中非空 `site_ref` 的排序去重集合；该集合与 snapshot
option token/source revision 一并进入 publication fingerprint。产品 `R5AuthorityPacket.sites` 集合
必须与 coverage 完全相等；S4 packet 的 risk/site/subject 成员必须是产品 packet 成员且来源闭合。
任一不等为 `blocked`。result-entry 中心 allow-list 只使用这套 coverage。

## 6. Progress 叠加边界

publication 状态不写入 R1 runtime DB。产品 router 的 progress 路由读取 R1 progress 后，再以同一
project/run 读取 launch/publication registry，生成唯一一份公开叠加：

- `publication_state`、`result_available`、`publication_status_text`；
- 运行完成但结果未 available 时显示“分析已结束，结果整理未完成”；
- 管理员发布动作沿用现有 role-action 过滤，医学监察员不看到不可执行按钮。

R1 `_public_overlay` 不复制 publication 文案。history 保持既有七字段闭集，只通过同事务更新后的
`result_available/main_action` 反映可用性。发布/结果入口 URL 只接受 public run token；内部 run id
继续只用于低层管理员 execution 路由。

## 7. Registry v2 迁移与原子 finalize

`launch_registry.sqlite3` schema 升为 v2。新增 publication 表、`UNIQUE(project_id, run_id)` 与
`UNIQUE(project_id, idempotency_key)` 约束；对 v1 只
允许一次显式、事务性、可重复运行的 additive migration：保留全部 launch rows，创建新表，最后
更新 schema version。迁移中断时整体回滚；未知版本 fail closed。不得要求用户删除旧历史。

新增最小 API：

- `reserve_publication(project, run, key, fingerprint)`：`BEGIN IMMEDIATE`，返回唯一 publication；
- `record_publication_failure(...)`：CAS 写 recoverable_failed/blocked，不改 result flag；
- `finalize_publication(...)`：CAS on run + revision + current state，同一事务写 publication
  `available` 并把 launch row 更新为 `result_available=true/main_action=查看本次结果`。

任何 finalize 故障注入后均不得出现单边提交。

publication 状态机固定为 `publishing | available | recoverable_failed | blocked`，CAS 只允许：

- `(无记录) → publishing`；
- `publishing → available | recoverable_failed | blocked`；
- `recoverable_failed → publishing | blocked`；
- `blocked → publishing`，但只允许显式重试且门禁输入已经变化；
- `available` 为不可回退、不可覆盖的终态。

其余转移全部拒绝。`record_publication_failure` 只可写 `recoverable_failed` 或 `blocked`；
`finalize_publication` 只可从 `publishing`、`recoverable_failed` 或 `blocked` 原子进入 `available`。

## 8. Receipt 读取复用

R1/R7 有界新增公开只读 API：按 run/revision/work-unit 返回最终 capability attempt 与持久化 R6
receipt 的必要内部字段。receipt 分类必须复用 R7 harness runtime 当前的单一分类函数；该函数可
从私有 helper 提升为模块内正式 API，不复制第二套规则。

deterministic mandatory unit 在 synthetic 下只要求 R1 terminal 状态与 ledger/audit 完整；
`evidence_count=0` 允许为空，不伪造 artifact 或 R6 receipt。AI 与 deterministic 覆盖合并后必须
等于 mandatory denominator。

## 9. Result-entry 精确公开 DTO

`GET /runs/{public_run_token}/result-entry` 仅在 publication 为 `available` 时签发；否则返回稳定中文失败
“结果尚未整理完成”，且不得回退到同项目其他运行或旧结果。成功时只返回：

- `project_ref`（canonical project id）；
- `public_run_token`；
- `snapshot_token`（当次已冻结公开 snapshot option token）；
- `data_cutoff_text`；
- `site_options[] = {site_ref, site_label}`，其中 `site_ref` 来自冻结 coverage，`site_label` 由产品投影
  确定性生成为 `中心 {site_ref}`，不依赖合成行或临时 fixture 中不存在的 label；
- `result_context_token`（由服务端派生的 opaque navigation token）。

不返回 authority/S4/receipt digest、内部 run id 或底层路由。07C-4 只把
`result_context_token + optional site_ref` 交给结果读取代理；代理重取 R5 packet 并与 publication
内部 digest 比对。Patient Journey 的具体入口字段推迟到 07C-4，不在本切预造。

## 10. 增补验收与实施顺序

在 v0.1 §9 基础上增加：

1. 不同 key/同冻结身份返回同 publication；同 run/冻结身份异导致 fingerprint 异时 409；blocked 后
   门禁输入补齐但冻结身份不变时可重试并最终 available。
2. setup/runtime manifest work-unit 或 mandatory 不一致 blocked。
3. coverage 与 product packet sites 不一致 blocked；S4 member 越界 blocked。
4. result-entry 重取 packet identity/digest 不一致整页失败关闭。
5. v1→v2 迁移保留 launch 历史；中断回滚；未知版本失败关闭。
6. 单条 publication 异常不得击穿其他 run 的 history/progress。

实施顺序修订为：

0. R5-owned authority input assembler + S4→product packet member bridge；
1. registry v2、publication store/state/CAS 与双 manifest/receipt gate；
2. R5 bridge 调用、site/member closure 与原子 finalize；
3. progress/history/result-entry 产品路由与公开投影；
4. synthetic 故障矩阵、R5/R7/产品相邻回归、独立接受与证据清理。
