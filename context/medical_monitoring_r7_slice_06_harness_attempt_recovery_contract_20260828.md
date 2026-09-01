# R7 Slice-06 Harness 调用、有限重试与恢复合同

日期：2026-08-28  
状态：`FROZEN_R7_SLICE_06_HARNESS_ATTEMPT_RECOVERY_V1_0`

## 1. 目标与停止线

把 R6 已冻结的模型档案与 adapter 以最薄接缝接入 R7 当前 Run/work-unit 生命周期，使每次模型
调用在发出前可追溯、完成后可验证、失败后只按冻结规则有限续作，并且不会因恢复、停止或配置
变化而悄悄更换模型身份。

本切只使用 synthetic prompt；不运行真实项目，不修改前端、R1、R6 或医学写作，不启动
8911/5174，不设计或测试系统安全功能。离线故障注入全部通过且独立审阅接受前，不调用真实模型。

## 2. 权威状态、节点类型与双层所有权

- capability 调用唯一事实源为 R1 `capability_attempt_journal` 及
  `work_unit_capability_attempts`；R7 不新增 attempt/progress/retry 表。
- R7 control 的 run/revision/generation/owner/lease 决定 worker 是否仍可领取或推进工作；R1
  attempt 的 owner/lease 决定该次 transport 结果是否仍可写回。
- 接入 harness 的 manifest node 必须是 R1 `AI_CANDIDATE`；不得对 Slice-04 的
  `DETERMINISTIC_SERVICE` 节点调用 capability controller，也不得用普通 `begin_work_unit` /
  `complete_work_unit` 完成 AI 单元。既有 manifest 不原地改写，需生成新 revision。
- dispatch 前和 R1 terminal journal 写入前必须同时核对两层 run/revision/owner/lease 与冻结身份。
  任一失效即先阻断 R1 terminal persist；旧输出仅作为已拒绝技术证据，不可成为候选医学结果或
  完成进度。
- 一个 work unit 同时最多有一个当前 `declared` 或 `running` attempt。`interrupted` 与 terminal
  attempt 作为不可变历史保留；新 attempt 只能以最新绑定 attempt 为 `continued_from`。
- R7 run lease 在阻塞 transport 期间由独立 `renew_inflight_lease` loop 每 5 秒续租。它与
  Slice-05 仅允许 running/未停止时领取新工作的 `heartbeat` 分开：普通运行和“正在停止”状态
  均可仅为当前 in-flight 单元续租；“正在停止”绝不允许领取新单元。R1 attempt lease 固定为
  `max(profile.timeout_seconds + 30 秒, 60 秒)`，不伪造 R1 不存在的续租接口。

## 3. 档案、预检与调用顺序

1. 从 R7 immutable Run binding 还原 frozen R6 profile，并核对 R6 execution-profile digest、
   adapter id/version、selector 与 effort。
2. 默认 profile 固定为
   `mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality:medium`；只有用户已显式冻结 DeepSeek
   profile 时才调用 `deepseek/DeepSeek V4 flash:max`。
3. 禁止 auto fallback、provider/model/effort 替换及“默认失败后改用 DeepSeek”。
4. R6 profile 与 R1 `ExecutionProfile` 是两种不同 schema，两个 digest 不得互相冒充。R7 必须
   生成并冻结一个 bridge domain object，同时内容寻址记录 R6 execution-profile digest 与 R1
   profile fingerprint；dispatch 和 terminal 前分别核对二者及映射字段。
5. preflight 必须在 controller assignment、attempt declare/claim/bind 与 transport 之前完成。
   预检失败保持零 assignment、零 attempt、零 ordinal、零 R1 work-unit 变化、零 transport；通过
   R1 通用 domain object/audit seam 保存去敏后的 R7 preflight diagnosis，control 转 interrupted。
