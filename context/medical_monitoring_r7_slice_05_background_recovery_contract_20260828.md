# R7 Slice-05 后台执行与中断恢复合同

日期：2026-08-28  
状态：`FROZEN_R7_SLICE_05_BACKGROUND_RECOVERY_V0_2`  
冻结依据：两席独立会商、Codex 源码核对与本文件验收矩阵

## 1. 目标与停止线

在 Slice-04 已准备的 synthetic/offline manifest 上，让本地应用进程中的工作线程在用户离开
页面后继续执行，并在进程重建后依据 SQLite 显示“已中断，可继续”。completed/total/percent、
八状态、阶段与工作播报仍只来自 R1 manifest/work-unit ledger。

不调用模型/harness、不运行真实项目、不修改前端、R1/R6 或医学写作，不启动 8911/5174。
真实模型 retry/continuation 属于 Slice-06；本切不声称 exactly-once 或旧 owner 回调全面隔离。

## 2. 单一控制记录与状态机

R7 在现有 `monitoring_runtime.sqlite3` 增加 `r7_execution_control`，主键仅为 `run_id`；同一项目
runtime 中每个 Run 只有一个控制记录。只允许：manifest_revision、generation、state、owner_token、
lease_expires_at、cancel_requested、created_at、updated_at。严禁 completed/total/current ordinal。

状态固定为 `prepared → running → cancelling → interrupted → running → finished`。新 revision 仅可从
prepared/interrupted/finished 建立；running/cancelling 时不同范围 prepare 失败闭合，当前同范围重放
仍幂等。revision 变化重置 control，generation 递增且不得倒退。

## 3. 原子领取与租约

- `BEGIN IMMEDIATE` 对 run_id 原子领取；15 秒 lease、每 5 秒或每次调度前续租，测试注入时钟。
- 每次成功 start/resume/过期恢复均递增 generation。CAS 续租必须同时匹配 run_id、revision、
  generation、owner、running 和未过期 lease；影响 0 行即停止，不再领取新单元。
- 进程内 registry 只保存线程句柄；构造、import、GET、prepare 均不得启动线程。
- 过期 lease 在重建时标为 interrupted、清 owner；不自动 resume。

R1 普通 work-unit complete 不认识 owner。故本切诚实保证：同进程旧 generation 在完成前再次
核对 CAS；跨连接迟到的同 key/同指纹完成由 R1 幂等吸收，冲突指纹由 R1 拒绝。不得声称租约能
拒绝所有已发出的旧回调。Slice-06 的真实模型回调必须走 capability attempt owner/lease。

## 4. 调度、停止与继续

- 稳定 key：`r7-background:{run_id}:{revision}:{work_unit_id}`，不含 generation，以支持 action 后、
  complete 前崩溃的 at-least-once 同键重放。
- 只调度依赖均为 passed/reused/skipped/not_applicable 的 pending/running 单元。
- 若 failed/blocked 上游使剩余 pending 永不可运行，worker 释放 owner 并进入 finished；不得自旋。
  这些 pending 不计完成，运行摘要显示部分工作未完成，resume 返回“没有可继续的工作”。
- cancel 先持久化 cancelling/cancel_requested；当前 synthetic 单元完成后不再领取下一项，转
  interrupted。产品中文统一为“停止/继续”，不使用“取消任务/删除”。
- resume 仅对 interrupted 且存在可运行 pending/running 单元生效；重复 start/resume/cancel 幂等。

## 5. 产品 API 与一致投影

在项目级 R7 前缀、catch-all 前增加 `POST .../execution/start|resume|cancel`，均需
`ADMINISTER_RUNTIME`；GET progress 保持 `READ_AI_RUN`。

GET 使用 R1 `audience_snapshot` 的 deferred read transaction，并在同一 SQLite 读快照取得 control。
R1 `headline` 与计数不得被 control 覆盖；另增 `run_status_text` 与中文 `available_actions`。公开
allowlist/泄漏扫描禁止 owner、lease、generation、thread、pid、token、sqlite、内部状态码。

稳定错误码至少覆盖：not prepared、already running、not interrupted、nothing to resume、not
running、prepare while running、runtime integrity failed；message 使用原生中文。

## 6. 恢复与完整性

start/resume 前核对 R1 audit/artifact/ledger 以及 control 行形状、run/revision、state-owner-lease
组合和 generation 单调性。异常失败闭合，不启动 worker、不返回局部进度。R1 `Store.recover()`
不是 work-unit 恢复器；checkpoint 由 ledger + control 构成，本切不另写第二套 checkpoint 进度。
孤儿 artifact 只报告，不自动删除。

## 7. 验收矩阵

1. import/router/GET/prepare 不启动线程；8911/5174 停止。
2. 未准备、错项目/Run/revision、篡改 audit/control 均零后台动作并失败闭合。
3. start 后无客户端轮询仍完成；新连接/重建从 SQLite 得到相同计数。
4. 两个 Store 连接并发 start，仅一个 action/单元；另一方幂等或 already-running。
5. action 后 complete 前注入故障；lease 过期后 resume 同 key，begin/complete 不重复成两套历史。
6. 旧 generation 不再领取；同指纹迟到完成被吸收，冲突指纹拒绝，不作 owner 拒绝的虚假断言。
7. stop 后不再新增 begin，pending 不计完成，重建仍为 interrupted；resume 同 revision 继续。
8. 未满足依赖不调度；失败上游使下游 pending 时 worker 结束且 resume 拒绝；运行中不同范围
   prepare 拒绝；允许 revision 变化后旧 revision 回调由 R1 StaleCallbackError 阻断。
9. 八状态、阶段计数、headline 与中文播报仍由 R1 投影；control 仅提供 overlay。
10. 全量响应泄漏扫描，无 owner/lease/generation/thread/pid/token/sqlite/provider/model。
11. focused、R7、R1、R6 与产品相邻回归通过；医学写作聚合哈希不变。

## 8. 接受边界

合同通过后实施只允许 R7 后台控制模块、现有 runtime adapter/product router 的最小接线、聚焦
测试、README/receipt。不得把 R1 `BackgroundProgressFacade` 原样复用为调度器，因为它对失败
依赖会持续重试；可复用其 `audience_snapshot` 与同键 at-least-once 原理。
