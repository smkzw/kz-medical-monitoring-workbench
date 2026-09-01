# Codex Main-Venue Plan: mm_r6_runtime_slice_06_acceptance_20260828

Date: 2026-08-28
Objective: Independently challenge and decide limited synthetic/offline acceptance readiness of R6 slice-06 post_lock_pre_cfdi fixed-total outputs against the frozen contract, focusing on fail-open identity, totals, nested references, immutable draft boundaries, and test adequacy.

## Task Decomposition

1. 两席独立按 frozen contract 逐项审查四输出与 8 个 Codex 已关闭缺口。
2. 各自运行最小反例 probe；区分构建期拒绝、单输出 validator 与跨输出 validator。
3. Codex 汇总不一致意见；若有可复现缺口，原会话定向复核修订，不新开席位。
4. 修订后重跑 focused/full/9-grid、review-gate、validate-conference 与 execution audit。

## Source Packet

以 conference context 的 source-of-truth 列表为准；不得读取真实项目或其他 participant 输出。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_pi_antigravity` | `google-antigravity` | `gemini-3.7-flash` | `runs/conference/mm_r6_runtime_slice_06_acceptance_20260828/general_pi_antigravity.md` |
| `general_grok46` | `grok-build` | `grok-4.6` | `runs/conference/mm_r6_runtime_slice_06_acceptance_20260828/general_grok46.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

每席 hard wait 120 分钟；仅在 terminal failure、空/截断且同会话恢复耗尽后使用声明 fallback。
记录 session id、实际 provider/model、轮次、开始/结束、fallback 和纳入状态。

## Codex Verification Checklist

- 审查每条反例能否在当前 SHA 上复现。
- 不以 worker 报告或测试数量替代代码检查。
- 如需修订，补回归测试并更新 receipt digest/count。
- 最终确认 8911/5174 停止、医学写作 aggregate 不变。
- 仅接受 synthetic/offline slice-06；明确排除产品、真实项目、医学和 Harness。
