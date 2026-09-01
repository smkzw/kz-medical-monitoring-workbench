# P10 LOOP 3.16 v6 Visit Canary 无损暂停

Date: 2026-08-01

## 当前结论

- v6 单主题真实 canary 已失败关闭，零候选持久化。
- v6 不得重试或复用；RUX protocol gate 为 **NO-GO**。
- MY009 与三个真实项目继续阻断。
- 8911 与 5174 必须保持停止。
- 未作任何候选接受、拒绝、采用、确认或激活决定。

## 已完成

- 创建并验证 21 个运行库的一致备份；18 个非空库 integrity OK，3 个空库
  字节保留。
- 唯一启动 8911，证明 v4/v5 历史和 8 个 proposed v4 候选保持。
- 恰好一次 v6 `visit_window_and_order` POST：
  `monai_93160e1e698569730d331fa50f6e`。
- 同一 attempt 仅一次受控 repair：
  `monattempt_a4d6ee94c29040fc97fb740963f2fce6`。
- 一次 10 分钟加一次 20 分钟硬等待；无固定间隔轮询、无重复 POST、无 retry。
- 捕获 failed / `invalid_ai_output` / 0 candidate 后立即停止 8911。
- 复用既有 Luna 会话完成只读独立审阅。
- Codex 回归：监查 254 passed；医学写作相邻 200 passed。

## 已确认缺陷

1. provider repaired 输出仍混合访视外 IP 给药、退出、安全随访、AE/CM 收集
   或多个 visit action family。
2. 服务端 medication-action gate 漏检首次给药/首次用药/应用研究药物等表达。
3. family 计数扫描 uncertainty/user action 等 review-only 字段，可能产生噪声。
4. 单次 repair 只收到 response-level 第一错误，缺少逐候选完整诊断。
5. 五个 repaired candidate 均不可部分持久化或 prose salvage。

## 下一安全动作

初始化一个新的、仅离线的
`monitoring_p10_protocol_v7_visit_scope_atomicity_corrective_20260801` 切片：

1. 增加字段感知的 IP/CM 给药与 first-dose、撤回知情同意、分布式 AE/CM
   收集边界。
2. 把完整主题边界扫描与 operative action-family 分类分开；review-only 字段
   不参与 family 计数。
3. 保持 operative schedule/window 与 rescheduling 必须拆分为两个候选。
4. 单次 controlled repair 返回完整、逐候选的确定性错误。
5. provider 可见合同升级为
   `monitoring-protocol-clause-structuring-v7`，不得复用 v6。
6. 完成独立审阅列出的全量负向矩阵、聚焦监查与医学写作相邻回归。

离线 v7 通过 Codex review 前，不启动 8911/5174，不运行 RUX canary、MY009
或三个真实项目，不触碰候选决策。

## 关键证据

- Task context:
  `context/monitoring_p10_loop316_protocol_v6_visit_canary_20260801_context.md`
- Independent review:
  `runs/codex-subagent_monitoring_p10_loop316_protocol_v6_visit_canary_20260801.md`
- Codex review:
  `reviews/codex_monitoring_p10_loop316_protocol_v6_visit_canary_20260801_review.md`
- Metrics:
  `metrics/monitoring_p10_loop316_protocol_v6_visit_canary_20260801_metrics.md`
- Pre-canary backup:
  `/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/runtime/backups/pre_loop316_protocol_v6_visit_canary_20260801_0340CST/`

## 当前停止点

本细分任务已完成并无损暂停。当前文件系统与以上记录是恢复真相。下一次用户要求
继续时，从新的离线 v7 corrective 初始化开始；不要重复 v6 canary 或重做本次审阅。
