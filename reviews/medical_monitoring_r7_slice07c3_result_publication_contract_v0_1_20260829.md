# R7 Slice-07C-3 结果发布与结果入口合同 v0.1

日期：2026-08-29  
状态：`R7_SLICE_07C3_RESULT_PUBLICATION_READY_FOR_REVIEW`

本合同只细化已冻结 Slice-07C v0.2 §16–20。冲突时以 v0.2 为上位权威。

## 1. 目标与边界

本切仅实现 synthetic/offline、服务端所有的结果发布事实面：后台运行完成后，逐项核对 R6
receipt、冻结运行身份和 R5 权威投影，原子形成一个可恢复、可审计的 `ResultPublication`。
只有发布状态为 `available` 时，运行历史和进度才可显示“查看本次结果”。

不实现 07C-4 中文向导/结果页/Patient Journey 前端，不启动服务，不调用真实模型或真实项目，
不修改医学写作，不扩展安全设计或测试。

## 2. 唯一身份与持久化

`ResultPublication` 与 launch registry 共用项目级 `launch_registry.sqlite3`，避免跨数据库先后
写入导致“已发布但入口未开放”或“入口开放但发布不存在”。同一事务内写 publication 终态并
更新 launch row 的 `result_available/main_action`。

每个 publication 不可变绑定：

- project id、内部 run id、public run token、publication revision；
- mode、execution basis、current snapshot ref/token、cutoff；
- manifest revision/digest 与 mandatory denominator；
- 排序去重后的 site coverage；
- 排序后的 R6 receipt identities 与 receipt-set digest；
- R5 product authority packet identity/digest；
- 风险检查层 S4 authority packet identities/digests；
- publication fingerprint、state、created/updated 时间。

公开响应不得返回内部 run id、数据库路径、provider/model/profile/adapter、原始 receipt、hash 字段名
或凭据；hash 只在内部审计面存在。

## 3. 发布状态与权限

状态固定为 `publishing | available | recoverable_failed | blocked`；无记录时 progress 投影为
`not_started`。只有运行管理员可发起/恢复发布；医学监察员可查看 progress、history 和已开放
结果入口，不获得底层发布控制。

- `recoverable_failed`：临时 I/O/组装中断，可由同一 publication 身份重试；
- `blocked`：运行未完成、mandatory receipt 缺失、receipt 身份/解析/覆盖漂移、R5 权威身份不一致
  或站点覆盖无法闭合；修复上游事实前不得重复把同一内容标为可用；
- `available`：不可回退、不可覆盖；同内容重放返回同一 revision，不同内容 409。

## 4. 唯一发布入口与幂等

产品入口建议为 `POST /runs/{public_run_token}/publication`，请求体只含 `idempotency_key`。
project/public token 解析、运行身份、快照、cutoff、receipt set、R5 packet 与 site coverage 均由
服务端读取，客户端不得提交或替换。

发布先在同一 registry 事务中 reserve publication revision 与规范运行指纹，再在事务外读取并
核对 runtime/authority，最后以 revision + state 的 CAS 事务写入终态。浏览器超时后重放同 key；
同 key/同冻结输入返回同一 publication，同 key/不同冻结输入返回 409。进程在 reserve 后中断，
同 key 继续同一 revision；不得新建第二条 publication。

## 5. R6 receipt 门禁

发布器只读取当前 manifest revision 对应的 mandatory work-unit 与其最终 capability attempt：

- 每项 receipt 的 invocation/profile/adapter/input/run scope 与冻结绑定一致；
- `state=complete`、`parse_state=parsed`、`analysis_complete=true`；
- expected/produced coverage 完全一致，missing 为空；
- fallback、unsupported operation、stale attempt、旧 manifest revision 均阻断；
- receipt set 覆盖全部 mandatory AI work-unit，且无未知 work-unit、重复身份或多终态。

非 AI 的 deterministic mandatory work-unit 以 R1 terminal ledger + artifact integrity 为门禁，不伪造
R6 receipt；两类覆盖合并后必须等于 manifest mandatory denominator。

