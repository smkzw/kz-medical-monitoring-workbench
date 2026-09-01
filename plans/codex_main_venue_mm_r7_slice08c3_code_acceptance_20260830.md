# Codex Main-Venue Plan: mm_r7_slice08c3_code_acceptance_20260830

Date: 2026-08-30
Objective: 独立审阅R7 Slice-08C-3合并后当前源码与测试，重点验证同身份同轴窗变化绑定、R7-only抽屉路由、overlay/push焦点键盘语义、中文医学标签、legacy R5隔离和离线回归；列出P0-P4并仅在P0-P2关闭后接受，视觉浏览器验收明确留08C-4

## Task Decomposition

1. 独立静态审阅冻结合同、合并源码、测试与执行证据。
2. 对同身份/同轴窗、event/risk 行集、R7-only 门禁、抽屉交互语义和 legacy 边界给出 P0-P4。
3. Codex 关闭 P0-P2 后，在同一 session 进行定向复核，直至 ACCEPT 或确认阻断。
4. Codex 独立复跑聚焦、全量 Node 测试与 Vite build；浏览器/视觉留 08C-4。

## Source Packet

- 冻结 08C-3 合同与合同接受记录。
- v0.2 连续性/视觉合同 §19–20。
- R5/R7 当前产品源码、纯函数、渲染/交互/集成测试。
- 执行审查、执行指标与当前文件系统。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `codebuddy-cli` | `deepseek-v4-flash` | `runs/conference/mm_r7_slice08c3_code_acceptance_20260830/general_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Round 1: 382.877 s，发现 P2×2；采纳并修复。
- Round 2: 同 session，确认原 P2 关闭并发现对称入口 P2×1；采纳并修复。
- Round 3: 同 session，确认全部 P0-P2 关闭，`ACCEPT`。
- 无超时、无 fallback、无新 session、无迟到输出。

## Codex Verification Checklist

- [x] 参与方输出含边界、证据、P0-P4 与可执行修复建议。
- [x] 同一 session 完成三轮审阅并给出最终 ACCEPT。
- [x] R5/R7 23/23 test files。
- [x] 医学监查全量 61/61 test files。
- [x] Vite build 1981 modules。
- [x] 视觉/ego(lite) 明确不在本切片接受范围。