6. 必须把同一个已冻结 `PreflightResult` 传入 R6 invoke，禁止 claim 后再次读取 catalog。
7. 预检通过后依次：R7 claim-permitted → controller register → R1 declare → 原子 claim → controller
   bind → transport（并行续 R7 lease）→ R7 commit-permitted → R1 terminal journal → 封存/登记
   receipt 与候选结果 → complete capability work unit。不得先调用再补记 attempt。
8. prompt、expected coverage、版本、profile、manifest revision、input hash 和重试上限均在首次
   attempt 前冻结；续作不得改变。

## 4. 失败分类与有限续作

每个 work unit 最多两个已 claim 且已绑定的 attempts：首次调用加一次续作。上限是 Run manifest
的冻结策略，由 R7 在 controller execute/resume 前根据 authoritative binding ordinal 强制执行；
R1 本身不提供此上限。进程重启、UI 连点或失败类别变化均不得重置额度。

可续作状态仅限 R1 已允许的 `timeout`、`partial`、`truncated`、`interrupted`：

- timeout/transport interruption：若仍有额度，可建立一个新 attempt；保留原始失败历史。
- partial/truncated：仅当已封存输出可验证且 coverage 未完成时可建立一个新 attempt；不把部分
  结果晋升为 work-unit success。
- interrupted：过期 lease 或进程中断后，旧 attempt 先原子标为 interrupted；若仍有额度，再建立
  一个新 attempt。已 claim/bind 的 interrupted attempt 计入两次上限，避免进程反复崩溃形成
  无界重复调用。

以下不得自动续作：profile/identity/catalog/credential/preflight 错误、输入或 revision 漂移、完整
输出的结构/证据校验失败、明确 failed/cancelled、重试上限耗尽。preflight 失败因零 attempt 而让
work unit 保持 pending、control 转 interrupted；其余状态由 R1 controller 映射为 failed/blocked。
任一场景均不得自旋。

Slice-06 仅使用 `CapabilityWorkUnitController` 的 register/execute/resume/reconcile 公开行为及
`CapabilityRuntime` 内部拥有的 journal seam。R7 禁止直接调用 Store 的
`_declare/_claim/_interrupt/_complete_capability_attempt` 或 `_runtime_attempt_journal`。R1 Store
虽允许 failed/cancelled 绑定续作，Slice-06 仍只采用 controller 的
timeout/partial/truncated/interrupted allowlist。

R7 必须定义独立的 `continuable_ai_unit` 判定：latest bound attempt 的状态属于
timeout/partial/truncated/interrupted，且 binding ordinal 小于 2。该判定参与 worker 调度、
`resume_execution` 的“是否可继续”以及 quiescent/finished 判定：

- control 仍为 running 时，第一次 timeout/partial/truncated/interrupted 后可立即以 controller
  resume 执行第二次；
- control 为 cancelling 时，即使仍有额度也不得对当前单元发起 linked retry；
- 重建或停止后，failed/blocked 的 AI work unit 只要满足该判定，就仍属于用户可继续范围；
- 只要仍有 `continuable_ai_unit`，不得把 Run 标为 finished 或返回 nothing-to-resume。

## 5. “续作链”与“同一模型会话”必须分开

R1 `continued_from` 只表示同一冻结输入/档案/work-unit 的新 attempt 续作链。当前 R6
`OmpPrintAdapter` 明确使用 `--no-session`，且 continue/resume/cancel 均 unsupported，因此：

- 本 adapter 的第二次 attempt 必须标为“新调用续作”，不得声称复用了同一模型 session。
- 不得生成虚构 session id 或把 logical chain 写成 same-session evidence。
- 未来只有 adapter 返回并可验证稳定 session handle、且其 capability manifest 明确支持
  continuation 时，才允许在同一 session 继续；同一 session 中因路由策略更新而切换模型也必须
  是用户明确行为，不能在当前 Run 内静默发生。

## 6. 停止、进程中断与迟到结果

- 用户停止首先把 R7 control 置为 cancelling，立即停止领取新 work unit。
- 当前 OMP print adapter 不支持传输层 cancel。系统只能显示“正在停止，当前分析可能完成”，
  不得显示“模型调用已取消”。本切不主动 SIGTERM/SIGKILL 当前 OMP 子进程；等待其返回或按
  profile timeout 结束，以免把本地终止冒充远端取消。
