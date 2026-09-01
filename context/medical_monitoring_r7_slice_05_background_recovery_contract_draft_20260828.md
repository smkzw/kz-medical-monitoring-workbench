# R7 Slice-05 后台执行与中断恢复合同草案

日期：2026-08-28  
状态：`DRAFT_R7_SLICE_05_BACKGROUND_RECOVERY_V0_1_FOR_CONFERENCE`

## 1. 目标与停止线

在 Slice-04 已准备的 synthetic/offline manifest 上，让本地应用进程中的工作线程在用户离开
进度页后继续执行，并在进程重建后从 SQLite 权威账本恢复未完成工作。进度数字仍只来自 R1
manifest/work-unit ledger；运行控制状态不得成为第二套 completed/total。

本切不调用 MTPLX/DeepSeek 或任何真实 harness，不运行真实项目，不修改前端、R1/R6 源码或
医学写作，不启动 8911/5174。真实模型失败后的 capability retry/continuation 属于 Slice-06；
本切不得伪造“已重试成功”。

## 2. 运行所有权

- R7 在同一 `monitoring_runtime.sqlite3` 增加独立的 `r7_execution_control` 表，仅保存操作状态：
  run/revision、generation、state、owner token、lease expiry、cancel request、updated_at。
- `BEGIN IMMEDIATE` 原子领取；同一 canonical project/run/revision 任一时刻最多一个有效 owner。
- worker 定期续租；租约到期后旧 owner 回调必须被拒绝。恢复过程先把过期 owner 标为
  `interrupted`，不得把运行中冒充完成。
- 进程内 registry 只保存活线程句柄，重建后必须以 SQLite 为准；不得持久化页面轮询状态。

## 3. 产品入口与中文语义

在项目级 R7 前缀、catch-all 前增加：

- `POST /runs/{run_id}/execution/start`：仅 prepared 且尚未运行时原子启动。
- `POST /runs/{run_id}/execution/resume`：仅 interrupted 且仍有 pending/running 单元时继续。
- `POST /runs/{run_id}/execution/cancel`：协作式请求停止；当前单元完成/安全中断后不再领取下一项。
- `GET /runs/{run_id}/progress` 继续返回权威计数，并增加用户可理解的运行摘要与可用操作；不返回
  owner、lease、generation、线程、数据库或内部状态码。

重复 start/resume/cancel 在同一有效状态下必须幂等。错误返回稳定中文 `{code,message}`。

## 4. 执行语义

- 只执行当前 manifest revision，按 ordinal 与 depends_on 选择可运行单元；依赖未满足不得越过。
- synthetic action 必须使用稳定的 `run/revision/work_unit` 幂等键。进程在 action 后、完成回调前
  崩溃时允许 at-least-once 重放；action 必须可幂等，合同不声称 exactly-once。
- 恢复 running 单元时使用原稳定键；R1 begin/complete 重放或冲突规则保持权威。
- 用户取消不是“完成”：pending 保持 pending；进度 headline 明确“已停止，可继续”。
- failed/blocked terminal work unit 不在本切通过改写账本重开。产品 `retry` 入口暂不开放；
  Slice-06 必须基于 R1 capability attempt continuation 冻结真实 retry 语义后再挂载。
- 所有单元 terminal 后释放 owner；存在 failed/blocked 时显示“本次监查已结束，部分工作未完成”。

## 5. 一致读取与恢复

- 已准备进度读取改用 R1 `audience_snapshot(db_path, artifact_dir, run_id)` 的 deferred read
  transaction，确保一次响应不跨两个提交快照。
- 启动协调器前运行 audit/integrity 检查；损坏时 fail closed，不启动 worker、不返回局部进度。
- 应用重建只恢复过期租约和可继续状态，不自动删除孤儿 artifact；清理由后续恢复/备份纵切处理。

## 6. 验收矩阵

1. import/router/GET 不启动线程；8911/5174 停止。
2. 未准备、错误项目/Run/revision、篡改账本均零后台动作并失败闭合。
3. start 后用户不轮询也能完成；刷新/重建只从 SQLite 得到相同计数。
4. 并发两个 coordinator 仅一个 action 调用；另一方得到幂等或 already-running。
5. action 后、complete 前故障注入，租约到期恢复后同键重放，最终只有一套权威 begin/complete。
6. 旧 owner/过期 lease 回调被拒绝且不覆盖新历史。
7. cancel 后不再领取新单元，pending 不计完成；resume 从同 revision 继续。
8. 依赖未满足不调度；当前 revision 改变时旧 worker 停止且回调被拒绝。
9. 八状态、阶段计数和结构化中文播报仍与 R1 权威投影一致。
10. 产品响应全量泄漏扫描；不出现 owner/lease/thread/manifest/provider/model/日志标签。
11. focused、R7、R1、R6、产品相邻回归通过；医学写作聚合哈希不变。

## 7. 待会商问题

1. `r7_execution_control` 放在现有 runtime SQLite 是否能在不修改 R1 的前提下保持清晰所有权。
2. 取消后允许 resume 是否应在中文上表述为“停止/继续”，避免用户把 cancel 理解为永久删除。
3. 进程重启后应自动恢复，还是先显示“已中断，可继续”；草案推荐后者以避免未知外部 action
   的 at-least-once 重放，待 Slice-06 根据 adapter continuation 能力再考虑自动恢复。
