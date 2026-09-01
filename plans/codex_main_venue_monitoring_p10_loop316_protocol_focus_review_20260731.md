# Codex Main-Venue Plan: monitoring_p10_loop316_protocol_focus_review_20260731

Date: 2026-07-31
Objective: 独立审查P10方案结构证据聚焦与50条输出预算实现，确认未放宽医学门、未破坏冻结输入身份，并识别真实RUX受控重试前的阻断缺陷。

## Task Decomposition

1. Codex Luna independently audits contracts, identity boundaries, and failure modes.
2. Pi/DeepSeek independently attacks bundle closure, evidence budget, repair size, and
   test adequacy.
3. Qwen chair compares both outputs against the actual source/test packet and issues a
   retry recommendation.
4. Codex rechecks every blocking claim in current files and decides whether to repair
   or allow exactly one controlled RUX retry.

## Source Packet

- Conference context and preceding execution handoff.
- Current focus implementation and its three focused test files.
- Pause record and Codex-observed real frozen-input projection.
- No runtime database access or real provider call is delegated.

## Participant Assignments

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_codex_luna` | `codex` | `gpt-5.6-luna` | `runs/conference/monitoring_p10_loop316_protocol_focus_review_20260731/general_codex_luna.md` |
| `general_pi_deepseek_flash` | `deepseek` | `deepseek-v4-flash` | `runs/conference/monitoring_p10_loop316_protocol_focus_review_20260731/general_pi_deepseek_flash.md` |

## Sub-Venue Review

| Role | Provider | Model | Output |
|---|---|---|---|
| `general_chair_pi_qwen38` | `alibaba` | `qwen3.8-max-preview` | `runs/conference/monitoring_p10_loop316_protocol_focus_review_20260731/general_chair_pi_qwen38.md` |

## Main-Venue Review

- Codex performs the final synthesis and acceptance.
- This conference mode has no Reasonix second-review role.

## Timeout And Retry Tracking

- Start: 2026-07-31 22:12 CST.
- Each role is dispatched once and waited to terminal state with the runner hard wait.
- No latency-driven re-dispatch or fixed-interval model polling.

## Codex Verification Checklist

- Confirm participants used current files and did not edit.
- Reproduce every alleged blocker in source/tests or reject it.
- Confirm full monitoring regression remains green after any remediation.
- Preserve all v2 gates, frozen input identity, proposed-only candidate state, and
  medical-writing ownership boundary.
- Permit at most one controlled retry only after review passes.