## 6. R5 权威复用边界（会商重点）

R7 不建立第二套医学聚合算法：

1. 风险检查/Query/Journey/history 的单风险权威必须调用既有
   `mm_r5.s4_projection.build_s4_authority_packet(runtime_input)` 并通过既有 S4 validator；
2. 项目/中心/受试者/Journey 产品读取继续消费既有
   `services.api.app.medical_monitoring_r5_product_adapter.R5AuthorityPacket`；R7 只接受注入的 typed
   `R5AuthorityProvider` 返回值，并核对 project/run/snapshot/cutoff/site coverage 与 authority hash；
3. publication 绑定 product packet digest 和其引用的 S4 packet digest 集合；不得由 R7 从模型文本、
   receipt marker 或前端 fixture 平行组装新的医学事实。

若现有 S4 builder 与产品 `R5AuthorityPacket` 之间没有已接受的确定性聚合桥，本切必须 fail closed，
先补一个只负责 typed identity/member join 的 R5-owned bridge；不得在 R7 内复制 builder。

## 7. Progress、history 与 result-entry

R7 progress 有界新增：

- `publication_state`；
- `result_available`（仅 available 为 true）；
- 原生中文 `publication_status_text`；
- 仅管理员可见的“整理结果/重新整理”动作。

运行完成但未发布时显示“分析已结束，结果整理未完成”，主动作仍为“查看本次进度”。
发布 available 后历史与 progress 同时显示“查看本次结果”。

`GET /runs/{public_run_token}/result-entry` 只返回公开四元组 project/run/snapshot/cutoff、site coverage
和前端已有项目看板/中心看板/Patient Journey 入口所需的公开标识。中心不在 coverage 中返回
“该中心不在本次监查范围”；任何 project/run/snapshot/cutoff/authority digest 不一致整页失败关闭，
不得回退到上一运行或空白旧看板。

## 8. 失败原子性

- publishing/recoverable_failed/blocked 均保持 `result_available=false`；
- R5 构建或验证失败不写半成品 packet，不改变已接受 publication；
- publication 可用与 launch result flag 在同一 SQLite 事务提交；
- 进程在最终事务前中断只留下可恢复 publishing；最终事务后重放返回 available；
- 已 available 的 publication 不得被后续规则版本、快照或运行状态回写。

## 9. 最小验收矩阵

1. completed + no publication 仍不可打开；running/interrupted/failed 发起发布均 blocked。
2. mandatory AI receipt 齐全可发布；缺失、partial、unparsed、coverage gap、身份漂移、fallback 阻断。
3. deterministic mandatory unit 与 AI receipt 合并后分母守恒。
4. 同 key 同输入重放、同 key 异输入 409、reserve 后中断同 revision 恢复。
5. 可恢复构建失败保持同 publication；修复后同身份变 available。
6. blocked 与 recoverable_failed 不混用；available 不可回退或覆盖。
7. publication 与 result_available 同事务；故障注入证明不存在一边提交。
8. R5 S4 builder/validator 确被调用；并行 builder、fixture fallback、candidate marker 冒充事实均失败。
9. project/run/snapshot/cutoff/site coverage 与 product packet、S4 packets、result-entry 全链一致。
10. 中心越界中文失败；公开 history/progress/result-entry 无内部身份、hash/provider/model/database 字段。
11. normal/-O/-OO 与多个 hash seed 下 publication fingerprint、site/order 和公开 JSON 稳定。
12. R7、产品路由、必要 R5 S4 相邻测试、医学写作聚合哈希和 8911/5174 停止均通过。

## 10. 实施拆分

合同接受后按依赖顺序实现，不并行消费未冻结接口：

1. publication store/state/CAS 与 receipt gate；
2. R5 S4/product packet bridge、原子 finalize；
3. progress/history/result-entry 产品路由与公开投影；
4. synthetic 故障矩阵、相邻回归、独立接受与证据清理。
