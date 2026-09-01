# Codex Main-Venue Plan: mm_r7_slice07c3_result_publication_acceptance_20260829

Date: 2026-08-29
Objective: 独立只读审阅 R7 Slice-07C-3 最终 synthetic/offline 实现：核对冻结合同、R5 typed bridge、registry v2/post-reservation manifest binding、R6 receipt/site/member 门禁、原子 finalize、progress/history/result-entry 和故障矩阵；只列可复现 P0-P2，不修改源码。

## Task Decomposition

1. 对照冻结合同静态审查 R5 bridge、registry、产品路由与测试。
2. 挑战 snapshot/manifest/receipt/site/member/finalize/result-entry 的失败关闭与恢复路径。
3. Codex 对 P2 全部作本切纠偏并独立复跑。
4. 同一独立会商 session 复审最终树，只有无 P0-P2 才接受。

## Source Packet

- 07C-3 v0.1/v0.2 冻结合同与接受记录。
- 三个执行报告、同会话纠偏报告、Codex 执行审查与测试证据。
- 当前 R5 publication bridge、R7 launch registry/product router/harness 与测试。

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `codebuddy-cli` | `deepseek-v4-flash` | `runs/conference/mm_r7_slice07c3_result_publication_acceptance_20260829/general_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

同一 CodeBuddy session `0a29ff93-44b4-4e05-9a86-355e865ec1b8` 完成两轮：Round 1 提出 6 个 P2，
Codex 全部修复；Round 2 返回 `ACCEPT`。无 fallback、超时或迟到输出。

## Codex Verification Checklist

- 核对执行/会商 provider-model 去重与 runner identity。
- Codex 复跑 7/22/179/249 门禁、compileall 和停止端口。
- 核对最终 P2 关闭后再写接受记录、运行 validate/review gate 和执行 cleanup。
