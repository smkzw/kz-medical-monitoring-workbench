# Codex Main-Venue Plan: mm_r7_slice08c3_contract_20260829

Date: 2026-08-29
Objective: 独立只读挑战并验收R7 Slice-08C-3 Patient Journey变化标记与详情抽屉最小实施合同；关闭P0-P2后才允许实现

## Task Decomposition

1. 对照冻结 08C 合同与当前 R5/R7 源码复核最小合同。
2. 由独立 participant 只读挑战身份/轴窗/变化/抽屉/可访问性与范围边界。
3. Codex 关闭 P0-P2，使用同一 session 复核；明确 ACCEPT 后才初始化实现 execution。

## Source Packet

- 见 `context/mm_r7_slice08c3_contract_20260829_conference_context.md` 的 Source Of Truth。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `codebuddy-cli` | `deepseek-v4-flash` | `runs/conference/mm_r7_slice08c3_contract_20260829/general_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Round 1：23:52–23:56 CST，deepseek-v4-flash:max，session `c3c46d39-6f84-49a2-80ef-8da3331e7a0f`，终态成功，结论 REVISE，无 fallback。
- Round 2：同一 session 未强制重读修订后的 packet，重复旧 REVISE；不作为接受依据。
- Round 3：同一 session `c3c46d39-6f84-49a2-80ef-8da3331e7a0f` 按当前磁盘重读，逐项关闭 P0/P1/P2，明确 ACCEPT。

## Codex Verification Checklist

- [x] 当前合同与权威 v0.1/v0.2 路由/源码已纳入 Source Of Truth。
- [x] Round 1 substantive P1/P2 已逐条处理；生成文件误判已澄清。
- [x] Round 3 同一 session 明确 ACCEPT。
- [ ] review/metrics、review-gate、conference validate 通过。
- [ ] 服务、浏览器、真实项目/模型保持停止。
