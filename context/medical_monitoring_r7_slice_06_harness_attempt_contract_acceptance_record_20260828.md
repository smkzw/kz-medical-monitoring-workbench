# R7 Slice-06 Harness 调用与恢复合同接受记录

日期：2026-08-28  
结论：`ACCEPT_R7_SLICE_06_HARNESS_ATTEMPT_RECOVERY_CONTRACT_V1_0`

## 接受对象

冻结合同：`context/medical_monitoring_r7_slice_06_harness_attempt_recovery_contract_20260828.md`  
SHA-256：`3c879889e30541b2556bc8c2643758029b52e7cc9876f9b27d7e0e5b73bbbc21`

## 关键决定

- 复用 R1 capability journal/controller；R7 不建立第二套 attempt/retry 账本。
- harness work unit 必须使用 AI_CANDIDATE manifest revision。
- preflight 失败保持零 assignment/attempt/ordinal/transport；去敏诊断走 domain-object audit。
- 默认 MTPLX medium；DeepSeek max 仅限用户显式冻结，禁止自动替换。
- R6 与 R1 两种档案身份分别校验并由 bridge 绑定，不互相冒充 digest。
- 最多两个 claimed-and-bound attempts，interrupted 计入上限；仍有额度的 failed/blocked AI 单元
  参与继续与 finished 判定。
- R6 `--no-session` 的新调用续作不声称同一会话；unsupported cancel 不冒充取消成功。
- 停止时不杀当前 OMP；双层身份仍有效时当前项可完成，之后不领取下一项。
- R6 receipt 必须确定性转换为满足 R1 父级 JSON-RPC classifier 的 envelope，不覆盖父级验证。

## 会商与边界

Pi/Gemini high 与 Grok Build medium 均按声明路由、同 session 完成，无 fallback。会商先后关闭阻塞
transport 租约、节点类型、预检状态、私有 journal、双身份、状态 envelope 与 retryable AI 单元
续作等缺口。8911/5174 保持停止；未调用真实模型、真实项目，未修改 R1/R6、前端或医学写作。

## 下一安全动作

只在 R7 实现 runner/profile-receipt bridge、in-flight lease renew、continuable AI 调度与最小产品
接线；先完成 fake catalog/transport 离线矩阵和独立实现审阅。离线接受前不得执行真实 smoke；
真实 smoke 也只使用 synthetic 最小 prompt，并按 MTPLX 与显式 DeepSeek 串行、禁止互相补位。