- 当前 attempt 返回后，若 run revision/generation/owner/lease 与 attempt owner/lease 均仍有效，
  R7 control 为 running 或 cancelling 都可接受当前 terminal 结果；cancelling 只允许这一项完成，
  随后停止且不得领取下一项。任一身份失效时，R7 runtime wrapper 必须在 R1 terminal journal
  之前抛出并触发 interrupted 路径，拒绝候选结果和完成进度。
- 进程重建先调用 R1 `recover_expired_capability_attempts(run_id=...)`，再恢复 R7 control；只做
  journal/lease reconciliation，不自动调用 `controller.reconcile` 触发 transport。用户选择“继续”
  后：已 interrupted 的 attempt 按剩余额度新建续作；崩溃在 declare 与 claim 之间的同一
  declared attempt 可在明确继续动作后按原 assignment/id claim，不新增 ordinal；若崩溃发生在
  controller register 后、R1 declare 前，则明确继续动作以同一 assignment/id 重新进入首次
  execute。二者均不得由重建过程自动触发；额度耗尽则“没有可继续的分析”。
- 本切保证 durable at-most-one accepted terminal result per attempt，不声称 provider 侧
  exactly-once，也不声称 unsupported cancel 已生效。

## 7. 产品公开语义

公开进度继续只来自 R1 audience projection，R7 control 仅覆盖“正在运行/正在停止/已中断/已结束”
和可用操作。公开输出不得包含 provider、model、selector、attempt、session、owner、lease、
generation、invocation、profile digest、argv、raw output、stderr、hash 或英文内部状态。

Slice-06 仅在 capability 调用期间以更准确文案覆盖 Slice-05 的宽泛运行摘要；R1 headline、计数
和 work-unit detail 不被覆盖。建议中文句式：

- “正在分析：正在核查不良事件与既往病史。”
- “正在停止，当前分析可能完成；系统不会开始下一项工作。”
- “分析已中断，可继续本次监查。”
- “上次分析未完成，正在重新分析同一项工作。”
- “模型连接或输出不完整，本项分析未完成。”
- “模型配置未通过核对，请检查模型设置后重试。”
- “本项分析未完成，已达到本次重试上限。”

这些是看板状态说明，不建立待办、审批或“人工复核未完成”流程。

## 8. 实现边界

允许新增一个 R7 harness work-unit runner、R6→R1 profile/receipt bridge、去敏 preflight diagnosis
domain object 及其最小 background/product 接线、聚焦测试、README、receipt 和阶段记录。必须
复用 R1 controller/journal 与 R6 profile/adapter；R1/R6 字节保持不变。

R7 runner 以 R1 `CapabilityRuntime` 的薄包装承接 R6 adapter：`_execute` 调用 R6 invoke；
`_complete_durable_attempt` 在调用父实现前执行 R7 commit-permitted。R6 receipt 不能直接作为
R1 classify response，因为 R1 要求 JSON-RPC 2.0、attempt id、完整 execution identity 与逐项
coverage。bridge 必须同时保存两层证据：

1. `TransportExecution.raw_output` 保留去路径化后的真实 R6 receipt；
2. `TransportExecution.stdout` 是由该 receipt 确定性构造的 R1 JSON-RPC envelope，id 等于
   attempt id，execution_identity 等于冻结 R1 profile，produced coverage 只可来自 R6 明确产出的
   expected-unit 映射；
3. R6 `timed_out` 仅映射 `timed_out=True`；R6 `partial`/`truncated` 通过 JSON-RPC
   `result.status` 映射，不能把非字符上限的 truncated 冒充 R1 `output_truncated`；R6 `failed` /
   not-evaluable 通过 JSON-RPC failed 映射，永不设置 cancelled；
4. R6 `complete` 且 `analysis_complete=true`、parse/coverage/profile/adapter/input 全部一致时，
   JSON-RPC status 才为 R1 `complete`；其他依次为 partial/truncated/timeout/failed。

