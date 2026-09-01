# Codex Main-Venue Plan: mm_r7_slice07c_three_mode_product_loop_contract_20260829

Date: 2026-08-29
Objective: 独立审阅 R7 Slice-07C 三模式产品闭环合同，挑战日常全量/增量、锁库前修订复核、核查前固定总量、特殊风险规则、后台长任务、结果发布与 R5 看板/Patient Journey 身份边界；仅评审合成范围合同，不改源码、不运行真实项目。

## Task Decomposition

1. Challenge business-mode semantics and incremental/full scope.
2. Challenge run/start/progress/result publication and long-wait recovery.
3. Challenge R5 overview/center/Journey identity and special-rule lifecycle.
4. Codex corrects the contract, resumes the same reviewer session, and owns final freeze.

## Source Packet

- v0.1 draft plus v0.2 corrective appendix.
- Accepted 07A progress, 07B flow, R6 harness and R5 authority contracts.
- Current implementation plan and Slice-07B acceptance record.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_single_object` | `codebuddy-cli` | `deepseek-v4-flash` | `runs/conference/mm_r7_slice07c_three_mode_product_loop_contract_20260829/general_single_object.md` |

## Conference Panel Coordination

- No sub-venue chair. Codex leads the assigned panel directly.

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

Round 1: CodeBuddy `deepseek-v4-flash:max`, 234.190 seconds, complete, incorporated. Same-session Round 2 is
required after v0.2; no fallback or replacement session is permitted while the recorded session is resumable.

## Codex Verification Checklist

- Verify v0.2 closes Round 1 A–J without expanding real-project scope.
- Validate conference packet, review/metrics gate, and exact source references.
- Freeze only the synthetic contract; implementation starts as a new governed execution.
