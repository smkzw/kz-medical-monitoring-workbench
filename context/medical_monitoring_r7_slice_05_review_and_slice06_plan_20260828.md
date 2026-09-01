# R7 Slice-05 复盘与 Slice-06 阶段前计划

日期：2026-08-28  
状态：`R7_SLICE_06_PHASE_BEFORE_REVIEW`

## 1. Slice-05 已证明什么

Slice-05 已把产品运行入口推进到 synthetic/offline 的后台执行与恢复：单 Run 控制记录、原子
领取、generation/lease、停止/继续、过期重建、依赖调度及一致中文进度投影均有确定性测试和
独立会商证据。它证明页面离开后本地线程可继续，进程重建后可从 SQLite 呈现“已中断，可继续”。

该结论没有证明真实模型调用、模型调用中的进程取消、同一模型会话续写、真实项目或前端体验。
R6 的 harness adapter 接入已受限接受，但尚未进入 R7 Run/work-unit 生命周期。

## 2. 从用户视角看当前阻断

资深医学监察员真正关心的不是 provider、attempt 或 lease，而是：点击开始后系统确实在分析；
模型暂时失败时不会重复生成相互矛盾的内容；停止后不会暗中继续领取新工作；恢复时不会悄悄
换模型；页面只用中文说明“正在分析、正在停止、已中断、可继续、分析失败”。

因此 Slice-06 的目标不是增加模型设置页面，而是建立模型调用的可信运行内核。模型内部身份和
原始错误保留在审计证据中，不进入风险、Patient Journey 或公开进度对象。

## 3. 现有基座复用结论

- R1 已有 `capability_attempt_journal`、`work_unit_capability_attempts`、owner/lease、不可变
  request/profile/input/revision 身份、terminal envelope、续作链和迟到回调阻断。不得在 R7
  再建第二套 attempt 表。
- R7 Slice-05 的 run-level generation/owner 负责“是否继续领取工作”；R1 attempt owner/lease
  负责“一次 capability 调用是否仍可写回”。两层必须同时有效。
- R6 `OmpPrintAdapter` 使用 `--no-session`，且 `continue_session`、`resume_session`、`cancel`
  均明确返回 unsupported。R1 的 `continued_from` 是可审计的新 attempt 续作链，不等于传输层
  同 session 续写。
- 默认档案必须仍为
  `mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality:medium`；DeepSeek 仅在用户显式选择
  `deepseek/DeepSeek V4 flash:max` 时使用，禁止自动替换身份。

## 4. Slice-06 步骤计划

1. 冻结 capability-attempt/有限重试/恢复合同，并独立会商挑战。
2. 在 R7 新增最薄的 harness work-unit runner，复用 R1 controller/journal 与 R6 profile/adapter；
   R1/R6 保持只读。
3. 先用 fake transport/canned catalog 完成离线故障注入和确定性验证，不启动产品服务。
4. 关闭 owner/lease 双层校验、有限重试、停止中的真实语义、迟到回调、无自动 fallback 和中文
   公开投影缺口。
5. 完成独立实现审阅后，仅对合成最小 prompt 做 MTPLX 与显式 DeepSeek 的真实 adapter smoke；
   真实调用失败也必须留下诚实 receipt，不能用另一模型补位。
6. 复跑 R7、R1、R6 功能与产品相邻回归，核对 8911/5174 停止及医学写作边界。
7. 完成 Slice-06 阶段后复盘，再进入 Slice-07 用户界面；届时才用 ego(lite) 验收真实进度、
   后台离页、恢复入口和中文体验。

## 5. 本阶段停止线

不运行五个真实项目，不启动 8911/5174，不修改前端、R1、R6 或医学写作子系统，不设计或测试
系统安全功能。合同冻结阶段不调用任何模型。真实 smoke 只能在实现、离线门禁和独立审阅均通过
后，以合成且不含临床资料的最小输入串行执行。