不得覆盖 R1 `_invoke_new` 或 `_normalize_transport_result` 来绕过既有证据验证；测试必须证明上述
envelope 经父级分类后得到同一状态。R6 coverage、parse、profile、adapter 或 input 任一不完整均
不得映射为 complete。
不得把模型身份写入医学对象、Patient Journey、风险、Query 或公开进度。

## 9. 验收矩阵

1. import、GET、prepare 不做 catalog/preflight/model 调用；8911/5174 停止。
2. fake catalog/transport 下，默认 MTPLX medium 与显式 DeepSeek max 的 exact selector/effort/
   profile digest 均与 Run binding 一致，无 fallback。
3. preflight 失败时零 assignment/attempt/work-unit begin/transport，work unit 保持 pending，control
   为 interrupted；去敏 diagnosis 可审计且公开错误为稳定中文。
4. dispatch 前已 durable declare/claim/bind；调用后 raw receipt、terminal attempt 和 work-unit
   completion 顺序可审计。
5. 两个进程/连接竞争同 work unit，仅一个有效 attempt dispatch；另一方不产生重复调用。
6. 120 秒 fake blocking transport 期间 R7 lease 持续有效；running/cancelling 中同 owner 的
   `renew_inflight_lease` 可续租，Slice-05 `heartbeat` 仍只负责 running/未停止时领取；cancelling
   不得领取下一项；run/attempt owner、lease、revision 或 profile 任一漂移时
   迟到 terminal 在 R1 journal 前被拒绝。
7. 每个 work unit 最多两个已 claim/bind attempts；第三次及非法状态续作失败闭合；第二次中断也
   不重置额度。failed/cancelled 不走自动续作。
8. 续作保持 input/version/profile/revision/coverage；logical `continued_from` 不出现虚构 session。
9. stop during active call 不终止当前 OMP 调用、不领取下一项；当前结果在双层身份仍有效时可
   诚实落账，否则拒绝；unsupported cancel 的中文和 receipt 均不冒充取消成功。
10. complete 且 coverage 完整才使 work unit passed；partial/truncated/failed/cancelled 不晋升。
11. 进程重建不自动 dispatch；expired running 先恢复 interrupted；declared 只在用户明确继续后
    才以原 id claim；register 后未 declare 的 assignment 同样只在明确继续后重入；额度不重置。
12. 响应泄漏扫描覆盖 provider/model/selector/attempt/session/owner/lease/generation/invocation/
    profile digest/argv/raw/stderr/hash。
13. focused、R7、R1、R6 功能与产品相邻回归通过；医学写作非缓存边界不变。
14. 离线门禁和独立审阅通过后，串行执行两个 synthetic 最小真实 smoke；分别保留真实 profile、
    catalog、argv、时长、终态与 receipt。任一路线失败均原样记录，不得用另一模型补位。
15. R6 complete/partial/truncated/timed_out/failed receipts 经 bridge 后分别被 R1 父级 classifier
    识别为 complete/partial/truncated/timeout/failed；不得用覆盖父级 parser 的方式制造通过。
16. attempt-1 timeout/partial/truncated/interrupted 在 running 时触发且仅触发一次 linked retry；
    重建后 failed/blocked AI 单元仍可继续；cancelling 时不触发 linked retry；仍有额度时 Run 不得
    finished 或误报 nothing-to-resume。

## 10. 会商结论

1. 保持 preflight 零 attempt；诊断走 R7 domain object/audit，不制造 declared 孤儿。
2. 上限为两个已 claim/bind attempts；足以阻断无界循环，第二次中断也不重置额度。
3. 明确 no-session、unsupported cancel；停止不杀当前 OMP，当前项可能完成但不再领取下一项。
4. 必须走 `CapabilityWorkUnitController`；R7 只以 `CapabilityRuntime` 薄包装插入 R7 terminal CAS，
   不直接调用 R1 private journal。
