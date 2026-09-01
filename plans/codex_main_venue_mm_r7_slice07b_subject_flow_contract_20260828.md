# Codex Main-Venue Plan: mm_r7_slice07b_subject_flow_contract_20260828

Date: 2026-08-28
Objective: 独立审阅 R7 Slice-07B 项目/中心受试者阶段流向看板合同。重点挑战阶段权威、路径守恒、四向对账、宽屏交互、中文体验、旧数据和 Journey 上下文；不得修改产品代码、启动服务或运行真实项目。

## Task Decomposition

1. 审阅阶段路径、守恒与四向对账。2. 审阅旧包/空范围/阻断三态。3. 审阅宽屏、键盘、中心范围和 Journey 往返。4. Codex 修订并独立核对当前源码。

## Source Packet

- v0.2 合同、v0.3 冻结修订、用户需求补充、阶段计划及当前 R5 源码。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `visual_single_object` | `grok-build` | `grok-4.6` | `runs/conference/mm_r7_slice07b_subject_flow_contract_20260828/visual_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

首轮 379.631 s、第二轮 151.431 s、第三轮 84.524 s；同一 session
`0ec88993-8d25-4069-b050-5f10a52c261e`，无 fallback。路由元数据随后按当前夜间清单刷新，
不改变已完成 primary 结果。

## Codex Verification Checklist

- [x] 三轮均为同一 session；[x] 无产品写入/服务/真实项目；[x] 阻断项进入 v0.2/v0.3 §9；
- [x] Codex 核对实际 R5 authority、adapter、route、页面和 CSS；[ ] 产品实现与 ego(lite) 留待下一执行包。
